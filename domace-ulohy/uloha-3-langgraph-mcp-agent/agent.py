import asyncio
import os
import sys
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from typing_extensions import TypedDict
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langchain.mcp import MCPAdapter  # beta: the import prints a LangChainBetaWarning
from fastmcp.client.group import ClientGroup
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from visualizer import visualize

load_dotenv()

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY or API_KEY == "TU JE API NA LLM ALE SOM CHUDOBNY":
    sys.exit("Najprv vlož do .env svoj Anthropic API kľúč (zatiaľ je tam len vtip).")

# Model
llm = ChatAnthropic(model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"), max_tokens=2048)

SYSTEM_PROMPT = """Si asistent e-shopu. Odpovedáš po slovensky.
Máš nástroje cez MCP:
- eshop_list_tables, eshop_run_sql - SQL databáza (SQLite): users, products, orders, order_items, reviews. Ceny sú v USD.
- eshop_search_reviews - hľadanie v texte recenzií
- eshop_calculator - všetky výpočty rob cez kalkulačku
- eshop_wikipedia_search - všeobecné informácie
Ak nepoznáš stĺpce, najprv zavolaj eshop_list_tables. Nevymýšľaj si dáta."""


# ============================================================================
# MCP CLIENT SETUP
# ============================================================================

MCP_CONFIG = {
    "mcpServers": {
        "eshop": {
            "command": sys.executable,
            "args": [str(Path(__file__).parent / "mcp_server" / "server.py")],
            "env": {"FASTMCP_LOG_LEVEL": "WARNING"},
        },
    }
}

# Tavily ako v lekcii - len ak je nastavený kľúč
if os.getenv("TAVILY_API_KEY"):
    MCP_CONFIG["mcpServers"]["tavily"] = {
        "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={os.getenv('TAVILY_API_KEY')}"
    }


async def get_mcp_tools():
    """Načíta nástroje z MCP serverov."""
    mcp = MCPAdapter(ClientGroup.from_config(MCP_CONFIG))
    tools = await mcp.list_tools()
    return tools


# Global variable to store all tools
all_tools = None


# ---------------------------
# Define the graph
# ---------------------------


# State
class State(TypedDict):
    messages: Annotated[list, add_messages]


# Node 1 ----------
def chatbot(state: State):
    llm_with_tools = llm.bind_tools(all_tools)
    messages = [SystemMessage(SYSTEM_PROMPT)] + state["messages"]
    return {"messages": [llm_with_tools.invoke(messages)]}


# Edge 1 -------------------
def route_tools(state: State) -> Literal["tools", "__end__"]:
    """Ak LLM chce zavolať nástroj, ideme do 'tools', inak koniec."""
    ai_message = state["messages"][-1]
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        for tool_call in ai_message.tool_calls:
            print(f"  -> volám nástroj {tool_call['name']} {tool_call['args']}")
        return "tools"
    return "__end__"


async def main():
    global all_tools

    print("Načítavam nástroje z MCP...")
    all_tools = await get_mcp_tools()
    print(f"Načítaných {len(all_tools)} nástrojov: {[t.name for t in all_tools]}\n")

    # Node 2 ----------
    tool_node = ToolNode(all_tools, handle_tool_errors=True)

    # Build graph
    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_conditional_edges(
        "chatbot", route_tools, {"tools": "tools", "__end__": "__end__"}
    )
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.set_entry_point("chatbot")

    # pamäť konverzácie, aby som sa mohol pýtať ďalej
    graph = graph_builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "1"}}

    visualize(graph, "graph.png")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        result = await graph.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]}, config
        )
        print("Assistant:", result["messages"][-1].text)


if __name__ == "__main__":
    asyncio.run(main())

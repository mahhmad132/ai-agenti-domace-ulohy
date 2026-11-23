import os
import sys
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

if not API_KEY or API_KEY == "TU JE API NA LLM ALE SOM CHUDOBNY":
    sys.exit("Najprv vlož do .env svoj Anthropic API kľúč (zatiaľ je tam len vtip).")

client = anthropic.Anthropic(api_key=API_KEY)


# Funkcie (nástroje), ktoré môže LLM zavolať
def calculator(operation: str, a: float, b: float):
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        result = a / b
    elif operation == "power":
        result = a**b
    else:
        return {"error": f"Neznáma operácia: {operation}"}
    return {"operation": operation, "a": a, "b": b, "result": result}


def calculate_order_price(unit_price: float, quantity: int, discount_percent: float = 0, vat_percent: float = 23):
    subtotal = unit_price * quantity
    discount = subtotal * discount_percent / 100
    without_vat = subtotal - discount
    vat = without_vat * vat_percent / 100
    total = without_vat + vat
    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "without_vat": round(without_vat, 2),
        "vat": round(vat, 2),
        "total": round(total, 2),
    }


# Popis nástrojov pre LLM
tools = [
    {
        "name": "calculator",
        "description": "Jednoduchá kalkulačka. Použi ju na každý výpočet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide", "power"],
                    "description": "Operácia, ktorú treba vykonať",
                },
                "a": {"type": "number", "description": "Prvé číslo"},
                "b": {"type": "number", "description": "Druhé číslo"},
            },
            "required": ["operation", "a", "b"],
        },
    },
    {
        "name": "calculate_order_price",
        "description": "Spočíta cenu objednávky v e-shope so zľavou a DPH.",
        "input_schema": {
            "type": "object",
            "properties": {
                "unit_price": {"type": "number", "description": "Cena za kus bez DPH v €"},
                "quantity": {"type": "integer", "description": "Počet kusov"},
                "discount_percent": {"type": "number", "description": "Zľava v %, napr. 15"},
                "vat_percent": {"type": "number", "description": "DPH v %, na Slovensku 23"},
            },
            "required": ["unit_price", "quantity"],
        },
    },
]

available_functions = {
    "calculator": calculator,
    "calculate_order_price": calculate_order_price,
}


def get_completion_from_messages(messages, model=MODEL):
    # Opakujeme, kým LLM chce volať nástroje (môže ich zavolať viac za sebou)
    while True:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system="Si asistent e-shopu. Odpovedáš po slovensky. Všetky výpočty rob cez nástroje.",
            messages=messages,
            tools=tools,
            tool_choice={"type": "auto"},
        )
        print("Stop reason:", response.stop_reason)

        if response.stop_reason != "tool_use":
            return response

        # odpoveď LLM (s tool_use) dáme do histórie
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for item in response.content:
            if item.type != "tool_use":
                continue

            function_name = item.name
            function_args = item.input
            print(f"LLM volá nástroj: {function_name}({function_args})")

            # zavoláme našu Python funkciu
            function_to_call = available_functions[function_name]
            function_response = function_to_call(**function_args)
            print("Výsledok nástroja:", function_response)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": item.id,
                    "content": json.dumps(function_response),
                }
            )

        # výsledok nástroja posielame späť LLM
        messages.append({"role": "user", "content": tool_results})


question = (
    "Zákazník kupuje 3 kusy proteínu po 29,90 € bez DPH so zľavou 15 %. "
    "Koľko zaplatí s DPH? A koľko by minul za rok, keby si to kupoval každý mesiac?"
)
if len(sys.argv) > 1:
    question = " ".join(sys.argv[1:])

messages = [{"role": "user", "content": question}]
print("Otázka:", question)

response = get_completion_from_messages(messages)
print("--- Odpoveď: ---")
print(response.content[0].text)

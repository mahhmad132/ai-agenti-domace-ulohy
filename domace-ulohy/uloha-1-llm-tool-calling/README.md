# Úloha 1 – LLM API + nástroj

Zadanie: Napíš Python skript, ktorý zavolá LLM API, použije nástroj (napr. výpočtovú funkciu) a vráti odpoveď späť LLM.

Použil som Anthropic Claude, podobne ako v lekcii `01_llm_api/02_anthropic/4_tools`.

## Ako to funguje

1. Skript pošle otázku do Claude spolu so zoznamom nástrojov (`tools`).
2. Claude vráti `stop_reason = "tool_use"` a povie, ktorý nástroj chce zavolať a s akými parametrami.
3. Skript zavolá Python funkciu.
4. Výsledok pošle späť do Claude ako `tool_result`.
5. Toto sa opakuje, kým Claude nemá všetko a nevráti normálnu odpoveď.

Nástroje:

- `calculator` – sčítanie, odčítanie, násobenie, delenie, mocnina
- `calculate_order_price` – cena objednávky so zľavou a DPH

## Spustenie

```bash
cp .env.example .env
# v .env nahraď "TU JE API NA LLM ALE SOM CHUDOBNY" svojím API kľúčom
uv run main.py
```

Vlastná otázka:

```bash
uv run main.py "Koľko je 12 na druhú krát 3?"
```

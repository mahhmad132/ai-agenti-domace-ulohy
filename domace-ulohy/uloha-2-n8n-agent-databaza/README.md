# Úloha 2 – Agent v n8n s databázou

Zadanie: Navrhni a vytvor agenta v ľubovoľnej „No code“ platforme, ktorý pracuje s databázou, používa nástroje a odpovedá na dotazy cez LLM.

Platforma: **n8n**, LLM: **Anthropic Claude**, databázy: **PostgreSQL + MongoDB** z kurzu (`03_N8N/databases`).

Workflow: [`eshop-analytik-agent.json`](eshop-analytik-agent.json)

![workflow](workflow.png)

## Čo to robí

Agent „E-shop analytik“ odpovedá v chate na otázky o e-shope. Workflow má tieto kroky:

1. **Chat – otázka** – chat trigger
2. **Priprav kontext** – pridá dnešný dátum
3. **AI Agent** – Claude + pamäť (10 správ) + nástroje:
   - `SQL dotaz Postgres` – agent si sám napíše SELECT (obalené cez `SELECT * FROM (...) LIMIT 50` ako v lekcii, takže vie iba čítať)
   - `Najdi recenzie MongoDB` – hľadanie recenzií
   - `Statistiky recenzii MongoDB` – agregácie (priemerné hodnotenie atď.)
   - `Kalkulacka`
   - `Wikipedia`
4. **Priprav záznam do logu** – Code node
5. **Ulož do logu (Postgres)** – uloží otázku a odpoveď do tabuľky `n8n_chat_log`
6. **Odpoveď do chatu**

Názvy nástrojov sú bez diakritiky, lebo n8n z nich robí názov toolu pre LLM a diakritiku mení na `_`.

## Spustenie

1. Spustiť n8n a databázy z kurzu (`docker compose up -d` v `03_N8N` a v `03_N8N/databases`).
2. V n8n: *Import from File* → `eshop-analytik-agent.json`.
3. Nastaviť credentials:
   - **Anthropic account** – API Key: ~~TU JE API NA LLM ALE SOM CHUDOBNY~~ → vlastný kľúč z console.anthropic.com
   - **Postgres account** – `host.docker.internal`, port `5433`, db `ecommerce`, `postgres` / `Heslo_1234`
   - **MongoDB account** – `mongodb://admin:admin123@host.docker.internal:27017/?authSource=admin`, db `ecommerce`
4. Open chat.

## Otázky na vyskúšanie

- Ktorých 5 produktov je najdrahších a koľko kusov máme na sklade?
- Ktorý zákazník minul najviac peňazí?
- Ktorý produkt má najlepšie hodnotenie v recenziách a koľko stojí s 23 % DPH?
- Na čo sa zákazníci sťažujú v recenziách s 2 hviezdičkami a menej?
- Predávame fitness tracker? Čo to vlastne je?

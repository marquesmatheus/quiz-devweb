# 🕹️ Quiz DevWeb 140 — Flask + JSON

Quiz divertido com 140 questões de Desenvolvimento Web:
Nginx (proxy reverso), HTML, CSS, Responsividade, JS + localStorage.

- 🌱 **100 fundamentos** (20 por tema) para reforçar a base
- 🔥 **40 avançadas** casca-grossa
- 🏁 modos: Fundamentos (100) • Avançado (40) • Maratona (140)
- Ordem das questões E das alternativas embaralhada por aluno (anti-cola)

## Rodar

```bash
pip install -r requirements.txt
python app.py
```

Abra http://127.0.0.1:5000

## Como funciona

- Aluno coloca **nome + foto** na home (`/`).
- Responde **1 questão por vez** (`/quiz`), com correção imediata (`/feedback` ✅❌ + explicação).
- Resultado final (`/resultado`) com revisão completa das 40.
- Ranking (`/ranking`) ordenado por acertos, com foto e data.

## Dados (sem banco!)

- `questions.json` — as 140 questões (100 fundamentos + 40 avançadas, letras balanceadas).
- `results.json` — ranking dos alunos: nome, foto, acertos, %, data.
- `static/uploads/` — fotos enviadas.

## Resetar ranking

Apague o conteúdo de `results.json` deixando só `[]`.

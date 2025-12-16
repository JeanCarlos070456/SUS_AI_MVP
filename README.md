# sus_ai_mvp (Streamlit)

MVP de uma “IA de Gestão Regionalizada do SUS” com:
- Chat operacional (intents simples)
- Dashboard (gráficos + tabela)
- Mapa (pontos de serviços)
- Documentos PDF (modo LOCAL) + indexação simples

## Rodar
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## PDFs (modo LOCAL)
1) Coloque PDFs em `assets/docs/`
2) Gere o índice:
```bash
python scripts/build_index.py
```
3) Abra a página **Documentos (PDF)** e use a busca.

## Trocar fontes MOCK por reais
- Edite `services/apis.py` (conexão) e `data/pipeline.py` (padronização/indicadores).

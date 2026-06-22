# 🏗️ CATALOGADOR-PDM

> Agente de **enquadramento descritivo** de materiais segundo o padrão **PDM**, operando sobre o ERP Senior Sapiens.
> Você cola uma descrição crua e fora de padrão; o agente devolve a descrição normalizada, classificada na taxonomia, com pendências e sugestões.

**Stack:** Python · Streamlit · API DeepSeek
**Tema:** navy (`#24374B` / `#26C672` / `#0094C6`)

---

## O que ele faz

A partir de uma entrada como `cabo flexivel 2,5 azul 750v`, o agente retorna:

- **Descrição enquadrada** na fórmula PDM (`NOME + MODIFICADOR + CARACTERÍSTICAS + COMPLEMENTOS + UNIDADE`), em caixa alta, sem acento, dentro de 100 caracteres.
- **Descrição curta** (≤99) para Nota Fiscal.
- **Classificação taxonômica** — Família → Subfamília → Grupo + regime descritivo (PDM / PDM-NORMA / OEM).
- **Decomposição** da descrição na fórmula mestra.
- **Informações necessárias** — quando falta um atributo obrigatório, o agente marca `‹ATRIBUTO›` na descrição e explica o que falta, por que e em que formato.
- **Análise e sugestões** de melhoria (gírias corrigidas, marca removida, risco de duplicidade).
- **Confiabilidade** do enquadramento (ALTA / MÉDIA / BAIXA).

A taxonomia completa (282 grupos, 19 famílias) e todas as regras PDM estão **embutidas no system prompt** (`system_prompt.py`). O app não depende de base externa.

---

## Estrutura do repositório

```
catalogador-pdm/
├── app.py                       # aplicação Streamlit (UI + chamada DeepSeek + parsing)
├── system_prompt.py             # system prompt com a taxonomia PDM embutida
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    ├── config.toml              # tema
    └── secrets.toml.example     # modelo da chave de API (renomeie para secrets.toml)
```

---

## Rodar localmente

### 1. Pré-requisitos
- Python 3.10+
- Uma chave da API DeepSeek (https://platform.deepseek.com)

### 2. Instalar
```bash
git clone https://github.com/SEU-USUARIO/catalogador-pdm.git
cd catalogador-pdm
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar a chave da API
Copie o exemplo e preencha:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Edite `.streamlit/secrets.toml`:
```toml
DEEPSEEK_API_KEY = "sk-sua-chave-aqui"
```
> O arquivo `secrets.toml` está no `.gitignore` e **nunca** será versionado.
> Alternativa: exportar `DEEPSEEK_API_KEY` como variável de ambiente, ou colar a chave no campo da própria interface (válido só para a sessão).

### 4. Executar
```bash
streamlit run app.py
```
Abra `http://localhost:8501`.

---

## Publicar no Streamlit Cloud

1. Suba o repositório no GitHub (sem o `secrets.toml`).
2. Acesse https://share.streamlit.io e conecte o repositório.
3. Em **App settings → Secrets**, cole:
   ```toml
   DEEPSEEK_API_KEY = "sk-sua-chave-aqui"
   ```
4. Defina `app.py` como arquivo principal e publique.

---

## Como usar

1. Cole a descrição crua no campo (ou clique num dos exemplos).
2. Clique em **Enquadrar**.
3. Leia a saída. Se houver pendências (atributos obrigatórios faltando), forneça os dados solicitados e enquadre novamente — por exemplo, reescrevendo `parafuso sextavado inox` como `parafuso sextavado inox M10x50 rosca 16unc`.

---

## Ajustes possíveis

| O que mudar | Onde |
|---|---|
| Modelo DeepSeek | `DEEPSEEK_MODEL` em `app.py` |
| Criatividade da resposta | `temperature` em `call_deepseek` (padrão 0.2 — baixo, para consistência) |
| Regras / taxonomia | `system_prompt.py` |
| Cores e tema | bloco `inject_css()` em `app.py` e `.streamlit/config.toml` |
| Limite de tokens da resposta | `max_tokens` em `call_deepseek` |

---

## Observações técnicas

- A resposta é solicitada **completa** (não-streaming) e em seguida o `app.py` faz o **parsing** dos cabeçalhos markdown (`## DESCRIÇÃO ENQUADRADA`, `## CLASSIFICAÇÃO TAXONÔMICA`, etc.) para renderizar cada bloco.
- `temperature` baixa (0.2) é proposital: catalogação exige consistência, não criatividade.
- O system prompt tem ~25 mil tokens (taxonomia embutida). Cada requisição envia esse contexto; se o volume de uso crescer muito, considere migrar para uma versão com recuperação do grupo sob demanda.

---

*CATALOGADOR-PDM · v1.0 — Governança de dados mestres*

"""
CATALOGADOR-PDM — Agente de enquadramento descritivo PDM
App Streamlit · Motor: DeepSeek · Tema navy

Fluxo: descrição crua -> system prompt (taxonomia embutida) -> DeepSeek -> parsing -> blocos visuais.
"""

import os
import re
import requests
import streamlit as st

from system_prompt import SYSTEM_PROMPT

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------------
DEEPSEEK_URL = "https://openrouter.ai/api/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek/deepseek-chat"

CORES = {
    "navy": "#24374B",
    "navy_deep": "#192737",
    "green": "#26C672",
    "teal": "#0094C6",
    "amber": "#E8943A",
    "red": "#D2544B",
}

st.set_page_config(
    page_title="CATALOGADOR-PDM",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ----------------------------------------------------------------------------
# CHAVE DE API  (Streamlit secrets  ->  variável de ambiente  ->  input manual)
# ----------------------------------------------------------------------------
def get_api_key() -> str | None:
    key = None
    try:
        key = st.secrets.get("DEEPSEEK_API_KEY")
    except Exception:
        key = None
    if not key:
        key = os.environ.get("DEEPSEEK_API_KEY")
    return key


# ----------------------------------------------------------------------------
# CHAMADA AO MODELO
# ----------------------------------------------------------------------------
def call_deepseek(api_key: str, user_text: str, temperature: float = 0.2) -> str:
    """Resposta completa (não-streaming)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        "temperature": temperature,
        "max_tokens": 1600,
        "stream": False,
    }
    resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ----------------------------------------------------------------------------
# PARSING DA RESPOSTA  (markdown estruturado -> dict de seções)
# ----------------------------------------------------------------------------
SECTION_KEYS = {
    "DESCRIÇÃO ENQUADRADA": "desc",
    "DESCRIÇÃO CURTA": "desc_curta",
    "CLASSIFICAÇÃO TAXONÔMICA": "taxo",
    "DECOMPOSIÇÃO": "decomp",
    "INFORMAÇÕES NECESSÁRIAS": "pend",
    "ENRIQUECIMENTO RECOMENDADO": "enriq",
    "ANÁLISE E SUGESTÕES": "sug",
    "CONFIABILIDADE": "conf",
}


def parse_sections(md: str) -> dict:
    """Quebra a resposta em seções pelos cabeçalhos ## do prompt."""
    sections: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in md.splitlines():
        m = re.match(r"^#{1,3}\s+(.*)", line.strip())
        if m:
            title = m.group(1).strip().upper()
            matched = None
            for needle, key in SECTION_KEYS.items():
                if needle in title:
                    matched = key
                    break
            if matched:
                if current:
                    sections[current] = "\n".join(buf).strip()
                current = matched
                buf = []
                continue
        if current:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf).strip()
    return sections


def extract_first_bold_or_line(text: str) -> str:
    """Pega a descrição enquadrada: primeiro **negrito** ou primeira linha não-vazia."""
    if not text:
        return ""
    b = re.search(r"\*\*(.+?)\*\*", text)
    if b:
        return b.group(1).strip()
    for ln in text.splitlines():
        ln = ln.strip().strip("`")
        if ln and not ln.lower().startswith("caracteres"):
            return ln
    return text.strip()


def find_char_count(text: str, total: int) -> str:
    m = re.search(rf"(\d+)\s*/\s*{total}", text or "")
    return m.group(0) if m else ""


def conf_level(text: str) -> str:
    t = (text or "").upper()
    if "ALTA" in t:
        return "high"
    if "BAIXA" in t:
        return "low"
    return "med"


# ----------------------------------------------------------------------------
# CSS — tema navy (espelha o protótipo)
# ----------------------------------------------------------------------------
def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        .stApp {{
            background:
              linear-gradient(rgba(36,55,75,.04) 1px, transparent 1px) 0 0/100% 28px,
              #EEF2F5;
        }}
        #MainMenu, footer, header[data-testid="stHeader"] {{ visibility: hidden; height:0; }}
        .block-container {{ padding-top: 1.2rem; max-width: 1180px; }}

        * {{ font-family: 'Inter', sans-serif; }}
        .mono {{ font-family: 'JetBrains Mono', monospace; }}

        /* ---- header bar ---- */
        .pdm-header {{
            background: {CORES['navy']};
            border-bottom: 3px solid {CORES['green']};
            border-radius: 14px 14px 0 0;
            padding: 16px 24px;
            display: flex; align-items: center; gap: 16px;
            margin-bottom: 0;
        }}
        .pdm-logo {{
            width: 40px; height: 40px; border-radius: 9px;
            background: linear-gradient(135deg, {CORES['green']}, {CORES['teal']});
            display: grid; place-items: center; font-weight: 800; font-size: 17px;
            color: {CORES['navy_deep']}; letter-spacing: -1px;
        }}
        .pdm-header h1 {{ color:#fff; font-size:16px; font-weight:700; margin:0; letter-spacing:.5px; }}
        .pdm-header p {{ color:#9FB4C6; font-size:11.5px; margin:0; font-weight:500; }}
        .pdm-ver {{
            margin-left:auto; font-family:'JetBrains Mono',monospace; font-size:11px;
            background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.15);
            padding:5px 12px; border-radius:20px; color:#B9CCDC;
        }}
        .pdm-ver b {{ color:{CORES['green']}; }}

        /* ---- output card ---- */
        .out-top {{
            background: linear-gradient(100deg, {CORES['navy']}, #2E4A66);
            color:#fff; padding:22px 26px; border-radius:16px 16px 0 0;
        }}
        .out-top .lbl {{ font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:1px; color:#9FD9C2; font-weight:600; }}
        .out-desc {{ font-family:'JetBrains Mono',monospace; font-size:20px; font-weight:600; line-height:1.35; margin-top:8px; word-break:break-word; }}
        .out-desc .slot {{ background:{CORES['amber']}; color:#3a2a10; padding:1px 7px; border-radius:5px; font-size:.85em; font-weight:700; }}
        .charcount {{ font-family:'JetBrains Mono',monospace; font-size:12px; color:#9FB4C6; margin-top:10px; }}
        .charcount b {{ color:#fff; }} .charcount .ok {{ color:{CORES['green']}; }}

        .blk {{ background:#fff; border:1px solid #D7E0E7; border-top:none; padding:18px 26px; }}
        .blk:last-child {{ border-radius:0 0 16px 16px; }}
        .blk-title {{
            font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:1.6px;
            text-transform:uppercase; color:#5A6B7A; font-weight:700; margin-bottom:12px;
            display:flex; align-items:center; gap:8px;
        }}
        .blk-title .dot {{ width:6px; height:6px; border-radius:50%; background:{CORES['teal']}; }}

        .taxo-wrap {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
        .node {{ font-size:13px; font-weight:600; padding:7px 13px; border-radius:9px;
                 background:#F8FAFB; border:1px solid #D7E0E7; color:{CORES['navy']}; }}
        .node .code {{ font-family:'JetBrains Mono',monospace; color:{CORES['teal']}; font-size:11.5px; margin-right:6px; }}
        .sep {{ color:#5A6B7A; font-weight:700; }}
        .regime {{ font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700; padding:6px 12px; border-radius:20px; }}
        .regime.pdm {{ background:#E7F5FF; color:{CORES['teal']}; border:1px solid #B6E2F7; }}
        .regime.norma {{ background:#E6F7EE; color:#138a4e; border:1px solid #ABE3C5; }}
        .regime.oem {{ background:#FCF1E2; color:{CORES['amber']}; border:1px solid #F0D2A8; }}

        .pend {{ background:#FCF1E2; border:1px solid #F0D2A8; border-radius:12px; padding:13px 16px; margin-bottom:10px; }}
        .pend strong {{ font-family:'JetBrains Mono',monospace; font-size:13px; color:#9a5e15; }}
        .pend p {{ font-size:13px; color:#7a5a2e; margin:4px 0 0; }}
        .ok-pill {{ display:inline-flex; align-items:center; gap:8px; font-size:13.5px; font-weight:600;
                    color:#138a4e; background:#E6F7EE; border:1px solid #ABE3C5; padding:9px 15px; border-radius:10px; }}

        .conf-meter {{ height:8px; background:#F8FAFB; border:1px solid #D7E0E7; border-radius:20px; overflow:hidden; }}
        .conf-fill {{ height:100%; border-radius:20px; }}
        .conf-fill.high {{ width:92%; background:linear-gradient(90deg, {CORES['green']}, {CORES['teal']}); }}
        .conf-fill.med  {{ width:60%; background:linear-gradient(90deg, {CORES['teal']}, #5FB5DE); }}
        .conf-fill.low  {{ width:30%; background:linear-gradient(90deg, {CORES['amber']}, #E8B45A); }}
        .conf-tag {{ font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:700; }}
        .conf-tag.high {{ color:#138a4e; }} .conf-tag.med {{ color:{CORES['teal']}; }} .conf-tag.low {{ color:{CORES['amber']}; }}

        /* input */
        .stTextArea textarea {{
            font-family:'JetBrains Mono',monospace !important; font-size:15px !important;
            border-radius:12px !important; border:1px solid #D7E0E7 !important;
        }}
        .stButton button {{
            background:{CORES['navy']} !important; color:#fff !important; font-weight:700 !important;
            border:none !important; border-radius:11px !important; padding:.55rem 1.6rem !important;
        }}
        .stButton button:hover {{ background:{CORES['navy_deep']} !important; }}
        .raw-in {{ font-family:'JetBrains Mono',monospace; font-size:14px; color:#9AA8B4;
                   text-decoration: line-through wavy {CORES['red']} 1px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# RENDERIZAÇÃO DOS BLOCOS
# ----------------------------------------------------------------------------
def render_result(sections: dict, raw_md: str):
    desc = extract_first_bold_or_line(sections.get("desc", ""))
    # marca slots <<FALTA: X>> em laranja
    desc_html = re.sub(r"<<\s*FALTA[: ]*([^>]+?)\s*>>", r'<span class="slot">‹\1›</span>', desc)

    c100 = find_char_count(sections.get("desc", ""), 100)
    c99 = find_char_count(sections.get("desc_curta", ""), 99)

    # cabeçalho da saída
    st.markdown(
        f"""
        <div class="out-top">
            <div class="lbl">▸ DESCRIÇÃO ENQUADRADA</div>
            <div class="out-desc">{desc_html or '—'}</div>
            <div class="charcount">
                {'DESCRIÇÃO: <b class="ok">'+c100+'</b>' if c100 else ''}
                {' &nbsp;·&nbsp; NF: <b>'+c99+'</b>' if c99 else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # taxonomia (renderiza o texto bruto da seção como bloco)
    taxo_raw = sections.get("taxo", "")
    regime = "pdm"
    if "PDM-NORMA" in taxo_raw.upper():
        regime = "norma"
    elif "OEM" in taxo_raw.upper():
        regime = "oem"
    taxo_html = md_lines_to_html(taxo_raw)
    st.markdown(
        f"""<div class="blk"><div class="blk-title"><span class="dot"></span>Classificação taxonômica</div>
        {taxo_html}</div>""",
        unsafe_allow_html=True,
    )

    # decomposição
    if sections.get("decomp"):
        st.markdown(
            f"""<div class="blk"><div class="blk-title"><span class="dot"></span>Decomposição · Fórmula PDM</div>
            {md_table_or_lines(sections['decomp'])}</div>""",
            unsafe_allow_html=True,
        )

    # pendências
    pend = sections.get("pend", "")
    pend_html = format_pendencies(pend)
    st.markdown(
        f"""<div class="blk"><div class="blk-title"><span class="dot"></span>Informações necessárias</div>
        {pend_html}</div>""",
        unsafe_allow_html=True,
    )

    # enriquecimento (opcional)
    if sections.get("enriq"):
        st.markdown(
            f"""<div class="blk"><div class="blk-title"><span class="dot"></span>Enriquecimento recomendado</div>
            {md_lines_to_html(sections['enriq'])}</div>""",
            unsafe_allow_html=True,
        )

    # sugestões
    if sections.get("sug"):
        st.markdown(
            f"""<div class="blk"><div class="blk-title"><span class="dot"></span>Análise e sugestões</div>
            {md_lines_to_html(sections['sug'])}</div>""",
            unsafe_allow_html=True,
        )

    # confiabilidade
    conf_txt = sections.get("conf", "")
    lvl = conf_level(conf_txt)
    label = {"high": "ALTA", "med": "MÉDIA", "low": "BAIXA"}[lvl]
    st.markdown(
        f"""<div class="blk"><div class="blk-title"><span class="dot"></span>Confiabilidade do enquadramento</div>
        <div style="display:flex;align-items:center;gap:14px">
            <div class="conf-meter" style="flex:1"><div class="conf-fill {lvl}"></div></div>
            <div class="conf-tag {lvl}">{label}</div>
        </div>
        <div style="font-size:12.5px;color:#5A6B7A;margin-top:8px">{strip_label(conf_txt)}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    with st.expander("Ver resposta completa do modelo (markdown bruto)"):
        st.code(raw_md, language="markdown")


# ----- helpers de formatação -----
def md_lines_to_html(text: str) -> str:
    out = []
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        ln = re.sub(r"^[-*•]\s*", "", ln)
        ln = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", ln)
        ln = re.sub(r"`([^`]+)`", r'<code style="background:#F8FAFB;padding:1px 6px;border-radius:4px;border:1px solid #D7E0E7;font-family:JetBrains Mono,monospace;font-size:12.5px">\1</code>', ln)
        out.append(f'<div style="font-size:13.5px;color:#1B2A38;padding:5px 0">{ln}</div>')
    return "".join(out) or '<div style="color:#5A6B7A">—</div>'


def md_table_or_lines(text: str) -> str:
    """Converte tabela markdown simples em HTML, ou cai para linhas."""
    rows = [r for r in (text or "").splitlines() if "|" in r]
    rows = [r for r in rows if not re.match(r"^\s*\|?[\s:|-]+\|?\s*$", r)]  # remove separador ---
    if len(rows) >= 2:
        html = '<table style="width:100%;border-collapse:collapse;font-size:13.5px">'
        for i, r in enumerate(rows):
            cells = [c.strip() for c in r.strip().strip("|").split("|")]
            if i == 0 and any(h.lower() in ("componente", "valor") for h in cells):
                continue  # pula cabeçalho da tabela
            if len(cells) >= 2:
                html += (
                    f'<tr><td style="padding:8px 12px;border-bottom:1px solid #D7E0E7;'
                    f'font-family:JetBrains Mono,monospace;font-size:11px;text-transform:uppercase;'
                    f'letter-spacing:.6px;color:#5A6B7A;font-weight:600;width:160px;white-space:nowrap">{cells[0]}</td>'
                    f'<td style="padding:8px 12px;border-bottom:1px solid #D7E0E7">{cells[1]}</td></tr>'
                )
        html += "</table>"
        return html
    return md_lines_to_html(text)


def format_pendencies(text: str) -> str:
    t = (text or "").strip()
    if not t or "nenhuma pend" in t.lower() or "✅" in t:
        return '<div class="ok-pill">✓ Nenhuma pendência — descrição completa para cadastro.</div>'
    items = re.split(r"\n(?=\s*[-*•⚠])", t)
    html = ""
    for it in items:
        it = it.strip()
        if not it:
            continue
        it = re.sub(r"^[\s]*[-•]\s*", "", it)  # remove bullet
        it = it.replace("⚠️", "").replace("⚠", "").strip()
        it = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", it)
        # primeira ocorrência de ATRIBUTO em maiúsculas vira destaque se não houver bold
        if "<strong>" not in it:
            it = re.sub(r"^([A-ZÇÃÕ_]{3,})\b", r"<strong>\1</strong>", it)
        it = it.replace("**", "")  # limpa marcadores órfãos
        html += f'<div class="pend">⚠ {it}</div>'
    return html or '<div class="ok-pill">✓ Nenhuma pendência.</div>'


def strip_label(text: str) -> str:
    return re.sub(r"^\s*(ALTA|MÉDIA|MEDIA|BAIXA)\s*[—\-:]*\s*", "", (text or "").strip(), flags=re.I)


# ----------------------------------------------------------------------------
# UI PRINCIPAL
# ----------------------------------------------------------------------------
def main():
    inject_css()

    st.markdown(
        """
        <div class="pdm-header">
            <div class="pdm-logo">PD</div>
            <div>
                <h1>CATALOGADOR-PDM</h1>
                <p>Enquadramento descritivo · Taxonomia PDM · ERP Senior Sapiens</p>
            </div>
            <div class="pdm-ver">DeepSeek · <b>v1.0</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    api_key = get_api_key()

    with st.container():
        st.write("")
        st.markdown(
            "##### Descrição entra crua. Sai pronta para o cadastro.",
        )

        # exemplos rápidos
        ex_cols = st.columns(4)
        examples = {
            "cabo flexivel 2,5 azul 750v": "completo",
            "parafuso sextavado inox": "falta dado",
            "grifo 12 pol gedore": "gíria + marca",
            "bota numero 42": "EPI / CA",
        }
        if "input_text" not in st.session_state:
            st.session_state.input_text = ""
        for col, (ex, tag) in zip(ex_cols, examples.items()):
            if col.button(f"{ex}\n({tag})", key=f"ex_{ex}", use_container_width=True):
                st.session_state.input_text = ex

        user_text = st.text_area(
            "Descrição do material (crua, fora de padrão)",
            value=st.session_state.input_text,
            height=90,
            placeholder="ex.: filtro de oleo p/ motor cummins  ·  disjuntor 25a curva c  ·  luva nitrilica G",
            label_visibility="collapsed",
        )

        col_run, col_temp = st.columns([1, 3])
        run = col_run.button("⚙️  Enquadrar", type="primary", use_container_width=True)

    if not api_key:
        st.warning(
            "🔑 Chave da API DeepSeek não configurada. Defina `DEEPSEEK_API_KEY` em "
            "`.streamlit/secrets.toml` (local) ou nos *Secrets* do Streamlit Cloud. "
            "Veja o README."
        )
        with st.expander("Inserir chave temporariamente (apenas nesta sessão)"):
            tmp = st.text_input("DEEPSEEK_API_KEY", type="password")
            if tmp:
                api_key = tmp

    if run:
        if not user_text.strip():
            st.error("Digite uma descrição para enquadrar.")
            return
        if not api_key:
            st.error("Configure a chave da API antes de enquadrar.")
            return
        with st.spinner("Enquadrando na taxonomia PDM…"):
            try:
                raw = call_deepseek(api_key, user_text.strip())
            except requests.HTTPError as e:
                st.error(f"Erro da API DeepSeek ({e.response.status_code}): {e.response.text[:300]}")
                return
            except Exception as e:
                st.error(f"Falha na chamada: {e}")
                return
        sections = parse_sections(raw)
        st.write("")
        render_result(sections, raw)


if __name__ == "__main__":
    main()

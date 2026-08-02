import streamlit as st
import pandas as pd
import math
import os
import glob
import html
import sqlite3
import base64
import io
import json
import unicodedata
import re
from PIL import Image

import importlib
import team_views
importlib.reload(team_views)

APP_DIR = os.path.dirname(os.path.abspath(__file__))

# O logo é opcional: sem ele o app continua funcionando normalmente.
ICONE = os.path.join(APP_DIR, "icone.png")
TEM_ICONE = os.path.isfile(ICONE)

# Configuração da Página (Comando adicionado para forçar a barra a abrir no PC)
st.set_page_config(page_title="Siga La Pelota - Banco de Dados", page_icon=ICONE if TEM_ICONE else "⚽", layout="wide", initial_sidebar_state="expanded")

# --- INJEÇÃO DE CSS BLINDADA ---
st.markdown("""
    <meta name="google" content="notranslate">
    <style>
    [data-testid="stAppViewContainer"] { background-color: #1a1d21; color: #e4e6eb; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #15181b; border-right: 1px solid #30363d; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    div[data-baseweb="input"] input, div[data-baseweb="select"] input { color: #ffffff !important; caret-color: #ffffff !important; }
    div[data-baseweb="select"] { color: #ffffff !important; }
    div[data-baseweb="popover"] li, div[data-baseweb="menu"] * { color: #ffffff !important; }
    span[data-baseweb="tag"] { background-color: #333333 !important; border: 1px solid #555555 !important; }
    span[data-baseweb="tag"] span { color: #ffffff !important; }
    h1:first-of-type { color: #FF0000 !important; }
    button[data-baseweb="tab"] {
      color: #9aa4b2 !important; font-weight: 700 !important;
      font-size: 1.55rem !important;
      line-height: 1.2 !important;
      padding-top: 0.5rem !important;
      padding-bottom: 0.5rem !important;
    }
    button[data-baseweb="tab"] p {
      font-size: 1.55rem !important;
      line-height: 1.2 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
      color: #ffffff !important; border-bottom-color: #FF0000 !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: #FF0000 !important; }
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
      padding-right: min(300px, 42vw) !important;
      align-items: center !important;
      min-height: 3.1rem !important;
    }
    .slp-tab-voltar {
      height: 0;
      position: relative;
      z-index: 60;
      pointer-events: none;
    }
    .slp-tab-voltar a {
      pointer-events: auto;
      position: absolute;
      right: 0;
      top: 0.35rem;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 0.4rem 0.85rem;
      border-radius: 6px;
      border: 1px solid #555555;
      background: #333333;
      color: #ffffff !important;
      font-weight: 700;
      font-size: 0.9rem;
      text-decoration: none !important;
      white-space: nowrap;
      box-shadow: 0 1px 4px rgba(0,0,0,0.35);
    }
    .slp-tab-voltar a:hover {
      background: #FF0000;
      border-color: #FF0000;
      color: #fff !important;
    }
    div[data-testid="stHtml"]:has(.slp-tab-voltar) {
      height: 0 !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: visible !important;
    }
    h2, h3, h4, h5, h6 { color: #ffffff !important; }
    [data-testid="stMetricLabel"] { color: #aaaaaa !important; font-size: 1.2rem !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] div { color: #ffffff !important; font-size: 3rem !important; font-weight: 900 !important; }
    .stButton>button { background-color: #333333; color: #ffffff !important; font-weight: bold; border-radius: 6px; border: 1px solid #555555; padding: 8px 16px; }
    .stButton>button:hover { background-color: #FF0000; border-color: #FF0000; }
    [data-testid="stDataFrame"] img { transform: scale(1.15); }
    .agradecimento-box { background-color: #15181b; border-left: 4px solid #FF0000; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
    /* Spinner / status de carregamento */
    [data-testid="stSpinner"] {
      text-align: center;
      padding: 1.5rem 0 0.5rem 0;
    }
    [data-testid="stSpinner"] > div {
      display: inline-flex !important;
      align-items: center;
      gap: 12px;
      background: #21262d;
      border: 1px solid #30363d;
      border-left: 4px solid #FF0000;
      border-radius: 10px;
      padding: 14px 22px;
      color: #ffffff !important;
      font-size: 1.05rem !important;
      font-weight: 700 !important;
      letter-spacing: 0.02em;
    }
    [data-testid="stSpinner"] svg,
    [data-testid="stSpinner"] img {
      width: 22px !important;
      height: 22px !important;
    }
    /* Esconde o “Running carregar_dados(...)” técnico do canto */
    [data-testid="stStatusWidget"] {
      visibility: hidden;
      height: 0;
      position: fixed;
    }
    .attr-text { font-size: 1.05rem; margin-bottom: 4px; border-bottom: 1px solid #30363d; padding-bottom: 3px; display: flex; justify-content: space-between; align-items: center; color: #e4e6eb; }
    .attr-text b { font-size: 1.15rem; font-weight: 800; }
    .pf-wrap {
      display: flex; gap: 22px; align-items: flex-start; flex-wrap: wrap;
      margin-bottom: 0; width: 100%;
    }
    .pf-foto {
      width: 220px; height: 220px; border-radius: 12px; object-fit: cover;
      border: 2px solid #FF0000; display: block; background: #0f1216; flex-shrink: 0;
    }
    .pf-main { flex: 1; min-width: 280px; }
    .pf-side { flex-shrink: 0; min-width: 200px; text-align: right; }
    .pf-nome { font-size: 2.1rem; font-weight: 800; color: #ffffff; margin: 0 0 6px 0; line-height: 1.15; }
    .pf-id { color: #9aa4b2; font-size: 0.95rem; margin: 6px 0 12px 0; }
    .pf-ratings { display: flex; gap: 20px; justify-content: flex-end; margin: 0 0 14px 0; }
    .pf-rate { display: flex; flex-direction: column; align-items: center; gap: 6px; }
    .pf-rate-lbl { font-size: 0.8rem; font-weight: 700; color: #8b949e; letter-spacing: 0.04em; }
    .pf-badge {
      display: inline-flex; align-items: center; justify-content: center;
      min-width: 64px; height: 52px; padding: 0 10px; border-radius: 8px;
      font-weight: 800; font-size: 1.65rem; color: #fff;
    }
    .pf-meta { color: #c9d1d9; font-size: 0.95rem; line-height: 1.55; margin: 0; }
    .pf-meta div { margin: 0; }
    .pf-meta b { color: #e4e6eb; }
    .pf-pos { margin: 0 0 2px 0; }
    .pf-club { color: #c9d1d9; font-size: 0.92rem; line-height: 1.45; text-align: right; }
    .pf-club b { color: #e4e6eb; }
    .pf-team-link {
      color: #58a6ff !important;
      text-decoration: none !important;
      font-weight: 700;
    }
    .pf-team-link:hover {
      color: #79b8ff !important;
      text-decoration: underline !important;
    }
    .pf-team-lines {
      color: #c9d1d9; font-size: 0.95rem; line-height: 1.55;
      text-align: right; margin: 0;
    }
    .pf-team-lines div { margin: 0; }
    .pf-team-lines b { color: #e4e6eb; font-weight: 700; }
    .pf-team-val { font-weight: 800; }
    @media (max-width: 768px) {
      .pf-wrap {
        flex-direction: column;
        align-items: center;
        gap: 14px;
        text-align: center;
      }
      .pf-foto {
        width: min(200px, 70vw);
        height: min(200px, 70vw);
        margin: 0 auto;
      }
      .pf-main {
        flex: none;
        min-width: 0;
        width: 100%;
        max-width: 420px;
        order: 2;
      }
      .pf-nome { font-size: 1.7rem; text-align: center; }
      .pf-pos { text-align: center; }
      .pf-id { text-align: center; }
      .pf-meta {
        text-align: left;
        max-width: 340px;
        margin: 0 auto;
        font-size: 0.9rem;
      }
      .pf-side {
        flex: none;
        min-width: 0;
        width: 100%;
        max-width: 420px;
        order: 3;
        margin-top: 4px;
        text-align: center;
      }
      .pf-ratings { margin-bottom: 10px; justify-content: center; }
      .pf-club { font-size: 0.9rem; text-align: center; }
    }
    .pf-card {
      background: #21262d; border: 1px solid #30363d; border-radius: 10px;
      padding: 12px 14px; margin-bottom: 10px;
    }
    .pf-card-head {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #30363d;
    }
    .pf-card-title { font-size: 1.05rem; font-weight: 700; color: #ffffff; margin: 0; }
    .pf-style {
      color: #e4e6eb; font-size: 0.95rem; padding: 5px 0;
      border-bottom: 1px solid #30363d;
    }
    .pf-style:last-child { border-bottom: 0; }
    .pf-style-empty { color: #8b949e; font-size: 0.9rem; font-style: italic; }
    .pl-pill {
      display: inline-block; padding: 1px 7px; border-radius: 4px;
      font-size: 0.72rem; font-weight: 800; margin-right: 4px; color: #fff;
    }
    .pl-badge {
      display: inline-flex; align-items: center; justify-content: center;
      min-width: 40px; height: 32px; padding: 0 6px; border-radius: 5px;
      font-weight: 800; font-size: 1.05rem; color: #fff;
    }
    .pl-badge-sm {
      display: inline-flex; align-items: center; justify-content: center;
      min-width: 32px; height: 28px; padding: 0 4px; border-radius: 4px;
      font-weight: 800; font-size: 0.9rem; color: #fff;
    }
    /* st.html injeta no DOM principal — zera margens e limita overflow da lista */
    [data-testid="stHtml"] {
      max-width: 100% !important;
      overflow-x: auto !important;
    }
    [data-testid="stHtml"] .pl-lista { display: flex; flex-direction: column; gap: 4px; }
    [data-testid="stHtml"] .pl-card,
    [data-testid="stHtml"] .pl-card * { margin-top: 0 !important; margin-bottom: 0 !important; }
    [data-testid="stHtml"] .pl-pills { margin-top: 2px !important; }
    [data-testid="stHtml"] .pl-sub,
    [data-testid="stHtml"] .pl-liga { margin-top: 2px !important; }
    /* Impede a lista de estourar a largura da página no mobile */
    [data-testid="stMainBlockContainer"],
    [data-testid="stVerticalBlock"],
    section.main {
      overflow-x: clip;
    }
    </style>
""", unsafe_allow_html=True)

# Traduz textos fixos do Streamlit (multiselect: "Select all" / "Select N matches")
st.html(
    """
<script>
(function () {
  var rootWin = window;
  try {
    if (window.parent && window.parent.document) rootWin = window.parent;
  } catch (e) {}
  if (rootWin.__slpPtUi) return;
  rootWin.__slpPtUi = true;
  var doc = rootWin.document;
  function traduzTexto(s) {
    if (!s) return null;
    var t = String(s).trim();
    if (t === "Select all") return "Selecionar tudo";
    var m = t.match(/^Select (\\d+) matches$/);
    if (m) return "Selecionar " + m[1] + " resultados";
    if (t === "No results") return "Nenhum resultado";
    m = t.match(/^Add:\\s*(.*)$/);
    if (m) return "Adicionar: " + m[1];
    m = t.match(/^You can only select up to (\\d+) options?\\. Remove an option first\\.$/);
    if (m) {
      return "Você só pode selecionar até " + m[1] + " opção(ões). Remova uma opção primeiro.";
    }
    return null;
  }
  function traduzirNo(el) {
    if (!el || el.nodeType !== 1) return;
    if (!el.children || el.children.length === 0) {
      var novo = traduzTexto(el.textContent || "");
      if (novo !== null && String(el.textContent).trim() !== novo) el.textContent = novo;
      return;
    }
    for (var i = 0; i < el.childNodes.length; i++) {
      var n = el.childNodes[i];
      if (n.nodeType === 3) {
        var nv = traduzTexto(n.nodeValue || "");
        if (nv !== null) n.nodeValue = nv;
      } else if (n.nodeType === 1) {
        traduzirNo(n);
      }
    }
  }
  var obs = new rootWin.MutationObserver(function (muts) {
    for (var i = 0; i < muts.length; i++) {
      var m = muts[i];
      if (m.type === "characterData" && m.target && m.target.parentElement) {
        traduzirNo(m.target.parentElement);
      }
      for (var j = 0; j < m.addedNodes.length; j++) {
        var n = m.addedNodes[j];
        if (n.nodeType === 1) traduzirNo(n);
      }
    }
  });
  obs.observe(doc.documentElement, {
    childList: true,
    subtree: true,
    characterData: true,
  });
  if (doc.body) traduzirNo(doc.body);
})();
</script>
""",
    unsafe_allow_javascript=True,
)

def mostrar_atributo(nome, valor):
    """Linha de atributo: nome + valor colorido (sem caixa)."""
    cor = cor_rating(valor)
    st.markdown(
        f"<div class='attr-text'><span>{html.escape(str(nome))}</span>"
        f"<b style='color:{cor}'>{valor}</b></div>",
        unsafe_allow_html=True,
    )

# --- Apoio visual da lista de jogadores ---
# Silhueta usada quando não existe foto local nem na CDN.
# Em base64 para não conflitar com as aspas do atributo onerror.
_AVATAR_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<circle cx="32" cy="32" r="32" fill="#1f242b"/>'
    '<circle cx="32" cy="25" r="11" fill="#3d444d"/>'
    '<path d="M11 60c0-12 9-19 21-19s21 7 21 19z" fill="#3d444d"/></svg>'
)
AVATAR_PADRAO = "data:image/svg+xml;base64," + base64.b64encode(_AVATAR_SVG.encode()).decode()

POS_GOLEIRO = {'GOL', 'GL', 'GK'}
POS_DEFESA = {'ZAG', 'LE', 'LD', 'ADE', 'ADD', 'CB', 'RCB', 'LCB', 'RB', 'LB', 'RWB', 'LWB', 'SW'}
POS_MEIO = {'VOL', 'MC', 'MEI', 'ME', 'MD', 'CDM', 'CM', 'CAM', 'RM', 'LM',
            'RDM', 'LDM', 'RCM', 'LCM', 'RAM', 'LAM'}
POS_ATAQUE = {'ATA', 'PE', 'PD', 'SA', 'ST', 'CF', 'RW', 'LW', 'RF', 'LF', 'RS', 'LS'}

def cor_rating(valor):
    """Cor de fundo da medalha de OVR/POT: vermelho (fraco) até verde (craque)."""
    try:
        v = int(valor)
    except (TypeError, ValueError):
        return "#6b7280"
    if v >= 90:
        return "#15803d"
    if v >= 85:
        return "#22c55e"
    if v >= 80:
        return "#84cc16"
    if v >= 75:
        return "#ca8a04"
    if v >= 70:
        return "#E07600"
    if v >= 65:
        return "#ea580c"
    if v >= 60:
        return "#e04f32"
    return "#C92E22"

def cor_posicao(pos):
    p = str(pos).strip().upper()
    if p == "SUB":
        return "#222c36"
    if p in ("RES", "RESERVA"):
        return "#1e2226"
    if p in POS_GOLEIRO:
        return "#C92E22"
    if p in POS_DEFESA:
        return "#E07600"
    if p in POS_MEIO:
        return "#598C11"
    if p in POS_ATAQUE:
        return "#2856BE"
    return "#94a3b8"


# Rótulos PT para posições da formação / escalação
POS_FORMACAO_PT = {
    "GK": "GOL", "SW": "ZAG",
    "CB": "ZAG", "RCB": "ZAG", "LCB": "ZAG",
    "RB": "LD", "LB": "LE", "RWB": "ADD", "LWB": "ADE",
    "CDM": "VOL", "RDM": "VOL", "LDM": "VOL",
    "CM": "MC", "RCM": "MC", "LCM": "MC",
    "CAM": "MEI", "RAM": "MEI", "LAM": "MEI",
    "RM": "MD", "LM": "ME",
    "RW": "PD", "LW": "PE", "RF": "PD", "LF": "PE",
    "CF": "SA", "ST": "ATA", "RS": "ATA", "LS": "ATA",
    "SUB": "SUB", "RES": "RES",
}


def rotulo_pos_formacao(pos):
    p = str(pos or "").strip().upper()
    if not p:
        return "—"
    return POS_FORMACAO_PT.get(p, p)

def pills_posicoes(jogador):
    """Pills coloridas com a posição principal e as secundárias."""
    posicoes = []
    for coluna in ['Position', 'Position2', 'Position3', 'Position4']:
        valor = str(jogador.get(coluna, '') or '').strip()
        if valor and valor.lower() not in ('nan', 'none') and valor not in posicoes:
            posicoes.append(valor)
    return "".join(
        f"<span class='pl-pill' style='background:{cor_posicao(p)}'>{html.escape(p)}</span>"
        for p in posicoes
    )

def badge_rating(valor, titulo=None, pequeno=False, grande=False):
    """Medalha colorida (rótulo fica no cabeçalho da lista / perfil)."""
    if grande:
        cls = "pf-badge"
    elif pequeno:
        cls = "pl-badge-sm"
    else:
        cls = "pl-badge"
    tip = f" title=\"{html.escape(titulo)}\"" if titulo else ""
    return f"<span class='{cls}'{tip} style='background:{cor_rating(valor)}'>{valor}</span>"

def estrelas_fintas(valor):
    """skillmoves no DB é 0-4; na UI mostra 1-5⭐."""
    try:
        v = int(valor)
    except (TypeError, ValueError):
        v = 0
    return max(1, min(5, v + 1))

MESES_PT = (
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
)

# Letras que não decompõem bem só com NFKD (nórdicas, eslavas, etc.)
_NORM_CHAR_MAP = str.maketrans({
    "Ø": "O", "ø": "o",
    "Ð": "D", "ð": "d",
    "Þ": "Th", "þ": "th",
    "Ł": "L", "ł": "l",
    "Æ": "AE", "æ": "ae",
    "Œ": "OE", "œ": "oe",
    "ß": "ss",
    "Đ": "D", "đ": "d",
    "Ħ": "H", "ħ": "h",
    "ı": "i",
    "İ": "I",
})

def normalizar_texto(texto):
    """Remove acentos/diacríticos e normaliza letras especiais (Ø→O, etc.). Sempre case-insensitive."""
    if texto is None:
        return ""
    s = str(texto).translate(_NORM_CHAR_MAP)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # casefold é mais forte que lower() (ex.: ß→ss) e cobre ANDRE/andre/André
    return s.casefold().lower()

def formatar_data_pt(valor):
    """ISO / datetime → 'Jan 11, 2025'. Vazio se inválido."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    texto = str(valor).strip()
    if not texto or texto.lower() in ("nan", "none", "nat", ""):
        return ""
    try:
        dt = pd.to_datetime(valor)
        if pd.isna(dt):
            return ""
        return f"{MESES_PT[dt.month - 1]} {dt.day}, {dt.year}"
    except Exception:
        return ""

def esta_emprestado(jog):
    try:
        if int(jog.get("is_on_loan", 0) or 0) == 1:
            return True
    except (TypeError, ValueError):
        pass
    return bool(str(jog.get("loaned_from_teamname", "") or "").strip())

def _tid_valido(tid):
    try:
        n = int(tid or 0)
    except (TypeError, ValueError):
        return 0
    return n if n > 0 else 0

def link_nome_time(nome, tid, estado_ui="", from_pid=None):
    """Nome do time como link para o perfil (?tid=), se houver ID válido."""
    tid_i = _tid_valido(tid)
    nome_txt = nome_time_exibicao(tid_i, nome) if tid_i else str(nome or "").strip()
    if nome_txt in ("", "nan", "None", "Sem Clube"):
        return html.escape(nome_txt or "Sem Clube")
    # FREE_AGENT_TEAM_IDS definido mais abaixo no módulo; resolvido em tempo de chamada.
    if tid_i <= 0 or tid_i in FREE_AGENT_TEAM_IDS:
        return html.escape(nome_txt)
    estado = html.escape(estado_ui or "")
    s_param = f"&s={estado}" if estado else ""
    from_param = ""
    pid_i = _tid_valido(from_pid)
    if pid_i > 0:
        from_param = f"&from_pid={pid_i}"
    href = f"?modo=times&tid={tid_i}{from_param}{s_param}"
    # Navega na janela principal (não abre aba nova; st.markdown forçaria target=_blank)
    return (
        f'<a class="pf-team-link" href="{html.escape(href)}" target="_self" '
        f'onclick="event.preventDefault();event.stopPropagation();'
        f'(function(h){{try{{var w=(window.parent&&window.parent!==window)?window.parent:window;'
        f'w.location.href=h;}}catch(e){{window.location.href=h;}}}})'
        f'(this.getAttribute(\'href\'));return false;">'
        f"{html.escape(nome_txt)}</a>"
    )

# FC 26/27 bitmasks (peditor022-N) with nomes oficiais em português.
PLAYSTYLE_TRAIT1 = (
    ("Chute colocado", 1),       # Finesse Shot
    ("Cavadinha", 2),            # Chip Shot
    ("Pombo sem asas", 4),       # Power Shot
    ("Bola parada", 8),          # Dead Ball
    ("Cabeceio Preciso", 16),    # Precision Header
    ("Acrobata", 32),            # Acrobatic
    ("Chute Direto Rasteiro", 64),  # Low Driven Shot
    ("Vanguarda", 128),          # Gamechanger
    ("Passe direto", 256),       # Incisive Pass
    ("Passe guiado", 512),       # Pinged Pass
    ("Passe longo", 1024),       # Long Ball Pass
    ("Tiki-taka", 2048),         # Tiki Taka
    ("Passe de GPS", 4096),      # Whipped Pass
    ("Criativo", 8192),          # Inventive
    ("Cercar", 16384),           # Jockey
    ("Barreira", 32768),         # Block
    ("Interceptação", 65536),    # Intercept
    ("Antecipação", 131072),     # Anticipate
    ("Carrinho limpo", 262144),  # Slide Tackle
    ("Força Aérea", 524288),     # Aerial Fortress
    ("Técnica", 1048576),        # Technical
    ("Veloz", 2097152),          # Rapid
    ("Domínio", 4194304),        # First Touch
    ("Malvadeza", 8388608),      # Trickster
    ("Cabeça fria", 16777216),   # Press Proven
    ("Pé de vento", 33554432),   # Quick Step
    ("Incansável", 67108864),    # Relentless
    ("Lateral longo", 134217728),  # Long Throw
    ("Xerife", 268435456),       # Bruiser
    ("Dominância", 536870912),   # Enforcer
)
PLAYSTYLE_TRAIT2 = (
    ("Arremesso longo", 1),   # Far Throw
    ("Usa os pés", 2),        # Footwork
    ("Saída aérea", 4),       # Cross Claimer
    ("Sai que é sua", 8),     # Rush Out
    ("Braço elástico", 16),   # Far Reach
    ("Deflector", 32),        # Deflector
    # Bits 64+ = Career Mode traits (não entram em Estilos de Jogo).
)

def estilos_de_jogo(jogador):
    """Decode base and plus PlayStyles; plus styles are suffixed with '+'."""
    def inteiro(coluna):
        try:
            return int(jogador.get(coluna, 0) or 0)
        except (TypeError, ValueError):
            return 0

    def decodificar(mask1, mask2):
        nomes = [nome for nome, bit in PLAYSTYLE_TRAIT1 if mask1 & bit]
        nomes.extend(nome for nome, bit in PLAYSTYLE_TRAIT2 if mask2 & bit)
        return nomes

    base = decodificar(inteiro("trait1"), inteiro("trait2"))
    plus = decodificar(inteiro("icontrait1"), inteiro("icontrait2"))
    # A plus mask upgrades the corresponding base style: show it once with "+".
    resultado = [nome for nome in base if nome not in plus]
    resultado.extend(f"{nome} +" for nome in plus)
    return resultado

def card_estilos(jogador):
    estilos = estilos_de_jogo(jogador)
    conteudo = (
        "".join(f"<div class='pf-style'>{html.escape(nome)}</div>" for nome in estilos)
        if estilos else "<div class='pf-style-empty'>Nenhum estilo de jogo</div>"
    )
    st.markdown(
        f"<div class='pf-card'><div class='pf-card-head'>"
        f"<span class='pf-card-title'>Estilos de Jogo</span></div>{conteudo}</div>",
        unsafe_allow_html=True,
    )

def card_categoria(titulo, media, atributos):
    """Card de categoria com badge de média + atributos com valor colorido."""
    badge = badge_rating(media, titulo)
    linhas = "".join(
        f"<div class='attr-text'><span>{html.escape(n)}</span>"
        f"<b style='color:{cor_rating(v)}'>{v}</b></div>"
        for n, v in atributos
    )
    st.markdown(
        f"<div class='pf-card'>"
        f"<div class='pf-card-head'><span class='pf-card-title'>{html.escape(titulo)}</span>{badge}</div>"
        f"{linhas}</div>",
        unsafe_allow_html=True,
    )

SORT_LABELS = {
    "playername": "Nome",
    "overallrating": "OVR",
    "potential": "POT",
    "teamname": "Time",
    "Ofensivo": "Ofe",
    "Habilidade": "Hab",
    "Movimentação": "Mov",
    "Força": "For",
    "Mentalidade": "Men",
    "Defesa": "Def",
}
SORT_DEFAULT_ASC = {"playername", "teamname"}
SORT_HEADER_KEYS = [
    "playername", "overallrating", "potential", "teamname",
    "Ofensivo", "Habilidade", "Movimentação", "Força", "Mentalidade", "Defesa",
]

# Chaves de UI que precisam sobreviver à navegação por URL (abrir perfil)
ESTADO_UI_KEYS = (
    "busca_nome",
    "filtro_regiao",
    "filtro_nacionalidade",
    "filtro_clube",
    "filtro_liga",
    "filtro_posicao",
    "filtro_face_real",
    "filtro_genero",
    "filtro_pe",
    "filtro_fintas",
    "filtro_emprestimo",
    "lista_pagina",
    "lista_pagina_retorno",
    "lista_pagina_times",
    "sort_col",
    "sort_asc",
    "banco_dados",
    "modo_app",
    "busca_time",
    "filtro_regiao_time",
    "filtro_liga_time",
    "filtro_genero_time",
    "jogador_retorno",
    "time_retorno",
)

def serializar_estado_ui():
    """Empacota filtros/ordenação para levar na URL ao abrir um perfil."""
    data = {}
    for key in ESTADO_UI_KEYS:
        if key not in st.session_state:
            continue
        val = st.session_state[key]
        if hasattr(val, "item"):
            try:
                val = val.item()
            except Exception:
                pass
        if isinstance(val, (list, tuple)):
            val = [str(x) if not isinstance(x, (str, int, float, bool, type(None))) else x for x in val]
        data[key] = val
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=str)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")

def restaurar_estado_ui(token):
    """Restaura filtros a partir do token da URL (antes dos widgets)."""
    if not token:
        return
    try:
        pad = "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(token + pad)
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return
    if not isinstance(data, dict):
        return
    for key, val in data.items():
        if key in ESTADO_UI_KEYS:
            st.session_state[key] = val

def rotulo_ordenacao(coluna):
    base = SORT_LABELS[coluna]
    if st.session_state.get("sort_col") != coluna:
        return base
    return f"{base} {'↑' if st.session_state.sort_asc else '↓'}"

def alternar_ordenacao(coluna):
    if st.session_state.get("sort_col") == coluna:
        st.session_state.sort_asc = not st.session_state.sort_asc
    else:
        st.session_state.sort_col = coluna
        st.session_state.sort_asc = coluna in SORT_DEFAULT_ASC

# Chaves de navegação na URL (histórico do browser)
_NAV_QUERY_KEYS = (
    "modo",
    "pid",
    "tid",
    "from_pid",
    "page",
    "sort",
    "asc",
    "voltar",
    "s",
)

def _query_nav_signature():
    parts = []
    for key in _NAV_QUERY_KEYS:
        if key in st.query_params:
            parts.append(f"{key}={st.query_params.get(key)}")
    return "&".join(parts)

def build_nav_query_dict():
    """Estado atual → query params estáveis (para back/forward)."""
    d = {}
    modo = st.session_state.get("modo_app") or "Jogadores"
    if modo == "Times":
        d["modo"] = "times"
        d["page"] = str(max(1, int(st.session_state.get("lista_pagina_times") or 1)))
        tid = st.session_state.get("time_selecionado")
        if tid is not None and str(tid).strip() not in ("", "None"):
            d["tid"] = str(tid)
            from_pid = st.session_state.get("jogador_retorno")
            if from_pid is not None and str(from_pid).strip() not in ("", "None"):
                d["from_pid"] = str(from_pid)
    else:
        d["modo"] = "jogadores"
        d["page"] = str(max(1, int(st.session_state.get("lista_pagina") or 1)))
        pid = st.session_state.get("jogador_selecionado")
        if pid is not None and str(pid).strip() not in ("", "None"):
            d["pid"] = str(pid)
            tid_ret = st.session_state.get("time_retorno")
            if tid_ret is not None and str(tid_ret).strip() not in ("", "None"):
                d["tid"] = str(tid_ret)
        else:
            d["sort"] = str(st.session_state.get("sort_col") or "overallrating")
            d["asc"] = "1" if st.session_state.get("sort_asc") else "0"
    return d

def sincronizar_url_navegacao():
    """Alinha a URL ao estado (replace). Não empilha histórico se já estiver igual."""
    desired = build_nav_query_dict()
    current = {}
    for key in ("modo", "pid", "tid", "from_pid", "page", "sort", "asc"):
        if key in st.query_params:
            current[key] = str(st.query_params.get(key))
    if current == desired:
        st.session_state._nav_url_sig = _query_nav_signature()
        return
    try:
        st.query_params.from_dict(desired)
    except Exception:
        for key in list(st.query_params.keys()):
            if key in _NAV_QUERY_KEYS:
                try:
                    del st.query_params[key]
                except Exception:
                    pass
        for key, val in desired.items():
            st.query_params[key] = val
    st.session_state._nav_url_sig = _query_nav_signature()

def href_navegacao_voltar(acao):
    """Destino real do Voltar (URL estável, não ação consumível)."""
    estado = serializar_estado_ui()
    s_q = f"&s={estado}" if estado else ""
    if acao == "lista_jogadores":
        page = st.session_state.get("lista_pagina_retorno") or st.session_state.get(
            "lista_pagina", 1
        )
        sort = st.session_state.get("sort_col") or "overallrating"
        asc = "1" if st.session_state.get("sort_asc") else "0"
        return f"?modo=jogadores&page={int(page)}&sort={sort}&asc={asc}{s_q}"
    if acao == "ao_time":
        tid = st.session_state.get("time_retorno")
        page = st.session_state.get("lista_pagina_times") or 1
        return f"?modo=times&tid={tid}&page={int(page)}{s_q}"
    if acao == "ao_jogador":
        pid = st.session_state.get("jogador_retorno")
        page = st.session_state.get("lista_pagina") or 1
        return f"?modo=jogadores&pid={pid}&page={int(page)}{s_q}"
    if acao == "lista_times":
        page = st.session_state.get("lista_pagina_times") or 1
        return f"?modo=times&page={int(page)}{s_q}"
    return f"?{s_q.lstrip('&')}" if s_q else "?"

def processar_query_params():
    """
    Aplica navegação da URL → session.
    Só reaplica quando a URL de navegação muda (back/forward / links),
    para não sobrescrever troca de aba feita pelos widgets.
    """
    had_s = "s" in st.query_params
    if had_s:
        restaurar_estado_ui(st.query_params.get("s"))
        try:
            del st.query_params["s"]
        except Exception:
            pass

    had_voltar = "voltar" in st.query_params
    if had_voltar:
        acao = str(st.query_params.get("voltar") or "").strip()
        try:
            del st.query_params["voltar"]
        except Exception:
            pass
        if acao == "lista_times":
            st.session_state.time_selecionado = None
            st.session_state.jogador_selecionado = None
            st.session_state.time_retorno = None
            st.session_state.jogador_retorno = None
            st.session_state.modo_app = "Times"
        elif acao == "ao_time":
            tid_ret = st.session_state.get("time_retorno")
            st.session_state.jogador_selecionado = None
            if tid_ret:
                st.session_state.time_selecionado = str(tid_ret)
            st.session_state.time_retorno = None
            st.session_state.jogador_retorno = None
            st.session_state.modo_app = "Times"
        elif acao == "ao_jogador":
            pid_ret = st.session_state.get("jogador_retorno")
            st.session_state.time_selecionado = None
            st.session_state.jogador_retorno = None
            if pid_ret:
                st.session_state.jogador_selecionado = str(pid_ret)
            st.session_state.modo_app = "Jogadores"
        elif acao == "lista_jogadores":
            st.session_state.jogador_selecionado = None
            st.session_state.time_retorno = None
            st.session_state.jogador_retorno = None
            st.session_state.modo_app = "Jogadores"
            retorno = st.session_state.get("lista_pagina_retorno")
            if retorno is not None:
                try:
                    st.session_state.lista_pagina = max(1, int(retorno))
                except (TypeError, ValueError):
                    pass
        sincronizar_url_navegacao()
        return

    sig = _query_nav_signature()
    if not had_s and st.session_state.get("_nav_url_sig") == sig:
        return
    st.session_state._nav_url_sig = sig

    modo_q = str(st.query_params.get("modo", "") or "").strip().lower()
    if modo_q in ("times", "time"):
        st.session_state.modo_app = "Times"
    elif modo_q in ("jogadores", "jogador", "players"):
        st.session_state.modo_app = "Jogadores"

    has_pid = "pid" in st.query_params and str(
        st.query_params.get("pid") or ""
    ).strip() not in ("", "None")
    has_tid = "tid" in st.query_params and str(
        st.query_params.get("tid") or ""
    ).strip() not in ("", "None")

    if "page" in st.query_params:
        try:
            pagina = max(1, int(st.query_params.get("page")))
            if st.session_state.get("modo_app") == "Times" or (
                has_tid and not has_pid
            ):
                st.session_state.lista_pagina_times = pagina
            if st.session_state.get("modo_app") != "Times" or has_pid:
                st.session_state.lista_pagina = pagina
                st.session_state.lista_pagina_retorno = pagina
        except (TypeError, ValueError):
            pass

    if "sort" in st.query_params:
        coluna = st.query_params.get("sort")
        if coluna in SORT_LABELS:
            st.session_state.sort_col = coluna
            st.session_state.sort_asc = str(st.query_params.get("asc", "0")) == "1"

    if has_pid:
        try:
            st.session_state.jogador_selecionado = str(int(st.query_params.get("pid")))
            tid_ret = None
            if has_tid:
                try:
                    tid_ret = str(int(st.query_params.get("tid")))
                except (TypeError, ValueError):
                    tid_ret = None
            st.session_state.time_retorno = tid_ret
            st.session_state.time_selecionado = None
            st.session_state.jogador_retorno = None
            st.session_state.modo_app = "Jogadores"
            st.session_state.lista_pagina_retorno = st.session_state.get(
                "lista_pagina", 1
            )
        except (TypeError, ValueError):
            pass
    elif has_tid:
        try:
            pid_ret = None
            if "from_pid" in st.query_params:
                try:
                    pid_ret = str(int(st.query_params.get("from_pid")))
                except (TypeError, ValueError):
                    pid_ret = None
            st.session_state.time_selecionado = str(int(st.query_params.get("tid")))
            st.session_state.jogador_selecionado = None
            st.session_state.time_retorno = None
            st.session_state.jogador_retorno = pid_ret
            st.session_state.modo_app = "Times"
        except (TypeError, ValueError):
            pass
    else:
        if st.session_state.get("modo_app") == "Times":
            st.session_state.time_selecionado = None
            st.session_state.jogador_retorno = None
        else:
            st.session_state.jogador_selecionado = None
            st.session_state.time_retorno = None

def exibir_time(jog, filtro_times=None):
    """
    Retorna (nome_exibido, tooltip, liga_exibida, teamid_crest) para a coluna Time.
    - Padrão: clube; tooltip "Clube - Seleção" se houver seleção.
    - Se o filtro incluir a seleção do jogador: mostra a seleção;
      tooltip "Seleção - Clube".
    """
    filtro_times = filtro_times or []
    club = str(jog.get("teamname", "") or "").strip()
    nation = str(jog.get("nationteamname", "") or "").strip()
    league = str(jog.get("leaguename", "") or "").strip()
    nation_league = str(jog.get("nationleaguename", "") or "").strip()

    if club in ("nan", "None"):
        club = ""
    if nation in ("nan", "None"):
        nation = ""
    club_ok = club and club != "Sem Clube"

    def _tid(val):
        try:
            return int(val or 0)
        except (TypeError, ValueError):
            return 0

    filter_on_nation = bool(filtro_times and nation and nation in filtro_times)

    if filter_on_nation and nation:
        primary = nation
        tip = f"{nation} - {club}" if club_ok else nation
        sub = nation_league
        crest_tid = _tid(jog.get("nationteamid"))
    elif club_ok:
        primary = club
        tip = f"{club} - {nation}" if nation else club
        sub = league
        crest_tid = _tid(jog.get("teamid"))
    elif nation:
        primary = nation
        tip = nation
        sub = nation_league
        crest_tid = _tid(jog.get("nationteamid"))
    else:
        primary = "Sem Clube"
        tip = primary
        sub = ""
        crest_tid = 0

    return primary, tip, sub, crest_tid

def _html_celula_time(time_nome, time_tip, time_liga, crest_tid=0):
    """Célula Time: brasão à esquerda + nome/liga (sem caixa no brasão)."""
    liga_html = (
        f'<div class="pl-liga">{html.escape(time_liga)}</div>'
        if time_liga else ""
    )
    crest_html = ""
    if crest_tid > 0:
        crest = obter_crest_tabela(crest_tid)
        if crest:
            crest_html = (
                f'<img class="pl-crest" src="{crest}" alt="" '
                f'onerror="this.style.display=\'none\'">'
            )
    return (
        f'<div class="pl-time" title="{html.escape(time_tip)}">'
        f"{crest_html}"
        f'<div class="pl-time-txt">'
        f'<div class="pl-clube">{html.escape(time_nome)}</div>'
        f"{liga_html}"
        f"</div></div>"
    )

def _query_ordenacao(coluna):
    """Query string para ordenar por coluna (alterna se já ativa)."""
    if st.session_state.get("sort_col") == coluna:
        asc = 0 if st.session_state.sort_asc else 1
    else:
        asc = 1 if coluna in SORT_DEFAULT_ASC else 0
    page = int(st.session_state.get("lista_pagina") or 1)
    return f"modo=jogadores&sort={coluna}&asc={asc}&page={page}"

def _itens_paginacao(pagina, total_paginas, proximas=3):
    """
    Números para a barra: página atual, próximas, … e última.
    Perto do fim, completa a janela com páginas anteriores.
    Retorna lista de int | '…'.
    """
    total_paginas = max(1, int(total_paginas))
    pagina = max(1, min(int(pagina), total_paginas))
    if total_paginas <= proximas + 2:
        return list(range(1, total_paginas + 1))

    inicio = pagina
    fim = min(total_paginas, pagina + proximas)
    faltam = (proximas + 1) - (fim - inicio + 1)
    if faltam > 0:
        inicio = max(1, inicio - faltam)

    itens = list(range(inicio, fim + 1))
    if fim < total_paginas - 1:
        itens.append("…")
    if fim < total_paginas:
        itens.append(total_paginas)
    return itens

def html_lista_jogadores(df_pagina, filtro_times=None, pagina=1, total_paginas=1):
    """Cabeçalho + linhas na MESMA CSS grid — colunas alinhadas de verdade."""
    filtro_times = filtro_times or []
    pagina = max(1, int(pagina or 1))
    total_paginas = max(1, int(total_paginas or 1))
    pagina = min(pagina, total_paginas)

    head_cells = ['<div class="pl-h-spacer"></div>']
    for coluna in SORT_HEADER_KEYS:
        ativo = " pl-h-active" if st.session_state.get("sort_col") == coluna else ""
        nome_cls = " pl-h-nome" if coluna == "playername" else ""
        head_cells.append(
            f'<div class="pl-h{ativo}{nome_cls}" data-q="{_query_ordenacao(coluna)}">'
            f"{html.escape(rotulo_ordenacao(coluna))}</div>"
        )
    header = (
        f'<div class="pl-grid pl-head">{"".join(head_cells)}</div>'
    )

    rows = []
    for _, jog in df_pagina.iterrows():
        pid = int(jog["playerid"])
        foto = obter_miniface_tabela(pid, jog.get("gender", 0))
        time_nome, time_tip, time_liga, crest_tid = exibir_time(jog, filtro_times)
        tem_selecao = int(jog.get("has_national_team", 0) or 0) == 1 or bool(
            str(jog.get("nationteamname", "") or "").strip()
        )
        globe = " · 🌎" if tem_selecao else ""
        loan = " · ↔️" if esta_emprestado(jog) else ""

        rows.append(
            f'<div class="pl-grid pl-card" title="Abrir perfil" '
            f'data-q="modo=jogadores&pid={pid}&page={pagina}">'
            f'<img class="pl-foto" src="{foto}" '
            f"onerror=\"this.onerror=null;this.src='{AVATAR_PADRAO}'\">"
            f'<div class="pl-info">'
            f'<div class="pl-nome">{html.escape(str(jog["playername"]))}</div>'
            f'<div class="pl-pills">{pills_posicoes(jog)}</div>'
            f'<div class="pl-sub">{html.escape(str(jog["nationality"]))}'
            f' · {jog["Idade"]} anos{loan}{globe} · ID {pid}</div>'
            f"</div>"
            f'<div class="pl-c">{badge_rating(jog["overallrating"], "Geral")}</div>'
            f'<div class="pl-c">{badge_rating(jog["potential"], "Potencial")}</div>'
            f"{_html_celula_time(time_nome, time_tip, time_liga, crest_tid)}"
            f'<div class="pl-c">{badge_rating(jog["Ofensivo"], "Ofensivo", True)}</div>'
            f'<div class="pl-c">{badge_rating(jog["Habilidade"], "Habilidade", True)}</div>'
            f'<div class="pl-c">{badge_rating(jog["Movimentação"], "Movimentação", True)}</div>'
            f'<div class="pl-c">{badge_rating(jog["Força"], "Força", True)}</div>'
            f'<div class="pl-c">{badge_rating(jog["Mentalidade"], "Mentalidade", True)}</div>'
            f'<div class="pl-c">{badge_rating(jog["Defesa"], "Defesa", True)}</div>'
            f"</div>"
        )

    css = """
    .pl-scroll {
      width: 100%;
      max-width: 100%;
      overflow-x: auto;
      overflow-y: visible;
      -webkit-overflow-scrolling: touch;
      overscroll-behavior-x: contain;
    }
    .pl-lista {
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 920px;
      width: max(100%, 920px);
      box-sizing: border-box;
    }
    .pl-grid {
      display: grid;
      grid-template-columns: 48px minmax(160px, 2.2fr) 40px 40px minmax(150px, 1.5fr) repeat(6, 32px);
      column-gap: 10px;
      align-items: center;
      width: 100%;
      min-width: 920px;
      padding: 5px 10px;
      box-sizing: border-box;
    }
    .pl-head {
      border-bottom: 1px solid #30363d;
      margin: 0 0 2px 0 !important;
      padding-bottom: 6px !important;
      background: transparent !important;
    }
    .pl-h {
      color: #8b949e; font-size: 0.7rem; font-weight: 700;
      letter-spacing: 0.05em; text-align: center; justify-self: center;
      padding: 2px 0; white-space: nowrap; cursor: pointer; user-select: none;
      margin: 0 !important;
    }
    .pl-h:hover { color: #ffffff; }
    .pl-h-active { color: #ffffff; }
    .pl-h-nome { justify-self: start; text-align: left; }
    .pl-h-spacer { width: 48px; height: 1px; }
    .pl-card {
      background: #21262d !important;
      border: 1px solid #30363d !important;
      border-radius: 8px !important;
      margin: 0 !important;
      cursor: pointer;
      transition: background .12s, border-color .12s;
    }
    .pl-card:hover { background: #2a3038 !important; border-color: #484f58 !important; }
    .pl-foto {
      width: 44px; height: 44px; border-radius: 50%; object-fit: cover;
      border: 2px solid #30363d; background: #0f1216; display: block;
    }
    .pl-info { min-width: 0; }
    .pl-nome { font-size: 1rem; font-weight: 700; color: #fff; line-height: 1.15; margin: 0 !important; }
    .pl-pills { margin-top: 2px !important; }
    .pl-sub { font-size: 0.68rem; color: #9aa4b2; margin: 1px 0 0 0 !important; line-height: 1.2; }
    .pl-time {
      min-width: 0;
      display: grid;
      grid-template-columns: 28px 1fr 28px;
      align-items: center;
      column-gap: 6px;
      text-align: center;
      padding-left: 20px;
      box-sizing: border-box;
    }
    .pl-crest {
      width: 28px; height: 28px;
      object-fit: contain;
      justify-self: start;
      border: none; background: transparent; border-radius: 0;
      display: block;
    }
    .pl-time-txt { min-width: 0; text-align: center; }
    .pl-clube {
      font-size: 0.82rem; font-weight: 600; color: #e4e6eb; text-align: center;
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap; line-height: 1.2;
      margin: 0 !important;
    }
    .pl-liga {
      font-size: 0.62rem; color: #9aa4b2; text-align: center; margin: 1px 0 0 0 !important;
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap; line-height: 1.15;
    }
    .pl-grid > * { min-width: 0; margin: 0 !important; }
    .pl-c { display: flex; justify-content: center; align-items: center; }
    .pl-pill {
      display: inline-block; padding: 1px 6px; border-radius: 4px;
      font-size: 0.62rem; font-weight: 800; margin-right: 3px; color: #fff;
      line-height: 1.35;
    }
    .pl-badge {
      display: inline-flex; align-items: center; justify-content: center;
      min-width: 34px; height: 26px; padding: 0 4px; border-radius: 4px;
      font-weight: 800; font-size: 0.9rem; color: #fff;
    }
    .pl-badge-sm {
      display: inline-flex; align-items: center; justify-content: center;
      min-width: 26px; height: 24px; padding: 0 2px; border-radius: 4px;
      font-weight: 800; font-size: 0.75rem; color: #fff;
    }
    .pl-pager {
      display: flex; justify-content: center; align-items: center; flex-wrap: wrap;
      gap: 6px; margin: 16px 0 8px 0; padding: 4px 0; user-select: none;
    }
    .pl-page {
      display: inline-flex; align-items: center; justify-content: center;
      min-width: 36px; height: 36px; padding: 0 10px; border-radius: 8px;
      border: 1px solid #30363d; background: #21262d; color: #e4e6eb;
      font-size: 0.9rem; font-weight: 700; cursor: pointer;
      transition: background .12s, border-color .12s, color .12s;
    }
    .pl-page:hover { background: #2a3038; border-color: #484f58; color: #fff; }
    .pl-page-active {
      background: #FF0000 !important; border-color: #FF0000 !important; color: #fff !important;
      cursor: default;
    }
    .pl-page-disabled {
      opacity: 0.35; cursor: default; pointer-events: none;
    }
    .pl-page-ellipsis {
      min-width: 28px; border: none; background: transparent; color: #8b949e;
      cursor: default; pointer-events: none; font-weight: 800;
    }
    .pl-page-arrow { font-size: 1.05rem; min-width: 40px; }
    .pl-pager-meta {
      width: 100%; text-align: center; color: #8b949e; font-size: 0.78rem;
      margin-top: 2px;
    }
    .pl-pager-goto {
      display: inline-flex; align-items: center; gap: 6px;
      margin-left: 8px; color: #8b949e; font-size: 0.82rem; font-weight: 600;
    }
    .pl-page-input {
      width: 64px; height: 36px; box-sizing: border-box;
      border-radius: 8px; border: 1px solid #30363d; background: #0f1216;
      color: #ffffff; font-size: 0.9rem; font-weight: 700; text-align: center;
      outline: none; padding: 0 6px;
    }
    .pl-page-input:focus { border-color: #FF0000; }
    .pl-page-go {
      min-width: 40px; height: 36px; padding: 0 12px; border-radius: 8px;
      border: 1px solid #30363d; background: #21262d; color: #e4e6eb;
      font-size: 0.85rem; font-weight: 700; cursor: pointer;
    }
    .pl-page-go:hover { background: #2a3038; border-color: #484f58; color: #fff; }
    """

    # Paginação: ←  atual … próximas  …  última  →  [ir para]
    prev_dis = " pl-page-disabled" if pagina <= 1 else ""
    next_dis = " pl-page-disabled" if pagina >= total_paginas else ""
    pager_parts = [
        f'<div class="pl-page pl-page-arrow{prev_dis}" data-q="modo=jogadores&page={pagina - 1}" '
        f'title="Anterior" aria-label="Página anterior">‹</div>',
    ]
    for item in _itens_paginacao(pagina, total_paginas):
        if item == "…":
            pager_parts.append('<div class="pl-page pl-page-ellipsis">…</div>')
            continue
        ativo = " pl-page-active" if item == pagina else ""
        pager_parts.append(
            f'<div class="pl-page{ativo}" data-q="modo=jogadores&page={item}">{item}</div>'
        )
    pager_parts.append(
        f'<div class="pl-page pl-page-arrow{next_dis}" data-q="modo=jogadores&page={pagina + 1}" '
        f'title="Próxima" aria-label="Próxima página">›</div>'
    )
    pager_parts.append(
        f'<label class="pl-pager-goto">Ir para '
        f'<input class="pl-page-input" type="number" min="1" max="{total_paginas}" '
        f'value="{pagina}" inputmode="numeric" aria-label="Número da página">'
        f'<button type="button" class="pl-page-go" title="Ir para a página">Ir</button>'
        f"</label>"
    )
    pager = (
        f'<div class="pl-pager">{"".join(pager_parts)}'
        f'<div class="pl-pager-meta">Página {pagina} de {total_paginas}</div></div>'
    )

    script = f"""
    <script>
    (function () {{
      var SLP_UI_STATE = {json.dumps(serializar_estado_ui())};
      function rootWin() {{
        try {{
          if (window.parent && window.parent !== window && window.parent.document) {{
            return window.parent;
          }}
        }} catch (e) {{}}
        return window;
      }}
      function scrollEl(win) {{
        var doc = win.document;
        var list = [
          doc.querySelector('[data-testid="stMain"]'),
          doc.querySelector('section.main'),
          doc.querySelector('.main'),
          doc.scrollingElement,
          doc.documentElement,
          doc.body
        ];
        var best = null;
        var bestOverflow = 0;
        for (var i = 0; i < list.length; i++) {{
          var el = list[i];
          if (!el) continue;
          var overflow = (el.scrollHeight || 0) - (el.clientHeight || 0);
          if (overflow > bestOverflow) {{
            bestOverflow = overflow;
            best = el;
          }}
        }}
        return best || doc.scrollingElement || doc.documentElement;
      }}
      function getScrollY(win) {{
        var el = scrollEl(win);
        var top = el && el.scrollTop ? el.scrollTop : 0;
        return Math.max(top, win.scrollY || 0, win.pageYOffset || 0);
      }}
      function setScrollY(win, y) {{
        var el = scrollEl(win);
        if (el) el.scrollTop = y;
        try {{ win.scrollTo(0, y); }} catch (e) {{}}
        try {{
          if (win.document.documentElement) win.document.documentElement.scrollTop = y;
          if (win.document.body) win.document.body.scrollTop = y;
        }} catch (e2) {{}}
      }}
      function go(q, keepScroll) {{
        var root = rootWin();
        try {{
          if (keepScroll) {{
            root.sessionStorage.setItem('slp_scroll_y', String(getScrollY(root)));
            root.sessionStorage.setItem('slp_restore_list', '1');
            var params = new URLSearchParams(q);
            var pid = params.get('pid');
            var page = params.get('page');
            if (pid) root.sessionStorage.setItem('slp_scroll_pid', String(pid));
            if (page) root.sessionStorage.setItem('slp_lista_pagina', String(page));
          }} else {{
            root.sessionStorage.setItem('slp_scroll_y', '0');
            root.sessionStorage.removeItem('slp_restore_list');
            root.sessionStorage.removeItem('slp_scroll_pid');
          }}
        }} catch (e) {{}}
        var u = new URL(root.location.href);
        ['pid','tid','from_pid','page','sort','asc','s','modo','voltar'].forEach(function (k) {{
          u.searchParams.delete(k);
        }});
        var incoming = new URLSearchParams(q);
        incoming.forEach(function (v, k) {{ u.searchParams.set(k, v); }});
        if (!incoming.has('modo')) {{
          if (incoming.has('pid')) u.searchParams.set('modo', 'jogadores');
          else if (incoming.has('tid')) u.searchParams.set('modo', 'times');
          else u.searchParams.set('modo', 'jogadores');
        }}
        if (typeof SLP_UI_STATE === 'string' && SLP_UI_STATE) {{
          u.searchParams.set('s', SLP_UI_STATE);
        }}
        root.location.href = u.pathname + '?' + u.searchParams.toString();
      }}
      function goFromInput() {{
        var inp = document.querySelector('.pl-pager .pl-page-input');
        if (!inp) return;
        var max = parseInt(inp.getAttribute('max'), 10) || 1;
        var n = parseInt(inp.value, 10);
        if (isNaN(n)) return;
        if (n < 1) n = 1;
        if (n > max) n = max;
        go('modo=jogadores&page=' + n, false);
      }}
      function restaurarPosicao() {{
        var root = rootWin();
        var y = null;
        var pid = null;
        try {{
          if (root.sessionStorage.getItem('slp_restore_list') !== '1') return false;
          y = root.sessionStorage.getItem('slp_scroll_y');
          pid = root.sessionStorage.getItem('slp_scroll_pid');
        }} catch (e) {{ return false; }}
        var pos = parseInt(y || '0', 10);
        var done = false;
        if (pid) {{
          var card = document.querySelector('.pl-lista [data-q*="pid=' + pid + '"]');
          if (card) {{
            try {{
              card.scrollIntoView({{ block: 'center', behavior: 'auto' }});
              done = true;
            }} catch (e2) {{}}
          }}
        }}
        if (!done && !isNaN(pos) && pos > 0) {{
          setScrollY(root, pos);
          done = true;
        }}
        return done;
      }}
      function limparRestore() {{
        var root = rootWin();
        try {{
          root.sessionStorage.removeItem('slp_scroll_y');
          root.sessionStorage.removeItem('slp_restore_list');
          root.sessionStorage.removeItem('slp_scroll_pid');
        }} catch (e) {{}}
      }}
      document.querySelectorAll('.pl-lista [data-q]').forEach(function (el) {{
        el.addEventListener('click', function (ev) {{
          ev.preventDefault();
          ev.stopPropagation();
          var q = el.getAttribute('data-q');
          if (q) go(q, true);
        }});
      }});
      document.querySelectorAll('.pl-pager [data-q]').forEach(function (el) {{
        el.addEventListener('click', function (ev) {{
          ev.preventDefault();
          ev.stopPropagation();
          if (el.classList.contains('pl-page-disabled') || el.classList.contains('pl-page-active')) return;
          var q = el.getAttribute('data-q');
          if (q) go(q, false);
        }});
      }});
      var gotoBtn = document.querySelector('.pl-pager .pl-page-go');
      var gotoInp = document.querySelector('.pl-pager .pl-page-input');
      if (gotoBtn) {{
        gotoBtn.addEventListener('click', function (ev) {{
          ev.preventDefault();
          ev.stopPropagation();
          goFromInput();
        }});
      }}
      if (gotoInp) {{
        gotoInp.addEventListener('keydown', function (ev) {{
          if (ev.key === 'Enter') {{
            ev.preventDefault();
            ev.stopPropagation();
            goFromInput();
          }}
        }});
        gotoInp.addEventListener('click', function (ev) {{ ev.stopPropagation(); }});
      }}
      // Streamlit pode resetar o scroll após o rerun — tenta várias vezes.
      try {{
        var root = rootWin();
        if (root.sessionStorage.getItem('slp_restore_list') === '1') {{
          var tries = 0;
          function tick() {{
            restaurarPosicao();
            tries += 1;
            if (tries < 30) {{
              setTimeout(tick, 50);
            }} else {{
              limparRestore();
            }}
          }}
          requestAnimationFrame(tick);
          setTimeout(tick, 0);
        }}
      }} catch (e) {{}}
    }})();
    </script>
    """

    return (
        f"<style>{css}</style>"
        f'<div class="pl-scroll"><div class="pl-lista">{header}{"".join(rows)}</div></div>'
        f"{pager}"
        f"{script}"
    )


def html_lista_elenco(elenco, players_by_id, obter_foto_fn, estado_ui="", team_id=None):
    """Lista do elenco no mesmo layout da aba Jogadores, com # e posição da formação."""
    head_cells = [
        '<div class="pl-h pl-h-num">#</div>',
        '<div class="pl-h pl-h-pos">Pos</div>',
        '<div class="pl-h-spacer"></div>',
        '<div class="pl-h pl-h-nome">Nome</div>',
    ]
    for coluna in SORT_HEADER_KEYS[1:]:  # sem playername (já em Nome); sem ordenação
        head_cells.append(
            f'<div class="pl-h">{html.escape(SORT_LABELS[coluna])}</div>'
        )
    header = f'<div class="el-grid el-head">{"".join(head_cells)}</div>'

    grupo_labels = {
        "Reserva": "Banco de Reservas",
        "Elenco": "Reservas",
    }

    rows = []
    grupo_atual = None
    for item in elenco:
        grupo = item.get("grupo") or ""
        # Sem separador para titulares (Starting XI)
        if grupo != grupo_atual:
            grupo_atual = grupo
            rotulo = grupo_labels.get(grupo)
            if rotulo:
                rows.append(
                    f'<div class="el-sep"><span class="el-sep-label">'
                    f"{html.escape(rotulo)}</span></div>"
                )

        pid = int(item.get("playerid") or 0)
        jog = players_by_id.get(pid)
        jersey = int(item.get("jersey") or 0)
        pos_raw = str(item.get("pos") or "").strip().upper()
        pos_lbl = rotulo_pos_formacao(pos_raw)
        pos_cor = cor_posicao(pos_raw if pos_raw in ("SUB", "RES") else pos_lbl)

        if jog is not None:
            nome = str(jog.get("playername") or item.get("name") or f"ID {pid}")
            nat = str(jog.get("nationality") or "")
            idade = jog.get("Idade", "")
            ovr = jog.get("overallrating", item.get("ovr", 0))
            pot = jog.get("potential", item.get("pot", 0))
            foto = obter_foto_fn(pid, jog.get("gender", 0)) or AVATAR_PADRAO
            time_nome, time_tip, time_liga, crest_tid = exibir_time(jog, None)
            tem_selecao = int(jog.get("has_national_team", 0) or 0) == 1 or bool(
                str(jog.get("nationteamname", "") or "").strip()
            )
            globe = " · 🌎" if tem_selecao else ""
            loan = " · ↔️" if esta_emprestado(jog) else ""
            ofe = jog.get("Ofensivo", 0)
            hab = jog.get("Habilidade", 0)
            mov = jog.get("Movimentação", 0)
            forc = jog.get("Força", 0)
            men = jog.get("Mentalidade", 0)
            defe = jog.get("Defesa", 0)
            pills = pills_posicoes(jog)
        else:
            nome = str(item.get("name") or f"ID {pid}")
            nat, idade = "", ""
            ovr = item.get("ovr", 0)
            pot = item.get("pot", 0)
            foto = AVATAR_PADRAO
            time_nome, time_tip, time_liga, crest_tid = "—", "", "", 0
            globe = loan = ""
            ofe = hab = mov = forc = men = defe = 0
            pills = ""

        num_txt = str(jersey) if jersey > 0 else "—"
        sub_bits = []
        if nat:
            sub_bits.append(html.escape(nat))
        if idade != "" and idade is not None:
            sub_bits.append(f"{idade} anos")
        if loan.strip():
            sub_bits.append(loan.strip(" ·"))
        if globe.strip():
            sub_bits.append(globe.strip(" ·"))
        sub_bits.append(f"ID {pid}")
        sub_line = " · ".join(sub_bits)

        q_pid = f"modo=jogadores&pid={pid}"
        if team_id is not None:
            q_pid += f"&tid={int(team_id)}"

        rows.append(
            f'<div class="el-grid pl-card" title="Abrir perfil" data-q="{q_pid}">'
            f'<div class="el-num">{html.escape(num_txt)}</div>'
            f'<div class="el-pos"><span class="pl-pill" style="background:{pos_cor}">'
            f"{html.escape(pos_lbl)}</span></div>"
            f'<img class="pl-foto" src="{foto}" '
            f"onerror=\"this.onerror=null;this.src='{AVATAR_PADRAO}'\">"
            f'<div class="pl-info">'
            f'<div class="pl-nome">{html.escape(nome)}</div>'
            f'<div class="pl-pills">{pills}</div>'
            f'<div class="pl-sub">{sub_line}</div>'
            f"</div>"
            f'<div class="pl-c">{badge_rating(ovr, "Geral")}</div>'
            f'<div class="pl-c">{badge_rating(pot, "Potencial")}</div>'
            f"{_html_celula_time(time_nome, time_tip, time_liga, crest_tid)}"
            f'<div class="pl-c">{badge_rating(ofe, "Ofensivo", True)}</div>'
            f'<div class="pl-c">{badge_rating(hab, "Habilidade", True)}</div>'
            f'<div class="pl-c">{badge_rating(mov, "Movimentação", True)}</div>'
            f'<div class="pl-c">{badge_rating(forc, "Força", True)}</div>'
            f'<div class="pl-c">{badge_rating(men, "Mentalidade", True)}</div>'
            f'<div class="pl-c">{badge_rating(defe, "Defesa", True)}</div>'
            f"</div>"
        )

    css = """
    .el-scroll { width:100%; overflow-x:auto; -webkit-overflow-scrolling:touch; }
    .el-lista {
      display:flex; flex-direction:column; gap:4px;
      min-width:980px; width:max(100%,980px); box-sizing:border-box;
    }
    .el-grid {
      display:grid;
      grid-template-columns: 36px 44px 48px minmax(160px,2.2fr) 40px 40px minmax(150px,1.5fr) repeat(6,32px);
      column-gap:10px; align-items:center; width:100%; min-width:980px;
      padding:5px 10px; box-sizing:border-box;
    }
    .el-head {
      border-bottom:1px solid #30363d; margin:0 0 2px 0 !important;
      padding-bottom:6px !important; background:transparent !important;
    }
    .el-num {
      font-size:0.85rem; font-weight:800; color:#e4e6eb; text-align:center;
    }
    .el-pos { display:flex; justify-content:center; align-items:center; }
    .el-pos .pl-pill { margin-right:0; min-width:2.4em; text-align:center; }
    .pl-h-num, .pl-h-pos { justify-self:center; text-align:center; }
    .el-sep {
      display:flex; align-items:center; gap:12px;
      margin:10px 0 4px 0; padding:0 4px;
      width:100%; min-width:980px; box-sizing:border-box;
    }
    .el-sep::before, .el-sep::after {
      content:""; flex:1; height:1px; background:#30363d;
    }
    .el-sep-label {
      color:#c9d1d9; font-size:0.78rem; font-weight:800;
      letter-spacing:0.06em; text-transform:uppercase; white-space:nowrap;
    }
    """
    # Reusa estilos da lista de jogadores (já injetados na página em geral via lista,
    # mas o elenco pode abrir sem ela — inclui o essencial).
    css += """
    .pl-card {
      background:#21262d !important; border:1px solid #30363d !important;
      border-radius:8px !important; margin:0 !important; cursor:pointer;
      transition:background .12s, border-color .12s;
    }
    .pl-card:hover { background:#2a3038 !important; border-color:#484f58 !important; }
    .pl-foto {
      width:44px; height:44px; border-radius:50%; object-fit:cover;
      border:2px solid #30363d; background:#0f1216; display:block;
    }
    .pl-info { min-width:0; }
    .pl-nome { font-size:1rem; font-weight:700; color:#fff; line-height:1.15; margin:0 !important; }
    .pl-pills { margin-top:2px !important; }
    .pl-sub { font-size:0.68rem; color:#9aa4b2; margin:1px 0 0 0 !important; line-height:1.2; }
    .pl-time {
      min-width:0; display:grid; grid-template-columns:28px 1fr 28px;
      align-items:center; column-gap:6px; text-align:center;
      padding-left:20px; box-sizing:border-box;
    }
    .pl-crest {
      width:28px; height:28px; object-fit:contain; justify-self:start;
      border:none; background:transparent; border-radius:0; display:block;
    }
    .pl-time-txt { min-width:0; text-align:center; }
    .pl-clube {
      font-size:0.82rem; font-weight:600; color:#e4e6eb; text-align:center;
      overflow:hidden; text-overflow:ellipsis; white-space:nowrap; line-height:1.2; margin:0 !important;
    }
    .pl-liga {
      font-size:0.62rem; color:#9aa4b2; text-align:center; margin:1px 0 0 0 !important;
      overflow:hidden; text-overflow:ellipsis; white-space:nowrap; line-height:1.15;
    }
    .el-grid > * { min-width:0; margin:0 !important; }
    .pl-c { display:flex; justify-content:center; align-items:center; }
    .pl-h {
      color:#8b949e; font-size:0.7rem; font-weight:700; letter-spacing:0.05em;
      text-align:center; justify-self:center; padding:2px 0; white-space:nowrap; margin:0 !important;
    }
    .pl-h-nome { justify-self:start; text-align:left; }
    .pl-h-spacer { width:48px; height:1px; }
    .pl-pill {
      display:inline-block; padding:1px 6px; border-radius:4px;
      font-size:0.62rem; font-weight:800; margin-right:3px; color:#fff; line-height:1.35;
    }
    .pl-badge {
      display:inline-flex; align-items:center; justify-content:center;
      min-width:34px; height:26px; padding:0 4px; border-radius:4px;
      font-weight:800; font-size:0.9rem; color:#fff;
    }
    .pl-badge-sm {
      display:inline-flex; align-items:center; justify-content:center;
      min-width:26px; height:24px; padding:0 2px; border-radius:4px;
      font-weight:800; font-size:0.75rem; color:#fff;
    }
    """
    estado_js = json.dumps(estado_ui if estado_ui is not None else "")
    script = f"""
    <script>
    (function(){{
      var SLP_UI_STATE = {estado_js};
      function rootWin(){{
        try {{ if (window.parent && window.parent!==window) return window.parent; }} catch(e){{}}
        return window;
      }}
      function go(q){{
        var root = rootWin();
        var u = new URL(root.location.href);
        ['pid','tid','from_pid','page','sort','asc','s','modo','voltar'].forEach(function(k){{
          u.searchParams.delete(k);
        }});
        var incoming = new URLSearchParams(q);
        incoming.forEach(function(v,k){{ u.searchParams.set(k,v); }});
        if (!incoming.has('modo')) {{
          if (incoming.has('pid')) u.searchParams.set('modo', 'jogadores');
          else if (incoming.has('tid')) u.searchParams.set('modo', 'times');
          else u.searchParams.set('modo', 'jogadores');
        }}
        if (typeof SLP_UI_STATE === 'string' && SLP_UI_STATE) u.searchParams.set('s', SLP_UI_STATE);
        root.location.href = u.pathname + '?' + u.searchParams.toString();
      }}
      document.querySelectorAll('.el-lista [data-q]').forEach(function(el){{
        el.addEventListener('click', function(ev){{
          ev.preventDefault(); ev.stopPropagation();
          var q = el.getAttribute('data-q');
          if (q) go(q);
        }});
      }});
    }})();
    </script>
    """
    return (
        f"<style>{css}</style>"
        f'<div class="el-scroll"><div class="el-lista">{header}{"".join(rows)}</div></div>'
        f"{script}"
    )


def render_lista_jogadores(df_pagina, filtro_times=None, pagina=1, total_paginas=1):
    """Renderiza cabeçalho + lista na mesma grid; cliques na mesma aba."""
    st.html(
        html_lista_jogadores(
            df_pagina, filtro_times, pagina=pagina, total_paginas=total_paginas
        ),
        unsafe_allow_javascript=True,
    )

# Ligas / times que não aparecem na lista / filtros.
# Jogadores só ligados a esses times (sem seleção) são ocultados do app.
HIDDEN_LEAGUE_IDS = frozenset({383, 384, 2240, 2255})
HIDDEN_TEAM_IDS = frozenset({114019})
# Agentes livres (liga 382): não listar como time; jogadores ficam visíveis
# e mantêm vínculo com seleção. Sem link de clube no perfil.
FREE_AGENT_TEAM_IDS = frozenset({111592, 131368})  # Passes Livres / Passes Livres Fem.
# Nomes forçados (o squad às vezes usa o mesmo rótulo para M/F).
TEAM_DISPLAY_NAMES = {
    131368: "Passes Livres Fem.",
}

def nome_time_exibicao(tid, nome=""):
    """Aplica override de nome por teamid, se houver."""
    try:
        tid_i = int(tid or 0)
    except (TypeError, ValueError):
        tid_i = 0
    if tid_i in TEAM_DISPLAY_NAMES:
        return TEAM_DISPLAY_NAMES[tid_i]
    return str(nome or "").strip()

# Nacionalidades (IDs de tables.json) → nomes em português
DICT_PAISES = {
    "1": "Albânia", "2": "Andorra", "3": "Armênia", "4": "Áustria", "5": "Azerbaijão",
    "6": "Bielorrússia", "7": "Bélgica", "8": "Bósnia e Herzegovina", "9": "Bulgária",
    "10": "Croácia", "11": "Chipre", "12": "República Tcheca", "13": "Dinamarca",
    "14": "Inglaterra", "15": "Montenegro", "16": "Ilhas Faroé", "17": "Finlândia",
    "18": "França", "19": "Macedônia do Norte", "20": "Geórgia", "21": "Alemanha",
    "22": "Grécia", "23": "Hungria", "24": "Islândia", "25": "República da Irlanda",
    "26": "Israel", "27": "Itália", "28": "Letônia", "29": "Liechtenstein",
    "30": "Lituânia", "31": "Luxemburgo", "32": "Malta", "33": "Moldávia",
    "34": "Holanda", "35": "Irlanda do Norte", "36": "Noruega", "37": "Polônia",
    "38": "Portugal", "39": "Romênia", "40": "Rússia", "41": "San Marino",
    "42": "Escócia", "43": "Eslováquia", "44": "Eslovênia", "45": "Espanha",
    "46": "Suécia", "47": "Suíça", "48": "Turquia", "49": "Ucrânia",
    "50": "País de Gales", "51": "Sérvia",
    "52": "Argentina", "53": "Bolívia", "54": "Brasil", "55": "Chile",
    "56": "Colômbia", "57": "Equador", "58": "Paraguai", "59": "Peru",
    "60": "Uruguai", "61": "Venezuela",
    "62": "Anguilla", "63": "Antígua e Barbuda", "64": "Aruba", "65": "Bahamas",
    "66": "Barbados", "67": "Belize", "68": "Bermudas", "69": "Ilhas Virgens Britânicas",
    "70": "Canadá", "71": "Ilhas Cayman", "72": "Costa Rica", "73": "Cuba",
    "74": "Dominica", "75": "Internacional", "76": "El Salvador", "77": "Granada",
    "78": "Guatemala", "79": "Guiana", "80": "Haiti", "81": "Honduras",
    "82": "Jamaica", "83": "México", "84": "Montserrat", "85": "Curaçao",
    "86": "Nicarágua", "87": "Panamá", "88": "Porto Rico", "89": "São Cristóvão e Névis",
    "90": "Santa Lúcia", "91": "São Vicente e Granadinas", "92": "Suriname",
    "93": "Trinidad e Tobago", "94": "Ilhas Turks e Caicos", "95": "Estados Unidos",
    "96": "Ilhas Virgens Americanas",
    "97": "Argélia", "98": "Angola", "99": "Benim", "100": "Botsuana",
    "101": "Burkina Faso", "102": "Burundi", "103": "Camarões", "104": "Cabo Verde",
    "105": "República Centro-Africana", "106": "Chade", "107": "Congo",
    "108": "Costa do Marfim", "109": "Djibuti", "110": "Congo RD", "111": "Egito",
    "112": "Guiné Equatorial", "113": "Eritreia", "114": "Etiópia", "115": "Gabão",
    "116": "Gâmbia", "117": "Gana", "118": "Guiné", "119": "Guiné-Bissau",
    "120": "Quênia", "121": "Lesoto", "122": "Libéria", "123": "Líbia",
    "124": "Madagascar", "125": "Malawi", "126": "Mali", "127": "Mauritânia",
    "128": "Maurício", "129": "Marrocos", "130": "Moçambique", "131": "Namíbia",
    "132": "Níger", "133": "Nigéria", "134": "Ruanda", "135": "São Tomé e Príncipe",
    "136": "Senegal", "137": "Seicheles", "138": "Serra Leoa", "139": "Somália",
    "140": "África do Sul", "141": "Sudão", "142": "Essuatíni", "143": "Tanzânia",
    "144": "Togo", "145": "Tunísia", "146": "Uganda", "147": "Zâmbia", "148": "Zimbábue",
    "149": "Afeganistão", "150": "Bahrein", "151": "Bangladesh", "152": "Butão",
    "153": "Brunei", "154": "Camboja", "155": "China", "157": "Guam",
    "158": "Hong Kong", "159": "Índia", "160": "Indonésia", "161": "Irã",
    "162": "Iraque", "163": "Japão", "164": "Jordânia", "165": "Cazaquistão",
    "166": "Coreia do Norte", "167": "Coreia do Sul", "168": "Kuwait",
    "169": "Quirguistão", "170": "Laos", "171": "Líbano", "172": "Macau",
    "173": "Malásia", "174": "Maldivas", "175": "Mongólia", "176": "Mianmar",
    "177": "Nepal", "178": "Omã", "179": "Paquistão", "180": "Palestina",
    "181": "Filipinas", "182": "Catar", "183": "Arábia Saudita", "184": "Singapura",
    "185": "Sri Lanka", "186": "Síria", "187": "Tajiquistão", "188": "Tailândia",
    "189": "Turcomenistão", "190": "Emirados Árabes Unidos", "191": "Uzbequistão",
    "192": "Vietnã", "193": "Iêmen",
    "194": "Samoa Americana", "195": "Austrália", "196": "Ilhas Cook", "197": "Fiji",
    "198": "Nova Zelândia", "199": "Papua Nova Guiné", "200": "Samoa",
    "201": "Ilhas Salomão", "202": "Taiti", "203": "Tonga", "204": "Vanuatu",
    "205": "Gibraltar", "206": "Groenlândia", "207": "República Dominicana",
    "208": "Estônia", "209": "Jogadores Criados", "210": "Agentes Livres",
    "211": "Resto do Mundo", "212": "Timor-Leste", "213": "Taipei Chinês",
    "214": "Comores", "215": "Nova Caledônia", "218": "Sudão do Sul",
    "219": "Kosovo", "222": "Internacional Feminino", "225": "CONMEBOL",
}

# Regiões → IDs de nacionalidade (agrupamento FIFA/EA de tables.json)
_REGIAO_IDS = {
    "América do Sul": [str(i) for i in range(52, 62)],
    "América do Norte": (
        [str(i) for i in range(62, 97) if i != 75] + ["206", "207"]
    ),
    "Europa": (
        [str(i) for i in range(1, 52)] + ["205", "208", "219"]
    ),
    "Ásia": (
        [str(i) for i in range(149, 194) if i != 156] + ["212", "213"]
    ),
    "Oceania": (
        [str(i) for i in range(194, 205)] + ["215"]
    ),
    "África": (
        [str(i) for i in range(97, 149)] + ["214", "218"]
    ),
}
OPCOES_REGIAO = list(_REGIAO_IDS.keys())
REGIAO_PAISES = {
    regiao: {DICT_PAISES[cid] for cid in ids if cid in DICT_PAISES}
    for regiao, ids in _REGIAO_IDS.items()
}

def _tabelas_auxiliares(conn):
    """Carrega teams / leagues / links se existirem no SQLite."""
    tables = {
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    out = {}
    for name in ("teams", "leagues", "leagueteamlinks", "teamplayerlinks"):
        if name in tables:
            out[name] = pd.read_sql_query(f"SELECT * FROM {name}", conn)
        else:
            out[name] = None
    return out

def _ids_times_ocultos(aux):
    """teamid (int) e teamname dos times ocultos (por liga ou teamid explícito)."""
    ltl = aux.get("leagueteamlinks")
    teams = aux.get("teams")
    hidden_ids = set(HIDDEN_TEAM_IDS)
    hidden_names = set()

    if ltl is not None and "teamid" in ltl.columns and "leagueid" in ltl.columns:
        ltl = ltl.copy()
        ltl["_tid"] = pd.to_numeric(ltl["teamid"], errors="coerce")
        ltl["_lid"] = pd.to_numeric(ltl["leagueid"], errors="coerce")
        hidden_ids.update(
            ltl.loc[ltl["_lid"].isin(HIDDEN_LEAGUE_IDS), "_tid"]
            .dropna()
            .astype(int)
            .tolist()
        )

    if teams is not None and "teamid" in teams.columns and "teamname" in teams.columns:
        teams = teams.copy()
        teams["_tid"] = pd.to_numeric(teams["teamid"], errors="coerce")
        for _, row in teams.iterrows():
            try:
                tid = int(row["_tid"])
            except (TypeError, ValueError):
                continue
            if tid in hidden_ids or tid in FREE_AGENT_TEAM_IDS:
                nome = str(row.get("teamname", "") or "").strip()
                if nome:
                    hidden_names.add(nome)
    return hidden_ids, hidden_names

def _mapa_times(aux):
    """teamid -> {teamname, leagueid, leaguename, is_international, is_hidden, is_free_agent}."""
    teams = aux.get("teams")
    leagues = aux.get("leagues")
    ltl = aux.get("leagueteamlinks")
    info = {}
    if teams is None or "teamid" not in teams.columns:
        return info

    league_by_id = {}
    if leagues is not None and "leagueid" in leagues.columns:
        for _, row in leagues.iterrows():
            try:
                lid = int(pd.to_numeric(row.get("leagueid"), errors="coerce"))
            except (TypeError, ValueError):
                continue
            league_by_id[lid] = {
                "leaguename": str(row.get("leaguename", "") or "").strip(),
                "is_international": int(pd.to_numeric(row.get("isinternationalleague"), errors="coerce") or 0) == 1,
            }

    team_league = {}
    if ltl is not None and "teamid" in ltl.columns and "leagueid" in ltl.columns:
        for _, row in ltl.iterrows():
            try:
                tid = int(pd.to_numeric(row.get("teamid"), errors="coerce"))
                lid = int(pd.to_numeric(row.get("leagueid"), errors="coerce"))
            except (TypeError, ValueError):
                continue
            if tid not in team_league:
                team_league[tid] = lid

    for _, row in teams.iterrows():
        try:
            tid = int(pd.to_numeric(row.get("teamid"), errors="coerce"))
        except (TypeError, ValueError):
            continue
        lid = team_league.get(tid)
        liga = league_by_id.get(lid, {}) if lid is not None else {}
        is_free_agent = tid in FREE_AGENT_TEAM_IDS
        is_hidden = (not is_free_agent) and (
            (tid in HIDDEN_TEAM_IDS)
            or (lid in HIDDEN_LEAGUE_IDS if lid is not None else False)
        )
        raw_name = str(row.get("teamname", "") or "").strip()
        info[tid] = {
            "teamname": nome_time_exibicao(tid, raw_name),
            "leagueid": lid if lid is not None else 0,
            "leaguename": "" if (is_hidden or is_free_agent) else liga.get("leaguename", ""),
            "is_international": bool(liga.get("is_international", False)),
            "is_hidden": is_hidden,
            "is_free_agent": is_free_agent,
        }
    return info

def _aplicar_bloqueio_ligas(df, aux):
    """
    No app (não no DB): ignora times das ligas ocultas.
    - Reatribui clube/seleção a partir de teamplayerlinks, pulando times ocultos.
    - Agentes livres → Sem Clube (sem link), mas o jogador permanece e mantém seleção.
    - Remove jogadores que só têm vínculo com times ocultos (não agentes livres).
    """
    hidden_ids, hidden_names = _ids_times_ocultos(aux)
    tpl = aux.get("teamplayerlinks")
    team_info = _mapa_times(aux)

    # Garante colunas
    for col, default in (
        ("teamname", "Sem Clube"),
        ("teamid", 0),
        ("leaguename", ""),
        ("leagueid", 0),
        ("nationteamname", ""),
        ("nationteamid", 0),
        ("nationleaguename", ""),
        ("has_national_team", 0),
        ("number", 0),
    ):
        if col not in df.columns:
            df[col] = default

    if tpl is not None and "playerid" in tpl.columns and "teamid" in tpl.columns and team_info:
        club = {}
        nation = {}
        linked_pids = set()
        free_agent_pids = set()
        for _, row in tpl.iterrows():
            try:
                pid = int(pd.to_numeric(row.get("playerid"), errors="coerce"))
                tid = int(pd.to_numeric(row.get("teamid"), errors="coerce"))
            except (TypeError, ValueError):
                continue
            linked_pids.add(pid)
            info = team_info.get(tid)
            if not info:
                continue
            if info.get("is_free_agent"):
                # Agente livre: mostra o nome (ex.: Passes Livres Fem.), sem ser
                # time selecionável; não conta como clube “normal” da liga.
                free_agent_pids.add(pid)
                if pid not in club:
                    club[pid] = {
                        "teamid": tid,
                        "teamname": info["teamname"] or "Sem Clube",
                        "leagueid": 0,
                        "leaguename": "",
                        "number": int(
                            pd.to_numeric(row.get("jerseynumber"), errors="coerce") or 0
                        ),
                    }
                continue
            if info.get("is_hidden"):
                continue
            entry = {
                "teamid": tid,
                "teamname": info["teamname"] or "Sem Clube",
                "leagueid": info["leagueid"],
                "leaguename": info["leaguename"],
                "number": int(pd.to_numeric(row.get("jerseynumber"), errors="coerce") or 0),
            }
            if info["is_international"]:
                if pid not in nation:
                    nation[pid] = entry
            else:
                if pid not in club:
                    club[pid] = entry

        # Aplica re-resolução por playerid
        pids = pd.to_numeric(df["playerid"], errors="coerce")
        new_teamname, new_teamid, new_league, new_leagueid = [], [], [], []
        new_nation, new_nationid, new_nationleague, new_has, new_number = [], [], [], [], []
        keep = []

        for i, pid_val in enumerate(pids):
            try:
                pid = int(pid_val)
            except (TypeError, ValueError):
                keep.append(True)
                new_teamname.append("Sem Clube")
                new_teamid.append(0)
                new_league.append("")
                new_leagueid.append(0)
                new_nation.append("")
                new_nationid.append(0)
                new_nationleague.append("")
                new_has.append(0)
                new_number.append(0)
                continue

            c = club.get(pid)
            n = nation.get(pid)
            if c:
                new_teamname.append(c["teamname"])
                new_teamid.append(c["teamid"])
                new_league.append(c["leaguename"])
                new_leagueid.append(c["leagueid"])
                new_number.append(c["number"])
            else:
                new_teamname.append("Sem Clube")
                new_teamid.append(0)
                new_league.append("")
                new_leagueid.append(0)
                new_number.append(n["number"] if n else 0)

            if n:
                new_nation.append(n["teamname"])
                new_nationid.append(n["teamid"])
                new_nationleague.append(n["leaguename"])
                new_has.append(1)
            else:
                new_nation.append("")
                new_nationid.append(0)
                new_nationleague.append("")
                new_has.append(0)

            # Visível: clube, seleção, sem vínculos, ou só agente livre.
            # Oculto: apenas times de ligas/times bloqueados.
            if c or n or pid not in linked_pids or pid in free_agent_pids:
                keep.append(True)
            else:
                keep.append(False)

        df = df.copy()
        df["teamname"] = new_teamname
        df["teamid"] = new_teamid
        df["leaguename"] = new_league
        df["leagueid"] = new_leagueid
        df["nationteamname"] = new_nation
        df["nationteamid"] = new_nationid
        df["nationleaguename"] = new_nationleague
        df["has_national_team"] = new_has
        df["number"] = new_number
        df = df.loc[keep].reset_index(drop=True)
        return df

    # Fallback (banco sem teamplayerlinks): limpa nomes ocultos e remove
    # quem só tinha time oculto (sem seleção visível).
    hide_club = df["teamname"].isin(hidden_names)
    free_mask = pd.Series(False, index=df.index)
    if "leagueid" in df.columns:
        lids = pd.to_numeric(df["leagueid"], errors="coerce").fillna(0).astype(int)
        hide_club = hide_club | lids.isin(HIDDEN_LEAGUE_IDS)
    if "teamid" in df.columns:
        tids = pd.to_numeric(df["teamid"], errors="coerce").fillna(0).astype(int)
        free_mask = tids.isin(FREE_AGENT_TEAM_IDS)
        hide_club = hide_club | (
            (tids.isin(HIDDEN_TEAM_IDS) | tids.isin(hidden_ids)) & ~free_mask
        )
    hide_nation = df["nationteamname"].isin(hidden_names)
    if "nationteamid" in df.columns:
        ntids = pd.to_numeric(df["nationteamid"], errors="coerce").fillna(0).astype(int)
        hide_nation = hide_nation | ntids.isin(HIDDEN_TEAM_IDS) | ntids.isin(hidden_ids)

    df = df.copy()
    # Agentes livres: só aplica nome de exibição (ex. Passes Livres Fem.)
    if "teamid" in df.columns and free_mask.any():
        tids = pd.to_numeric(df["teamid"], errors="coerce").fillna(0).astype(int)
        df.loc[free_mask, "teamname"] = tids[free_mask].map(
            lambda t: nome_time_exibicao(t, "")
        )
        df.loc[free_mask, "leaguename"] = ""
        df.loc[free_mask, "leagueid"] = 0

    df.loc[hide_club, "teamname"] = "Sem Clube"
    df.loc[hide_club, "leaguename"] = ""
    if "leagueid" in df.columns:
        df.loc[hide_club, "leagueid"] = 0
    if "teamid" in df.columns:
        df.loc[hide_club, "teamid"] = 0
    df.loc[hide_nation, "nationteamname"] = ""
    df.loc[hide_nation, "nationleaguename"] = ""
    df["has_national_team"] = df["nationteamname"].astype(str).str.strip().ne("").astype(int)

    nation_ok = df["nationteamname"].astype(str).str.strip().ne("")
    # Tinha só time oculto (não agente livre) e não sobrou seleção → some
    drop = hide_club & ~nation_ok
    df = df.loc[~drop].reset_index(drop=True)
    return df

def listar_bancos():
    """Lista bancos FCM (novo) e players_*.db (legado), mais recentes primeiro."""
    arquivos = []
    for padrao in ("FCM *.db", "players_*.db"):
        arquivos.extend(glob.glob(os.path.join(APP_DIR, padrao)))
    # remove duplicatas preservando ordem
    vistos = set()
    unicos = []
    for p in arquivos:
        key = os.path.normcase(os.path.abspath(p))
        if key in vistos:
            continue
        vistos.add(key)
        unicos.append(p)
    unicos.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return unicos

def rotulo_banco(path):
    """Nome amigável no seletor (sem extensão .db)."""
    return os.path.splitext(os.path.basename(path))[0]

def ler_build_info(db_path):
    """Lê metadados do SQLite (versão / patch / data)."""
    info = {}
    try:
        conn = sqlite3.connect(db_path)
        try:
            rows = conn.execute("SELECT key, value FROM build_info").fetchall()
            info = {str(k): str(v) if v is not None else "" for k, v in rows}
        finally:
            conn.close()
    except Exception:
        pass
    return info

def formatar_data_header(db_date):
    """'22-07-2026' → 'Jul 22, 2026' (mês em inglês, como no exemplo)."""
    meses_en = (
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    )
    s = str(db_date or "").strip()
    try:
        partes = s.replace("/", "-").split("-")
        if len(partes) == 3:
            d, m, y = int(partes[0]), int(partes[1]), int(partes[2])
            if 1 <= m <= 12:
                return f"{meses_en[m - 1]} {d}, {y}"
    except (TypeError, ValueError):
        pass
    return s

def titulo_patch_squad(db_path, rotulo_fallback=""):
    """
    'Siga La Pelota - Base de Dados FCM 26 v4.1 (Jul 22, 2026)'
    Usa build_info; se faltar, tenta o nome do arquivo.
    """
    info = ler_build_info(db_path)
    ver = (info.get("game_version") or "").strip()
    patch = (info.get("patch") or "").strip()
    data_fmt = formatar_data_header(info.get("db_date", ""))

    if not ver or not patch:
        # Fallback: "FCM 26 v4.1 - 22-07-2026"
        nome = rotulo_fallback or rotulo_banco(db_path)
        m = re.search(
            r"FCM\s+(\d+)\s+(v[\d.]+)\s*-\s*(\d{2}-\d{2}-\d{4})",
            nome,
            flags=re.IGNORECASE,
        )
        if m:
            ver = ver or m.group(1)
            patch = patch or m.group(2)
            data_fmt = data_fmt or formatar_data_header(m.group(3))

    partes = []
    if ver:
        partes.append(ver)
    if patch:
        partes.append(patch)
    versao = " ".join(partes) if partes else (rotulo_fallback or rotulo_banco(db_path))
    if data_fmt:
        return f"Siga La Pelota - Base de Dados FCM {versao} ({data_fmt})"
    return f"Siga La Pelota - Base de Dados FCM {versao}"

@st.cache_data(show_spinner=False)
def carregar_dados(db_path, _cache_buster=None, _norm_ver=4):
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM players", conn)
        aux = _tabelas_auxiliares(conn)
    finally:
        conn.close()

    tem_headclasscode = "headclasscode" in df.columns
    tem_preferredfoot = "preferredfoot" in df.columns

    for coluna in ['commonname', 'firstname', 'lastname']:
        if coluna not in df.columns:
            df[coluna] = ''
        df[coluna] = df[coluna].replace('', pd.NA)

    df['playername'] = df['commonname'].fillna(df['firstname'].fillna('') + ' ' + df['lastname'].fillna('')).astype(str).str.strip()
    df['playername_norm'] = df['playername'].map(normalizar_texto)
    
    df['nationality'] = df['nationality'].fillna('0').astype(str).str.split('.').str[0]
    df['nationality'] = df['nationality'].map(lambda x: DICT_PAISES.get(x, x))

    if 'gender' not in df.columns:
        df['gender'] = 0
    else:
        df['gender'] = pd.to_numeric(df['gender'], errors='coerce').fillna(0).astype(int).clip(0, 1)
    
    # TRADUTOR DE POSIÇÕES
    dict_pos = {
        'GK': 'GOL', 'CB': 'ZAG', 'LB': 'LE', 'RB': 'LD', 'LWB': 'ADE', 'RWB': 'ADD',
        'CDM': 'VOL', 'CM': 'MC', 'CAM': 'MEI', 'LM': 'ME', 'RM': 'MD',
        'LW': 'PE', 'RW': 'PD', 'CF': 'SA', 'ST': 'ATA'
    }
    df['Position'] = df['Position'].fillna('RES').astype(str).str.strip()
    df['Position'] = df['Position'].map(lambda x: dict_pos.get(x, x))
    
    for p_col in ['Position2', 'Position3', 'Position4']:
        if p_col in df.columns:
            df[p_col] = df[p_col].astype(str).str.strip()
            df[p_col] = df[p_col].map(lambda x: dict_pos.get(x, x)).replace('nan', '')
    
    # TRATAMENTO DE CLUBES E REMOÇÃO DE MANAGERS
    if 'teamname' in df.columns:
        df['teamname'] = df['teamname'].fillna('Sem Clube').astype(str).str.strip()
        # Managers (não confundir com Passes Livres / agentes livres)
        df = df[~df['teamname'].str.contains('Managers com passe livre', case=False, na=False)]
    else:
        df['teamname'] = 'Sem Clube'

    # Colunas de liga / seleção / empréstimo (bancos novos); defaults para bancos antigos
    for col, default in (
        ('leaguename', ''),
        ('nationteamname', ''),
        ('nationleaguename', ''),
        ('has_national_team', 0),
        ('trait1', 0),
        ('trait2', 0),
        ('icontrait1', 0),
        ('icontrait2', 0),
        ('playerjointeamdate', ''),
        ('contractvaliduntil', 0),
        ('is_on_loan', 0),
        ('loaned_from_teamid', 0),
        ('loaned_from_teamname', ''),
        ('loandateend', ''),
        ('preferredfoot', 0),
        ('headclasscode', 1),
    ):
        if col not in df.columns:
            df[col] = default
        df[col] = df[col].fillna(default)
    df['leaguename'] = df['leaguename'].astype(str).replace({'nan': '', 'None': ''}).str.strip()
    df['nationteamname'] = df['nationteamname'].astype(str).replace({'nan': '', 'None': ''}).str.strip()
    df['nationleaguename'] = df['nationleaguename'].astype(str).replace({'nan': '', 'None': ''}).str.strip()
    df['loaned_from_teamname'] = df['loaned_from_teamname'].astype(str).replace({'nan': '', 'None': ''}).str.strip()
    df['loandateend'] = df['loandateend'].astype(str).replace({'nan': '', 'None': 'NaT', 'NaT': ''}).str.strip()
    df['playerjointeamdate'] = df['playerjointeamdate'].astype(str).replace({'nan': '', 'None': 'NaT', 'NaT': ''}).str.strip()
    df['has_national_team'] = pd.to_numeric(df['has_national_team'], errors='coerce').fillna(0).astype(int)
    df['is_on_loan'] = pd.to_numeric(df['is_on_loan'], errors='coerce').fillna(0).astype(int)
    df['contractvaliduntil'] = pd.to_numeric(df['contractvaliduntil'], errors='coerce').fillna(0).astype(int)
    df['loaned_from_teamid'] = pd.to_numeric(df['loaned_from_teamid'], errors='coerce').fillna(0).astype(int)
    df['preferredfoot'] = pd.to_numeric(df['preferredfoot'], errors='coerce').fillna(0).astype(int)
    df['headclasscode'] = pd.to_numeric(df['headclasscode'], errors='coerce').fillna(1).astype(int)

    # Bloqueio só no app: oculta times das ligas 383/384/2240/2255 e
    # remove jogadores que só existem nesses times.
    df = _aplicar_bloqueio_ligas(df, aux)
        
    df['playerid'] = pd.to_numeric(df['playerid'], errors='coerce').fillna(0).astype(int).astype(str)
    
    # Um jogador = uma linha (clube + seleção já vêm denormalizados)
    df = df.drop_duplicates(subset=['playerid'], keep='first')
    
    df['birthdate'] = pd.to_datetime(df['birthdate'], errors='coerce')
    df['Idade'] = (pd.Timestamp.now() - df['birthdate']).dt.days // 365
    df['Idade'] = df['Idade'].fillna(25).astype(int)
    
    colunas_numericas = ['overallrating', 'potential', 'height', 'weight', 'weakfootabilitytypecode',
                         'skillmoves',
                         'crossing', 'finishing', 'headingaccuracy', 'shortpassing', 'volleys', 
                         'dribbling', 'curve', 'freekickaccuracy', 'longpassing', 'ballcontrol', 
                         'acceleration', 'sprintspeed', 'agility', 'reactions', 'balance', 'shotpower', 
                         'jumping', 'stamina', 'strength', 'longshots', 'aggression', 'interceptions', 
                         'positioning', 'vision', 'penalties', 'composure', 'defensiveawareness', 
                         'standingtackle', 'slidingtackle', 'gkdiving', 'gkhandling', 'gkkicking', 
                         'gkpositioning', 'gkreflexes', 'trait1', 'trait2',
                         'icontrait1', 'icontrait2']
    
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
    # CÁLCULO DE MÉDIAS
    df['Ofensivo'] = df[['crossing', 'finishing', 'headingaccuracy', 'shortpassing', 'volleys']].mean(axis=1).round().astype(int)
    df['Habilidade'] = df[['dribbling', 'curve', 'freekickaccuracy', 'longpassing', 'ballcontrol']].mean(axis=1).round().astype(int)
    df['Movimentação'] = df[['acceleration', 'sprintspeed', 'agility', 'reactions', 'balance']].mean(axis=1).round().astype(int)
    df['Força'] = df[['shotpower', 'jumping', 'stamina', 'strength', 'longshots']].mean(axis=1).round().astype(int)
    df['Mentalidade'] = df[['aggression', 'interceptions', 'positioning', 'vision', 'penalties', 'composure']].mean(axis=1).round().astype(int)
    df['Defesa'] = df[['defensiveawareness', 'standingtackle', 'slidingtackle']].mean(axis=1).round().astype(int)

    opcoes_liga, mapa_liga = _opcoes_filtro_liga(df, aux)
    return df, opcoes_liga, mapa_liga, tem_headclasscode, tem_preferredfoot

def _opcoes_filtro_liga(df, aux):
    """Rótulos 'leaguename (país)' → leaguename, só ligas visíveis / não ocultas."""
    presentes = {
        str(x).strip()
        for x in list(df.get("leaguename", [])) + list(df.get("nationleaguename", []))
        if x and str(x).strip() not in ("", "nan", "None")
    }
    mapa = {}
    leagues = aux.get("leagues") if aux else None
    if leagues is not None and "leaguename" in leagues.columns:
        for _, row in leagues.iterrows():
            try:
                lid = int(pd.to_numeric(row.get("leagueid"), errors="coerce"))
            except (TypeError, ValueError):
                lid = -1
            if lid in HIDDEN_LEAGUE_IDS:
                continue
            nome = str(row.get("leaguename", "") or "").strip()
            if not nome or nome not in presentes:
                continue
            try:
                cid = str(int(pd.to_numeric(row.get("countryid"), errors="coerce") or 0))
            except (TypeError, ValueError):
                cid = "0"
            pais = DICT_PAISES.get(cid, "")
            rotulo = f"{nome} ({pais})" if pais else nome
            mapa[rotulo] = nome
    else:
        for nome in sorted(presentes):
            mapa[nome] = nome
    return sorted(mapa.keys(), key=lambda s: s.casefold()), mapa

bancos = listar_bancos()
if not bancos:
    st.error(
        "Nenhum banco de dados encontrado. Gere um arquivo "
        "`FCM 26 vX.Y - DD-MM-YYYY.db` executando "
        "`python db-builder/build_players_db.py`."
    )
    st.stop()

if 'jogador_selecionado' not in st.session_state:
    st.session_state.jogador_selecionado = None
if 'time_selecionado' not in st.session_state:
    st.session_state.time_selecionado = None
if 'time_retorno' not in st.session_state:
    st.session_state.time_retorno = None
if 'jogador_retorno' not in st.session_state:
    st.session_state.jogador_retorno = None
if 'sort_col' not in st.session_state:
    st.session_state.sort_col = 'overallrating'
if 'sort_asc' not in st.session_state:
    st.session_state.sort_asc = False
if 'lista_pagina' not in st.session_state:
    st.session_state.lista_pagina = 1
if 'lista_pagina_times' not in st.session_state:
    st.session_state.lista_pagina_times = 1
if 'modo_app' not in st.session_state:
    st.session_state.modo_app = "Jogadores"

# Restaura filtros/página/perfil da URL ANTES dos widgets da sidebar
processar_query_params()

# Troca de aba pedida após o widget `modo_app` (ex.: botão Voltar)
if "_modo_app_set" in st.session_state:
    _prox = st.session_state.pop("_modo_app_set")
    if _prox in ("Jogadores", "Times"):
        st.session_state.modo_app = _prox

rotulos_bancos = [rotulo_banco(b) for b in bancos]
if st.session_state.get("banco_dados") not in rotulos_bancos:
    st.session_state.banco_dados = rotulos_bancos[0]
if TEM_ICONE:
    st.sidebar.image(ICONE, width=150)
banco_escolhido_nome = st.sidebar.selectbox(
    "🗃️ Squad",
    rotulos_bancos,
    key="banco_dados",
)
banco_escolhido = bancos[rotulos_bancos.index(banco_escolhido_nome)]

try:
    with st.spinner("Carregando dados…"):
        df, opcoes_liga, mapa_liga, tem_headclasscode, tem_preferredfoot = carregar_dados(
            banco_escolhido, _cache_buster=os.path.getmtime(banco_escolhido)
        )
except Exception as e:
    st.error(f"Não foi possível ler o banco de dados **{banco_escolhido_nome}**: {e}")
    st.stop()

if df.empty or 'overallrating' not in df.columns:
    st.error(f"O banco de dados **{banco_escolhido_nome}** não contém dados de jogadores válidos.")
    st.stop()

@st.cache_data(show_spinner=False)
def carregar_aux_times(db_path, _cache_buster=None):
    return team_views.carregar_tabelas_times(db_path)

aux_times = carregar_aux_times(
    banco_escolhido, _cache_buster=os.path.getmtime(banco_escolhido)
)
df_times = team_views.montar_df_times(
    aux_times,
    DICT_PAISES,
    HIDDEN_LEAGUE_IDS,
    HIDDEN_TEAM_IDS | FREE_AGENT_TEAM_IDS,
    normalizar_texto,
)
tem_formacoes = (
    aux_times.get("formations") is not None
    and not aux_times["formations"].empty
    and aux_times.get("default_teamsheets") is not None
    and not aux_times["default_teamsheets"].empty
)

# Motores de Imagens
def _normalizar_genero(gender):
    """FC usa 0/1; trata strings e ausências como 0."""
    try:
        return 1 if int(gender) == 1 else 0
    except (TypeError, ValueError):
        return 0

def _caminhos_miniface(player_id, gender=0):
    id_limpo = str(player_id).strip()
    heads_dirs = ("heads", "Heads")
    prefixes = (f"p{id_limpo}", f"n{id_limpo}", id_limpo)
    # DDS tem prioridade sobre PNG
    exts = (".dds", ".DDS", ".png", ".PNG", ".jpg", ".jpeg", ".webp")
    caminhos = []
    for pasta in heads_dirs:
        for prefix in prefixes:
            for ext in exts:
                caminhos.append(os.path.join(APP_DIR, pasta, f"{prefix}{ext}"))
    g = _normalizar_genero(gender)
    for pasta in heads_dirs:
        for ext in (".dds", ".DDS", ".png", ".PNG"):
            caminhos.append(os.path.join(APP_DIR, pasta, f"notfound_{g}{ext}"))
    return caminhos

def _caminhos_crest(team_id):
    """Brasões em crest/: l{teamid}.dds|.png — DDS primeiro; senão notfound.png."""
    try:
        id_limpo = str(int(team_id))
    except (TypeError, ValueError):
        id_limpo = str(team_id).strip()
    pastas = ("crest", "Crest")
    caminhos = []
    for pasta in pastas:
        for ext in (".dds", ".DDS", ".png", ".PNG"):
            caminhos.append(os.path.join(APP_DIR, pasta, f"l{id_limpo}{ext}"))
    for pasta in pastas:
        for nome in ("notfound.png", "notfound.PNG", "notfound.dds", "notfound.DDS"):
            caminhos.append(os.path.join(APP_DIR, pasta, nome))
    return caminhos

def _primeira_imagem_existente(caminhos):
    for caminho in caminhos:
        if os.path.exists(caminho):
            try:
                mtime = os.path.getmtime(caminho)
            except OSError:
                mtime = 0
            return caminho, mtime
    return "", 0

def _imagem_para_data_uri(caminho, tamanho):
    try:
        with Image.open(caminho) as img:
            img = img.convert("RGBA")
            img.thumbnail((tamanho, tamanho))
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            encoded = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def _miniface_data_uri(caminho, mtime, tamanho, _img_ver=2):
    if not caminho:
        return None
    return _imagem_para_data_uri(caminho, tamanho)

def obter_miniface_tabela(player_id, gender=0):
    caminho, mtime = _primeira_imagem_existente(_caminhos_miniface(player_id, gender))
    data_uri = _miniface_data_uri(caminho, mtime, 120)
    return data_uri or AVATAR_PADRAO

def obter_miniface_perfil(player_id, gender=0):
    caminho, mtime = _primeira_imagem_existente(_caminhos_miniface(player_id, gender))
    data_uri = _miniface_data_uri(caminho, mtime, 300)
    return data_uri or AVATAR_PADRAO

@st.cache_data(show_spinner=False)
def _crest_data_uri(caminho, mtime, tamanho, _img_ver=2):
    if not caminho:
        return None
    return _imagem_para_data_uri(caminho, tamanho)

def obter_crest_tabela(team_id):
    caminho, mtime = _primeira_imagem_existente(_caminhos_crest(team_id))
    data_uri = _crest_data_uri(caminho, mtime, 120)
    return data_uri or AVATAR_PADRAO

def obter_crest_perfil(team_id):
    caminho, mtime = _primeira_imagem_existente(_caminhos_crest(team_id))
    data_uri = _crest_data_uri(caminho, mtime, 300)
    return data_uri or AVATAR_PADRAO

# =====================================================================
# BARRA LATERAL (Filtros — conforme a aba ativa)
# =====================================================================
st.sidebar.header("🔍 Central de Filtros")

_PLACEHOLDER_ESCOLHER = "Escolher..."

if st.session_state.get("modo_app") not in ("Jogadores", "Times"):
    st.session_state.modo_app = "Jogadores"
modo_filtros = st.session_state.modo_app

# Defaults das faixas (jogadores) — usados quando a aba Times está ativa
_FAIXA_PADRAO = {
    "filtro_idade": (15, 50),
    "filtro_ovr": (40, 99),
    "filtro_pot": (40, 99),
    "filtro_altura": (150, 220),
    "filtro_peso": (50, 110),
    "filtro_perna_ruim": (1, 5),
    "filtro_cruzamento": (1, 99),
    "filtro_finalizacao": (1, 99),
    "filtro_precisao_cabeceio": (1, 99),
    "filtro_passe_curto": (1, 99),
    "filtro_voleios": (1, 99),
    "filtro_dribles": (1, 99),
    "filtro_curva": (1, 99),
    "filtro_precisao_faltas": (1, 99),
    "filtro_lancamento": (1, 99),
    "filtro_controle_bola": (1, 99),
    "filtro_aceleracao": (1, 99),
    "filtro_pique": (1, 99),
    "filtro_agilidade": (1, 99),
    "filtro_reacao": (1, 99),
    "filtro_equilibrio": (1, 99),
    "filtro_forca_chute": (1, 99),
    "filtro_impulsao": (1, 99),
    "filtro_folego": (1, 99),
    "filtro_forca": (1, 99),
    "filtro_chutes_longe": (1, 99),
    "filtro_combatividade": (1, 99),
    "filtro_interceptacao": (1, 99),
    "filtro_pos_ataque": (1, 99),
    "filtro_visao": (1, 99),
    "filtro_penaltis": (1, 99),
    "filtro_compostura": (1, 99),
    "filtro_hab_defensiva": (1, 99),
    "filtro_dividida_pe": (1, 99),
    "filtro_carrinho": (1, 99),
    "filtro_elast_gl": (1, 99),
    "filtro_manejo_gl": (1, 99),
    "filtro_chute_gl": (1, 99),
    "filtro_pos_gl": (1, 99),
    "filtro_reflexos_gl": (1, 99),
}

def _faixa(key):
    v = st.session_state.get(key, _FAIXA_PADRAO[key])
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return tuple(v)
    return _FAIXA_PADRAO[key]

if modo_filtros == "Jogadores":
    st.sidebar.markdown("##### 👤 Jogadores")
    busca_nome = st.sidebar.text_input("Nome", key="busca_nome")

    # Migra seleções antigas em inglês (se houver na sessão)
    _REGIAO_PT = {
        "South America": "América do Sul",
        "North America": "América do Norte",
        "Europe": "Europa",
        "Asia": "Ásia",
        "Oceania": "Oceania",
        "Africa": "África",
    }
    _sel_reg = st.session_state.get("filtro_regiao") or []
    if _sel_reg:
        _migradas = [_REGIAO_PT.get(r, r) for r in _sel_reg]
        _migradas = [r for r in _migradas if r in OPCOES_REGIAO]
        if _migradas != list(_sel_reg):
            st.session_state.filtro_regiao = _migradas

    filtro_regiao = st.sidebar.multiselect(
        "Regiões",
        OPCOES_REGIAO,
        key="filtro_regiao",
        placeholder=_PLACEHOLDER_ESCOLHER,
    )
    paises_das_regioes = set()
    for regiao in filtro_regiao:
        paises_das_regioes |= REGIAO_PAISES.get(regiao, set())

    todas_nacionalidades = sorted(df['nationality'].unique().tolist())
    if paises_das_regioes:
        todas_nacionalidades = [n for n in todas_nacionalidades if n in paises_das_regioes]
    sel_nat = st.session_state.get("filtro_nacionalidade") or []
    if sel_nat:
        validas = [n for n in sel_nat if n in todas_nacionalidades]
        if validas != list(sel_nat):
            st.session_state.filtro_nacionalidade = validas
    filtro_nacionalidade = st.sidebar.multiselect(
        "Nacionalidade / País",
        todas_nacionalidades,
        key="filtro_nacionalidade",
        placeholder=_PLACEHOLDER_ESCOLHER,
    )

    todos_times = sorted({
        t for t in (
            list(df['teamname'].unique()) + list(df['nationteamname'].unique())
        )
        if t and str(t).strip() and str(t) not in ('nan', 'None', 'Sem Clube')
    })
    filtro_clube = st.sidebar.multiselect(
        "Clube / Seleção",
        todos_times,
        key="filtro_clube",
        placeholder=_PLACEHOLDER_ESCOLHER,
    )

    filtro_liga = st.sidebar.multiselect(
        "Liga",
        opcoes_liga,
        key="filtro_liga",
        placeholder=_PLACEHOLDER_ESCOLHER,
    )

    todas_posicoes = sorted(df['Position'].unique().tolist())
    filtro_posicao = st.sidebar.multiselect(
        "Posição",
        todas_posicoes,
        key="filtro_posicao",
        placeholder=_PLACEHOLDER_ESCOLHER,
    )

    filtro_face_real = st.sidebar.selectbox(
        "Face Real",
        ["Qualquer", "Sim", "Não"],
        key="filtro_face_real",
    )
    filtro_genero = st.sidebar.selectbox(
        "Gênero",
        ["Qualquer", "Masculino", "Feminino"],
        key="filtro_genero",
    )
    filtro_pe = st.sidebar.selectbox(
        "Pé Preferido",
        ["Qualquer", "Destro", "Canhoto", "Ambidestro"],
        key="filtro_pe",
    )
    filtro_fintas = st.sidebar.selectbox(
        "Fintas",
        ["Qualquer", "1 ⭐", "2 ⭐", "3 ⭐", "4 ⭐", "5 ⭐"],
        key="filtro_fintas",
    )
    filtro_emprestimo = st.sidebar.selectbox(
        "Empréstimo",
        ["Qualquer", "Sim", "Não"],
        key="filtro_emprestimo",
    )
    if (filtro_face_real != "Qualquer" and not tem_headclasscode) or (
        filtro_pe != "Qualquer" and not tem_preferredfoot
    ):
        st.sidebar.caption(
            "⚠️ Reconstrua o banco (db-builder) para Face Real / Pé Preferido."
        )

    with st.sidebar.expander("Físico & Perfil Básico", expanded=False):
        idade_min, idade_max = st.slider("Idade", 15, 50, (15, 50), key="filtro_idade")
        ovr_min, ovr_max = st.slider("Geral", 40, 99, (40, 99), key="filtro_ovr")
        pot_min, pot_max = st.slider("Potencial", 40, 99, (40, 99), key="filtro_pot")
        altura_min, altura_max = st.slider("Altura (cm)", 150, 220, (150, 220), key="filtro_altura")
        peso_min, peso_max = st.slider("Peso (kg)", 50, 110, (50, 110), key="filtro_peso")
        perna_ruim = st.slider("Perna Ruim (Estrelas)", 1, 5, (1, 5), key="filtro_perna_ruim")

    with st.sidebar.expander("Categoria Ofensivo"):
        cruzamento = st.slider("Cruzamento", 1, 99, (1, 99), key="filtro_cruzamento")
        finalizacao = st.slider("Finalização", 1, 99, (1, 99), key="filtro_finalizacao")
        precisao_cabeceio = st.slider("Precisão Cabeceio", 1, 99, (1, 99), key="filtro_precisao_cabeceio")
        passe_curto = st.slider("Passe Curto", 1, 99, (1, 99), key="filtro_passe_curto")
        voleios = st.slider("Voleios", 1, 99, (1, 99), key="filtro_voleios")

    with st.sidebar.expander("Categoria Habilidade"):
        dribles = st.slider("Dribles", 1, 99, (1, 99), key="filtro_dribles")
        curva = st.slider("Curva", 1, 99, (1, 99), key="filtro_curva")
        precisao_faltas = st.slider("Precisão nas Faltas", 1, 99, (1, 99), key="filtro_precisao_faltas")
        lancamento = st.slider("Lançamento", 1, 99, (1, 99), key="filtro_lancamento")
        controle_bola = st.slider("Controle de Bola", 1, 99, (1, 99), key="filtro_controle_bola")

    with st.sidebar.expander("Categoria Movimentação"):
        aceleracao = st.slider("Aceleração", 1, 99, (1, 99), key="filtro_aceleracao")
        pique = st.slider("Pique", 1, 99, (1, 99), key="filtro_pique")
        agilidade = st.slider("Agilidade", 1, 99, (1, 99), key="filtro_agilidade")
        reacao = st.slider("Reação", 1, 99, (1, 99), key="filtro_reacao")
        equilibrio = st.slider("Equilíbrio", 1, 99, (1, 99), key="filtro_equilibrio")

    with st.sidebar.expander("Categoria Força"):
        forca_chute = st.slider("Força do Chute", 1, 99, (1, 99), key="filtro_forca_chute")
        impulsao = st.slider("Impulsão", 1, 99, (1, 99), key="filtro_impulsao")
        folego = st.slider("Fôlego", 1, 99, (1, 99), key="filtro_folego")
        forca = st.slider("Força", 1, 99, (1, 99), key="filtro_forca")
        chutes_longe = st.slider("Chutes de Longe", 1, 99, (1, 99), key="filtro_chutes_longe")

    with st.sidebar.expander("Categoria Mentalidade"):
        combatividade = st.slider("Combatividade", 1, 99, (1, 99), key="filtro_combatividade")
        interceptacao = st.slider("Interceptação", 1, 99, (1, 99), key="filtro_interceptacao")
        pos_ataque = st.slider("Pos. de Ataque", 1, 99, (1, 99), key="filtro_pos_ataque")
        visao = st.slider("Visão de Jogo", 1, 99, (1, 99), key="filtro_visao")
        penaltis = st.slider("Pênaltis", 1, 99, (1, 99), key="filtro_penaltis")
        compostura_filtro = st.slider("Compostura", 1, 99, (1, 99), key="filtro_compostura")

    with st.sidebar.expander("Categoria Defesa"):
        hab_defensiva = st.slider("Habilidade Defensiva", 1, 99, (1, 99), key="filtro_hab_defensiva")
        dividida_pe = st.slider("Dividida em Pé", 1, 99, (1, 99), key="filtro_dividida_pe")
        carrinho = st.slider("Carrinho", 1, 99, (1, 99), key="filtro_carrinho")

    with st.sidebar.expander("Categoria Goleiro"):
        elast_gl = st.slider("Elasticidade GL", 1, 99, (1, 99), key="filtro_elast_gl")
        manejo_gl = st.slider("Manejo GL", 1, 99, (1, 99), key="filtro_manejo_gl")
        chute_gl = st.slider("Chute GL", 1, 99, (1, 99), key="filtro_chute_gl")
        pos_gl = st.slider("Posicionamento GL", 1, 99, (1, 99), key="filtro_pos_gl")
        reflexos_gl = st.slider("Reflexos GL", 1, 99, (1, 99), key="filtro_reflexos_gl")

    # Valores dos filtros de times (aba inativa) — preservados na sessão
    busca_time = st.session_state.get("busca_time", "") or ""
    filtro_regiao_time = st.session_state.get("filtro_regiao_time") or []
    filtro_liga_time = st.session_state.get("filtro_liga_time") or []
    filtro_genero_time = st.session_state.get("filtro_genero_time", "Qualquer")
    paises_regiao_time = set()
    for regiao in filtro_regiao_time:
        paises_regiao_time |= REGIAO_PAISES.get(regiao, set())

else:
    st.sidebar.markdown("##### 🏟️ Times")
    busca_time = st.sidebar.text_input("Nome", key="busca_time")
    filtro_regiao_time = st.sidebar.multiselect(
        "Regiões",
        OPCOES_REGIAO,
        key="filtro_regiao_time",
        placeholder=_PLACEHOLDER_ESCOLHER,
    )
    paises_regiao_time = set()
    for regiao in filtro_regiao_time:
        paises_regiao_time |= REGIAO_PAISES.get(regiao, set())

    opcoes_liga_time = sorted(
        {
            x
            for x in df_times.get("leaguename", pd.Series(dtype=str)).dropna().unique().tolist()
            if x and str(x).strip()
        },
        key=lambda s: s.casefold(),
    )
    filtro_liga_time = st.sidebar.multiselect(
        "Liga",
        opcoes_liga_time,
        key="filtro_liga_time",
        placeholder=_PLACEHOLDER_ESCOLHER,
    )
    filtro_genero_time = st.sidebar.selectbox(
        "Gênero",
        ["Qualquer", "Masculino", "Feminino"],
        key="filtro_genero_time",
    )
    if not tem_formacoes:
        st.sidebar.caption(
            "⚠️ Reconstrua o Squad (db-builder) para formações / escalação."
        )

    # Valores dos filtros de jogadores (aba inativa)
    busca_nome = st.session_state.get("busca_nome", "") or ""
    filtro_regiao = st.session_state.get("filtro_regiao") or []
    paises_das_regioes = set()
    for regiao in filtro_regiao:
        paises_das_regioes |= REGIAO_PAISES.get(regiao, set())
    filtro_nacionalidade = st.session_state.get("filtro_nacionalidade") or []
    filtro_clube = st.session_state.get("filtro_clube") or []
    filtro_liga = st.session_state.get("filtro_liga") or []
    filtro_posicao = st.session_state.get("filtro_posicao") or []
    filtro_face_real = st.session_state.get("filtro_face_real", "Qualquer")
    filtro_genero = st.session_state.get("filtro_genero", "Qualquer")
    filtro_pe = st.session_state.get("filtro_pe", "Qualquer")
    filtro_fintas = st.session_state.get("filtro_fintas", "Qualquer")
    filtro_emprestimo = st.session_state.get("filtro_emprestimo", "Qualquer")
    idade_min, idade_max = _faixa("filtro_idade")
    ovr_min, ovr_max = _faixa("filtro_ovr")
    pot_min, pot_max = _faixa("filtro_pot")
    altura_min, altura_max = _faixa("filtro_altura")
    peso_min, peso_max = _faixa("filtro_peso")
    perna_ruim = _faixa("filtro_perna_ruim")
    cruzamento = _faixa("filtro_cruzamento")
    finalizacao = _faixa("filtro_finalizacao")
    precisao_cabeceio = _faixa("filtro_precisao_cabeceio")
    passe_curto = _faixa("filtro_passe_curto")
    voleios = _faixa("filtro_voleios")
    dribles = _faixa("filtro_dribles")
    curva = _faixa("filtro_curva")
    precisao_faltas = _faixa("filtro_precisao_faltas")
    lancamento = _faixa("filtro_lancamento")
    controle_bola = _faixa("filtro_controle_bola")
    aceleracao = _faixa("filtro_aceleracao")
    pique = _faixa("filtro_pique")
    agilidade = _faixa("filtro_agilidade")
    reacao = _faixa("filtro_reacao")
    equilibrio = _faixa("filtro_equilibrio")
    forca_chute = _faixa("filtro_forca_chute")
    impulsao = _faixa("filtro_impulsao")
    folego = _faixa("filtro_folego")
    forca = _faixa("filtro_forca")
    chutes_longe = _faixa("filtro_chutes_longe")
    combatividade = _faixa("filtro_combatividade")
    interceptacao = _faixa("filtro_interceptacao")
    pos_ataque = _faixa("filtro_pos_ataque")
    visao = _faixa("filtro_visao")
    penaltis = _faixa("filtro_penaltis")
    compostura_filtro = _faixa("filtro_compostura")
    hab_defensiva = _faixa("filtro_hab_defensiva")
    dividida_pe = _faixa("filtro_dividida_pe")
    carrinho = _faixa("filtro_carrinho")
    elast_gl = _faixa("filtro_elast_gl")
    manejo_gl = _faixa("filtro_manejo_gl")
    chute_gl = _faixa("filtro_chute_gl")
    pos_gl = _faixa("filtro_pos_gl")
    reflexos_gl = _faixa("filtro_reflexos_gl")

# =====================================================================
# ABAS (janela principal)
# =====================================================================
# Botão Voltar na mesma linha das abas
_voltar_cfg = None
if st.session_state.get("jogador_selecionado") is not None:
    if st.session_state.get("time_retorno"):
        _voltar_cfg = ("ao_time", "⬅️ Voltar ao Time")
    else:
        _voltar_cfg = ("lista_jogadores", "⬅️ Voltar à Lista")
elif st.session_state.get("time_selecionado") is not None:
    if st.session_state.get("jogador_retorno"):
        _voltar_cfg = ("ao_jogador", "⬅️ Voltar ao Jogador")
    else:
        _voltar_cfg = ("lista_times", "⬅️ Voltar à Lista de Times")

if _voltar_cfg:
    _v_acao, _v_rotulo = _voltar_cfg
    _v_href = html.escape(href_navegacao_voltar(_v_acao))
    st.html(
        f"""
        <div class="slp-tab-voltar">
          <a href="{_v_href}" target="_self"
             onclick="event.preventDefault();
               (function(h){{try{{var w=(window.parent&&window.parent!==window)?window.parent:window;
               w.location.href=h;}}catch(e){{window.location.href=h;}}}})
               (this.getAttribute('href'));return false;">{html.escape(_v_rotulo)}</a>
        </div>
        """,
        unsafe_allow_javascript=True,
    )

tab_jogadores, tab_times = st.tabs(
    ["Jogadores", "Times"],
    default=st.session_state.modo_app,
    key="modo_app",
    on_change="rerun",
)

with tab_times:
    df_t = df_times.copy()
    if busca_time:
        termo_t = normalizar_texto(busca_time).strip()
        if termo_t:
            df_t = df_t[
                df_t["teamname_norm"]
                .fillna("")
                .astype(str)
                .str.contains(termo_t, case=False, regex=False, na=False)
            ]
    if paises_regiao_time:
        df_t = df_t[df_t["pais"].isin(paises_regiao_time)]
    if filtro_liga_time:
        df_t = df_t[df_t["leaguename"].isin(filtro_liga_time)]
    if filtro_genero_time == "Masculino":
        df_t = df_t[df_t["iswomencompetition"] == 0]
    elif filtro_genero_time == "Feminino":
        df_t = df_t[df_t["iswomencompetition"] == 1]

    df_t = df_t.sort_values(
        by="overallrating", ascending=False, kind="mergesort"
    ).reset_index(drop=True)

    titulo_lista = titulo_patch_squad(banco_escolhido, banco_escolhido_nome)

    # Perfil do time
    if st.session_state.time_selecionado is not None:
        tid = str(st.session_state.time_selecionado)
        match_t = df_times[df_times["teamid"].astype(str) == tid]
        if match_t.empty:
            st.warning("Time não encontrado. Voltando à lista…")
            st.session_state.time_selecionado = None
            st.rerun()
        time_row = match_t.iloc[0]
        nome_time = str(time_row.get("teamname", ""))
        liga_time = str(time_row.get("leaguename", "") or "")
        ovr_t = int(time_row.get("overallrating") or 0)
        def_t = int(time_row.get("defenserating") or 0)
        meio_t = int(time_row.get("midfieldrating") or 0)
        ata_t = int(time_row.get("attackrating") or 0)
        ovr_badge_t = badge_rating(ovr_t, "Geral", grande=True)
        crest_grande = obter_crest_perfil(tid)

        st.html(
            f"""
            <div class="pf-wrap">
              <img class="pf-foto" src="{crest_grande}" alt=""
                   style="object-fit:contain;background:#0f1216;padding:8px;box-sizing:border-box;"
                   onerror="this.onerror=null;this.src='{AVATAR_PADRAO}'">
              <div class="pf-main">
                <div class="pf-nome">{html.escape(nome_time)}</div>
                <div class="pf-id" style="font-style:italic;">{html.escape(liga_time) or "Sem liga"}</div>
                <div class="pf-meta">
                  <div><b>ID:</b> {tid}</div>
                </div>
              </div>
              <div class="pf-side">
                <div class="pf-ratings">
                  <div class="pf-rate"><div class="pf-rate-lbl">Geral</div>{ovr_badge_t}</div>
                </div>
                <div class="pf-team-lines">
                  <div><b>Defesa:</b> <span class="pf-team-val" style="color:{cor_rating(def_t)}">{def_t}</span></div>
                  <div><b>Meio:</b> <span class="pf-team-val" style="color:{cor_rating(meio_t)}">{meio_t}</span></div>
                  <div><b>Ataque:</b> <span class="pf-team-val" style="color:{cor_rating(ata_t)}">{ata_t}</span></div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_javascript=False,
        )
        st.markdown("---")

        if not tem_formacoes:
            st.info(
                "Formações/escalação ainda não estão neste Squad. "
                "Execute o db-builder novamente para incluir "
                "`formations` e `default_teamsheets`."
            )
        else:
            slots, form_name = team_views.lineup_slots(
                aux_times,
                tid,
                df,
                obter_miniface_tabela,
            )
            roles, captain = team_views.set_piece_roles(
                aux_times, tid, df, obter_miniface_tabela
            )
            st.html(
                team_views.html_formacao_e_bolas(
                    slots, form_name, roles, team_id=tid, captain=captain
                ),
                unsafe_allow_javascript=True,
            )

            elenco = team_views.squad_rows(aux_times, tid, df)
            st.subheader("Elenco")
            if not elenco:
                st.caption("Nenhum jogador na escalação.")
            else:
                players_by_id = {}
                for _, prow in df.iterrows():
                    try:
                        pid_k = int(prow["playerid"])
                    except (TypeError, ValueError):
                        continue
                    if pid_k > 0:
                        players_by_id[pid_k] = prow
                st.html(
                    html_lista_elenco(
                        elenco,
                        players_by_id,
                        obter_miniface_tabela,
                        estado_ui=serializar_estado_ui(),
                        team_id=tid,
                    ),
                    unsafe_allow_javascript=True,
                )

    else:
        # Lista de times (só quando nenhum perfil está aberto)
        if TEM_ICONE:
            col_logo1, col_logo2 = st.columns([1, 6])
            with col_logo1:
                st.image(ICONE, width=90)
            with col_logo2:
                st.title(f"⚽ {titulo_lista}")
        else:
            st.title(f"⚽ {titulo_lista}")

        st.markdown("### Times")
        if df_times.empty:
            st.warning("Nenhum time encontrado neste Squad.")

        total_times = len(df_t)
        total_paginas_t = max(1, math.ceil(total_times / 50))
        if st.session_state.lista_pagina_times > total_paginas_t:
            st.session_state.lista_pagina_times = total_paginas_t
        if st.session_state.lista_pagina_times < 1:
            st.session_state.lista_pagina_times = 1
        pagina_t = st.session_state.lista_pagina_times

        st.write(f"Encontrados **{total_times}** times.")
        ini = (pagina_t - 1) * 50
        df_pag_t = df_t.iloc[ini : ini + 50].copy().reset_index(drop=True)
        st.html(
            team_views.html_lista_times(
                df_pag_t,
                pagina=pagina_t,
                total_paginas=total_paginas_t,
                estado_ui=serializar_estado_ui(),
                obter_crest_fn=obter_crest_tabela,
            ),
            unsafe_allow_javascript=True,
        )

with tab_jogadores:
    # PROCESSAMENTO DO FILTRO REATIVO (Jogadores)
    df_filtrado = df.copy()
    if busca_nome:
        termo = normalizar_texto(busca_nome).strip()
        if termo:
            if "playername_norm" not in df_filtrado.columns:
                df_filtrado = df_filtrado.copy()
                df_filtrado["playername_norm"] = df_filtrado["playername"].map(normalizar_texto)
            df_filtrado = df_filtrado[
                df_filtrado["playername_norm"]
                .fillna("")
                .astype(str)
                .str.contains(termo, case=False, regex=False, na=False)
            ]
    if paises_das_regioes:
        df_filtrado = df_filtrado[df_filtrado['nationality'].isin(paises_das_regioes)]
    if filtro_nacionalidade: df_filtrado = df_filtrado[df_filtrado['nationality'].isin(filtro_nacionalidade)]
    if filtro_clube:
        df_filtrado = df_filtrado[
            df_filtrado['teamname'].isin(filtro_clube)
            | df_filtrado['nationteamname'].isin(filtro_clube)
        ]
    if filtro_liga:
        ligas_sel = {mapa_liga.get(r, r) for r in filtro_liga}
        df_filtrado = df_filtrado[
            df_filtrado['leaguename'].isin(ligas_sel)
            | df_filtrado['nationleaguename'].isin(ligas_sel)
        ]
    if filtro_posicao: df_filtrado = df_filtrado[df_filtrado['Position'].isin(filtro_posicao)]
    if filtro_face_real == "Sim" and tem_headclasscode:
        df_filtrado = df_filtrado[df_filtrado['headclasscode'] == 0]
    elif filtro_face_real == "Não" and tem_headclasscode:
        df_filtrado = df_filtrado[df_filtrado['headclasscode'] == 1]
    if filtro_genero == "Masculino":
        df_filtrado = df_filtrado[df_filtrado['gender'] == 0]
    elif filtro_genero == "Feminino":
        df_filtrado = df_filtrado[df_filtrado['gender'] == 1]
    if filtro_pe == "Destro" and tem_preferredfoot:
        df_filtrado = df_filtrado[df_filtrado['preferredfoot'] == 0]
    elif filtro_pe == "Canhoto" and tem_preferredfoot:
        df_filtrado = df_filtrado[df_filtrado['preferredfoot'] == 1]
    elif filtro_pe == "Ambidestro" and tem_preferredfoot:
        df_filtrado = df_filtrado[
            df_filtrado['preferredfoot'].isin([0, 1])
            & (df_filtrado['weakfootabilitytypecode'] == 5)
        ]
    if filtro_fintas != "Qualquer":
        # UI 1–5⭐ ↔ skillmoves 0–4 no DB
        try:
            estrelas = int(str(filtro_fintas).strip()[0])
            skill_db = max(0, min(4, estrelas - 1))
            df_filtrado = df_filtrado[
                pd.to_numeric(df_filtrado["skillmoves"], errors="coerce").fillna(0).astype(int)
                == skill_db
            ]
        except (TypeError, ValueError, IndexError):
            pass
    if filtro_emprestimo == "Sim":
        df_filtrado = df_filtrado[df_filtrado['is_on_loan'] == 1]
    elif filtro_emprestimo == "Não":
        df_filtrado = df_filtrado[df_filtrado['is_on_loan'] == 0]

    df_filtrado = df_filtrado[
        (df_filtrado['Idade'].between(idade_min, idade_max)) & (df_filtrado['overallrating'].between(ovr_min, ovr_max)) &
        (df_filtrado['potential'].between(pot_min, pot_max)) & (df_filtrado['height'].between(altura_min, altura_max)) &
        (df_filtrado['weight'].between(peso_min, peso_max)) & (df_filtrado['weakfootabilitytypecode'].between(perna_ruim[0], perna_ruim[1])) &
        (df_filtrado['crossing'].between(cruzamento[0], cruzamento[1])) & (df_filtrado['finishing'].between(finalizacao[0], finalizacao[1])) &
        (df_filtrado['headingaccuracy'].between(precisao_cabeceio[0], precisao_cabeceio[1])) & (df_filtrado['shortpassing'].between(passe_curto[0], passe_curto[1])) &
        (df_filtrado['volleys'].between(voleios[0], voleios[1])) &
        (df_filtrado['dribbling'].between(dribles[0], dribles[1])) & (df_filtrado['curve'].between(curva[0], curva[1])) &
        (df_filtrado['freekickaccuracy'].between(precisao_faltas[0], precisao_faltas[1])) & (df_filtrado['longpassing'].between(lancamento[0], lancamento[1])) &
        (df_filtrado['ballcontrol'].between(controle_bola[0], controle_bola[1])) &
        (df_filtrado['acceleration'].between(aceleracao[0], aceleracao[1])) & (df_filtrado['sprintspeed'].between(pique[0], pique[1])) &
        (df_filtrado['agility'].between(agilidade[0], agilidade[1])) & (df_filtrado['reactions'].between(reacao[0], reacao[1])) &
        (df_filtrado['balance'].between(equilibrio[0], equilibrio[1])) &
        (df_filtrado['shotpower'].between(forca_chute[0], forca_chute[1])) & (df_filtrado['jumping'].between(impulsao[0], impulsao[1])) &
        (df_filtrado['stamina'].between(folego[0], folego[1])) & (df_filtrado['strength'].between(forca[0], forca[1])) &
        (df_filtrado['longshots'].between(chutes_longe[0], chutes_longe[1])) &
        (df_filtrado['aggression'].between(combatividade[0], combatividade[1])) & (df_filtrado['interceptions'].between(interceptacao[0], interceptacao[1])) &
        (df_filtrado['positioning'].between(pos_ataque[0], pos_ataque[1])) & (df_filtrado['vision'].between(visao[0], visao[1])) &
        (df_filtrado['penalties'].between(penaltis[0], penaltis[1])) & (df_filtrado['composure'].between(compostura_filtro[0], compostura_filtro[1])) &
        (df_filtrado['defensiveawareness'].between(hab_defensiva[0], hab_defensiva[1])) & (df_filtrado['standingtackle'].between(dividida_pe[0], dividida_pe[1])) &
        (df_filtrado['slidingtackle'].between(carrinho[0], carrinho[1])) &
        (df_filtrado['gkdiving'].between(elast_gl[0], elast_gl[1])) & (df_filtrado['gkhandling'].between(manejo_gl[0], manejo_gl[1])) &
        (df_filtrado['gkkicking'].between(chute_gl[0], chute_gl[1])) & (df_filtrado['gkpositioning'].between(pos_gl[0], pos_gl[1])) &
        (df_filtrado['gkreflexes'].between(reflexos_gl[0], reflexos_gl[1]))
    ]

    sort_col = st.session_state.sort_col if st.session_state.sort_col in df_filtrado.columns else "overallrating"
    df_filtrado = df_filtrado.sort_values(
        by=sort_col, ascending=st.session_state.sort_asc, kind="mergesort"
    ).reset_index(drop=True)

    # =====================================================================
    # TELA 1: LISTA DE JOGADORES
    # =====================================================================
    if st.session_state.jogador_selecionado is None:
        titulo_lista = titulo_patch_squad(banco_escolhido, banco_escolhido_nome)
        if TEM_ICONE:
            col_logo1, col_logo2 = st.columns([1, 6])
            with col_logo1:
                st.image(ICONE, width=90)
            with col_logo2:
                st.title(f"⚽ {titulo_lista}")
        else:
            st.title(f"⚽ {titulo_lista}")

        st.warning("📱 **Atenção!!** Clique na **setinha `>`** no canto superior esquerdo para abrir ou recolher o Menu de Filtros e Pesquisa!")

        st.markdown("""
            <div class="agradecimento-box">
                ❤️ <b>Agradecimento Especial:</b> Desenvolvido em parceria e com o apoio fundamental da equipe <b>FC Mania Mod</b>. 
                Um agradecimento de elite ao amigo <b>DecoRuiz</b>, que forneceu todo o suporte técnico, paciência e a extração dos 
                dados necessários para tornar esta ferramenta possível para toda a comunidade!
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        total_jogadores = len(df_filtrado)
        total_paginas = max(1, math.ceil(total_jogadores / 50))

        st.info(
            "💡 **Dica:** Clique em qualquer lugar da linha do jogador para abrir o perfil. "
            "Use o cabeçalho para ordenar.\n\n"
            "🌎 = vinculado a uma seleção\n\n"
            "↔️ = jogador emprestado"
        )

        if st.session_state.lista_pagina > total_paginas:
            st.session_state.lista_pagina = total_paginas
        if st.session_state.lista_pagina < 1:
            st.session_state.lista_pagina = 1
        pagina_selecionada = st.session_state.lista_pagina
        st.session_state.lista_pagina_retorno = pagina_selecionada

        st.write(f"Encontrados **{total_jogadores}** jogadores.")

        inicio = (pagina_selecionada - 1) * 50
        fim = inicio + 50
        df_pagina = df_filtrado.iloc[inicio:fim].copy().reset_index(drop=True)

        render_lista_jogadores(
            df_pagina,
            filtro_clube,
            pagina=pagina_selecionada,
            total_paginas=total_paginas,
        )

    # =====================================================================
    # TELA 2: PERFIL DO JOGADOR
    # =====================================================================
    else:
        pid = str(st.session_state.jogador_selecionado)
        matches = df[df['playerid'].astype(str) == pid]
        if matches.empty:
            st.warning("Jogador não encontrado. Voltando à lista…")
            st.session_state.jogador_selecionado = None
            st.rerun()
        jog = matches.iloc[0]

        foto_grande = obter_miniface_perfil(jog['playerid'], jog.get('gender', 0))
        ovr_badge = badge_rating(jog['overallrating'], "Geral", grande=True)
        pot_badge = badge_rating(jog['potential'], "Potencial", grande=True)
        pills = pills_posicoes(jog)

        first = str(jog.get('firstname', '') or '').strip()
        last = str(jog.get('lastname', '') or '').strip()
        nome_completo = f"{first} {last}".strip() or str(jog['playername'])

        nasc_txt = formatar_data_pt(jog.get('birthdate'))
        fintas = estrelas_fintas(jog.get('skillmoves', 0))

        selecao = str(jog.get('nationteamname', '') or '').strip()
        if selecao in ('nan', 'None'):
            selecao = ""
        clube = str(jog.get('teamname', '') or '').strip()
        liga = str(jog.get('leaguename', '') or '').strip()
        if liga in ('nan', 'None'):
            liga = ""

        chegada = formatar_data_pt(jog.get('playerjointeamdate'))
        try:
            contrato_ano = int(jog.get('contractvaliduntil', 0) or 0)
        except (TypeError, ValueError):
            contrato_ano = 0
        emprestado_de = str(jog.get('loaned_from_teamname', '') or '').strip()
        if emprestado_de in ('nan', 'None'):
            emprestado_de = ""
        emprestado_ate = formatar_data_pt(jog.get('loandateend'))
        on_loan = esta_emprestado(jog)

        estado_ui_link = serializar_estado_ui()
        from_pid = jog.get("playerid")
        clube_link = link_nome_time(
            clube, jog.get("teamid"), estado_ui_link, from_pid=from_pid
        )
        emprestado_link = link_nome_time(
            emprestado_de,
            jog.get("loaned_from_teamid"),
            estado_ui_link,
            from_pid=from_pid,
        )
        selecao_link = link_nome_time(
            selecao, jog.get("nationteamid"), estado_ui_link, from_pid=from_pid
        )

        club_html = f"<div><b>Clube:</b> {clube_link}"
        if liga:
            club_html += f" <span style='color:#9aa4b2'>({html.escape(liga)})</span>"
        club_html += "</div>"
        if on_loan and emprestado_de:
            club_html += f"<div><b>Emprestado de:</b> {emprestado_link}</div>"
        if on_loan and emprestado_ate:
            club_html += f"<div><b>Emprestado até:</b> {html.escape(emprestado_ate)}</div>"
        if chegada:
            rotulo_chegada = "Chegada ao Clube de Origem" if on_loan else "Chegada ao Clube"
            club_html += f"<div><b>{rotulo_chegada}:</b> {html.escape(chegada)}</div>"
        if contrato_ano > 0:
            club_html += f"<div><b>Contrato até:</b> {contrato_ano}</div>"
        if selecao:
            club_html += f"<div><b>Seleção:</b> {selecao_link}</div>"

        idade_html = f"<b>Idade:</b> {jog['Idade']} anos"
        if nasc_txt:
            idade_html += f" <span style='color:#9aa4b2'>({html.escape(nasc_txt)})</span>"

        st.html(
            f"""
            <div class="pf-wrap">
              <img class="pf-foto" src="{foto_grande}"
                   onerror="this.onerror=null;this.src='{AVATAR_PADRAO}'">
              <div class="pf-main">
                <div class="pf-nome">{html.escape(str(jog['playername']))}</div>
                <div class="pf-pos">{pills}</div>
                <div class="pf-id">ID: {jog['playerid']}</div>
                <div class="pf-meta">
                  <div><b>Nome completo:</b> {html.escape(nome_completo)}</div>
                  <div>{idade_html}</div>
                  <div><b>Perna Ruim:</b> {jog['weakfootabilitytypecode']}⭐</div>
                  <div><b>Fintas:</b> {fintas}⭐</div>
                  <div><b>Altura - Peso:</b> {jog['height']} cm - {jog['weight']} kg</div>
                  <div><b>Nacionalidade:</b> {html.escape(str(jog['nationality']))}</div>
                </div>
              </div>
              <div class="pf-side">
                <div class="pf-ratings">
                  <div class="pf-rate"><div class="pf-rate-lbl">Geral</div>{ovr_badge}</div>
                  <div class="pf-rate"><div class="pf-rate-lbl">Potencial</div>{pot_badge}</div>
                </div>
                <div class="pf-club">{club_html}</div>
              </div>
            </div>
            """,
            unsafe_allow_javascript=True,
        )

        st.markdown(
            """
            <div style="border-top:1px solid #30363d; margin:10px 0 6px 0;"></div>
            <h3 style="margin:0 0 8px 0; color:#fff; font-size:1.25rem;">📊 Todos os Atributos Detalhados</h3>
            """,
            unsafe_allow_html=True,
        )

        p1, p2, p3, p4 = st.columns(4)

        with p1:
            card_categoria("Ofensivo", jog["Ofensivo"], [
                ("Cruzamento", jog["crossing"]),
                ("Finalização", jog["finishing"]),
                ("Precisão Cabeceio", jog["headingaccuracy"]),
                ("Passe Curto", jog["shortpassing"]),
                ("Voleios", jog["volleys"]),
            ])
            card_categoria("Mentalidade", jog["Mentalidade"], [
                ("Combatividade", jog["aggression"]),
                ("Interceptação", jog["interceptions"]),
                ("Pos. de Ataque", jog["positioning"]),
                ("Visão de Jogo", jog["vision"]),
                ("Pênaltis", jog["penalties"]),
                ("Compostura", jog["composure"]),
            ])

        with p2:
            card_categoria("Habilidade", jog["Habilidade"], [
                ("Dribles", jog["dribbling"]),
                ("Curva", jog["curve"]),
                ("Precisão nas Faltas", jog["freekickaccuracy"]),
                ("Lançamento", jog["longpassing"]),
                ("Controle de Bola", jog["ballcontrol"]),
            ])
            card_categoria("Defesa", jog["Defesa"], [
                ("Habilidade Defensiva", jog["defensiveawareness"]),
                ("Dividida em Pé", jog["standingtackle"]),
                ("Carrinho", jog["slidingtackle"]),
            ])

        with p3:
            card_categoria("Movimentação", jog["Movimentação"], [
                ("Aceleração", jog["acceleration"]),
                ("Pique", jog["sprintspeed"]),
                ("Agilidade", jog["agility"]),
                ("Reação", jog["reactions"]),
                ("Equilíbrio", jog["balance"]),
            ])
            gk_vals = [
                jog["gkdiving"], jog["gkhandling"], jog["gkkicking"],
                jog["gkpositioning"], jog["gkreflexes"],
            ]
            gk_media = int(round(sum(int(v) for v in gk_vals) / len(gk_vals)))
            card_categoria("Goleiro", gk_media, [
                ("Elasticidade GL", jog["gkdiving"]),
                ("Manejo GL", jog["gkhandling"]),
                ("Chute GL", jog["gkkicking"]),
                ("Posicionamento GL", jog["gkpositioning"]),
                ("Reflexos GL", jog["gkreflexes"]),
            ])

        with p4:
            card_categoria("Força", jog["Força"], [
                ("Força do Chute", jog["shotpower"]),
                ("Impulsão", jog["jumping"]),
                ("Fôlego", jog["stamina"]),
                ("Força", jog["strength"]),
                ("Chutes de Longe", jog["longshots"]),
            ])
            card_estilos(jog)

        st.markdown("---")
        st.caption("Ficha técnica viabilizada graças ao suporte de DecoRuiz e equipe FC Mania Mod.")

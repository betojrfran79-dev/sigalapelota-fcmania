import streamlit as st
import pandas as pd
import math
import os
import base64
import io
from PIL import Image

# Configuração da Página
st.set_page_config(page_title="Siga La PelotA - Database", page_icon="icone.png", layout="wide")

# --- INJEÇÃO DE CSS E BLOQUEIO DE TRADUÇÃO AUTOMÁTICA ---
st.markdown("""
    <meta name="google" content="notranslate">
    
    <style>
    /* Tema Escuro Base */
    [data-testid="stAppViewContainer"] { background-color: #1a1d21; color: #e4e6eb; font-family: 'Inter', sans-serif; }
    
    /* Barra Lateral */
    [data-testid="stSidebar"] { background-color: #15181b; border-right: 1px solid #30363d; }
    
    /* Força os textos da barra lateral a serem brancos, EXCETO dentro das caixas de entrada */
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    
    /* CORREÇÃO: Tinta preta ao digitar no campo Nome E nos menus de Seleção Múltipla */
    div[data-baseweb="input"] input, 
    div[data-baseweb="select"] input { 
        color: #000000 !important; 
    }
    
    /* CORREÇÃO: Deixa o texto das caixinhas selecionadas (tags) legíveis */
    span[data-baseweb="tag"] {
        background-color: #333333 !important;
        border: 1px solid #555555 !important;
    }
    span[data-baseweb="tag"] span {
        color: #ffffff !important;
    }
    
    /* Cores dos Títulos e Métricas */
    h1:first-of-type { color: #FF0000 !important; }
    h2, h3, h4, h5, h6 { color: #ffffff !important; }
    .stMetric .stMetricLabel { color: #cccccc !important; }
    .stMetric .stMetricValue { color: #FF0000 !important; }
    
    /* Botões Gerais */
    .stButton>button { background-color: #333333; color: #ffffff !important; font-weight: bold; border-radius: 6px; border: 1px solid #555555; padding: 8px 16px; }
    .stButton>button:hover { background-color: #FF0000; border-color: #FF0000; }
    .st-emotion-cache-p5m40 { border-bottom: 1px solid #30363d; }
    
    /* Efeitos Visuais */
    [data-testid="stDataFrame"] img { transform: scale(1.15); }
    .agradecimento-box { background-color: #15181b; border-left: 4px solid #FF0000; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    df = pd.read_excel('squad_info_all_EA FC.xlsx')
    df['playername'] = df['commonname'].fillna(df['firstname'].fillna('') + ' ' + df['lastname'].fillna(''))
    df['playername'] = df['playername'].str.strip()
    df['Position'] = df['Position'].str.strip()
    if 'teamname' in df.columns:
        df['teamname'] = df['teamname'].str.strip()
    
    df['birthdate'] = pd.to_datetime(df['birthdate'], format='%d/%m/%Y', errors='coerce')
    df['Idade'] = (pd.Timestamp.now() - df['birthdate']).dt.days // 365
    return df

df = carregar_dados()

def obter_miniface(player_id):
    id_str = str(player_id).zfill(6)
    pasta1 = id_str[:3]
    pasta2 = id_str[3:]
    
    # Busca robusta (ignora maiúsculas nas extensões e procura várias opções)
    possiveis_caminhos = [
        f"heads/p{player_id}.png", f"heads/p{player_id}.PNG", 
        f"heads/{player_id}.png", f"heads/{player_id}.PNG",
        f"heads/p{player_id}.dds", f"heads/p{player_id}.DDS",
        f"heads/{player_id}.dds", f"heads/{player_id}.DDS"
    ]
    
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            try:
                if caminho.lower().endswith('.png'):
                    with open(caminho, "rb") as image_file:
                        encoded = base64.b64encode(image_file.read()).decode()
                    return f"data:image/png;base64,{encoded}"
                elif caminho.lower().endswith('.dds'):
                    img = Image.open(caminho)
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    encoded = base64.b64encode(buffer.getvalue()).decode()
                    return f"data:image/png;base64,{encoded}"
            except Exception:
                pass # Se falhar, tenta o próximo caminho ou a internet
    
    # Fallback da Internet
    return f"https://cdn.sofifa.net/players/{pasta1}/{pasta2}/24_120.png"

if 'jogador_selecionado' not in st.session_state:
    st.session_state.jogador_selecionado = None

# =====================================================================
# TELA 1: BUSCA COM PAGINAÇÃO
# =====================================================================
if st.session_state.jogador_selecionado is None:
    col_logo1, col_logo2 = st.columns([1, 6])
    with col_logo1:
        st.image("icone.png", width=90)
    with col_logo2:
        st.title("⚽ Siga La Pelota - FC Mania - DataBase")
    
    st.markdown("""
        <div class="agradecimento-box">
            ❤️ <b>Agradecimento Especial:</b> Desenvolvido em parceria e com o apoio fundamental da equipe <b>FC Mania Mod</b>. 
            Um agradecimento de elite ao amigo <b>DecoRuiz</b>, que forneceu todo o suporte técnico, paciência e a extração dos 
            dados necessários para tornar esta ferramenta possível para toda a comunidade!
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # --- SIDEBAR (SEM FORMULÁRIO PARA NÃO BUGAR NO CELULAR) ---
    st.sidebar.image("icone.png", width=150)
    st.sidebar.header("🔍 Central de Filtros")

    busca_nome = st.sidebar.text_input("Nome", "")
    todas_nacionalidades = sorted(df['nationality'].dropna().unique().tolist())
    filtro_nacionalidade = st.sidebar.multiselect("Nacionalidade (ID)", todas_nacionalidades)
    todos_times = sorted(df['teamname'].dropna().unique().tolist())
    filtro_clube = st.sidebar.multiselect("Clube", todos_times)
    todas_posicoes = sorted(df['Position'].dropna().unique().tolist())
    filtro_posicao = st.sidebar.multiselect("Posição", todas_posicoes)

    with st.sidebar.expander("Físico & Perfil Básico", expanded=False):
        idade_min, idade_max = st.slider("Idade", 15, 50, (15, 50))
        ovr_min, ovr_max = st.slider("Overall", 40, 99, (40, 99))
        pot_min, pot_max = st.slider("Potencial", 40, 99, (40, 99))
        altura_min, altura_max = st.slider("Altura (cm)", 150, 220, (150, 220))
        peso_min, peso_max = st.slider("Peso (kg)", 50, 110, (50, 110))
        perna_ruim = st.slider("Perna Ruim (Estrelas)", 1, 5, (1, 5))

    with st.sidebar.expander("Categoria Ofensivo"):
        cruzamento = st.slider("Cruzamento", 1, 99, (1, 99))
        finalizacao = st.slider("Finalização", 1, 99, (1, 99))
        precisao_cabeceio = st.slider("Precisão Cabeceio", 1, 99, (1, 99))
        passe_curto = st.slider("Passe Curto", 1, 99, (1, 99))
        voleios = st.slider("Voleios", 1, 99, (1, 99))

    with st.sidebar.expander("Categoria Habilidade"):
        dribles = st.slider("Dribles", 1, 99, (1, 99))
        curva = st.slider("Curva", 1, 99, (1, 99))
        precisao_faltas = st.slider("Precisão nas Faltas", 1, 99, (1, 99))
        lancamento = st.slider("Lançamento", 1, 99, (1, 99))
        controle_bola = st.slider("Controle de Bola", 1, 99, (1, 99))

    with st.sidebar.expander("Categoria Movimentação"):
        aceleracao = st.slider("Aceleração", 1, 99, (1, 99))
        pique = st.slider("Pique", 1, 99, (1, 99))
        agilidade = st.slider("Agilidade", 1, 99, (1, 99))
        reacao = st.slider("Reação", 1, 99, (1, 99))
        equilibrio = st.slider("Equilíbrio", 1, 99, (1, 99))

    with st.sidebar.expander("Categoria Força"):
        forca_chute = st.slider("Força do Chute", 1, 99, (1, 99))
        impulsao = st.slider("Impulsão", 1, 99, (1, 99))
        folego = st.slider("Fôlego", 1, 99, (1, 99))
        forca = st.slider("Força", 1, 99, (1, 99))
        chutes_longe = st.slider("Chutes de Longe", 1, 99, (1, 99))

    with st.sidebar.expander("Categoria Mentalidade"):
        combatividade = st.slider("Combatividade", 1, 99, (1, 99))
        interceptacao = st.slider("Interceptação", 1, 99, (1, 99))
        pos_ataque = st.slider("Pos. de Ataque", 1, 99, (1, 99))
        visao = st.slider("Visão de Jogo", 1, 99, (1, 99))
        penaltis = st.slider("Pênaltis", 1, 99, (1, 99))
        compostura = st.slider("Compostura", 1, 99, (1, 99))

    with st.sidebar.expander("Categoria Defesa"):
        hab_defensiva = st.slider("Habilidade Defensiva", 1, 99, (1, 99))
        dividida_pe = st.slider("Dividida em Pe", 1, 99, (1, 99))
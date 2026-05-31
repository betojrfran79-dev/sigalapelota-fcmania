import streamlit as st
import pandas as pd
import math
import os
import base64
import io
from PIL import Image

# Configuração da Página
st.set_page_config(page_title="Siga La PelotA - Database", page_icon="icone.png", layout="wide")

# --- INJEÇÃO DE CSS BLINDADA ---
st.markdown("""
    <meta name="google" content="notranslate">
    <style>
    [data-testid="stAppViewContainer"] { background-color: #1a1d21; color: #e4e6eb; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #15181b; border-right: 1px solid #30363d; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    div[data-baseweb="input"] input, div[data-baseweb="select"] input { color: #000000 !important; }
    span[data-baseweb="tag"] { background-color: #333333 !important; border: 1px solid #555555 !important; }
    span[data-baseweb="tag"] span { color: #ffffff !important; }
    h1:first-of-type { color: #FF0000 !important; }
    h2, h3, h4, h5, h6 { color: #ffffff !important; }
    [data-testid="stMetricLabel"] { color: #aaaaaa !important; font-size: 1.2rem !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] div { color: #ffffff !important; font-size: 3rem !important; font-weight: 900 !important; }
    .stButton>button { background-color: #333333; color: #ffffff !important; font-weight: bold; border-radius: 6px; border: 1px solid #555555; padding: 8px 16px; }
    .stButton>button:hover { background-color: #FF0000; border-color: #FF0000; }
    [data-testid="stDataFrame"] img { transform: scale(1.15); }
    .agradecimento-box { background-color: #15181b; border-left: 4px solid #FF0000; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
    .attr-text { font-size: 1.2rem; margin-bottom: 8px; border-bottom: 1px solid #30363d; padding-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }
    .attr-text b { color: #FF0000; font-size: 1.3rem; }
    </style>
""", unsafe_allow_html=True)

# Função auxiliar para imprimir os atributos organizados
def mostrar_atributo(nome, valor):
    st.markdown(f"<div class='attr-text'><span>{nome}:</span> <b>{valor}</b></div>", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    df = pd.read_excel('squad_info_all_EA FC.xlsx')
    
    df['playername'] = df['commonname'].fillna(df['firstname'].fillna('') + ' ' + df['lastname'].fillna('')).astype(str).str.strip()
    
    # 1º PEDIDO: DICIONÁRIO COMPLETO DE PAÍSES (Banco de Dados EA/SoFIFA)
    dict_paises = {
        '1': 'Albânia', '2': 'Andorra', '3': 'Armênia', '4': 'Áustria', '5': 'Azerbaijão', 
        '6': 'Bielorrússia', '7': 'Bélgica', '8': 'Bósnia e Herzegovina', '9': 'Bulgária', 
        '10': 'Croácia', '11': 'Chipre', '12': 'República Tcheca', '13': 'Dinamarca', 
        '14': 'Inglaterra', '15': 'Estônia', '16': 'Ilhas Faroé', '17': 'Finlândia', 
        '18': 'França', '19': 'Macedônia do Norte', '20': 'Geórgia', '21': 'Alemanha', 
        '22': 'Grécia', '23': 'Hungria', '24': 'Islândia', '25': 'Irlanda', '26': 'Israel', 
        '27': 'Itália', '28': 'Letônia', '29': 'Liechtenstein', '30': 'Lituânia', 
        '31': 'Luxemburgo', '32': 'Malta', '33': 'Moldávia', '34': 'Holanda', 
        '35': 'Irlanda do Norte', '36': 'Noruega', '37': 'Polônia', '38': 'Portugal', 
        '39': 'Romênia', '40': 'Rússia', '41': 'San Marino', '42': 'Escócia', '43': 'Eslováquia', 
        '44': 'Eslovênia', '45': 'Espanha', '46': 'Suécia', '47': 'Suíça', '48': 'Turquia', 
        '49': 'Ucrânia', '50': 'País de Gales', '51': 'Sérvia', '52': 'Argentina', '53': 'Bolívia', 
        '54': 'Brasil', '55': 'Chile', '56': 'Colômbia', '57': 'Equador', '58': 'Paraguai', 
        '59': 'Peru', '60': 'Uruguai', '61': 'Venezuela', '62': 'Anguilla', 
        '63': 'Antígua e Barbuda', '64': 'Aruba', '65': 'Bahamas', '66': 'Barbados', 
        '67': 'Belize', '68': 'Bermudas', '69': 'Ilhas Virgens Britânicas', '70': 'Canadá', 
        '71': 'Ilhas Cayman', '72': 'Costa Rica', '73': 'Cuba', '74': 'Dominica', 
        '75': 'República Dominicana', '76': 'El Salvador', '77': 'Granada', '78': 'Guatemala', 
        '79': 'Guiana', '80': 'Haiti', '81': 'Honduras', '82': 'Jamaica', '83': 'México', 
        '84': 'Montserrat', '85': 'Antilhas Holandesas', '86': 'Nicarágua', '87': 'Panamá', 
        '88': 'Porto Rico', '89': 'São Cristóvão e Neves', '90': 'Santa Lúcia', 
        '91': 'São Vicente e Granadinas', '92': 'Suriname', '93': 'Trinidad e Tobago', 
        '94': 'Ilhas Turks e Caicos', '95': 'Estados Unidos', '96': 'Ilhas Virgens Americanas', 
        '97': 'Argélia', '98': 'Angola', '99': 'Benin', '100': 'Botsuana', '101': 'Burkina Faso', 
        '102': 'Burundi', '103': 'Camarões', '104': 'Cabo Verde', '105': 'República Centro-Africana', 
        '106': 'Chade', '107': 'Congo', '108': 'Egito', '109': 'Guiné Equatorial', '110': 'Eritreia', 
        '111': 'Costa do Marfim', '112': 'Etiópia', '113': 'Gabão', '114': 'Gâmbia', '115': 'Geórgia', 
        '117': 'Gana', '118': 'Guiné', '119': 'Guiné-Bissau', '120': 'Quênia', 
        '121': 'Lesoto', '122': 'Libéria', '123': 'Líbia', '124': 'Madagascar', '125': 'Malawi', 
        '126': 'Marrocos', '127': 'Moçambique', '128': 'Namíbia', '129': 'Nigéria', '130': 'Ruanda', 
        '131': 'São Tomé e Príncipe', '132': 'Senegal', '133': 'Seychelles', '134': 'Serra Leoa', 
        '135': 'Somália', '136': 'África do Sul', '137': 'Sudão', '138': 'Suazilândia', '139': 'Tanzânia', 
        '140': 'Togo', '141': 'Tunísia', '142': 'Uganda', '143': 'Zâmbia', '144': 'Zimbábue', 
        '145': 'Afeganistão', '146': 'Bahrein', '147': 'Bangladesh', '148': 'Butão', '149': 'Austrália', 
        '150': 'Brunei', '151': 'Camboja', '152': 'China', '153': 'Taiwan', '154': 'Guam', '155': 'Hong Kong', 
        '156': 'Índia', '157': 'Indonésia', '158': 'Irã', '159': 'Iraque', '160': 'Japão', '161': 'Jordânia', 
        '162': 'Cazaquistão', '164': 'Coreia do Norte', '165': 'Coreia do Sul', 
        '166': 'Kuwait', '167': 'Quirguistão', '168': 'Laos', '169': 'Líbano', '170': 'Macau', '171': 'Malásia', 
        '172': 'Maldivas', '173': 'Mongólia', '174': 'Mianmar', '175': 'Nepal', '176': 'Omã', 
        '177': 'Arábia Saudita', '178': 'Cingapura', '179': 'Ilhas Salomão', '180': 'Sri Lanka', 
        '181': 'Síria', '182': 'Tajiquistão', '183': 'Tailândia', '184': 'Turcomenistão', 
        '185': 'Emirados Árabes Unidos', '186': 'Uzbequistão', '187': 'Vietnã', '188': 'Iêmen', 
        '189': 'Fiji', '190': 'Nova Caledônia', '191': 'Nova Zelândia', '192': 'Papua Nova Guiné', 
        '193': 'Samoa', '194': 'Tahiti', '195': 'Tonga', '196': 'Vanuatu', '197': 'Montenegro', 
        '198': 'República do Congo', '201': 'Curaçao', '202': 'Kosovo', '203': 'Mali', '204': 'Mauritânia', 
        '205': 'Níger', '206': 'República Dominicana'
    }
    df['nationality'] = df['nationality'].fillna('0').astype(str).str.split('.').str[0]
    df['nationality'] = df['nationality'].map(lambda x: dict_paises.get(x, x))
    
    # 2º PEDIDO: TRADUTOR DE POSIÇÕES PARA PT-BR
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
    
    if 'teamname' in df.columns:
        df['teamname'] = df['teamname'].fillna('Sem Clube').astype(str).str.strip()
    else:
        df['teamname'] = 'Sem Clube'
        
    df['playerid'] = pd.to_numeric(df['playerid'], errors='coerce').fillna(0).astype(int).astype(str)
    
    df['birthdate'] = pd.to_datetime(df['birthdate'], errors='coerce')
    df['Idade'] = (pd.Timestamp.now() - df['birthdate']).dt.days // 365
    df['Idade'] = df['Idade'].fillna(25).astype(int)
    
    colunas_numericas = ['overallrating', 'potential', 'height', 'weight', 'weakfootabilitytypecode', 
                         'crossing', 'finishing', 'headingaccuracy', 'shortpassing', 'volleys', 
                         'dribbling', 'curve', 'freekickaccuracy', 'longpassing', 'ballcontrol', 
                         'acceleration', 'sprintspeed', 'agility', 'reactions', 'balance', 'shotpower', 
                         'jumping', 'stamina', 'strength', 'longshots', 'aggression', 'interceptions', 
                         'positioning', 'vision', 'penalties', 'composure', 'defensiveawareness', 
                         'standingtackle', 'slidingtackle', 'gkdiving', 'gkhandling', 'gkkicking', 
                         'gkpositioning', 'gkreflexes']
    
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
    # 3º PEDIDO: CÁLCULO E CRIAÇÃO DAS COLUNAS DE MÉDIAS
    df['Ofensivo'] = df[['crossing', 'finishing', 'headingaccuracy', 'shortpassing', 'volleys']].mean(axis=1).round().astype(int)
    df['Habilidade'] = df[['dribbling', 'curve', 'freekickaccuracy', 'longpassing', 'ballcontrol']].mean(axis=1).round().astype(int)
    df['Movimentação'] = df[['acceleration', 'sprintspeed', 'agility', 'reactions', 'balance']].mean(axis=1).round().astype(int)
    df['Força'] = df[['shotpower', 'jumping', 'stamina', 'strength', 'longshots']].mean(axis=1).round().astype(int)
    df['Mentalidade'] = df[['aggression', 'interceptions', 'positioning', 'vision', 'penalties', 'composure']].mean(axis=1).round().astype(int)
    df['Defesa'] = df[['defensiveawareness', 'standingtackle', 'slidingtackle']].mean(axis=1).round().astype(int)
            
    return df

df = carregar_dados()

# Motores de Imagens (Leve para tabela, Pesado para perfil)
@st.cache_data(show_spinner=False)
def obter_miniface_tabela(player_id):
    id_limpo = str(player_id).strip()
    id_str = id_limpo.zfill(6)
    pasta1 = id_str[:3]
    pasta2 = id_str[3:]
    possiveis_caminhos = [f"heads/p{id_limpo}.png", f"heads/p{id_limpo}.PNG", f"heads/{id_limpo}.png", f"heads/{id_limpo}.PNG", f"Heads/p{id_limpo}.png", f"Heads/p{id_limpo}.PNG", f"Heads/{id_limpo}.png", f"Heads/{id_limpo}.PNG"]
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            try:
                with Image.open(caminho) as img:
                    img.thumbnail((120, 120))
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    encoded = base64.b64encode(buffer.getvalue()).decode()
                return f"data:image/png;base64,{encoded}"
            except Exception:
                pass 
    return f"https://cdn.sofifa.net/players/{pasta1}/{pasta2}/24_120.png"

@st.cache_data(show_spinner=False)
def obter_miniface_perfil(player_id):
    id_limpo = str(player_id).strip()
    id_str = id_limpo.zfill(6)
    pasta1 = id_str[:3]
    pasta2 = id_str[3:]
    possiveis_caminhos = [f"heads/p{id_limpo}.png", f"heads/p{id_limpo}.PNG", f"heads/{id_limpo}.png", f"heads/{id_limpo}.PNG", f"Heads/p{id_limpo}.png", f"Heads/p{id_limpo}.PNG", f"Heads/{id_limpo}.png", f"Heads/{id_limpo}.PNG"]
    for caminho in possiveis_caminhos:
        if os.path.exists(caminho):
            try:
                with Image.open(caminho) as img:
                    img.thumbnail((300, 300))
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    encoded = base64.b64encode(buffer.getvalue()).decode()
                return f"data:image/png;base64,{encoded}"
            except Exception:
                pass 
    return f"https://cdn.sofifa.net/players/{pasta1}/{pasta2}/24_120.png"

if 'jogador_selecionado' not in st.session_state:
    st.session_state.jogador_selecionado = None

# =====================================================================
# 4º PEDIDO: BARRA LATERAL GLOBAL (MANTÉM OS FILTROS EM SEGUNDO PLANO)
# =====================================================================
st.sidebar.image("icone.png", width=150)
st.sidebar.header("🔍 Central de Filtros")

busca_nome = st.sidebar.text_input("Nome", "")

todas_nacionalidades = sorted(df['nationality'].unique().tolist())
filtro_nacionalidade = st.sidebar.multiselect("Nacionalidade / País", todas_nacionalidades)

todos_times = sorted(df['teamname'].unique().tolist())
filtro_clube = st.sidebar.multiselect("Clube", todos_times)

todas_posicoes = sorted(df['Position'].unique().tolist())
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
    compostura_filtro = st.slider("Compostura", 1, 99, (1, 99))

with st.sidebar.expander("Categoria Defesa"):
    hab_defensiva = st.slider("Habilidade Defensiva", 1, 99, (1, 99))
    dividida_pe = st.slider("Dividida em Pe", 1, 99, (1, 99))
    carrinho = st.slider("Carrinho", 1, 99, (1, 99))

with st.sidebar.expander("Categoria Goleiro"):
    elast_gl = st.slider("Elasticidade GL", 1, 99, (1, 99))
    manejo_gl = st.slider("Manejo GL", 1, 99, (1, 99))
    chute_gl = st.slider("Chute GL", 1, 99, (1, 99))
    pos_gl = st.slider("Posicionamento GL", 1, 99, (1, 99))
    reflexos_gl = st.slider("Reflexos GL", 1, 99, (1, 99))

# PROCESSAMENTO DO FILTRO REATIVO
df_filtrado = df.copy()
if busca_nome: df_filtrado = df_filtrado[df_filtrado['playername'].str.contains(busca_nome, case=False, na=False)]
if filtro_nacionalidade: df_filtrado = df_filtrado[df_filtrado['nationality'].isin(filtro_nacionalidade)]
if filtro_clube: df_filtrado = df_filtrado[df_filtrado['teamname'].isin(filtro_clube)]
if filtro_posicao: df_filtrado = df_filtrado[df_filtrado['Position'].isin(filtro_posicao)]

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
    (df_filtrado['acceleration'].between(aceleracao[0], acceleration[1])) if 'acceleration' in df_filtrado.columns and 'acceleration' in locals() else df_filtrado['acceleration'].between(aceleracao[0], aceleracao[1]) & (df_filtrado['sprintspeed'].between(pique[0], pique[1])) &
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

df_filtrado = df_filtrado.sort_values(by="overallrating", ascending=False).reset_index(drop=True)

# =====================================================================
# TELA 1: LISTA DE JOGADORES
# =====================================================================
if st.session_state.jogador_selecionado is None:
    col_logo1, col_logo2 = st.columns([1, 6])
    with col_logo1:
        st.image("icone.png", width=90)
    with col_logo2:
        st.title("⚽ Siga La Pelota - FC Mania - DataBase")
    
    st.warning("📱 **Acessando pelo celular?** Clique na **setinha `>`** no canto superior esquerdo para abrir o Menu de Filtros e Pesquisa!")
    
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
    
    st.info("💡 **Dica:** Para abrir o perfil completo com todos os atributos, clique na **caixa de seleção** à esquerda da foto do jogador.")
    
    col_res, col_pag = st.columns([3, 1])
    with col_res:
        st.write(f"Encontrados **{total_jogadores}** jogadores.")
    with col_pag:
        pagina_selecionada = st.selectbox("Página", range(1, total_paginas + 1))
    
    inicio = (pagina_selecionada - 1) * 50
    fim = inicio + 50
    df_pagina = df_filtrado.iloc[inicio:fim].copy().reset_index(drop=True)

    df_pagina['Foto'] = df_pagina['playerid'].apply(obter_miniface_tabela)
    
    colunas_tabela = ['Foto', 'playername', 'overallrating', 'potential', 'teamname', 'Position', 'Idade', 
                      'Ofensivo', 'Habilidade', 'Movimentação', 'Força', 'Mentalidade', 'Defesa']
    
    df_exibir_clean = df_pagina[colunas_tabela].rename(columns={
        'playername': 'Nome', 'overallrating': 'OVR', 'potential': 'POT', 'teamname': 'Clube', 'Position': 'Pos',
        'Ofensivo': 'Ofen', 'Habilidade': 'Habi', 'Movimentação': 'Movi', 'Força': 'Forç', 'Mentalidade': 'Ment', 'Defesa': 'Defe'
    })

    evento = st.dataframe(
        df_exibir_clean,
        column_config={"Foto": st.column_config.ImageColumn("Foto")},
        hide_index=False,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    if evento.selection.rows:
        linha_selecionada = evento.selection.rows[0]
        id_selecionado = df_pagina.loc[linha_selecionada, 'playerid']
        st.session_state.jogador_selecionado = id_selecionado
        st.rerun()

# =====================================================================
# TELA 2: PERFIL DO JOGADOR
# =====================================================================
else:
    if st.button("⬅️ Voltar à Lista"):
        st.session_state.jogador_selecionado = None
        st.rerun()

    st.markdown("---")
    jog = df[df['playerid'] == st.session_state.jogador_selecionado].iloc[0]
    
    foto_grande = obter_miniface_perfil(jog['playerid'])

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown(f'<img src="{foto_grande}" style="width: 100%; max-width: 280px; border-radius: 12px; border: 2px solid #FF0000;">', unsafe_allow_html=True)
        st.markdown(f"<br><h4>ID: {jog['playerid']}</h4>", unsafe_allow_html=True)
        posicoes = [str(jog['Position'])]
        for p in ['Position2', 'Position3', 'Position4']:
            if pd.notna(jog[p]) and str(jog[p]).strip() != '':
                posicoes.append(str(jog[p]))
        st.write(f"**Posições:** {', '.join(posicoes)}")
        st.write(f"**Clube:** {jog['teamname']}")

    with col2:
        st.markdown(f"<h1>{jog['playername']}</h1>", unsafe_allow_html=True)
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.metric("OVERALL", jog['overallrating'])
            st.write(f"**Idade:** {jog['Idade']} anos")
            st.write(f"**Perna Ruim (Estrelas):** {jog['weakfootabilitytypecode']}")
        with c_p2:
            st.metric("POTENCIAL", jog['potential'])
            st.write(f"**Altura:** {jog['height']} cm")
            st.write(f"**Peso:** {jog['weight']} kg")
            st.write(f"**País:** {jog['nationality']}")

    st.markdown("---")
    st.markdown("### 📊 Todos os Atributos Detalhados")

    p1, p2, p3, p4 = st.columns(4)
    
    with p1:
        st.markdown(f"#### Ofensivo (Média: {jog['Ofensivo']})")
        mostrar_atributo("Cruzamento", jog['crossing'])
        mostrar_atributo("Finalização", jog['finishing'])
        mostrar_atributo("Precisão Cabeceio", jog['headingaccuracy'])
        mostrar_atributo("Passe Curto", jog['shortpassing'])
        mostrar_atributo("Voleios", jog['volleys'])
        
        st.write("")
        st.markdown(f"#### Habilidade (Média: {jog['Habilidade']})")
        mostrar_atributo("Dribles", jog['dribbling'])
        mostrar_atributo("Curva", jog['curve'])
        mostrar_atributo("Precisão nas Faltas", jog['freekickaccuracy'])
        mostrar_atributo("Lançamento", jog['longpassing'])
        mostrar_atributo("Controle de Bola", jog['ballcontrol'])

    with p2:
        st.markdown(f"#### Movimentação (Média: {jog['Movimentação']})")
        mostrar_atributo("Aceleração", jog['acceleration'])
        mostrar_atributo("Pique", jog['sprintspeed'])
        mostrar_atributo("Agilidade", jog['agility'])
        mostrar_atributo("Reação", jog['reactions'])
        mostrar_atributo("Equilíbrio", jog['balance'])
        
        st.write("")
        st.markdown(f"#### Força (Média: {jog['Força']})")
        mostrar_atributo("Força do Chute", jog['shotpower'])
        mostrar_atributo("Impulsão", jog['jumping'])
        mostrar_atributo("Fôlego", jog['stamina'])
        mostrar_atributo("Força", jog['strength'])
        mostrar_atributo("Chutes de Longe", jog['longshots'])

    with p3:
        st.markdown(f"#### Mentalidade (Média: {jog['Mentalidade']})")
        mostrar_atributo("Combatividade", jog['aggression'])
        mostrar_atributo("Interceptação", jog['interceptions'])
        mostrar_atributo("Pos. de Ataque", jog['positioning'])
        mostrar_atributo("Visão de Jogo", jog['vision'])
        mostrar_atributo("Pênaltis", jog['penalties'])
        mostrar_atributo("Compostura", jog['composure'])

    with p4:
        st.markdown(f"#### Defesa (Média: {jog['Defesa']})")
        mostrar_atributo("Habilidade Defensiva", jog['defensiveawareness'])
        mostrar_atributo("Dividida em Pe", jog['standingtackle'])
        mostrar_atributo("Carrinho", jog['slidingtackle'])
        
        if jog['gkdiving'] > 10:
            st.write("")
            st.markdown("#### Goleiro")
            mostrar_atributo("Elasticidade GL", jog['gkdiving'])
            mostrar_atributo("Manejo GL", jog['gkhandling'])
            mostrar_atributo("Chute GL", jog['gkkicking'])
            mostrar_atributo("Posicionamento GL", jog['gkpositioning'])
            mostrar_atributo("Reflexos GL", jog['gkreflexes'])

    st.markdown("---")
    st.caption("Ficha técnica viabilizada graças ao suporte de DecoRuiz e equipe FC Mania Mod.")
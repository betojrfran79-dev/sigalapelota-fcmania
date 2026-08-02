# -*- coding: utf-8 -*-
"""Helpers for the Teams tab: list rows, pitch/lineup, squad sheet."""

from __future__ import annotations

import base64
import html
import os
import sqlite3

import pandas as pd

APP_DIR = os.path.dirname(os.path.abspath(__file__))
FIELD_PATH = os.path.join(APP_DIR, "assets", "field_dark.png")

SHEET_POSITION_MAP = {
    1: "SW", 4: "RCB", 5: "CB", 6: "LCB", 3: "RB", 7: "LB", 2: "RWB", 8: "LWB",
    9: "RDM", 10: "CDM", 11: "LDM", 12: "RM", 16: "LM", 13: "RCM", 14: "CM", 15: "LCM",
    17: "RAM", 18: "CAM", 19: "LAM", 20: "RF", 21: "CF", 22: "LF", 23: "RW", 27: "LW",
    24: "RS", 25: "ST", 26: "LS", 0: "GK", 28: "SUB", 29: "RES", -1: "",
}


def _to_int(value, default=0):
    try:
        s = str(value).strip()
        if s == "" or s.lower() in ("nan", "none"):
            return default
        return int(float(s))
    except Exception:
        return default


def _to_float(value, default=0.0):
    try:
        s = str(value).strip().replace(",", ".")
        if s == "" or s.lower() in ("nan", "none"):
            return default
        return float(s)
    except Exception:
        return default


def _img_data_uri(path):
    if not path or not os.path.isfile(path):
        return ""
    try:
        with open(path, "rb") as f:
            enc = base64.b64encode(f.read()).decode("ascii")
        return f"data:image/png;base64,{enc}"
    except Exception:
        return ""


def field_background_uri():
    return _img_data_uri(FIELD_PATH)


def field_aspect_ratio():
    """Proporção real do PNG do campo."""
    try:
        from PIL import Image

        with Image.open(FIELD_PATH) as im:
            w, h = im.size
            if w > 0 and h > 0:
                return w, h
    except Exception:
        pass
    return 1024, 465


def carregar_tabelas_times(db_path):
    """Carrega times enriquecidos + tabelas de formação/escalação."""
    conn = sqlite3.connect(db_path)
    try:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        out = {}
        for name in (
            "teams",
            "leagues",
            "leagueteamlinks",
            "teamplayerlinks",
            "formations",
            "default_teamsheets",
        ):
            if name in tables:
                out[name] = pd.read_sql_query(f"SELECT * FROM {name}", conn)
            else:
                out[name] = pd.DataFrame()
    finally:
        conn.close()
    return out


def montar_df_times(aux, dict_paises, hidden_league_ids, hidden_team_ids, normalizar_texto):
    """DataFrame de times para lista/filtros (com liga e país)."""
    teams = aux.get("teams")
    if teams is None or teams.empty:
        return pd.DataFrame()

    df = teams.copy()
    for col in (
        "teamid",
        "overallrating",
        "defenserating",
        "midfieldrating",
        "attackrating",
        "nationality",
        "gender",
    ):
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    if "teamname" not in df.columns:
        df["teamname"] = ""
    df["teamname"] = df["teamname"].fillna("").astype(str).str.strip()

    df["leagueid"] = 0
    df["leaguename"] = ""
    ltl = aux.get("leagueteamlinks")
    leagues = aux.get("leagues")
    liga_por_tid = {}
    if ltl is not None and not ltl.empty and "teamid" in ltl.columns:
        for _, row in ltl.iterrows():
            tid = _to_int(row.get("teamid"), -1)
            lid = _to_int(row.get("leagueid"), -1)
            if tid < 0 or lid < 0 or tid in liga_por_tid:
                continue
            liga_por_tid[tid] = lid
    liga_nome = {}
    liga_country = {}
    liga_women = {}
    if leagues is not None and not leagues.empty and "leagueid" in leagues.columns:
        for _, row in leagues.iterrows():
            lid = _to_int(row.get("leagueid"), -1)
            if lid < 0:
                continue
            liga_nome[lid] = str(row.get("leaguename", "") or "").strip()
            try:
                liga_country[lid] = str(
                    int(pd.to_numeric(row.get("countryid"), errors="coerce") or 0)
                )
            except Exception:
                liga_country[lid] = "0"
            liga_women[lid] = _to_int(row.get("iswomencompetition"), 0)

    lids = df["teamid"].map(lambda t: liga_por_tid.get(int(t), 0))
    df["leagueid"] = lids.fillna(0).astype(int)
    df["leaguename"] = df["leagueid"].map(lambda lid: liga_nome.get(int(lid), ""))
    df["iswomencompetition"] = (
        df["leagueid"].map(lambda lid: liga_women.get(int(lid), 0)).fillna(0).astype(int)
    )
    df["countryid"] = df["nationality"].astype(str)
    mask_sem_pais = df["countryid"].isin(["0", ""])
    df.loc[mask_sem_pais, "countryid"] = df.loc[mask_sem_pais, "leagueid"].map(
        lambda lid: liga_country.get(int(lid), "0")
    )
    df["pais"] = df["countryid"].map(lambda c: dict_paises.get(str(c), ""))

    hide = df["leagueid"].isin(hidden_league_ids) | df["teamid"].isin(hidden_team_ids)
    df = df.loc[~hide].copy()
    df = df[df["teamname"].astype(str).str.len() > 0]
    df["teamname_norm"] = df["teamname"].map(normalizar_texto)
    return df.reset_index(drop=True)


def _texto_limpo(value):
    """Evita 'nan' vindo de float/pd.NA ao montar nomes."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    s = str(value).strip()
    if s.lower() in ("nan", "none", "nat", "<na>"):
        return ""
    return s


def display_name_jogador(row):
    """Nome na formação: commonname completo quando existir; senão sobrenome."""
    common = _texto_limpo(row.get("commonname"))
    last = _texto_limpo(row.get("lastname"))
    first = _texto_limpo(row.get("firstname"))
    playername = _texto_limpo(row.get("playername"))
    if common:
        nome = common
    else:
        nome = last or playername or first or "?"
        if " " in nome and nome == playername:
            nome = nome.split()[-1]
    if len(nome) > 14:
        nome = nome[:13] + "."
    return nome


def lineup_slots(aux, team_id, players_df, obter_foto_fn):
    """11 titulares; Y invertido (GK embaixo); X corrigido; perspectiva trapézio."""
    tid = int(team_id)
    formations = aux.get("formations")
    sheets = aux.get("default_teamsheets")
    tpl = aux.get("teamplayerlinks")
    if formations is None or formations.empty or sheets is None or sheets.empty:
        return [], ""

    frows = formations[pd.to_numeric(formations["teamid"], errors="coerce") == tid]
    trows = sheets[pd.to_numeric(sheets["teamid"], errors="coerce") == tid]
    if frows.empty or trows.empty:
        return [], ""

    formation = frows.iloc[0]
    teamsheet = trows.iloc[0]
    formation_name = str(formation.get("formationname", "") or "").strip()

    jersey_map = {}
    if tpl is not None and not tpl.empty:
        sub = tpl[pd.to_numeric(tpl["teamid"], errors="coerce") == tid]
        for _, row in sub.iterrows():
            pid = _to_int(row.get("playerid"), -1)
            if pid > 0:
                jersey_map[pid] = _to_int(row.get("jerseynumber"), 0)

    players_by_id = {}
    if players_df is not None and not players_df.empty:
        for _, row in players_df.iterrows():
            pid = _to_int(row.get("playerid"), -1)
            if pid > 0:
                players_by_id[pid] = row

    # Campo do usuário (trapézio): base larga / topo estreito.
    # GK ancora embaixo; ataque esticado um pouco mais para o topo.
    margin_x = 0.03
    margin_y_top = 0.08
    margin_y_bot = 0.10
    top_width = 0.62
    bot_width = 0.96
    y_stretch = 1.08  # leve empurrão do ataque; GK ancorado embaixo

    slots = []
    for i in range(11):
        ox = _to_float(formation.get(f"offset{i}x"), 0.5)
        oy = _to_float(formation.get(f"offset{i}y"), 0.5)
        pos_id = _to_int(formation.get(f"position{i}"), -1)

        # ny: 0 = ataque (topo), 1 = goleiro (base) — Y invertido vs offset do jogo
        ny = 1.0 - max(0.0, min(1.0, oy))
        ny = 1.0 - min(1.0, (1.0 - ny) * y_stretch)
        # X: sem inverter (L/R estava espelhado com 1-ox)
        nx = max(0.0, min(1.0, ox))

        depth_w = top_width + (bot_width - top_width) * ny
        usable_x = 1.0 - 2.0 * margin_x
        usable_y = 1.0 - margin_y_top - margin_y_bot
        left_pct = (0.5 + (nx - 0.5) * depth_w * usable_x) * 100.0
        top_pct = (margin_y_top + ny * usable_y) * 100.0

        pid = _to_int(teamsheet.get(f"playerid{i}"), -1)
        jog = players_by_id.get(pid)
        nome = "Vazio"
        ovr = 0
        foto = ""
        if jog is not None:
            nome = display_name_jogador(jog)
            ovr = _to_int(jog.get("overallrating"), 0)
            gender = _to_int(jog.get("gender"), 0)
            try:
                foto = obter_foto_fn(pid, gender) or ""
            except Exception:
                foto = ""
        jersey = jersey_map.get(pid, i + 1) if pid > 0 else i + 1
        slots.append(
            {
                "slot": i,
                "playerid": pid,
                "left": left_pct,
                "top": top_pct,
                "name": nome,
                "ovr": ovr,
                "foto": foto,
                "jersey": jersey,
                "pos": SHEET_POSITION_MAP.get(pos_id, ""),
            }
        )
    return slots, formation_name


def squad_rows(aux, team_id, players_df):
    tid = int(team_id)
    sheets = aux.get("default_teamsheets")
    formations = aux.get("formations")
    tpl = aux.get("teamplayerlinks")
    if sheets is None or sheets.empty:
        return []

    trows = sheets[pd.to_numeric(sheets["teamid"], errors="coerce") == tid]
    if trows.empty:
        return []
    teamsheet = trows.iloc[0]

    formation = None
    if formations is not None and not formations.empty:
        frows = formations[pd.to_numeric(formations["teamid"], errors="coerce") == tid]
        if not frows.empty:
            formation = frows.iloc[0]

    jersey_map = {}
    if tpl is not None and not tpl.empty:
        sub = tpl[pd.to_numeric(tpl["teamid"], errors="coerce") == tid]
        for _, row in sub.iterrows():
            pid = _to_int(row.get("playerid"), -1)
            if pid > 0:
                jersey_map[pid] = _to_int(row.get("jerseynumber"), 0)

    players_by_id = {}
    if players_df is not None and not players_df.empty:
        for _, row in players_df.iterrows():
            pid = _to_int(row.get("playerid"), -1)
            if pid > 0:
                players_by_id[pid] = row

    rows = []
    for i in range(52):
        col = f"playerid{i}"
        if col not in teamsheet.index:
            continue
        pid = _to_int(teamsheet.get(col), -1)
        if pid <= 0:
            continue
        if i <= 10:
            grupo = "Titular"
            pos_id = _to_int(formation.get(f"position{i}"), -1) if formation is not None else -1
            pos = SHEET_POSITION_MAP.get(pos_id, "")
        elif i <= 19:
            # Banco de reservas: 9 jogadores (slots 11–19)
            grupo = "Reserva"
            pos = "SUB"
        else:
            grupo = "Elenco"
            pos = "RES"
        jog = players_by_id.get(pid)
        nome = f"ID {pid}"
        ovr = 0
        pot = 0
        if jog is not None:
            common = _texto_limpo(jog.get("commonname"))
            first = _texto_limpo(jog.get("firstname"))
            last = _texto_limpo(jog.get("lastname"))
            pname = _texto_limpo(jog.get("playername"))
            nome = common or pname or f"{first} {last}".strip() or f"ID {pid}"
            ovr = _to_int(jog.get("overallrating"), 0)
            pot = _to_int(jog.get("potential"), 0)
        rows.append(
            {
                "slot": i,
                "grupo": grupo,
                "pos": pos,
                "playerid": pid,
                "name": nome,
                "jersey": jersey_map.get(pid, 0),
                "ovr": ovr,
                "pot": pot,
            }
        )
    return rows


def set_piece_roles(aux, team_id, players_df, obter_foto_fn):
    """Cobradores / capitão a partir de default_teamsheets."""
    roles_spec = (
        ("Capitão", "captainid"),
        ("Cobrador de Falta", "freekicktakerid"),
        ("Falta de Longe", "longkicktakerid"),
        ("Falta pela Direita", "rightfreekicktakerid"),
        ("Falta pela Esquerda", "leftfreekicktakerid"),
        ("Pênaltis", "penaltytakerid"),
        ("Escanteio Direita", "rightcornerkicktakerid"),
        ("Escanteio Esquerda", "leftcornerkicktakerid"),
    )
    sheets = aux.get("default_teamsheets")
    if sheets is None or sheets.empty:
        return [], None
    tid = int(team_id)
    trows = sheets[pd.to_numeric(sheets["teamid"], errors="coerce") == tid]
    if trows.empty:
        return [], None
    teamsheet = trows.iloc[0]

    players_by_id = {}
    if players_df is not None and not players_df.empty:
        for _, row in players_df.iterrows():
            pid = _to_int(row.get("playerid"), -1)
            if pid > 0:
                players_by_id[pid] = row

    out = []
    captain = None
    for label, col in roles_spec:
        if col not in teamsheet.index:
            continue
        pid = _to_int(teamsheet.get(col), -1)
        nome = "—"
        foto = ""
        if pid > 0 and pid in players_by_id:
            jog = players_by_id[pid]
            nome = display_name_jogador(jog)
            full = _texto_limpo(jog.get("playername")) or nome
            nome = full
            gender = _to_int(jog.get("gender"), 0)
            try:
                foto = obter_foto_fn(pid, gender) or ""
            except Exception:
                foto = ""
        elif pid > 0:
            nome = f"ID {pid}"
        item = {"label": label, "playerid": pid if pid > 0 else 0, "name": nome, "foto": foto}
        if label == "Capitão":
            captain = item
        else:
            out.append(item)
    return out, captain


def _sp_row_html(r, team_id=None):
    pid = int(r.get("playerid") or 0)
    foto = r.get("foto") or ""
    if not foto:
        foto = (
            "data:image/svg+xml;base64,"
            + base64.b64encode(
                b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
                b'<rect width="64" height="64" fill="#1f242b"/>'
                b'<circle cx="32" cy="25" r="11" fill="#3d444d"/>'
                b'<path d="M11 60c0-12 9-19 21-19s21 7 21 19z" fill="#3d444d"/></svg>'
            ).decode()
        )
    nome = html.escape(_texto_limpo(r.get("name")) or "—")
    label = html.escape(str(r.get("label") or ""))
    click = ""
    if pid > 0:
        click = f'data-q="modo=jogadores&pid={pid}"'
        if team_id is not None:
            click = f'data-q="modo=jogadores&pid={pid}&tid={int(team_id)}"'
    return (
        f'<div class="sp-row" {click}>'
        f'<div class="sp-label">{label}</div>'
        f'<img class="sp-foto" src="{foto}" alt="">'
        f'<div class="sp-nome">{nome}</div>'
        f"</div>"
    )


def html_set_pieces(roles, team_id=None, captain=None):
    """Painel de cobradores à direita da formação (Capitão acima do título)."""
    if not roles and not captain:
        return ""
    cap_html = _sp_row_html(captain, team_id) if captain else ""
    items = [_sp_row_html(r, team_id) for r in (roles or [])]
    return f"""
<style>
.sp-wrap {{
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0 0 0 4px;
  background: transparent !important;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}}
.sp-cap {{
  flex: 0 0 auto;
  margin: 0 0 2px 0;
}}
.sp-cap .sp-row {{
  border-bottom: none;
  padding: 2px 2px 4px 2px;
}}
.sp-sep {{
  flex: 0 0 auto;
  height: 1px;
  background: #30363d;
  margin: 4px 2px 6px 2px;
}}
.sp-list {{
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 0;
}}
.sp-row {{
  display: grid;
  grid-template-columns: minmax(118px, 0.95fr) 32px minmax(120px, 1.35fr);
  column-gap: 8px; align-items: center;
  padding: 2px 2px;
  border-bottom: 1px solid #21262d;
  cursor: pointer;
  background: transparent !important;
}}
.sp-row:last-child {{ border-bottom: none; }}
.sp-row:hover {{ background: rgba(255,255,255,0.03) !important; }}
.sp-label {{
  color: #c9d1d9; font-size: 0.78rem; font-weight: 600;
  line-height: 1.15;
}}
.sp-foto {{
  width: 30px; height: 30px; border-radius: 50%; object-fit: cover;
  border: 1px solid #30363d; background: #0f1216; display: block;
}}
.sp-nome {{
  color: #fff; font-size: 0.84rem; font-weight: 700;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  min-width: 0;
}}
</style>
<div class="sp-wrap">
  {f'<div class="sp-cap">{cap_html}</div>' if cap_html else ''}
  {f'<div class="sp-sep"></div>' if cap_html and items else ''}
  <div class="sp-list">{''.join(items)}</div>
</div>
<script>
(function(){{
  function rootWin(){{
    try {{ if (window.parent && window.parent!==window) return window.parent; }} catch(e){{}}
    return window;
  }}
  function go(q){{
    var root = rootWin();
    var u = new URL(root.location.href);
    ['pid','tid','from_pid','page','sort','asc','s','modo','voltar'].forEach(function(k){{ u.searchParams.delete(k); }});
    var incoming = new URLSearchParams(q);
    incoming.forEach(function(v,k){{ u.searchParams.set(k,v); }});
    if (!incoming.has('modo')) {{
      if (incoming.has('pid')) u.searchParams.set('modo', 'jogadores');
      else if (incoming.has('tid')) u.searchParams.set('modo', 'times');
      else u.searchParams.set('modo', 'times');
    }}
    root.location.href = u.pathname + '?' + u.searchParams.toString();
  }}
  document.querySelectorAll('.sp-wrap [data-q]').forEach(function(el){{
    el.addEventListener('click', function(ev){{
      ev.preventDefault(); ev.stopPropagation();
      var q = el.getAttribute('data-q');
      if (q) go(q);
    }});
  }});
}})();
</script>
"""


def html_pitch(slots, formation_name="", team_id=None):
    bg = field_background_uri()
    fw, fh = field_aspect_ratio()
    markers = []
    for s in slots:
        foto = s.get("foto") or ""
        if not foto:
            foto = (
                "data:image/svg+xml;base64,"
                + base64.b64encode(
                    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
                    b'<rect width="64" height="64" fill="#1f242b"/>'
                    b'<circle cx="32" cy="25" r="11" fill="#3d444d"/>'
                    b'<path d="M11 60c0-12 9-19 21-19s21 7 21 19z" fill="#3d444d"/></svg>'
                ).decode()
            )
        nome = html.escape(_texto_limpo(s.get("name")) or "?")
        ovr = int(s.get("ovr") or 0)
        left = float(s.get("left") or 50)
        top = float(s.get("top") or 50)
        pid = int(s.get("playerid") or 0)
        if pid > 0:
            click = f'data-q="modo=jogadores&pid={pid}"'
            if team_id is not None:
                click = f'data-q="modo=jogadores&pid={pid}&tid={int(team_id)}"'
        else:
            click = ""
        # Âncora = só a foto (centro tático). OVR e nome não deslocam o centro.
        markers.append(
            f'<div class="tm-slot" style="left:{left:.2f}%;top:{top:.2f}%;" {click}>'
            f'<div class="tm-photo-wrap">'
            f'<img class="tm-foto" src="{foto}" alt="">'
            f'<span class="tm-ovr">{ovr}</span>'
            f"</div>"
            f'<div class="tm-nome">{nome}</div>'
            f"</div>"
        )
    if formation_name:
        titulo = html.escape(f"Formation: {formation_name}")
    else:
        titulo = "Formation"
    # PNG com alpha via <img> — sem background sólido por baixo
    bg_img = (
        f'<img class="tm-pitch-bg" src="{bg}" alt="" draggable="false">'
        if bg
        else ""
    )
    return f"""
<style>
.tm-pitch-wrap {{
  width: 100%;
  max-width: 920px;
  margin: 0 0 12px 0;
  background: transparent !important;
}}
.tm-form-name {{
  text-align: center; color: #c9d1d9; font-weight: 700;
  margin: 0 0 6px 0; font-size: 0.95rem;
}}
.tm-pitch {{
  position: relative;
  width: 100%;
  aspect-ratio: {fw} / {fh};
  background: transparent !important;
  background-color: transparent !important;
  border-radius: 0;
  border: none;
  overflow: visible;
  box-shadow: none;
}}
.tm-pitch-bg {{
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: fill;
  display: block;
  pointer-events: none;
  z-index: 0;
  background: transparent !important;
}}
.tm-slot {{
  position: absolute;
  /* Centro do slot = centro da foto (largura fixa = foto) */
  width: 60px;
  transform: translate(-50%, -50%);
  cursor: pointer;
  z-index: 2;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}}
.tm-photo-wrap {{
  position: relative;
  width: 60px;
  height: 60px;
  background: transparent !important;
}}
.tm-foto {{
  width: 60px; height: 60px;
  object-fit: cover;
  display: block;
  border: none !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}}
.tm-ovr {{
  position: absolute;
  left: calc(100% + 3px);
  bottom: 2px;
  color: #fff;
  font-size: 1.05rem;
  font-weight: 800;
  line-height: 1;
  text-shadow: 0 1px 3px #000, 0 0 6px #000;
  background: transparent !important;
  white-space: nowrap;
  pointer-events: none;
}}
.tm-nome {{
  color: #fff;
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.15;
  text-shadow: 0 1px 3px #000, 0 0 6px #000;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 110px;
  margin-left: 50%;
  transform: translateX(-50%);
  text-align: center;
  margin-top: 4px;
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}}
</style>
<div class="tm-pitch-wrap">
  <div class="tm-form-name">{titulo}</div>
  <div class="tm-pitch">{bg_img}{''.join(markers)}</div>
</div>
<script>
(function(){{
  function rootWin(){{
    try {{ if (window.parent && window.parent!==window) return window.parent; }} catch(e){{}}
    return window;
  }}
  function go(q){{
    var root = rootWin();
    var u = new URL(root.location.href);
    ['pid','tid','from_pid','page','sort','asc','s','modo','voltar'].forEach(function(k){{ u.searchParams.delete(k); }});
    var incoming = new URLSearchParams(q);
    incoming.forEach(function(v,k){{ u.searchParams.set(k,v); }});
    if (!incoming.has('modo')) {{
      if (incoming.has('pid')) u.searchParams.set('modo', 'jogadores');
      else if (incoming.has('tid')) u.searchParams.set('modo', 'times');
      else u.searchParams.set('modo', 'times');
    }}
    root.location.href = u.pathname + '?' + u.searchParams.toString();
  }}
  document.querySelectorAll('.tm-pitch [data-q]').forEach(function(el){{
    el.addEventListener('click', function(ev){{
      ev.preventDefault(); ev.stopPropagation();
      var q = el.getAttribute('data-q');
      if (q) go(q);
    }});
  }});
}})();
</script>
"""


def html_formacao_e_bolas(slots, formation_name, roles, team_id=None, captain=None):
    """Formação à esquerda + bolas paradas à direita (mesma altura do campo)."""
    pitch = html_pitch(slots, formation_name, team_id=team_id)
    roles_html = html_set_pieces(roles, team_id=team_id, captain=captain) if (roles or captain) else ""
    if not roles_html:
        return pitch
    return f"""
<style>
.tt-layout {{
  display: flex;
  align-items: stretch;
  gap: 20px;
  width: 100%;
  margin: 0 0 20px 0;
  background: transparent !important;
}}
.tt-pitch-col {{
  flex: 1.7 1 0;
  min-width: 0;
}}
.tt-pitch-col .tm-pitch-wrap {{
  margin-bottom: 0 !important;
  max-width: none;
}}
.tt-roles-col {{
  flex: 1 1 300px;
  max-width: 440px;
  display: flex;
  align-items: stretch;
  min-width: 260px;
}}
.tt-roles-col .sp-wrap {{
  width: 100%;
  height: 100%;
}}
@media (max-width: 900px) {{
  .tt-layout {{ flex-direction: column; }}
  .tt-roles-col {{ max-width: none; min-height: 0; }}
  .tt-roles-col .sp-list {{ justify-content: flex-start; gap: 0; }}
}}
</style>
<div class="tt-layout">
  <div class="tt-pitch-col">{pitch}</div>
  <div class="tt-roles-col">{roles_html}</div>
</div>
"""


def _cor(v):
    try:
        n = int(v)
    except Exception:
        n = 0
    if n >= 80:
        return "#2e7d32"
    if n >= 70:
        return "#f9a825"
    if n >= 60:
        return "#ef6c00"
    return "#c62828"


def _itens_paginacao(pagina, total_paginas, proximas=3):
    """Mesma janela de páginas da lista de jogadores."""
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


def html_lista_times(df_pagina, pagina=1, total_paginas=1, estado_ui="", obter_crest_fn=None):
    pagina = max(1, int(pagina or 1))
    total_paginas = max(1, int(total_paginas or 1))
    pagina = min(pagina, total_paginas)
    rows = []
    for _, t in df_pagina.iterrows():
        tid = int(t["teamid"])
        nome = html.escape(str(t.get("teamname", "")))
        liga = html.escape(str(t.get("leaguename", "") or ""))
        ovr = int(t.get("overallrating") or 0)
        defe = int(t.get("defenserating") or 0)
        meio = int(t.get("midfieldrating") or 0)
        ata = int(t.get("attackrating") or 0)
        crest = ""
        if obter_crest_fn is not None:
            try:
                crest = obter_crest_fn(tid) or ""
            except Exception:
                crest = ""
        if crest:
            logo_html = (
                f'<img class="tl-logo" src="{crest}" alt="" '
                f'onerror="this.onerror=null;this.style.display=\'none\'">'
            )
        else:
            logo_html = '<div class="tl-logo tl-logo-fallback">🏟️</div>'
        rows.append(
            f'<div class="tl-grid tl-card" data-q="modo=times&tid={tid}&page={pagina}">'
            f'<div class="tl-c">{logo_html}</div>'
            f'<div class="tl-info">'
            f'<div class="tl-nome">{nome}</div>'
            f'<div class="tl-sub">ID {tid}</div>'
            f"</div>"
            f'<div class="tl-c"><div class="pl-badge" style="background:{_cor(ovr)}">{ovr}</div></div>'
            f'<div class="tl-liga">{liga}</div>'
            f'<div class="tl-c"><div class="pl-badge-sm" style="background:{_cor(defe)}">{defe}</div></div>'
            f'<div class="tl-c"><div class="pl-badge-sm" style="background:{_cor(meio)}">{meio}</div></div>'
            f'<div class="tl-c"><div class="pl-badge-sm" style="background:{_cor(ata)}">{ata}</div></div>'
            f"</div>"
        )

    header = (
        '<div class="tl-grid tl-head">'
        '<div class="pl-h-spacer"></div>'
        '<div class="pl-h pl-h-nome">Time</div>'
        '<div class="pl-h">OVR</div>'
        '<div class="pl-h">Liga</div>'
        '<div class="pl-h">Def</div>'
        '<div class="pl-h">Meio</div>'
        '<div class="pl-h">Ata</div>'
        "</div>"
    )

    prev_dis = " pl-page-disabled" if pagina <= 1 else ""
    next_dis = " pl-page-disabled" if pagina >= total_paginas else ""
    pager_parts = [
        f'<div class="pl-page pl-page-arrow{prev_dis}" data-q="modo=times&page={pagina - 1}" '
        f'title="Anterior" aria-label="Página anterior">‹</div>',
    ]
    for item in _itens_paginacao(pagina, total_paginas):
        if item == "…":
            pager_parts.append('<div class="pl-page pl-page-ellipsis">…</div>')
            continue
        ativo = " pl-page-active" if item == pagina else ""
        pager_parts.append(
            f'<div class="pl-page{ativo}" data-q="modo=times&page={item}">{item}</div>'
        )
    pager_parts.append(
        f'<div class="pl-page pl-page-arrow{next_dis}" data-q="modo=times&page={pagina + 1}" '
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
        f'<div class="pl-pager tl-pager">{"".join(pager_parts)}'
        f'<div class="pl-pager-meta">Página {pagina} de {total_paginas}</div></div>'
    )

    css = """
    .tl-scroll { width:100%; overflow-x:auto; }
    .tl-lista { display:flex; flex-direction:column; gap:4px; min-width:720px; }
    .tl-grid {
      display:grid;
      grid-template-columns: 48px minmax(160px,2.2fr) 40px minmax(120px,1.4fr) repeat(3, 36px);
      column-gap:10px; align-items:center; width:100%;
      padding:6px 10px; box-sizing:border-box;
    }
    .tl-head { border-bottom:1px solid #30363d; margin-bottom:2px; }
    .tl-card {
      background:#21262d !important; border:1px solid #30363d !important;
      border-radius:8px !important; cursor:pointer;
    }
    .tl-card:hover { background:#2a3038 !important; border-color:#484f58 !important; }
    .tl-logo {
      width:44px; height:44px; border-radius:50%; background:#0f1216;
      border:2px solid #30363d; display:flex; align-items:center; justify-content:center;
      font-size:1.2rem; object-fit:contain; box-sizing:border-box; padding:2px;
    }
    img.tl-logo { display:block; padding:3px; }
    .tl-nome { font-size:1rem; font-weight:700; color:#fff; margin:0; }
    .tl-sub { font-size:0.68rem; color:#9aa4b2; margin:1px 0 0 0; }
    .tl-liga {
      font-size:0.78rem; color:#c9d1d9; text-align:center;
      overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
    }
    .tl-c { display:flex; justify-content:center; align-items:center; }
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
    estado_js = json_dumps_safe(estado_ui)
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
        ['pid','tid','from_pid','page','sort','asc','s','modo','voltar'].forEach(function(k){{ u.searchParams.delete(k); }});
        var incoming = new URLSearchParams(q);
        incoming.forEach(function(v,k){{ u.searchParams.set(k,v); }});
        if (!incoming.has('modo')) {{
          if (incoming.has('pid')) u.searchParams.set('modo', 'jogadores');
          else if (incoming.has('tid')) u.searchParams.set('modo', 'times');
          else u.searchParams.set('modo', 'times');
        }}
        if (typeof SLP_UI_STATE === 'string' && SLP_UI_STATE) u.searchParams.set('s', SLP_UI_STATE);
        root.location.href = u.pathname + '?' + u.searchParams.toString();
      }}
      function goFromInput(){{
        var inp = document.querySelector('.tl-pager .pl-page-input');
        if (!inp) return;
        var max = parseInt(inp.getAttribute('max'), 10) || 1;
        var n = parseInt(inp.value, 10);
        if (isNaN(n)) return;
        if (n < 1) n = 1;
        if (n > max) n = max;
        go('modo=times&page=' + n);
      }}
      document.querySelectorAll('.tl-lista [data-q]').forEach(function(el){{
        el.addEventListener('click', function(ev){{
          ev.preventDefault(); ev.stopPropagation();
          var q = el.getAttribute('data-q');
          if (q) go(q);
        }});
      }});
      document.querySelectorAll('.tl-pager [data-q]').forEach(function(el){{
        el.addEventListener('click', function(ev){{
          ev.preventDefault(); ev.stopPropagation();
          if (el.classList.contains('pl-page-disabled') || el.classList.contains('pl-page-active')) return;
          var q = el.getAttribute('data-q');
          if (q) go(q);
        }});
      }});
      var gotoBtn = document.querySelector('.tl-pager .pl-page-go');
      var gotoInp = document.querySelector('.tl-pager .pl-page-input');
      if (gotoBtn) {{
        gotoBtn.addEventListener('click', function(ev){{
          ev.preventDefault(); ev.stopPropagation();
          goFromInput();
        }});
      }}
      if (gotoInp) {{
        gotoInp.addEventListener('keydown', function(ev){{
          if (ev.key === 'Enter') {{
            ev.preventDefault(); ev.stopPropagation();
            goFromInput();
          }}
        }});
        gotoInp.addEventListener('click', function(ev){{ ev.stopPropagation(); }});
      }}
    }})();
    </script>
    """
    return (
        f"<style>{css}</style>"
        f'<div class="tl-scroll"><div class="tl-lista">{header}{"".join(rows)}</div></div>'
        f"{pager}"
        f"{script}"
    )


def json_dumps_safe(value):
    import json
    return json.dumps(value if value is not None else "")

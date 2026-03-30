import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import gspread
from google.oauth2.service_account import Credentials
import numpy as np
import re
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To

def send_email_notification(to_email, subject, body):
    try:
        to_email = str(to_email).strip() if to_email else ''
        if not to_email or to_email == 'nan' or '@' not in to_email:
            st.warning(f"⚠️ Correo no enviado: destinatario inválido ('{to_email}')")
            return False
        if "sendgrid" not in st.secrets:
            st.error("Error: Configuración de 'sendgrid' no encontrada en st.secrets.")
            return False
        sg = SendGridAPIClient(api_key=st.secrets["sendgrid"]["api_key"])
        from_email = Email(
            "datahublobueno@gmail.com",
            st.secrets["sendgrid"].get("from_name", "Synapse Data Hub")
        )
        message = Mail(
            from_email=from_email,
            to_emails=To(to_email),
            subject=str(subject),
            html_content=str(body)
        )
        response = sg.send(message)
        if response.status_code in [200, 201, 202]:
            st.toast(f"✅ Correo enviado a {to_email}")
            return True
        else:
            st.error(f"SendGrid respondió con código {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Error enviando email a {to_email}: {str(e)}")
        return False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Synapse | Data Ops", page_icon="⚡", layout="wide")

CATEGORIAS_DATA = [
    "📈 Reportes y Rendimiento",
    "🕵️ Inteligencia Competitiva",
    "⚙️ Ingeniería y Gobierno de Datos",
    "📊 Dashboards y Visualización",
    "🔍 Investigación Estratégica y Audiencias",
    "⚡ Análisis Ad-Hoc",
    "🤖 Innovación y Entrenamiento (IA)"
]

# --- CONFIGURACIÓN DE NIVEL DE SERVICIO (SLA ANTIGRAVITY) ---
SLA_MAPPING = {
    1: {"label": "Nivel 1: Consulta Puntual", "horas": 0.5, "dias_habiles": 1},
    2: {"label": "Nivel 2: Reporte Básico",   "horas": 3.0, "dias_habiles": 2},
    3: {"label": "Nivel 3: Informe Medio",    "horas": 8.0, "dias_habiles": 3},
    4: {"label": "Nivel 4: Informe Complejo", "horas": 24.0, "dias_habiles": 5},
    5: {"label": "Nivel 5: Dashboard Medio",  "horas": 45.0, "dias_habiles": 15},
    6: {"label": "Nivel 6: Alta Estrategia",  "horas": 60.0, "dias_habiles": 20}
}

def calcular_entrega_antigravity(nivel_id):
    config = SLA_MAPPING.get(nivel_id)
    if not config: return datetime.now()
    fecha_actual = datetime.now()
    dias_a_sumar = int(config["dias_habiles"])
    while dias_a_sumar > 0:
        fecha_actual += timedelta(days=1)
        if fecha_actual.weekday() < 5:
            dias_a_sumar -= 1
    return fecha_actual

# --- DISEÑO MEJORADO (CSS PREMIUM) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .title-banner {
        background: linear-gradient(135deg, #111111 0%, #1a1a1a 100%);
        padding: 40px 30px;
        border-radius: 12px;
        margin-bottom: 30px;
        border-left: 6px solid #f97316;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    .title-banner h1 {
        margin: 0; font-size: 3.5rem; font-weight: 300;
        letter-spacing: 2px; color: white; line-height: 1.1;
    }
    .title-banner p {
        margin: 10px 0 0 0; font-size: 0.9rem;
        letter-spacing: 4px; color: #aaa; text-transform: uppercase;
    }
    .highlight { color: #f97316; font-weight: 600; }
    .brand-blue { color: #3b82f6; }
    
    div[data-testid="stTabs"] button {
        font-size: 1.1rem; border-radius: 4px; padding: 10px 20px; transition: all 0.3s ease;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: white !important; background-color: #f97316 !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] > div { background-color: transparent !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] p { color: white !important; font-weight: bold !important; }
    div[data-testid="metric-container"] {
        border-radius: 12px; padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .streamlit-expanderHeader { border-radius: 8px; border: 1px solid rgba(128, 128, 128, 0.2); }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_resource
def get_gsheets_client():
    if "gcp_service_account" not in st.secrets: return None
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error autenticando: {e}")
        return None

@st.cache_resource
def get_sheet():
    client = get_gsheets_client()
    if not client: return None
    try:
        url = st.secrets.get("google_sheets", {}).get("spreadsheet_url", "")
        if not url: return None
        return client.open_by_url(url)
    except Exception as e:
        st.error(f"Error abriendo Google Sheet: {e}")
        return None

@st.cache_data(ttl=60)
def _load_users():
    s = get_sheet()
    try: return pd.DataFrame(s.worksheet('USERS').get_all_records(default_blank=np.nan))
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def _load_brands():
    s = get_sheet()
    try: return pd.DataFrame(s.worksheet('BRANDS').get_all_records(default_blank=np.nan))
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def _load_reqs():
    s = get_sheet()
    try: return pd.DataFrame(s.worksheet('REQUESTS').get_all_records(default_blank=np.nan))
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def _load_weekly():
    s = get_sheet()
    try: return pd.DataFrame(s.worksheet('WEEKLY_ASSIGNMENTS').get_all_records(default_blank=np.nan))
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def _load_types():
    s = get_sheet()
    try: return pd.DataFrame(s.worksheet('REQUEST_TYPES').get_all_records(default_blank=np.nan))
    except: return pd.DataFrame()

def load_table(t):
    if t == 'USERS': return _load_users()
    if t == 'BRANDS': return _load_brands()
    if t == 'REQUESTS': return _load_reqs()
    if t == 'WEEKLY_ASSIGNMENTS': return _load_weekly()
    if t == 'REQUEST_TYPES': return _load_types()
    return pd.DataFrame()

def clear_cache(t=None):
    if t == 'USERS': _load_users.clear()
    elif t == 'BRANDS': _load_brands.clear()
    elif t == 'REQUESTS': _load_reqs.clear()
    elif t == 'WEEKLY_ASSIGNMENTS': _load_weekly.clear()
    elif t == 'REQUEST_TYPES': _load_types.clear()
    else: st.cache_data.clear()

def save_row(table_name, row_dict):
    sheet = get_sheet()
    if not sheet: return False
    try:
        ws = sheet.worksheet(table_name)
        headers = ws.row_values(1)
        if not headers:
            headers = list(row_dict.keys())
            ws.append_row(headers)
        row_values = [str(row_dict.get(h, "")) if not pd.isna(row_dict.get(h, "")) else "" for h in headers]
        ws.append_row(row_values)
        clear_cache(table_name)
        return True
    except Exception as e:
        st.error(f"Error guardando en {table_name}: {e}")
        return False

def update_row(table_name, match_col, match_val, update_dict):
    import time
    sheet = get_sheet()
    if not sheet: return False
    for attempt in range(3):
        try:
            ws = sheet.worksheet(table_name)
            headers = ws.row_values(1)
            
            df = load_table(table_name)
            if df.empty or match_col not in df.columns: return False
            
            matches = df.index[df[match_col].astype(str) == str(match_val)].tolist()
            if not matches: return False
            sheet_row = matches[0] + 2
            
            for k, v in update_dict.items():
                if k in headers:
                    c_idx = headers.index(k) + 1
                    val = "" if pd.isna(v) else str(v)
                    ws.update_cell(sheet_row, c_idx, val)
                    
            clear_cache(table_name)
            return True
        except Exception as e:
            if "429" in str(e):
                time.sleep(2)
            else:
                st.error(f"Error actualizando en {table_name}: {e}")
                return False
    st.error("Límite de Google Sheets superado. Espera 60 segundos por favor.")
    return False

def delete_row(table_name, match_col, match_val):
    import time
    sheet = get_sheet()
    if not sheet: return False
    for attempt in range(3):
        try:
            ws = sheet.worksheet(table_name)
            df = load_table(table_name)
            if df.empty or match_col not in df.columns: return False
            
            matches = df.index[df[match_col].astype(str) == str(match_val)].tolist()
            if not matches: return False
            sheet_row = matches[0] + 2
            
            ws.delete_rows(sheet_row)
            clear_cache(table_name)
            return True
        except Exception as e:
            if "429" in str(e):
                time.sleep(2)
            else:
                st.error(f"Error borrando en {table_name}: {e}")
                return False
    st.error("Límite de Google Sheets superado. Espera 60 segundos por favor.")
    return False

def generate_id(table_name, id_col):
    df = load_table(table_name)
    if df.empty or id_col not in df.columns: return 1
    max_val = pd.to_numeric(df[id_col], errors='coerce').max()
    return int(max_val) + 1 if not pd.isna(max_val) else 1

# --- LÓGICA DE DATOS ---
def get_users():
    df = load_table('USERS')
    if not df.empty and 'IS_ACTIVE' in df.columns:
        df = df[df['IS_ACTIVE'].astype(str).str.upper().isin(['TRUE', '1', 'YES'])]
    return df

def get_brands():
    df = load_table('BRANDS')
    if not df.empty and 'IS_ACTIVE' in df.columns:
        df = df[df['IS_ACTIVE'].astype(str).str.upper().isin(['TRUE', '1', 'YES'])]
    return df

def get_request_types():
    df = load_table('REQUEST_TYPES')
    if not df.empty and 'IS_ACTIVE' in df.columns:
        df = df[df['IS_ACTIVE'].astype(str).str.upper().isin(['TRUE', '1', 'YES'])]
    return df

def get_team_members():
    df = get_users()
    if not df.empty:
        valid_pos = ['DATA_LEAD', 'DATA LEAD', 'DATA_STRATEGIST', 'DATA STRATEGIST', 'DATA_ANALYST', 'DATA ANALYST', 'RESEARCH_EXECUTIVE', 'RESEARCH EXECUTIVE', 'DATA_RESEARCH', 'DATA RESEARCH', 'DATA_OPS', 'DATA OPS']
        df = df[df['POSITION'].astype(str).str.upper().isin(valid_pos)]
        df = df.sort_values(by=['POSITION', 'FULL_NAME'])
    return df

def get_requests():
    req = load_table('REQUESTS')
    users = get_users()
    brands = get_brands()
    if req.empty: return req
    
    if not brands.empty:
        req = req.merge(brands[['BRAND_ID', 'BRAND_NAME']], on='BRAND_ID', how='left')
    else: req['BRAND_NAME'] = 'N/A'
    
    if not users.empty:
        req = req.merge(users[['USER_ID', 'FULL_NAME', 'EMAIL']], left_on='ASSIGNED_TO', right_on='USER_ID', how='left')
        req.rename(columns={'FULL_NAME': 'ASSIGNED_TO_NAME', 'EMAIL': 'ASSIGNED_TO_EMAIL'}, inplace=True)
        if 'REQUESTER_EMAIL' in req.columns and 'EMAIL' in users.columns:
            u_dd = users[['EMAIL', 'FULL_NAME']].drop_duplicates('EMAIL')
            req = req.merge(u_dd, left_on='REQUESTER_EMAIL', right_on='EMAIL', how='left')
            req.rename(columns={'FULL_NAME': 'REQUESTER_NAME'}, inplace=True)
    else: req['ASSIGNED_TO_NAME'] = 'Sin asignar'
    
    req['BRAND_NAME'] = req.get('BRAND_NAME', 'N/A')
    req['ASSIGNED_TO_NAME'] = req.get('ASSIGNED_TO_NAME', 'Sin asignar').fillna('Sin asignar')
    req['REQUESTER_NAME'] = req.get('REQUESTER_NAME', req.get('REQUESTER_EMAIL', 'Desconocido')).fillna(req.get('REQUESTER_EMAIL', 'Desconocido'))
    
    req['PRIORITY_SCORE'] = pd.to_numeric(req.get('PRIORITY_SCORE', 0), errors='coerce').fillna(0)
    req['TOTAL_ESTIMATED_HOURS'] = pd.to_numeric(req.get('TOTAL_ESTIMATED_HOURS', 40), errors='coerce').fillna(40)
    
    # Calcular Horas Planeadas/Ejecutadas
    assigns = load_table('WEEKLY_ASSIGNMENTS')
    if not assigns.empty and 'HOURS_ASSIGNED' in assigns.columns:
        assigns['HOURS_ASSIGNED'] = pd.to_numeric(assigns['HOURS_ASSIGNED'], errors='coerce').fillna(0)
        planned = assigns.groupby('REQUEST_ID')['HOURS_ASSIGNED'].sum().reset_index()
        planned.rename(columns={'HOURS_ASSIGNED': 'HOURS_EXECUTED'}, inplace=True)
        req = req.merge(planned, on='REQUEST_ID', how='left')
    else:
        req['HOURS_EXECUTED'] = 0
        
    req['HOURS_EXECUTED'] = pd.to_numeric(req.get('HOURS_EXECUTED', 0), errors='coerce').fillna(0)
    req['HOURS_REMAINING'] = req['TOTAL_ESTIMATED_HOURS'] - req['HOURS_EXECUTED']
    
    def extract_rw(c):
        if pd.isna(c): return 0.0
        return sum(float(m) for m in re.findall(r'\(\+([0-9.]+)h\)', str(c)))
        
    if 'BUSINESS_CONTEXT' in req.columns:
        req['REWORK_HOURS'] = req['BUSINESS_CONTEXT'].apply(extract_rw)
    else: req['REWORK_HOURS'] = 0.0
    req['IS_REWORKED'] = req['REWORK_HOURS'] > 0
    
    return req

def get_pending_requests():
    req = get_requests()
    if req.empty: return req
    pending = req[req['STATUS'].astype(str).str.upper() == 'PENDIENTE']
    if pending.empty: return pending
    pending['TOTAL_ESTIMATED_HOURS'] = pd.to_numeric(pending.get('TOTAL_ESTIMATED_HOURS', 40), errors='coerce').fillna(40)
    return pending.sort_values('PRIORITY_SCORE', ascending=False)

def get_my_assigned_tasks(email):
    req = get_requests()
    if req.empty or 'ASSIGNED_TO_EMAIL' not in req.columns: return pd.DataFrame()
    my_tasks = req[req['ASSIGNED_TO_EMAIL'].astype(str).str.strip().str.upper() == email.strip().upper()]
    
    def get_days(d):
        try: return (datetime.strptime(str(d), "%Y-%m-%d").date() - date.today()).days
        except: return 0
    
    if not my_tasks.empty:
        my_tasks['DAYS_TO_DEADLINE'] = my_tasks['DEADLINE'].apply(get_days)
    return my_tasks

def get_in_progress_tasks():
    req = get_requests()
    if req.empty: return req
    inp = req[req['STATUS'].astype(str).str.upper() == 'EN PROGRESO']
    return inp.sort_values('PRIORITY_SCORE', ascending=False)

def get_task_weekly_plan(request_id):
    wa = load_table('WEEKLY_ASSIGNMENTS')
    usr = load_table('USERS')
    if wa.empty: return pd.DataFrame()
    
    wa = wa[wa['REQUEST_ID'].astype(str) == str(request_id)]
    if not wa.empty and not usr.empty:
        wa = wa.merge(usr[['USER_ID', 'FULL_NAME']], on='USER_ID', how='left')
    else:
        wa['FULL_NAME'] = 'Desconocido'
    return wa.sort_values('WEEK_START')

def get_workload_by_week(week_start):
    wa = load_table('WEEKLY_ASSIGNMENTS')
    usr = get_team_members()
    if usr.empty: return pd.DataFrame()
    
    if not wa.empty:
        wa = wa[wa['WEEK_START'].astype(str) == str(week_start)]
        if not wa.empty:
            agg = wa.groupby('USER_ID')[['HOURS_ASSIGNED', 'HOURS_MON', 'HOURS_TUE', 'HOURS_WED', 'HOURS_THU', 'HOURS_FRI']].sum().reset_index()
            usr = usr.merge(agg, on='USER_ID', how='left')
        else:
            for c in ['HOURS_ASSIGNED', 'HOURS_MON', 'HOURS_TUE', 'HOURS_WED', 'HOURS_THU', 'HOURS_FRI']: usr[c] = 0
    else:
        for c in ['HOURS_ASSIGNED', 'HOURS_MON', 'HOURS_TUE', 'HOURS_WED', 'HOURS_THU', 'HOURS_FRI']: usr[c] = 0
        
    return usr.fillna(0).sort_values('FULL_NAME')

def get_tasks_needing_review():
    req = get_requests()
    if req.empty: return req
    # Mostrar como alerta tareas bloqueadas o esperando info
    df = req[req['STATUS'].astype(str).str.upper().isin(['BLOQUEADO', 'ESPERANDO INFO'])]
    if not df.empty:
        df['ALERT_STATUS'] = 'URGENT'
        df['PERCENT_TIME_USED'] = 100
    return df

def get_current_week_start():
    today = date.today()
    return today - timedelta(days=today.weekday())

def get_week_options(num_weeks=8):
    current = get_current_week_start()
    return [(current + timedelta(weeks=i), f"Sem {i+1}: {(current + timedelta(weeks=i)).strftime('%d/%m')} - {(current + timedelta(weeks=i) + timedelta(days=4)).strftime('%d/%m')}") for i in range(num_weeks)]

# --- ACCIONES ---
def insert_request(data):
    data['REQUEST_ID'] = generate_id('REQUESTS', 'REQUEST_ID')
    data['STATUS'] = 'PENDIENTE'
    data['UPDATED_AT'] = str(datetime.now())
    return save_row('REQUESTS', data)

def add_weekly_assignment(request_id, user_id, week_start, hours, created_by, notes, hw):
    data = {
        'ASSIGNMENT_ID': generate_id('WEEKLY_ASSIGNMENTS', 'ASSIGNMENT_ID'),
        'REQUEST_ID': request_id, 'USER_ID': user_id, 'WEEK_START': str(week_start),
        'HOURS_ASSIGNED': hours, **hw, 'CREATED_BY': created_by, 'NOTES': notes
    }
    return save_row('WEEKLY_ASSIGNMENTS', data)

def mark_task_complete(request_id):
    return update_row('REQUESTS', 'REQUEST_ID', request_id, {
        'STATUS': 'COMPLETADO', 'COMPLETED_AT': str(datetime.now()), 'UPDATED_AT': str(datetime.now())
    })

# --- SESIÓN DE USUARIO (LOGIN) ---

import base64
import os

def render_logo(width=350):
    if os.path.exists("assets/new_logo.png"):
        with open("assets/new_logo.png", "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        st.markdown(
            f'''
            <div style="background-color: #111111; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 25px;">
                <img src="data:image/png;base64,{encoded}" style="max-width: {width}px; width: 100%; height: auto;">
            </div>
            ''',
            unsafe_allow_html=True
        )
    else:
        st.title("Synapse")

if "user_email" not in st.session_state:
    # Logo
    render_logo(width=400)
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.info("👋 Bienvenido a Synapse. Por favor, ingresa tu correo para continuar.")
        email_input = st.text_input("Correo electrónico", placeholder="ejemplo@lobueno.com")
        if st.button("Ingresar", type="primary", use_container_width=True):
            if email_input:
                st.session_state.user_email = email_input.strip()
                clear_cache()
                st.rerun()
            else:
                st.error("Por favor, ingresa un correo válido.")
    st.stop()

user_email = st.session_state.user_email
users_df = load_table('USERS')
if not users_df.empty:
    user_match = users_df[users_df['EMAIL'].astype(str).str.strip().str.upper() == user_email.strip().upper()]
    if not user_match.empty:
        app_role = str(user_match.iloc[0].get('ROLE', 'VIEWER')).strip().upper()
        if not app_role: app_role = 'VIEWER'
        user_name = str(user_match.iloc[0].get('FULL_NAME', user_email)).strip()
        if not user_name: user_name = user_email
    else:
        app_role, user_name = 'VIEWER', user_email
else:
    app_role, user_name = 'VIEWER', user_email

def is_admin(r): return r.upper() in ['ADMIN', 'OWNER']
def is_opts(r): return False # unused logic
def is_ops(r): return r.upper() in ['ADMIN', 'OWNER', 'OPS', 'DATA STRATEGIST', 'DATA_STRATEGIST', 'DATA ANALYST', 'DATA_ANALYST', 'RESEARCH EXECUTIVE', 'RESEARCH_EXECUTIVE', 'DATA LEAD', 'DATA_LEAD']
def is_owner(r): return r.upper() == 'OWNER'
def is_strategist_or_admin(r): return r.upper() in ['ADMIN', 'OWNER', 'DATA STRATEGIST', 'DATA_STRATEGIST']

with st.sidebar:
    # Logo Principal UI en el Sidebar
    render_logo(width=300)
    
    st.markdown(f"### 👤 {user_name}")
    st.markdown(f"**Rol:** `{app_role}`")
    
    import os
    if os.path.exists("workflow_synapse.html"):
        st.divider()
        with open("workflow_synapse.html", "rb") as f:
            st.download_button(
                label="📄 Descargar Manual App",
                data=f.read(),
                file_name="Manual_Procesos_Synapse.html",
                mime="text/html",
                use_container_width=True
            )
            
    st.divider()
    
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        del st.session_state.user_email
        st.rerun()

# --- UI PRINCIPAL ---
if is_ops(app_role):
    tabs = st.tabs(["📝 Nueva", "📊 Dashboard", "🎯 Mis Tareas", "👥 Asignar", "📋 Equipo", "⚙️ Admin"])
    
    with tabs[0]:
        st.subheader("Crear Nueva Solicitud")
        col1, col2 = st.columns(2)
        with col1:
            req_type = st.selectbox("Tipo de Tarea Genérica", CATEGORIAS_DATA, key="o_type", help="Selecciona la categoría que mejor describa la tarea. Ej: Si buscas analizar un reporte mensual, elige 'Reportes y Rendimiento'.")
            title = st.text_input("Detalle de la tarea (ej: Informe Terpel Julio) *", key="o_tit", help="Un nombre corto y descriptivo para la solicitud. Ej: 'Análisis de Redes Sociales de Marca X'.")
            b_df = get_brands()
            brand = st.selectbox("Marca", ["Seleccionar..."] + b_df['BRAND_NAME'].tolist() if not b_df.empty else ["Sin marcas"], key="o_brnd", help="La marca a la que pertenece esta solicitud. Ej: 'Honda'.")
        with col2:
            sla_options = {k: v["label"] for k, v in SLA_MAPPING.items()}
            sla_level = st.selectbox("Nivel de Servicio (SLA)", options=list(sla_options.keys()), format_func=lambda x: sla_options[x], index=1, key="o_sla", help="El nivel de urgencia/complejidad. Ej: Nivel 1 es para dudas rápidas, Nivel 4 para informes complejos.")
            
            calculated_deadline = calcular_entrega_antigravity(sla_level).date()
            calculated_hours = SLA_MAPPING[sla_level]["horas"]
            
            if is_admin(app_role):
                deadline = st.date_input("Fecha límite (Override Admin)", value=calculated_deadline, help="Fecha oficial de entrega. Como admin, puedes forzar esta fecha.")
                est_hrs = st.number_input("Horas estimadas (Total)", value=float(calculated_hours), help="Horas de esfuerzo estimado para completar la tarea.")
            else:
                st.info(f"⏱️ **Basado en la complejidad de Nivel {sla_level}, tu entrega estimada es el {calculated_deadline.strftime('%d/%m/%Y')} (Esfuerzo: {calculated_hours} horas).**")
                deadline = calculated_deadline
                est_hrs = calculated_hours
        
        st.divider()
        context = st.text_area("Contexto y Objetivo *", key="o_ctx", help="¿Cuál es el problema de negocio a resolver? Ej: 'Necesitamos entender por qué las ventas cayeron en la categoría de calzado.'")
        kpis = st.text_area("KPIs esperados *", key="o_kpi", help="Métricas que el entregable debe contener. Ej: 'Volumen de ventas, Costo de adquisición (CAC), Conversión (%)'.")
        usage = st.text_area("Uso del Dato *", key="o_use", help="¿Para qué se usará esta información? Ej: 'Para la presentación de resultados al cliente el próximo miércoles.'")
        
        if st.button("✅ Enviar Solicitud", type="primary", use_container_width=True, key="o_btn"):
            if not all([title, context, kpis, usage]) or brand == "Seleccionar...":
                st.error("❌ Completa todos los campos obligatorios")
            else:
                b_id = int(b_df[b_df['BRAND_NAME'] == brand]['BRAND_ID'].iloc[0]) if not b_df.empty else 1
                data = {
                    "TITLE": title, "REQUESTER_EMAIL": user_email, "BRAND_ID": b_id,
                    "REQUEST_TYPE": req_type, "BUSINESS_CONTEXT": context, "EXPECTED_KPIS": kpis,
                    "DATA_USAGE": usage, "DEADLINE": str(deadline), "TOTAL_ESTIMATED_HOURS": float(est_hrs),
                    "EFFORT_LEVEL": sla_level, "SLA_EXPECTED": SLA_MAPPING[sla_level]["label"],
                    "PRIORITY_SCORE": 6.0
                }
                if insert_request(data):
                    req_details = f"""
                    Hola, hemos recibido tu solicitud <b>{title}</b>.<br><br>
                    <b>Detalles de la solicitud:</b><br>
                    <ul>
                        <li><b>Marca:</b> {brand}</li>
                        <li><b>Tipo:</b> {req_type}</li>
                        <li><b>Nivel SLA:</b> {SLA_MAPPING[sla_level]['label']}</li>
                        <li><b>Contexto:</b> {context}</li>
                        <li><b>KPIs:</b> {kpis}</li>
                        <li><b>Uso del Dato:</b> {usage}</li>
                    </ul>
                    <br>
                    Basado en la complejidad, la entrega estimada es para el <b>{deadline}</b>.<br>
                    El estado actual es: <b>PENDIENTE</b>.<br><br>
                    Atentamente,<br>Synapse Data Ops
                    """
                    send_email_notification(user_email, f"Solicitud Recibida - {title}", req_details)
                    st.success("✅ Solicitud enviada exitosamente")
    
    with tabs[1]:
        st.subheader("📊 Dashboard Global")
        df_base = get_requests()
        if not df_base.empty:
            with st.expander("🔍 Buscador y Filtros Globales", expanded=False):
                cf1, cf2, cf3, cf4 = st.columns(4)
                f_status = cf1.multiselect("Filtrar Estado", df_base['STATUS'].unique(), default=[])
                f_date_col = cf2.selectbox("Columna Fechas", ["DEADLINE", "CREATED_AT", "Sin Fecha"])
                if f_date_col != "Sin Fecha":
                    if f_date_col in df_base.columns:
                        try:
                            _dates = pd.to_datetime(df_base[df_base[f_date_col].notnull()][f_date_col]).dt.date
                            min_d, max_d = _dates.min(), _dates.max()
                        except: min_d, max_d = date.today(), date.today()
                        f_date_range = cf3.date_input("Rango", value=[min_d, max_d])
                    else: f_date_range = []
                else: f_date_range = []
                
                f_search = cf4.text_input("Buscador de Texto (Tarea/Email)")
                
                cf5, cf6 = st.columns(2)
                # Filtro por Marca
                brand_list = df_base['BRAND_NAME'].dropna().unique().tolist() if 'BRAND_NAME' in df_base.columns else []
                f_brand = cf5.multiselect("🏷️ Filtrar por Marca", sorted(brand_list), default=[])
                
                # Asignaciones Semanales Activas
                wko = get_week_options(8)
                f_week = cf6.selectbox("📅 Semanas Planeadas", ["Todas"] + [x[1] for x in wko])
                
            df = df_base.copy()
            if f_status: df = df[df['STATUS'].astype(str).str.upper().isin([s.upper() for s in f_status])]
            if f_brand and 'BRAND_NAME' in df.columns: df = df[df['BRAND_NAME'].isin(f_brand)]
            if f_search: 
                q = f_search.lower()
                df = df[df['TITLE'].str.lower().str.contains(q) | df['REQUESTER_NAME'].str.lower().str.contains(q)]
            if f_date_col != "Sin Fecha" and len(f_date_range) > 0 and f_date_col in df.columns:
                df['_dtemp'] = pd.to_datetime(df[f_date_col]).dt.date
                if len(f_date_range) == 2: df = df[(df['_dtemp'] >= f_date_range[0]) & (df['_dtemp'] <= f_date_range[1])]
                else: df = df[df['_dtemp'] == f_date_range[0]]
            if f_week != "Todas":
                wk_dt = [x[0] for x in wko if x[1] == f_week][0]
                __wa = load_table('WEEKLY_ASSIGNMENTS')
                if not __wa.empty:
                    valid_reqs = __wa[__wa['WEEK_START'].astype(str) == str(wk_dt)]['REQUEST_ID'].unique().tolist()
                    df = df[df['REQUEST_ID'].astype(str).isin([str(x) for x in valid_reqs])]
            
            # Rendering Metrics Row
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Solicitudes", len(df))
            col2.metric("Pendientes", len(df[df['STATUS'].astype(str).str.upper() == 'PENDIENTE']))
            col3.metric("En Progreso", len(df[df['STATUS'].astype(str).str.upper() == 'EN PROGRESO']))
            col4.metric("Completados", len(df[df['STATUS'].astype(str).str.upper() == 'COMPLETADO']))
            col5.metric("Total Hrs Reproceso", f"{df['REWORK_HOURS'].sum():.1f}h")
            
            show_cols = ['REQUEST_ID', 'TITLE', 'REQUESTER_NAME', 'TOTAL_ESTIMATED_HOURS', 'HOURS_EXECUTED', 'HOURS_REMAINING', 'REWORK_HOURS', 'BRAND_NAME', 'STATUS', 'DEADLINE', 'ASSIGNED_TO_NAME', 'PRIORITY_SCORE']
            valid_cols = [c for c in show_cols if c in df.columns]
            st.dataframe(df[valid_cols].sort_values(by=['PRIORITY_SCORE', 'REQUEST_ID'], ascending=[False, False]), use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("🛠️ Gestionar Solicitudes Activas")
            reqs = df_base[df_base['STATUS'].astype(str).str.upper() != 'COMPLETADO']
            if not reqs.empty:
                sel_req = st.selectbox("Selecciona una Solicitud", reqs.apply(lambda x: f"{x['REQUEST_ID']} - {x['TITLE']} ({x['STATUS']})", axis=1))
                req_idx = int(sel_req.split(" - ")[0])
                req_data = reqs[reqs['REQUEST_ID'] == req_idx].iloc[0]
                
                with st.expander("👁️ Detalles Completos y Métricas de la Solicitud", expanded=False):
                    st.write(f"**Solicitante:** {req_data.get('REQUESTER_NAME', '')}")
                    st.write(f"**Contexto y Objetivo:** {req_data.get('BUSINESS_CONTEXT', '')}")
                    st.write(f"**KPIs Esperados:** {req_data.get('EXPECTED_KPIS', '')}")
                    st.write(f"**Uso del Dato:** {req_data.get('DATA_USAGE', '')}")
                    st.info(f"**SLA:** {req_data.get('SLA_EXPECTED', '')} | **Deadline Oficial:** {req_data.get('DEADLINE', '')}")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Horas Totales", req_data.get('TOTAL_ESTIMATED_HOURS', 0))
                    m2.metric("Horas Ejecutadas", req_data.get('HOURS_EXECUTED', 0))
                    m3.metric("Horas Faltantes", req_data.get('HOURS_REMAINING', 0))
                    
                    st.divider()
                    st.markdown("**📅 Desglose de Asignaciones por Semana**")
                    w_plan = get_task_weekly_plan(req_idx)
                    if not w_plan.empty:
                        st.dataframe(w_plan[['WEEK_START', 'FULL_NAME', 'HOURS_ASSIGNED', 'NOTES']].rename(columns={'WEEK_START': 'Semana', 'FULL_NAME': 'Asignado a', 'HOURS_ASSIGNED': 'Horas', 'NOTES': 'Notas'}), hide_index=True, use_container_width=True)
                    else:
                        st.info("Esta tarea aún no tiene horas asignadas en ninguna semana.")

                if is_strategist_or_admin(app_role):
                    c1, c2 = st.columns(2)
                    with c1:
                        with st.form(f"ask_info_{req_idx}"):
                            st.markdown("**1. Solicitar Aclaración al Creador**")
                            fb = st.text_area("¿Qué información hace falta?", key="fbk")
                            if st.form_submit_button("Pedir Información al Creador", use_container_width=True):
                                if fb:
                                    update_row('REQUESTS', 'REQUEST_ID', req_idx, {'STATUS': 'ESPERANDO INFO', 'ADMIN_FEEDBACK': fb, 'UPDATED_AT': str(datetime.now())})
                                    e_target = req_data.get('REQUESTER_EMAIL', '')
                                    if pd.isna(e_target): e_target = ''
                                    send_email_notification(e_target, f"Acción Requerida: {req_data['TITLE']}", f"El equipo de Datos requiere más detalles para avanzar con tu solicitud <b>{req_data['TITLE']}</b>.<br><br><b>Mensaje de Ops:</b> {fb}<br><br>Por favor, ingresa a la pestaña 'Mis Solicitudes' en Synapse para responder.")
                                    st.success("Aclaración solicitada con éxito.")
                                    st.rerun()
                    with c2:
                        with st.form(f"resched_{req_idx}"):
                            st.markdown("**2. Reprogramar Fecha de Entrega**")
                            try: prev_date = datetime.strptime(str(req_data['DEADLINE']), "%Y-%m-%d").date()
                            except: prev_date = date.today()
                            new_date = st.date_input("Nueva Fecha Oficial", value=prev_date, key="ndate")
                            if st.form_submit_button("Actualizar Fecha de Entrega", use_container_width=True):
                                if str(new_date) != str(prev_date):
                                    update_row('REQUESTS', 'REQUEST_ID', req_idx, {'DEADLINE': str(new_date), 'UPDATED_AT': str(datetime.now())})
                                    e_target = req_data.get('REQUESTER_EMAIL', '')
                                    if pd.isna(e_target): e_target = ''
                                    send_email_notification(e_target, f"Fecha Reprogramada: {req_data['TITLE']}", f"Te informamos que la fecha de entrega oficial de <b>{req_data['TITLE']}</b> ha sido reestimada al <b>{new_date}</b>.")
                                    st.success("Fecha y SLA actualizados.")
                                    st.rerun()
                                    
                    with st.form(f"rework_{req_idx}"):
                        st.markdown("**3. Registrar Reproceso (Adición de Horas)**")
                        rw_cause = st.text_area("Causa del Reproceso", key="rwcause")
                        rw_hours = st.number_input("Horas a Adicionar", value=0.0, step=0.5, key="rwhours")
                        if st.form_submit_button("Registrar Reproceso", use_container_width=True):
                            if rw_cause and rw_hours > 0:
                                new_ctx = str(req_data.get('BUSINESS_CONTEXT', '')) + f"\n\n[REPROCESO {datetime.now().strftime('%Y-%m-%d')}]: {rw_cause} (+{rw_hours}h)"
                                new_total = float(req_data.get('TOTAL_ESTIMATED_HOURS', 0)) + float(rw_hours)
                                update_row('REQUESTS', 'REQUEST_ID', req_idx, {'BUSINESS_CONTEXT': new_ctx, 'TOTAL_ESTIMATED_HOURS': new_total, 'UPDATED_AT': str(datetime.now())})
                                e_target = req_data.get('REQUESTER_EMAIL', '')
                                if pd.isna(e_target): e_target = ''
                                send_email_notification(e_target, f"Actualización de Alcance: {req_data['TITLE']}", f"Se ha registrado un reproceso en tu solicitud <b>{req_data['TITLE']}</b>.<br><br><b>Causa:</b> {rw_cause}<br>Horas adicionadas al estimado: {rw_hours}h.")
                                st.success("Reproceso registrado correctamente.")
                                st.rerun()
    
                    st.divider()
                    st.markdown("**4. Cierre de Solicitud (Finalización)**")
                    if st.button("🏁 Marcar Solicitud como COMPLETADA", type="primary", use_container_width=True):
                        if update_row('REQUESTS', 'REQUEST_ID', req_idx, {'STATUS': 'COMPLETADO', 'UPDATED_AT': str(datetime.now())}):
                            e_target = req_data.get('REQUESTER_EMAIL', '')
                            if pd.isna(e_target): e_target = ''
                            send_email_notification(e_target, f"Solicitud Completada: {req_data['TITLE']}", f"¡Buenas noticias!<br>Tu solicitud <b>{req_data['TITLE']}</b> ha sido finalizada con éxito por el equipo de Datos.<br><br>Gracias por utilizar Synapse.")
                            st.success("Tarea cerrada de forma definitiva.")
                            st.rerun()
                else:
                    st.warning("🔒 Tu rol actual no tiene permisos para Gestionar, Revisar o Finalizar esta solicitud. Debe hacerlo un Data Strategist o Administrador.")
        else:
            st.info("No hay solicitudes registradas.")
            
    with tabs[2]:
        st.subheader("🎯 Mis Tareas Asignadas")
        my_tasks_base = get_my_assigned_tasks(user_email)
        
        if not my_tasks_base.empty:
            with st.expander("🔍 Filtrar Mis Tareas", expanded=False):
                c_f1, c_f2 = st.columns(2)
                my_status = c_f1.multiselect("Estado", my_tasks_base['STATUS'].unique(), default=[])
                my_search = c_f2.text_input("Buscar Tarea")
                
            my_tasks = my_tasks_base.copy()
            if my_status: my_tasks = my_tasks[my_tasks['STATUS'].astype(str).str.upper().isin([s.upper() for s in my_status])]
            if my_search:
                q = my_search.lower()
                my_tasks = my_tasks[my_tasks['TITLE'].str.lower().str.contains(q)]
                
            if not my_tasks.empty:
                for _, task in my_tasks.iterrows():
                    days_left = task.get('DAYS_TO_DEADLINE', 0)
                    urg = "🔴" if days_left < 0 else "🟡" if days_left <= 2 else "🟢"
                    with st.expander(f"{urg} {task['TITLE']} | {days_left} días restantes"):
                        c1, c2 = st.columns(2)
                        c1.write(f"**Marca:** {task.get('BRAND_NAME', 'N/A')}")
                        c1.write(f"**Solicitante:** {task.get('REQUESTER_NAME', 'N/A')}")
                        c2.write(f"**Deadline:** {task['DEADLINE']}")
                        c2.write(f"**Estado:** {task['STATUS']}")
                        st.info(f"**Contexto y Objetivo:** {task['BUSINESS_CONTEXT']}")
                        st.write(f"**📈 KPIs Esperados:** {task.get('EXPECTED_KPIS', 'N/A')}")
                        st.write(f"**📅 Uso del Dato:** {task.get('DATA_USAGE', 'N/A')}")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Horas Totales", task.get('TOTAL_ESTIMATED_HOURS', 0))
                        m2.metric("Horas Ejecutadas", task.get('HOURS_EXECUTED', 0))
                        m3.metric("Horas Faltantes", task.get('HOURS_REMAINING', 0))
                        with st.form(f"f_rev_{task['REQUEST_ID']}"):
                            st.markdown("**Entregables para Revisión**")
                            rev_links = st.text_input("Enlaces a documentos o Dashboards (Obligatorio)")
                            rev_desc = st.text_area("Breve explicación de la tarea realizada (Obligatorio)")
                            if st.form_submit_button("👀 Enviar a Revisión", use_container_width=True):
                                if rev_links and rev_desc:
                                    new_ctx = str(task.get('BUSINESS_CONTEXT', '')) + f"\n\n[ENTREGADO PARA REVISIÓN]:\nEnlaces: {rev_links}\nExplicación: {rev_desc}"
                                    if update_row('REQUESTS', 'REQUEST_ID', task['REQUEST_ID'], {'STATUS': 'EN REVISIÓN', 'BUSINESS_CONTEXT': new_ctx, 'UPDATED_AT': str(datetime.now())}):
                                        send_email_notification('datahublobueno@gmail.com', f"Tarea para Revisión: {task['TITLE']}", f"El usuario {user_name} ha marcado la tarea <b>{task['TITLE']}</b> como lista para revisión.<br><br><b>Enlaces:</b> {rev_links}<br><b>Explicación:</b> {rev_desc}<br><br>Revisa el dashboard de Synapse para validar y cerrar la solicitud de forma final.")
                                        st.success("Tarea enviada a revisión correctamente.")
                                        st.rerun()
                                else:
                                    st.error("Debes incluir los enlaces y la explicación para enviar a revisión.")
            else:
                st.info("No hay tareas que coincidan con la búsqueda.")
        else:
            st.success("✅ No tienes tareas pendientes")
            
    with tabs[3]:
        st.subheader("👥 Asignar Tareas")
        st.caption("Planificación y asignación semanal de pendientes.")
        week_options = get_week_options(8)
        sel_wk_idx = st.selectbox("📅 Semana", range(len(week_options)), format_func=lambda x: week_options[x][1])
        sel_week = week_options[sel_wk_idx][0]
        
        pending_df = get_pending_requests()
        if not pending_df.empty:
            tgt_req = st.selectbox("📌 Solicitud Pendiente", pending_df.apply(lambda x: f"{x['REQUEST_ID']} - {x['TITLE']}", axis=1).tolist())
            req_idx = int(tgt_req.split(" - ")[0])
            r_data = pending_df[pending_df['REQUEST_ID'] == req_idx].iloc[0]
            
            with st.expander("👁️ Detalles Completos de la Solicitud", expanded=True):
                st.write(f"**Solicitante:** {r_data.get('REQUESTER_NAME', '')}")
                st.write(f"**Contexto y Objetivo:** {r_data.get('BUSINESS_CONTEXT', '')}")
                st.write(f"**KPIs Esperados:** {r_data.get('EXPECTED_KPIS', '')}")
                st.write(f"**Uso del Dato:** {r_data.get('DATA_USAGE', '')}")
                st.info(f"**SLA:** {r_data.get('SLA_EXPECTED', '')} | **Deadline Oficial:** {r_data.get('DEADLINE', '')}")
                m1, m2, m3 = st.columns(3)
                m1.metric("Horas Totales", r_data.get('TOTAL_ESTIMATED_HOURS', 0))
                m2.metric("Horas Ejecutadas", r_data.get('HOURS_EXECUTED', 0))
                m3.metric("Horas Faltantes", r_data.get('HOURS_REMAINING', 0))
                
            with st.form("assign_new"):
                c1, c2 = st.columns(2)
                team_df = get_team_members()
                tgt_usr = c1.selectbox("Asignar a", team_df['FULL_NAME'].tolist() if not team_df.empty else [])
                
                hrs = c2.number_input("Horas a asignar esta semana", 1, 40, 8)
                nts = c2.text_input("Notas de asignación")
                
                st.write("**Distribución Diaria (Opcional):**")
                d1, d2, d3, d4, d5 = st.columns(5)
                hw = {
                    'HOURS_MON': d1.number_input("L", 0, 8, 0), 'HOURS_TUE': d2.number_input("M", 0, 8, 0),
                    'HOURS_WED': d3.number_input("X", 0, 8, 0), 'HOURS_THU': d4.number_input("J", 0, 8, 0),
                    'HOURS_FRI': d5.number_input("V", 0, 8, 0)
                }
                
                if is_strategist_or_admin(app_role):
                    if st.form_submit_button("✅ Asignar y Notificar", use_container_width=True):
                        req_id = int(tgt_req.split(" - ")[0])
                        u_id = int(team_df[team_df['FULL_NAME'] == tgt_usr]['USER_ID'].iloc[0])
                        update_row('REQUESTS', 'REQUEST_ID', req_id, {'STATUS': 'EN PROGRESO', 'ASSIGNED_TO': u_id, 'UPDATED_AT': str(datetime.now())})
                        if add_weekly_assignment(req_id, u_id, sel_week, hrs, user_email, nts, hw):
                            usr_email = team_df[team_df['FULL_NAME'] == tgt_usr]['EMAIL'].iloc[0]
                            send_email_notification(usr_email, f"Nueva Asignación: {r_data['TITLE']}", f"Hola {tgt_usr},<br><br>Se te ha asignado la tarea <b>{r_data['TITLE']}</b> (Deadline: {r_data['DEADLINE']}).<br>Horas asignadas esta semana: {hrs}h.<br><br><b>Contexto:</b> {r_data.get('BUSINESS_CONTEXT', '')}<br><br>Revisa tu pestaña 'Mis Tareas' en Synapse.")
                            send_email_notification(r_data.get('REQUESTER_EMAIL', ''), f"Tarea Asignada: {r_data['TITLE']}", f"Tu solicitud <b>{r_data['TITLE']}</b> ha sido aprobada y asignada.<br><br><b>Asignado a:</b> {tgt_usr}<br><b>Fecha de Entrega Oficial:</b> {r_data['DEADLINE']}<br><br>Se encuentra formalmente EN PROGRESO.")
                            st.success("Asignación guardada y notificada a los involucrados.")
                            st.rerun()
                else:
                    st.form_submit_button("✅ Asignar y Notificar", use_container_width=True, disabled=True)
                    st.warning("🔒 Solo un Data Strategist o Administrador puede asignar tareas a este equipo.")
        else:
            st.info("No hay tareas pendientes por asignar.")

    with tabs[4]:
        st.subheader("📋 Carga del Equipo")
        
        with st.expander("🔍 Filtros de Equipo", expanded=False):
            eq_c1, eq_c2 = st.columns(2)
            eq_week_opts = get_week_options(12)
            eq_wk_idx = eq_c1.selectbox("📅 Semana", range(len(eq_week_opts)), format_func=lambda x: eq_week_opts[x][1], key="eq_wk")
            eq_week = eq_week_opts[eq_wk_idx][0]
            eq_name_filter = eq_c2.text_input("🔎 Filtrar por Colaborador", key="eq_name")
        
        wk_df = get_workload_by_week(eq_week)
        if eq_name_filter and not wk_df.empty:
            wk_df = wk_df[wk_df['FULL_NAME'].str.lower().str.contains(eq_name_filter.lower())]
        
        if not wk_df.empty:
            all_reqs = get_requests()
            for _, r in wk_df.iterrows():
                h_used = pd.to_numeric(r['HOURS_ASSIGNED'], errors='coerce')
                h_used = int(h_used) if not pd.isna(h_used) else 0
                pct = min(h_used / 40.0, 1.0)
                st.write(f"**{r['FULL_NAME']}** - {h_used}h / 40h asignadas")
                st.progress(pct)
                
                user_id = r['USER_ID']
                if not all_reqs.empty:
                    u_reqs = all_reqs[(all_reqs['ASSIGNED_TO'] == user_id) & (all_reqs['STATUS'].astype(str).str.upper() == 'EN PROGRESO')]
                    if not u_reqs.empty:
                        with st.expander(f"Ver {len(u_reqs)} Tareas Activas y Progreso Esperado"):
                            for _, ur in u_reqs.iterrows():
                                try:
                                    t_start = pd.to_datetime(ur.get('UPDATED_AT')).date()
                                    t_end = pd.to_datetime(ur.get('DEADLINE')).date()
                                    t_days_tot = (t_end - t_start).days if (t_end - t_start).days > 0 else 1
                                    t_elap = (date.today() - t_start).days
                                    t_pct = min(max(t_elap / t_days_tot, 0.0), 1.0)
                                except:
                                    t_pct = 0.0
                                st.markdown(f"🔹 **{ur['TITLE']}** (Entrega: {ur['DEADLINE']})")
                                st.progress(t_pct)
                                st.caption(f"Avance esperado por desgaste de tiempo: {int(t_pct*100)}%")
            show_eq_cols = [c for c in ['FULL_NAME', 'HOURS_MON', 'HOURS_TUE', 'HOURS_WED', 'HOURS_THU', 'HOURS_FRI', 'HOURS_ASSIGNED'] if c in wk_df.columns]
            st.dataframe(wk_df[show_eq_cols], hide_index=True)
        else:
            st.info("No hay datos de carga para la semana y filtro seleccionados.")
            
    with tabs[5]:
        if is_admin(app_role):
            st.subheader("⚙️ Panel de Administración")
            t1, t2, t3 = st.tabs(["Marcas", "Usuarios", "Eliminar Tareas"])
            with t1:
                b_df = load_table('BRANDS')
                if not b_df.empty: st.dataframe(b_df, hide_index=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    with st.form("new_brand"):
                        bn = st.text_input("Nombre de Marca")
                        if st.form_submit_button("➕ Agregar Marca"):
                            if bn:
                                save_row('BRANDS', {'BRAND_ID': generate_id('BRANDS', 'BRAND_ID'), 'BRAND_NAME': bn, 'IS_ACTIVE': 'TRUE'})
                                st.success("Marca agregada")
                with c2:
                    if not b_df.empty:
                        with st.form("del_brand"):
                            br_to_del = st.selectbox("Marca a eliminar", b_df['BRAND_NAME'].tolist())
                            confirm_br = st.checkbox("Confirmo que deseo ELIMINAR esta marca y sus datos asociados")
                            if st.form_submit_button("🗑️ Eliminar Marca", type="primary"):
                                if confirm_br:
                                    br_id = b_df[b_df['BRAND_NAME'] == br_to_del]['BRAND_ID'].iloc[0]
                                    if delete_row('BRANDS', 'BRAND_ID', br_id):
                                        st.success(f"Marca {br_to_del} eliminada")
                                        st.rerun()
                                else:
                                    st.warning("Debes marcar la casilla de confirmación")
            with t2:
                u_df = load_table('USERS')
                if not u_df.empty: st.dataframe(u_df, hide_index=True)
                with st.form("new_user"):
                    c1, c2 = st.columns(2)
                    em = c1.text_input("Email", help="Correo electrónico del usuario")
                    fn = c2.text_input("Nombre Completo", help="Nombre y apellido")
                    rol = st.selectbox("Rol", ["VIEWER", "OPS", "ADMIN", "OWNER", "DATA ANALYST", "RESEARCH EXECUTIVE"])
                    pos = st.selectbox("Posición", ["DATA_LEAD", "DATA_STRATEGIST", "DATA_ANALYST", "RESEARCH_EXECUTIVE", "DATA_RESEARCH", "DATA_OPS", "EXTERNAL"])
                    if st.form_submit_button("➕ Agregar Usuario"):
                        if em and fn:
                            save_row('USERS', {'USER_ID': generate_id('USERS', 'USER_ID'), 'EMAIL': em, 'FULL_NAME': fn, 'ROLE': rol, 'POSITION': pos, 'IS_ACTIVE': 'TRUE', 'WEEKLY_HOURS': 40})
                            st.success("Usuario agregado")
            with t3:
                if is_owner(app_role):
                    st.subheader("🗑️ Eliminar Tareas / Solicitudes")
                    req_df = get_requests()
                    if not req_df.empty:
                        req_to_del_str = st.selectbox("Selecciona Solicitud para ELIMINAR", 
                                                   req_df.apply(lambda x: f"{x['REQUEST_ID']} - {x['TITLE']} ({x['BRAND_NAME']})", axis=1))
                        req_id_to_del = int(req_to_del_str.split(" - ")[0])
                        
                        st.warning(f"⚠️ Estás a punto de eliminar permanentemente la tarea: **{req_to_del_str}**")
                        confirm_task = st.checkbox("Confirmo que deseo ELIMINAR esta tarea definitivamente")
                        if st.button("🗑️ Eliminar Tarea Permanentemente", type="primary"):
                            if confirm_task:
                                if delete_row('REQUESTS', 'REQUEST_ID', req_id_to_del):
                                    st.success("Tarea eliminada correctamente")
                                    st.rerun()
                            else:
                                st.error("Debes confirmar la eliminación")
                    else:
                        st.info("No hay tareas para eliminar")
                else:
                    st.warning("Acceso denegado. Solo el rol OWNER puede eliminar tareas.")
        else:
            st.warning("Acceso restringido a administradores.")
else:
    # Vista VIEWERS
    tabs = st.tabs(["📝 Nueva Solicitud", "📋 Mis Solicitudes"])
    with tabs[0]:
        st.subheader("Crear Nueva Solicitud")
        col1, col2 = st.columns(2)
        with col1:
            req_type = st.selectbox("Tipo de Tarea Genérica", CATEGORIAS_DATA, key="v_type", help="Selecciona la categoría que mejor describa la tarea. Ej: Si buscas analizar un reporte mensual, elige 'Reportes y Rendimiento'.")
            title = st.text_input("Detalle de la tarea (ej: Informe Terpel Julio) *", key="v_tit", help="Un nombre corto y descriptivo para la solicitud. Ej: 'Análisis de Redes Sociales de Marca X'.")
            b_df = get_brands()
            brand = st.selectbox("Marca", ["Seleccionar..."] + b_df['BRAND_NAME'].tolist() if not b_df.empty else ["Sin marcas"], key="v_brd", help="La marca a la que pertenece esta solicitud. Ej: 'Honda'.")
        with col2:
            sla_options = {k: v["label"] for k, v in SLA_MAPPING.items()}
            sla_level = st.selectbox("Nivel de Servicio (SLA)", options=list(sla_options.keys()), format_func=lambda x: sla_options[x], index=1, key="v_sla", help="El nivel de urgencia/complejidad. Ej: Nivel 1 es para dudas rápidas, Nivel 4 para informes complejos.")
            
            calculated_deadline = calcular_entrega_antigravity(sla_level).date()
            calculated_hours = SLA_MAPPING[sla_level]["horas"]
            st.info(f"⏱️ **Basado en la complejidad de Nivel {sla_level}, tu entrega estimada es el {calculated_deadline.strftime('%d/%m/%Y')} (Esfuerzo: {calculated_hours} horas).**")
            deadline = calculated_deadline
            
        st.divider()
        context = st.text_area("Contexto y Objetivo *", key="v_ctx", help="¿Cuál es el problema de negocio a resolver? Ej: 'Necesitamos entender por qué las ventas cayeron en la categoría de calzado.'")
        kpis = st.text_area("KPIs esperados *", key="v_kpi", help="Métricas que el entregable debe contener. Ej: 'Volumen de ventas, Costo de adquisición (CAC), Conversión (%)'.")
        usage = st.text_area("Uso del Dato *", key="v_use", help="¿Para qué se usará esta información? Ej: 'Para la presentación de resultados al cliente el próximo miércoles.'")
        
        if st.button("✅ Enviar Solicitud", type="primary", use_container_width=True, key="v_btn"):
            if not all([title, context, kpis, usage]) or brand == "Seleccionar...":
                st.error("❌ Completa todos los campos")
            else:
                b_id = int(b_df[b_df['BRAND_NAME'] == brand]['BRAND_ID'].iloc[0]) if not b_df.empty else 1
                data = {
                    "TITLE": title, "REQUESTER_EMAIL": user_email, "BRAND_ID": b_id,
                    "REQUEST_TYPE": req_type, "BUSINESS_CONTEXT": context, "EXPECTED_KPIS": kpis, 
                    "DATA_USAGE": usage, "DEADLINE": str(deadline),
                    "TOTAL_ESTIMATED_HOURS": float(calculated_hours),
                    "EFFORT_LEVEL": sla_level, "SLA_EXPECTED": SLA_MAPPING[sla_level]["label"],
                    "PRIORITY_SCORE": 6.0
                }
                if insert_request(data):
                    req_details = f"""
                    Hola, hemos recibido tu solicitud <b>{title}</b>.<br><br>
                    <b>Detalles de la solicitud:</b><br>
                    <ul>
                        <li><b>Marca:</b> {brand}</li>
                        <li><b>Tipo:</b> {req_type}</li>
                        <li><b>Nivel SLA:</b> {SLA_MAPPING[sla_level]['label']}</li>
                        <li><b>Contexto:</b> {context}</li>
                        <li><b>KPIs:</b> {kpis}</li>
                        <li><b>Uso del Dato:</b> {usage}</li>
                    </ul>
                    <br>
                    Basado en la complejidad, la entrega estimada es para el <b>{deadline}</b>.<br>
                    El estado actual es: <b>PENDIENTE</b>.<br><br>
                    Atentamente,<br>Synapse Data Ops
                    """
                    send_email_notification(user_email, f"Solicitud Recibida - {title}", req_details)
                    send_email_notification(
                        "datahublobueno@gmail.com",
                        f"NUEVA SOLICITUD: {title}",
                        f"El usuario {user_email} ha creado una nueva solicitud de nivel {SLA_MAPPING[sla_level]['label']}.<br>Revisa el dashboard de Synapse para asignar recursos."
                    )
                    st.success("✅ Solicitud enviada exitosamente")
    
    with tabs[1]:
        st.subheader("📋 Mis Solicitudes")
        req = get_requests()
        if not req.empty:
            my_req = req[req['REQUESTER_EMAIL'].astype(str).str.upper() == user_email.upper()]
            for _, r in my_req.iterrows():
                with st.expander(f"📌 {r['TITLE']} - {r['STATUS']}"):
                    st.write(f"**Asignado a:** {r.get('ASSIGNED_TO_NAME', 'Pendiente')}")
                    st.write(f"**Deadline:** {r.get('DEADLINE', 'N/A')}")
                    st.info(f"**Contexto y Objetivo:** {r.get('BUSINESS_CONTEXT', '')}")
                    st.write(f"**KPIs Esperados:** {r.get('EXPECTED_KPIS', '')}")
                    st.write(f"**Uso del Dato:** {r.get('DATA_USAGE', '')}")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Horas Totales Estimadas", r.get('TOTAL_ESTIMATED_HOURS', 0))
                    m2.metric("Horas Ejecutadas", r.get('HOURS_EXECUTED', 0))
                    m3.metric("Horas Faltantes", r.get('HOURS_REMAINING', 0))
                    
                    if str(r.get('STATUS', '')).upper() == 'ESPERANDO INFO':
                        st.warning(f"**Admin solicita aclaración:** {r.get('ADMIN_FEEDBACK', 'Por favor brinda más contexto/datos sobre esta solicitud.')}")
                        with st.form(f"v_upd_{r['REQUEST_ID']}"):
                            extra = st.text_area("Añade la información solicitada o enlaces de Drive:")
                            if st.form_submit_button("Enviar Aclaración", use_container_width=True):
                                if extra:
                                    n_ctx = str(r.get('BUSINESS_CONTEXT', '')) + f"\n\n[ACLARACIÓN {datetime.now().strftime('%Y-%m-%d')}]: {extra}"
                                    update_row('REQUESTS', 'REQUEST_ID', r['REQUEST_ID'], {'STATUS': 'PENDIENTE', 'BUSINESS_CONTEXT': n_ctx, 'UPDATED_AT': str(datetime.now())})
                                    send_email_notification('datahublobueno@gmail.com', f"Aclaración Recibida: {r['TITLE']}", f"El usuario {user_email} ha respondido a la solicitud de info en la tarea: <b>{r['TITLE']}</b>.<br><br><b>Información Añadida:</b><br>{extra}")
                                    st.success("Aclaración enviada al equipo.")
                                    st.rerun()

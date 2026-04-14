import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string
import pandas as pd
import hashlib

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="Hazard Corp | Enterprise Portal", layout="wide", page_icon="🔒")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0B0E11; }

    .header-status {
        background: #161B22;
        padding: 15px 20px;
        border-radius: 8px;
        border-left: 5px solid #10B981;
        margin-bottom: 20px;
    }

    div[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace; color: #10B981; }

    /* Sidebar mejorado */
    .css-1d391kg { background-color: #161B22 !important; }

    /* Inputs personalizados */
    .stTextInput input, .stPassword input {
        background-color: #0D1117 !important;
        border: 1px solid #30363D !important;
        color: #E6EDF3 !important;
        border-radius: 8px !important;
    }

    /* Botón primario */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }

    /* Botón danger */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE BASE DE DATOS Y USUARIOS ---
DB_NAME = 'hazard_enterprise_v3.db'

ADMIN_RESET_PASSWORD = "admin1234"

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db(reset=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if reset:
        c.execute("DROP TABLE IF EXISTS detalles")
        c.execute("DROP TABLE IF EXISTS ventas")

    # Tabla de Ventas
    c.execute('''CREATE TABLE IF NOT EXISTS ventas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, folio TEXT, cliente TEXT, fecha TEXT, iva_porc REAL, total REAL, vendedor TEXT)''')

    # Tabla de Detalles
    c.execute('''CREATE TABLE IF NOT EXISTS detalles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, descripcion TEXT, cant REAL, precio REAL, subtotal REAL,
                  FOREIGN KEY(venta_id) REFERENCES ventas(id))''')

    conn.commit()
    conn.close()

def generar_folio():
    return f"HZ-{datetime.now().strftime('%y%m')}-{''.join(random.choice(string.digits) for _ in range(4))}"

init_db()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Identidad Corporativa")

    logo_file = st.file_uploader("Actualizar Logo", type=["png", "jpg", "jpeg"])
    if 'logo_data' not in st.session_state:
        st.session_state.logo_data = None
    st.session_state.logo_data = logo_file.getvalue() if logo_file else st.session_state.logo_data

    if 'nombre_empresa' not in st.session_state:
        st.session_state.nombre_empresa = "Hazard Corp"
    if 'rfc_empresa' not in st.session_state:
        st.session_state.rfc_empresa = "MODD9009069Q1"
    if 'direccion' not in st.session_state:
        st.session_state.direccion = "Héroe de Nacozari #904, Col. Ampliación Bellavista C.P. 35058, Gómez Palacio Dgo."
    if 'telefono' not in st.session_state:
        st.session_state.telefono = "87-18-45-71-17"

    st.session_state.nombre_empresa = st.text_input("Razón Social", value=st.session_state.nombre_empresa)
    st.session_state.rfc_empresa = st.text_input("RFC", value=st.session_state.rfc_empresa)
    st.session_state.direccion = st.text_area("Domicilio Fiscal", value=st.session_state.direccion)
    st.session_state.telefono = st.text_input("Contacto", value=st.session_state.telefono)

    st.divider()
    st.markdown("### 🔐 Herramientas de Admin")

    # Widget para limpiar BD con contraseña
    with st.expander("⚠️ LIMPIAR BASE DE DATOS"):
        password_input = st.text_input("Contraseña de administrador", type="password", key="admin_pass")
        if st.button("Confirmar Limpieza", key="confirm_reset"):
            if password_input == ADMIN_RESET_PASSWORD:
                init_db(reset=True)
                st.success("Base de datos reiniciada correctamente.")
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")

# --- 4. MOTOR DE PDF ---
class PDF(FPDF):
    def header(self):
        if 'logo_data' in st.session_state and st.session_state.logo_data:
            with open("temp_logo.png", "wb") as f: f.write(st.session_state.logo_data)
            self.image("temp_logo.png", 10, 8, 30)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, st.session_state.nombre_empresa.upper(), ln=True, align='R')
        self.set_font('Arial', '', 8)
        self.cell(0, 4, f"RFC: {st.session_state.rfc_empresa}", ln=True, align='R')
        self.multi_cell(0, 4, st.session_state.direccion, align='R')
        self.cell(0, 4, f"Tel: {st.session_state.telefono}", ln=True, align='R')
        self.ln(12)

# --- 5. DASHBOARD PRINCIPAL ---
st.markdown(f"""
    <div class="header-status">
        <strong>Panel de Control:</strong> {st.session_state.nombre_empresa}
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 Generar Cotización/Venta", "🔍 Historial de Folios", "📊 Reporte Global"])

with tab1:
    c1, c2, c3 = st.columns([2.5, 1, 1])
    cliente = c1.text_input("Cliente / Razón Social")
    fecha_v = c2.date_input("Fecha de Emisión")
    iva_p = c3.number_input("IVA %", value=16.0)

    st.markdown("#### Configuración de Partidas")
    sub_t1, sub_t2 = st.tabs(["Equipamiento", "Cableado Estructurado"])

    if 'carrito' not in st.session_state: st.session_state.carrito = []

    with sub_t1:
        col_d, col_c, col_p = st.columns([3, 1, 1])
        desc_e = col_d.text_input("Descripción del Producto", placeholder="Ej. Kit 4 Cámaras 1080p")
        cant_e = col_c.number_input("Cantidad", min_value=1.0, value=1.0, key="c_eq")
        prec_e = col_p.number_input("Precio Unitario", min_value=0.0, key="p_eq")
        if st.button("Agregar Equipo"):
            if desc_e and prec_e > 0:
                st.session_state.carrito.append({"desc": desc_e, "cant": cant_e, "prec": prec_e})
                st.rerun()

    with sub_t2:
        col_cd, col_cm, col_cp = st.columns([3, 1, 1])
        cable_tipo = col_cd.selectbox("Tipo de Cable", ["Cable UTP Cat5e Ext.", "Cable UTP Cat6 Int.", "Coaxial RG59 + Corriente"])
        metros = col_cm.number_input("Metros", min_value=1.0, value=1.0)
        precio_m = col_cp.number_input("Precio por Metro", value=18.0)
        if st.button("Agregar Cableado"):
            st.session_state.carrito.append({"desc": f"{cable_tipo} ({metros}m)", "cant": metros, "prec": precio_m})
            st.rerun()

    if st.session_state.carrito:
        st.table(st.session_state.carrito)
        subt = sum(p['cant'] * p['prec'] for p in st.session_state.carrito)
        total_v = subt * (1 + (iva_p/100))
        st.metric("TOTAL NETO", f"${total_v:,.2f} MXN")

        if st.button("✅ REGISTRAR Y GENERAR FOLIO", type="primary"):
            if cliente:
                folio = generar_folio()
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("INSERT INTO ventas (folio, cliente, fecha, iva_porc, total, vendedor) VALUES (?,?,?,?,?,?)",
                          (folio, cliente, str(fecha_v), iva_p, total_v, "Sistema"))
                v_id = cur.lastrowid
                for p in st.session_state.carrito:
                    cur.execute("INSERT INTO detalles (venta_id, descripcion, cant, precio, subtotal) VALUES (?,?,?,?,?)",
                              (v_id, p['desc'], p['cant'], p['prec'], p['cant']*p['prec']))
                conn.commit(); conn.close()
                st.session_state.carrito = []
                st.success(f"Registro exitoso. Folio: {folio}")
                st.balloons()
            else:
                st.error("Falta el nombre del cliente.")

with tab2:
    search = st.text_input("Buscar por Folio o Cliente...")
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM ventas WHERE (folio LIKE ? OR cliente LIKE ?) ORDER BY id DESC"
    params = (f'%{search}%', f'%{search}%')
    ventas_list = pd.read_sql_query(query, conn, params=params)
    conn.close()

    for index, row in ventas_list.iterrows():
        with st.expander(f"FOLIO: {row['folio']} | {row['cliente']} | Vendedor: {row['vendedor']}"):
            conn = sqlite3.connect(DB_NAME)
            items = pd.read_sql_query("SELECT descripcion, cant, precio FROM detalles WHERE venta_id=?", conn, params=(row['id'],))
            conn.close()
            st.table(items)

            # Botón de PDF
            items_list = items.to_dict('records')
            for i in items_list: i['desc'] = i['descripcion']; i['prec'] = i['precio']

            pdf = PDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 10); pdf.cell(0, 10, f"CLIENTE: {row['cliente']}", ln=True)
            pdf.cell(0, 10, f"FOLIO: {row['folio']} | FECHA: {row['fecha']}", ln=True)
            pdf.ln(5)

with tab3:
    st.markdown("#### Inteligencia de Negocio")
    conn = sqlite3.connect(DB_NAME)
    query_global = """
        SELECT v.folio, v.fecha, v.cliente, v.vendedor, d.descripcion, d.cant, d.precio, d.subtotal
        FROM detalles d JOIN ventas v ON d.venta_id = v.id ORDER BY v.id DESC
    """
    df_global = pd.read_sql_query(query_global, conn)
    conn.close()

    if not df_global.empty:
        st.dataframe(df_global, use_container_width=True, hide_index=True)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_global.to_excel(writer, index=False, sheet_name='Reporte_Master')
        st.download_button("Descargar Reporte Maestro (Excel)", buffer.getvalue(),
                         f"Reporte_Hazard_{datetime.now().strftime('%Y%m%d')}.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Sin registros globales.")

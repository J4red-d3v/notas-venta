import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string
import pandas as pd
import hashlib
import time
import os

# --- 1. CONFIGURACIÓN DE SEGURIDAD Y ESTILO ---
st.set_page_config(page_title="Hazard Corp | Enterprise Portal", layout="wide", page_icon="🔒")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0B0E11 0%, #0D1117 100%); }
    
    .login-container {
        max-width: 420px;
        margin: 80px auto;
        padding: 40px 30px;
        background: rgba(22, 27, 34, 0.95);
        border-radius: 12px;
        border: 1px solid #2EA04330;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    .login-title { text-align: center; color: #10B981; font-weight: 700; font-size: 28px; margin-bottom: 8px; }
    .login-subtitle { text-align: center; color: #C9D1D9; font-size: 14px; margin-bottom: 32px; }
    
    .header-status {
        background: linear-gradient(90deg, #161B22 0%, #0D1117 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #10B981;
        margin-bottom: 24px;
    }
    div[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace; color: #10B981; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE BASE DE DATOS ---
DB_NAME = 'hazard_enterprise_v3.db'

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def init_db(reset=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if reset:
        c.execute("DROP TABLE IF EXISTS detalles")
        c.execute("DROP TABLE IF EXISTS ventas")
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, folio TEXT, cliente TEXT, fecha TEXT, iva_porc REAL, total REAL, vendedor TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS detalles 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, descripcion TEXT, cant REAL, precio REAL, subtotal REAL,
                  FOREIGN KEY(venta_id) REFERENCES ventas(id))''')
    
    c.execute("SELECT * FROM usuarios WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (username, password, role) VALUES (?,?,?)", ('admin', make_hashes('admin123'), 'Admin'))
        c.execute("INSERT INTO usuarios (username, password, role) VALUES (?,?,?)", ('vendedor', make_hashes('ventas123'), 'Vendedor'))
    conn.commit()
    conn.close()

def generar_folio():
    return f"HZ-{datetime.now().strftime('%y%m')}-{''.join(random.choice(string.digits) for _ in range(4))}"

init_db()

# --- 3. LÓGICA DE AUTENTICACIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_ui():
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">HAZARD CORP</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Enterprise Portal</div>', unsafe_allow_html=True)
        
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        
        if st.button("🔐 Ingresar al Sistema", use_container_width=True):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT password, role FROM usuarios WHERE username=?", (user,))
            res = c.fetchone()
            conn.close()
            
            if res and check_hashes(pw, res[0]):
                st.session_state.logged_in = True
                st.session_state.username = user
                st.session_state.role = res[1]
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. MOTOR DE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, st.session_state.get('nombre_empresa', 'HAZARD CORP'), ln=True, align='L')
        self.set_font('Arial', '', 9)
        self.cell(0, 5, f"RFC: {st.session_state.get('rfc_empresa', '')}", ln=True, align='L')
        self.ln(10)

def generar_pdf(row, items):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Folio: {row['folio']}", ln=True)
    pdf.cell(0, 10, f"Cliente: {row['cliente']}", ln=True)
    pdf.ln(5)
    # Aquí puedes añadir más detalles a la tabla del PDF
    return pdf.output(dest='S').encode('latin1')

# --- 5. APLICACIÓN PRINCIPAL ---
if not st.session_state.logged_in:
    login_ui()
else:
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        st.info(f"Rol: {st.session_state.role}")
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.logged_in = False
            st.rerun()
        
        st.divider()
        st.session_state.nombre_empresa = st.text_input("Razón Social", value="Hazard Corp")
        st.session_state.rfc_empresa = st.text_input("RFC", value="MODD9009069Q1")
        st.session_state.direccion = st.text_area("Dirección", value="Gómez Palacio Dgo.")
        st.session_state.telefono = st.text_input("Teléfono", value="8718457117")

    st.markdown(f"""<div class="header-status"><strong>{st.session_state.nombre_empresa}</strong> | Usuario: {st.session_state.username}</div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 Nueva Venta", "🔍 Historial", "📊 Admin"])

    with tab1:
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Nombre del Cliente")
        iva_p = c2.number_input("IVA %", value=16.0)
        
        if 'carrito' not in st.session_state: st.session_state.carrito = []
        
        with st.expander("Agregar Productos"):
            col_d, col_c, col_p = st.columns([3, 1, 1])
            d = col_d.text_input("Descripción")
            c = col_c.number_input("Cant", min_value=1.0, value=1.0)
            p = col_p.number_input("Precio", min_value=0.0)
            if st.button("➕ Añadir"):
                st.session_state.carrito.append({"desc": d, "cant": c, "prec": p})
        
        if st.session_state.carrito:
            df_car = pd.DataFrame(st.session_state.carrito)
            st.table(df_car)
            sub = sum(i['cant']*i['prec'] for i in st.session_state.carrito)
            total = sub * (1 + iva_p/100)
            st.metric("Total a Cobrar", f"${total:,.2f}")
            
            if st.button("✅ Finalizar Venta"):
                folio = generar_folio()
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("INSERT INTO ventas (folio, cliente, fecha, iva_porc, total, vendedor) VALUES (?,?,?,?,?,?)",
                          (folio, cliente, str(datetime.now().date()), iva_p, total, st.session_state.username))
                v_id = cur.lastrowid
                for i in st.session_state.carrito:
                    cur.execute("INSERT INTO detalles (venta_id, descripcion, cant, precio, subtotal) VALUES (?,?,?,?,?)",
                              (v_id, i['desc'], i['cant'], i['prec'], i['cant']*i['prec']))
                conn.commit()
                conn.close()
                st.session_state.carrito = []
                st.success(f"Venta guardada: {folio}")

    with tab2:
        conn = sqlite3.connect(DB_NAME)
        if st.session_state.role == "Admin":
            df_h = pd.read_sql_query("SELECT * FROM ventas ORDER BY id DESC", conn)
        else:
            df_h = pd.read_sql_query("SELECT * FROM ventas WHERE vendedor=? ORDER BY id DESC", conn, params=(st.session_state.username,))
        conn.close()
        st.dataframe(df_h, use_container_width=True)

    with tab3:
        if st.session_state.role == "Admin":
            st.write("Panel de Control de Administrador")
            # Aquí podrías poner el botón de limpiar base de datos
        else:
            st.warning("Acceso restringido.")
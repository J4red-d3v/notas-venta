import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="Hazard Corp | Elite Sales System", layout="wide", page_icon="💎")

# CSS para inyectar un diseño moderno
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stDownloadButton>button { background-color: #28a745 !important; color: white !important; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #1e3a8a; }
    .product-row { padding: 10px; border-bottom: 1px solid #dee2e6; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE BASE DE DATOS (V3) ---
def init_db():
    conn = sqlite3.connect('hazard_elite_v3.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ventas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, folio TEXT, cliente TEXT, fecha TEXT, iva_porc REAL, total REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, descripcion TEXT, cant REAL, precio REAL, subtotal REAL)''')
    conn.commit()
    conn.close()

def generar_folio():
    return f"HZ-{datetime.now().year}-{''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))}"

init_db()

# --- GESTIÓN DE ESTADO (CARRITO) ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- SIDEBAR: IDENTIDAD CORPORATIVA ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3222/3222800.png", width=100)
    st.title("Admin Panel")
    nombre_negocio = st.text_input("Empresa", value="Hazard Corp")
    logo_file = st.file_uploader("Actualizar Logo", type=["png", "jpg", "jpeg"])
    logo_bytes = logo_file.getvalue() if logo_file else None
    st.divider()
    if st.button("🗑️ Vaciar Formulario"):
        st.session_state.carrito = []
        st.rerun()

# --- MOTOR DE GENERACIÓN DE PDF ---
class FacturaPDF(FPDF):
    def header(self):
        if logo_bytes:
            with open("temp_logo.png", "wb") as f: f.write(logo_bytes)
            self.image("temp_logo.png", 10, 8, 35)
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(110, 10, nombre_negocio.upper(), 0, 0, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} - Documento generado por {nombre_negocio}', 0, 0, 'C')

def exportar_pdf(info, productos):
    pdf = FacturaPDF()
    pdf.add_page()
    
    # Info Venta
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(100, 10, f"CLIENTE: {info['cliente']}", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f"FECHA: {info['fecha']}", 0, 1, 'R')
    pdf.cell(100, 10, f"FOLIO DE RASTREO: {info['folio']}", 0, 1)
    pdf.ln(5)

    # Tabla Header
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(90, 10, ' DESCRIPCION', 1, 0, 'L', True)
    pdf.cell(20, 10, 'CANT', 1, 0, 'C', True)
    pdf.cell(40, 10, 'PRECIO U.', 1, 0, 'C', True)
    pdf.cell(40, 10, 'TOTAL', 1, 1, 'C', True)

    # Tabla Body
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    subtotal_acumulado = 0
    for p in productos:
        pdf.cell(90, 10, f" {p['desc']}", 1)
        pdf.cell(20, 10, f"{p['cant']}", 1, 0, 'C')
        pdf.cell(40, 10, f"${p['prec']:,.2f}", 1, 0, 'C')
        linea = p['cant'] * p['prec']
        pdf.cell(40, 10, f"${linea:,.2f}", 1, 1, 'C')
        subtotal_acumulado += linea

    # Desglose Final
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(150, 8, "SUBTOTAL:", 0, 0, 'R')
    pdf.cell(40, 8, f"${subtotal_acumulado:,.2f}", 0, 1, 'R')
    
    iva_monto = subtotal_acumulado * (info['iva'] / 100)
    pdf.cell(150, 8, f"IVA ({info['iva']}%):", 0, 0, 'R')
    pdf.cell(40, 8, f"${iva_monto:,.2f}", 0, 1, 'R')
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(20, 50, 100)
    pdf.cell(150, 12, "TOTAL NETO A PAGAR:", 0, 0, 'R')
    pdf.cell(40, 12, f"${subtotal_acumulado + iva_monto:,.2f}", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ PRINCIPAL ---
st.title("📦 Sistema de Facturación Elite")
t1, t2 = st.tabs(["🆕 Crear Nota de Venta", "📊 Historial y Rastreo"])

with t1:
    with st.container(border=True):
        col_cli, col_fec, col_iva = st.columns([2, 1, 1])
        cli = col_cli.text_input("Nombre del Cliente")
        fec = col_fec.date_input("Fecha de Venta")
        iva_p = col_iva.number_input("IVA %", min_value=0.0, value=16.0)

    st.subheader("Lista de Productos")
    with st.expander("➕ Agregar Item", expanded=True):
        c_desc, c_cant, c_prec = st.columns([3, 1, 1])
        item_desc = c_desc.text_input("Descripción del Producto")
        item_cant = c_cant.number_input("Cantidad", min_value=1.0, value=1.0)
        item_prec = c_prec.number_input("Precio Unitario", min_value=0.0, value=0.0)
        
        if st.button("Añadir a la Factura"):
            if item_desc and item_prec > 0:
                st.session_state.carrito.append({
                    "desc": item_desc, "cant": item_cant, "prec": item_prec
                })
                st.rerun()

    if st.session_state.carrito:
        # Mostrar tabla previa
        st.markdown("### Resumen de la Venta")
        sub_total = 0
        for i, p in enumerate(st.session_state.carrito):
            st.markdown(f"**{int(p['cant'])}x** {p['desc']} — ${p['prec']*p['cant']:,.2f}")
            sub_total += p['prec']*p['cant']
        
        st.divider()
        col_t1, col_t2 = st.columns(2)
        total_final = sub_total * (1 + (iva_p/100))
        col_t1.metric("Subtotal", f"${sub_total:,.2f}")
        col_t2.metric("Total (c/ IVA)", f"${total_final:,.2f}")

        if st.button("🚀 REGISTRAR VENTA Y GENERAR PDF"):
            if cli:
                folio = generar_folio()
                conn = sqlite3.connect('hazard_elite_v3.db')
                cur = conn.cursor()
                cur.execute("INSERT INTO ventas (folio, cliente, fecha, iva_porc, total) VALUES (?,?,?,?,?)",
                          (folio, cli, fec.strftime("%Y-%m-%d"), iva_p, total_final))
                v_id = cur.lastrowid
                for p in st.session_state.carrito:
                    cur.execute("INSERT INTO detalles (venta_id, descripcion, cant, precio, subtotal) VALUES (?,?,?,?,?)",
                              (v_id, p['desc'], p['cant'], p['prec'], p['cant']*p['prec']))
                conn.commit()
                conn.close()
                st.session_state.carrito = []
                st.success(f"Venta Guardada con Folio: {folio}")
                st.balloons()
            else:
                st.error("Error: Se requiere el nombre del cliente.")

with t2:
    search = st.text_input("🔍 Buscar por Folio o Nombre de Cliente")
    conn = sqlite3.connect('hazard_elite_v3.db')
    cur = conn.cursor()
    query = "SELECT * FROM ventas WHERE folio LIKE ? OR cliente LIKE ? ORDER BY id DESC"
    cur.execute(query, (f'%{search}%', f'%{search}%'))
    ventas = cur.fetchall()
    
    for v in ventas:
        with st.expander(f"🧾 Folio: {v[1]} | Cliente: {v[2]} | Total: ${v[5]:,.2f}"):
            cur.execute("SELECT descripcion, cant, precio FROM detalles WHERE venta_id = ?", (v[0],))
            items_db = cur.fetchall()
            prods_pdf = []
            for it in items_db:
                st.write(f"- {it[1]}x {it[0]} — ${it[2]:,.2f}")
                prods_pdf.append({"desc": it[0], "cant": it[1], "prec": it[2]})
            
            # Botón de descarga para historial
            pdf_data = exportar_pdf({"folio": v[1], "cliente": v[2], "fecha": v[3], "iva": v[4]}, prods_pdf)
            st.download_button(f"📥 Descargar PDF {v[1]}", pdf_data, f"Factura_{v[1]}.pdf", "application/pdf", key=f"hist_{v[1]}")
    conn.close()
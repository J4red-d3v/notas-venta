import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string
import pandas as pd

# --- 1. CONFIGURACIÓN DE ESTILO PREMIUM ---
st.set_page_config(page_title="Hazard Corp | Gestión Administrativa", layout="wide", page_icon="🏢")

# CSS personalizado para un look profesional
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0e1117;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #00ffcc;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1e293b;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #94a3b8;
    }

    .stTabs [aria-selected="true"] {
        background-color: #334155 !important;
        color: white !important;
        border-bottom: 2px solid #00ffcc !important;
    }
    
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #334155;
        padding-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE BASE DE DATOS ---
def init_db(reset=False):
    conn = sqlite3.connect('hazard_enterprise.db')
    c = conn.cursor()
    if reset:
        c.execute("DROP TABLE IF EXISTS detalles")
        c.execute("DROP TABLE IF EXISTS ventas")
    
    c.execute('''CREATE TABLE IF NOT EXISTS ventas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, folio TEXT, cliente TEXT, fecha TEXT, iva_porc REAL, total REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS detalles 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, descripcion TEXT, cant REAL, precio REAL, subtotal REAL,
                  FOREIGN KEY(venta_id) REFERENCES ventas(id))''')
    conn.commit()
    conn.close()

def generar_folio():
    return f"INV-{''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))}"

# Inicialización silenciosa
if 'initialized' not in st.session_state:
    init_db()
    st.session_state.initialized = True

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- 3. PANEL DE CONTROL (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80) # Icono corporativo genérico
    st.subheader("Configuración de Entidad")
    nombre_empresa = st.text_input("Razón Social", value="Hazard Corp")
    rfc_empresa = st.text_input("RFC Registro", value="MODD9009069Q1")
    direccion = st.text_area("Domicilio Fiscal", value="Héroe de Nacozari #904, Col. Ampliación Bellavista C.P. 35058, Gómez Palacio Dgo.")
    telefono = st.text_input("Contacto", value="87-18-45-71-17")
    
    st.divider()
    with st.expander("Mantenimiento de Sistema"):
        if st.button("🔴 RESETEAR BASE DE DATOS"):
            init_db(reset=True)
            st.session_state.carrito = []
            st.success("Sistema restaurado a cero.")
            st.rerun()

# --- 4. MOTOR DE PDF PROFESIONAL ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, nombre_empresa.upper(), ln=True, align='L')
        self.set_font('Arial', '', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f"RFC: {rfc_empresa}", ln=True, align='L')
        self.multi_cell(0, 5, direccion, align='L')
        self.cell(0, 5, f"Tel: {telefono}", ln=True, align='L')
        self.line(10, 45, 200, 45)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} | Comprobante emitido por Hazard Corp', 0, 0, 'C')

def exportar_pdf(info_venta, items):
    pdf = PDF()
    pdf.add_page()
    
    # Info del Cliente
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(100, 7, f"RECEPTOR: {info_venta['cliente'].upper()}")
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f"EMISIÓN: {info_venta['fecha']}", align='R', ln=True)
    pdf.cell(0, 7, f"FOLIO: {info_venta['folio']}", align='R', ln=True)
    pdf.ln(10)

    # Tabla
    pdf.set_fill_color(240, 240, 240); pdf.set_font('Arial', 'B', 10)
    pdf.cell(100, 10, " DESCRIPCIÓN DEL CONCEPTO", 1, 0, 'L', True)
    pdf.cell(25, 10, "CANT.", 1, 0, 'C', True)
    pdf.cell(30, 10, "P. UNITARIO", 1, 0, 'C', True)
    pdf.cell(35, 10, "SUBTOTAL", 1, 1, 'C', True)

    pdf.set_font('Arial', '', 10)
    for it in items:
        pdf.cell(100, 9, f" {it['desc']}", 1)
        pdf.cell(25, 9, f"{it['cant']}", 1, 0, 'C')
        pdf.cell(30, 9, f"${it['prec']:,.2f}", 1, 0, 'C')
        linea = it['cant'] * it['prec']
        pdf.cell(35, 9, f"${linea:,.2f}", 1, 1, 'C')

    # Totales
    pdf.ln(5)
    total_raw = sum(i['cant']*i['prec'] for i in items)
    iva_calc = total_raw * (info_venta['iva']/100)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(155, 7, "SUBTOTAL EXW", 0, 0, 'R')
    pdf.cell(35, 7, f"${total_raw:,.2f}", 0, 1, 'R')
    pdf.cell(155, 7, f"IVA ({info_venta['iva']}%)", 0, 0, 'R')
    pdf.cell(35, 7, f"${iva_calc:,.2f}", 0, 1, 'R')
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(155, 10, "TOTAL NETO (MXN)", 0, 0, 'R')
    pdf.cell(35, 10, f"${total_raw + iva_calc:,.2f}", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 5. INTERFAZ PRINCIPAL ---
st.markdown('<p class="main-header">Panel de Operaciones</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 Nueva Emisión", "🔍 Historial de Ventas", "📊 Inteligencia de Datos (Excel)"])

with tab1:
    c1, c2, c3 = st.columns([2, 1, 1])
    cliente = c1.text_input("Identificación del Cliente", placeholder="Nombre o Razón Social")
    fecha_v = c2.date_input("Fecha de Operación")
    iva_p = c3.number_input("Tasa IVA %", min_value=0.0, value=16.0, step=1.0)

    st.markdown("---")
    with st.container():
        col_d, col_c, col_p, col_b = st.columns([3, 1, 1, 0.8])
        desc = col_d.text_input("Descripción del Producto/Servicio")
        cant = col_c.number_input("Cantidad", min_value=0.01, value=1.0)
        prec = col_p.number_input("Precio Unitario", min_value=0.0)
        
        if col_b.button("Añadir", use_container_width=True):
            if desc and prec > 0:
                st.session_state.carrito.append({"desc": desc, "cant": cant, "prec": prec})
                st.rerun()

    if st.session_state.carrito:
        st.table(st.session_state.carrito)
        sub = sum(p['cant'] * p['prec'] for p in st.session_state.carrito)
        total_v = sub * (1 + (iva_p/100))
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Monto Total", f"${total_v:,.2f} MXN")
        
        if col_m2.button("✅ REGISTRAR Y FINALIZAR VENTA", type="primary"):
            if cliente:
                folio = generar_folio()
                conn = sqlite3.connect('hazard_enterprise.db')
                cur = conn.cursor()
                cur.execute("INSERT INTO ventas (folio, cliente, fecha, iva_porc, total) VALUES (?,?,?,?,?)",
                          (folio, cliente, str(fecha_v), iva_p, total_v))
                v_id = cur.lastrowid
                for p in st.session_state.carrito:
                    cur.execute("INSERT INTO detalles (venta_id, descripcion, cant, precio, subtotal) VALUES (?,?,?,?,?)",
                              (v_id, p['desc'], p['cant'], p['prec'], p['cant']*p['prec']))
                conn.commit(); conn.close()
                st.session_state.carrito = []
                st.success(f"Operación registrada bajo folio: {folio}")
                st.balloons()
            else:
                st.warning("Se requiere el nombre del cliente para proceder.")

with tab2:
    busqueda = st.text_input("Filtrar por folio o cliente...", placeholder="Ej: INV-A1B2C3")
    conn = sqlite3.connect('hazard_enterprise.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM ventas WHERE folio LIKE ? OR cliente LIKE ? ORDER BY id DESC", (f'%{busqueda}%', f'%{busqueda}%'))
    ventas = cur.fetchall()
    
    for v in ventas:
        with st.expander(f"ORDEN: {v[1]} | {v[2]} | Total: ${v[5]:,.2f}"):
            cur.execute("SELECT descripcion, cant, precio FROM detalles WHERE venta_id = ?", (v[0],))
            items_db = cur.fetchall()
            list_pdf = []
            for it in items_db:
                st.text(f"• {it[1]}x {it[0]} - ${it[2]:,.2f}")
                list_pdf.append({"desc": it[0], "cant": it[1], "prec": it[2]})
            
            pdf_bytes = exportar_pdf({"folio": v[1], "cliente": v[2], "fecha": v[3], "iva": v[4]}, list_pdf)
            st.download_button(f"Descargar Comprobante {v[1]}", pdf_bytes, f"Factura_{v[1]}.pdf", "application/pdf")
    conn.close()

with tab3:
    st.subheader("Reporte de Movimientos")
    conn = sqlite3.connect('hazard_enterprise.db')
    query = """
        SELECT v.fecha as Fecha, v.folio as Folio, v.cliente as Cliente, 
               d.descripcion as Concepto, d.cant as Cantidad, d.precio as Precio_Unit, d.subtotal as Neto
        FROM detalles d JOIN ventas v ON d.venta_id = v.id ORDER BY v.id DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Excel Engine
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data_Hazard')
        
        st.download_button(
            label="Descargar Reporte en Excel",
            data=out.getvalue(),
            file_name=f"Reporte_Hazard_{datetime.now().strftime('%d_%m_%y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Sin registros de productos disponibles.")
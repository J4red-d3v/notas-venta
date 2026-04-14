import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string
import pandas as pd

# --- 1. CONFIGURACIÓN DE INTERFAZ DE ALTO NIVEL ---
st.set_page_config(page_title="Hazard Corp | Business Suite", layout="wide", page_icon="⚖️")

# CSS para estética corporativa y profesional
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0B0E11;
    }

    /* Estilo para los encabezados */
    .header-text {
        color: #FFFFFF;
        font-size: 1.8rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        margin-bottom: 20px;
        border-left: 4px solid #10B981;
        padding-left: 15px;
    }

    /* Ajuste de Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #1A1D23;
        border-radius: 4px 4px 0px 0px;
        color: #94A3B8;
        padding: 10px 25px;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background-color: #2D333B !important;
        color: #10B981 !important;
        border-bottom: 2px solid #10B981 !important;
    }

    /* Métricas */
    div[data-testid="stMetricValue"] {
        font-family: 'Roboto Mono', monospace;
        color: #10B981;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
def init_db(reset=False):
    conn = sqlite3.connect('hazard_enterprise_v2.db')
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
    return f"REF-{''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))}"

# Inicialización
init_db()

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- 3. PANEL DE CONFIGURACIÓN Y LOGOTIPO ---
with st.sidebar:
    st.markdown("### Identidad Corporativa")
    
    # Manejo del Logo Cambiable
    logo_file = st.file_uploader("Cargar Logotipo", type=["png", "jpg", "jpeg"])
    if logo_file:
        st.image(logo_file, use_container_width=True)
        logo_data = logo_file.getvalue()
    else:
        # Logo por defecto si no hay carga
        st.info("Sin logotipo cargado.")
        logo_data = None

    st.divider()
    
    nombre_empresa = st.text_input("Razón Social", value="Hazard Corp")
    rfc_empresa = st.text_input("RFC / Registro Fiscal", value="MODD9009069Q1")
    direccion = st.text_area("Domicilio", value="Héroe de Nacozari #904, Col. Ampliación Bellavista C.P. 35058, Gómez Palacio Dgo.")
    telefono = st.text_input("Línea de Contacto", value="87-18-45-71-17")
    
    st.divider()
    if st.button("LIMPIAR REGISTROS (DB)", use_container_width=True, help="Elimina todo el historial"):
        init_db(reset=True)
        st.session_state.carrito = []
        st.success("Base de datos purgada.")
        st.rerun()

# --- 4. EXPORTACIÓN PROFESIONAL ---
class PDF(FPDF):
    def header(self):
        if logo_data:
            with open("current_logo.png", "wb") as f: f.write(logo_data)
            self.image("current_logo.png", 10, 8, 33)
        
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, nombre_empresa.upper(), ln=True, align='R')
        self.set_font('Arial', '', 9)
        self.cell(0, 5, f"RFC: {rfc_empresa}", ln=True, align='R')
        self.multi_cell(0, 5, direccion, align='R')
        self.cell(0, 5, f"Tel: {telefono}", ln=True, align='R')
        self.line(10, 42, 200, 42)
        self.ln(12)

def exportar_pdf(info_venta, items):
    pdf = PDF()
    pdf.add_page()
    
    # Encabezado de Venta
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(0, 8, f" DETALLES DEL DOCUMENTO", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(100, 8, f"CLIENTE: {info_venta['cliente'].upper()}")
    pdf.cell(0, 8, f"FECHA: {info_venta['fecha']}", align='R', ln=True)
    pdf.cell(0, 8, f"FOLIO: {info_venta['folio']}", align='R', ln=True)
    pdf.ln(5)

    # Tabla de Conceptos
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(30, 30, 30); pdf.set_text_color(255, 255, 255)
    pdf.cell(95, 10, " DESCRIPCIÓN", 1, 0, 'L', True)
    pdf.cell(20, 10, "CANT", 1, 0, 'C', True)
    pdf.cell(35, 10, "P. UNITARIO", 1, 0, 'C', True)
    pdf.cell(40, 10, "SUBTOTAL", 1, 1, 'C', True)

    pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
    subtotal_acumulado = 0
    for it in items:
        pdf.cell(95, 9, f" {it['desc']}", 1)
        pdf.cell(20, 9, f"{it['cant']}", 1, 0, 'C')
        pdf.cell(35, 9, f"${it['prec']:,.2f}", 1, 0, 'C')
        linea = it['cant'] * it['prec']
        pdf.cell(40, 9, f"${linea:,.2f}", 1, 1, 'C')
        subtotal_acumulado += linea

    # Resumen Financiero
    pdf.ln(5)
    iva_calc = subtotal_acumulado * (info_venta['iva']/100)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(150, 7, "SUBTOTAL:", 0, 0, 'R')
    pdf.cell(40, 7, f"${subtotal_acumulado:,.2f}", 0, 1, 'R')
    pdf.cell(150, 7, f"IVA ({info_venta['iva']}%):", 0, 0, 'R')
    pdf.cell(40, 7, f"${iva_calc:,.2f}", 0, 1, 'R')
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 10, "TOTAL NETO:", 0, 0, 'R')
    pdf.cell(40, 10, f"${subtotal_acumulado + iva_calc:,.2f}", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 5. INTERFAZ OPERATIVA ---
st.markdown('<div class="header-text">Business Management System</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Emisión de Nota", "Control de Folios", "Reporte Consolidado"])

with tab1:
    c1, c2, c3 = st.columns([2.5, 1, 1])
    cliente = c1.text_input("Razón Social / Cliente", placeholder="Nombre completo del receptor")
    fecha_op = c2.date_input("Fecha de Emisión")
    tasa_iva = c3.number_input("Tasa IVA %", value=16.0, step=1.0)

    st.markdown("#### Partidas del Documento")
    with st.container(border=True):
        col_d, col_c, col_p, col_a = st.columns([4, 1, 1.5, 1])
        desc = col_d.text_input("Concepto", placeholder="Descripción del producto o servicio")
        cant = col_c.number_input("Cant.", min_value=0.01, value=1.0)
        prec = col_p.number_input("Precio Unit.", min_value=0.0, format="%.2f")
        if col_a.button("Registrar", use_container_width=True):
            if desc and prec > 0:
                st.session_state.carrito.append({"desc": desc, "cant": cant, "prec": prec})
                st.rerun()

    if st.session_state.carrito:
        st.table(st.session_state.carrito)
        
        # Cálculos en tiempo real
        neto = sum(p['cant'] * p['prec'] for p in st.session_state.carrito)
        total_final = neto * (1 + (tasa_iva/100))
        
        m1, m2 = st.columns(2)
        m1.metric("Importe Total (MXN)", f"${total_final:,.2f}")
        
        if m2.button("FINALIZAR Y ALMACENAR OPERACIÓN", type="primary", use_container_width=True):
            if cliente:
                folio = generar_folio()
                conn = sqlite3.connect('hazard_enterprise_v2.db')
                cur = conn.cursor()
                cur.execute("INSERT INTO ventas (folio, cliente, fecha, iva_porc, total) VALUES (?,?,?,?,?)",
                          (folio, cliente, str(fecha_op), tasa_iva, total_final))
                v_id = cur.lastrowid
                for p in st.session_state.carrito:
                    cur.execute("INSERT INTO detalles (venta_id, descripcion, cant, precio, subtotal) VALUES (?,?,?,?,?)",
                              (v_id, p['desc'], p['cant'], p['prec'], p['cant']*p['prec']))
                conn.commit(); conn.close()
                st.session_state.carrito = []
                st.success(f"Operación finalizada. Folio: {folio}")
                st.balloons()
            else:
                st.error("Se requiere la Razón Social del cliente.")

with tab2:
    search = st.text_input("Filtrar registros por Folio o Cliente", placeholder="Buscar...")
    conn = sqlite3.connect('hazard_enterprise_v2.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM ventas WHERE folio LIKE ? OR cliente LIKE ? ORDER BY id DESC", (f'%{search}%', f'%{search}%'))
    records = cur.fetchall()
    
    for r in records:
        with st.expander(f"FOLIO: {r[1]} | {r[2]} | ${r[5]:,.2f}"):
            cur.execute("SELECT descripcion, cant, precio FROM detalles WHERE venta_id = ?", (r[0],))
            detalles_db = cur.fetchall()
            list_for_pdf = []
            for d in detalles_db:
                st.text(f"• {d[1]}x {d[0]} - ${d[2]:,.2f}")
                list_for_pdf.append({"desc": d[0], "cant": d[1], "prec": d[2]})
            
            pdf_out = exportar_pdf({"folio": r[1], "cliente": r[2], "fecha": r[3], "iva": r[4]}, list_for_pdf)
            st.download_button(f"Descargar PDF {r[1]}", pdf_out, f"Nota_{r[1]}.pdf", "application/pdf")
    conn.close()

with tab3:
    st.markdown("#### Historial de Movimientos")
    conn = sqlite3.connect('hazard_enterprise_v2.db')
    report_query = """
        SELECT v.fecha as 'Fecha', v.folio as 'Folio', v.cliente as 'Receptor', 
               d.descripcion as 'Concepto', d.cant as 'Cantidad', d.precio as 'P.Unitario', d.subtotal as 'Neto'
        FROM detalles d JOIN ventas v ON d.venta_id = v.id ORDER BY v.id DESC
    """
    df_final = pd.read_sql_query(report_query, conn)
    conn.close()

    if not df_final.empty:
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        
        # Generación de Excel
        xlsx_buffer = io.BytesIO()
        with pd.ExcelWriter(xlsx_buffer, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Reporte_Ventas')
        
        st.download_button(
            label="Descargar Consolidado (Excel)",
            data=xlsx_buffer.getvalue(),
            file_name=f"Reporte_Admin_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No existen registros para mostrar en el reporte.")
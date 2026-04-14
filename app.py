import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string
import pandas as pd

# --- 1. CONFIGURACIÓN Y ESTÉTICA CORPORATIVA ---
st.set_page_config(page_title="Hazard Corp | Security Systems Manager", layout="wide", page_icon="🛡️")

# CSS Profesional: Minimalista, Oscuro y Acentos en Verde Esmeralda
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0F1115; }
    
    .main-title {
        color: #FFFFFF;
        font-size: 1.6rem;
        font-weight: 600;
        border-left: 5px solid #10B981;
        padding-left: 15px;
        margin-bottom: 25px;
    }

    /* Estilo de métricas y tablas */
    div[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace; color: #10B981; }
    .stTable { border: 1px solid #2D333B; border-radius: 8px; }

    /* Tabs profesionales */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1A1D23;
        border-radius: 4px 4px 0px 0px;
        color: #94A3B8;
        padding: 12px 30px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2D333B !important;
        color: #10B981 !important;
        border-bottom: 2px solid #10B981 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE DATOS ---
DB_NAME = 'hazard_security_pro.db'

def init_db(reset=False):
    conn = sqlite3.connect(DB_NAME)
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
    return f"HZ-{datetime.now().year}-{''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))}"

init_db()

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- 3. BARRA LATERAL: IDENTIDAD Y SISTEMA ---
with st.sidebar:
    st.markdown("### Identidad Corporativa")
    logo_file = st.file_uploader("Cargar Logotipo", type=["png", "jpg", "jpeg"])
    logo_data = logo_file.getvalue() if logo_file else None
    if logo_data: st.image(logo_data, use_container_width=True)

    st.divider()
    nombre_empresa = st.text_input("Razón Social", value="Hazard Corp")
    rfc_empresa = st.text_input("Registro Fiscal (RFC)", value="MODD9009069Q1")
    direccion = st.text_area("Dirección Fiscal", value="Héroe de Nacozari #904, Col. Ampliación Bellavista C.P. 35058, Gómez Palacio Dgo.")
    telefono = st.text_input("Teléfono de Contacto", value="87-18-45-71-17")
    
    st.divider()
    if st.button("LIMPIAR TODA LA BASE DE DATOS", type="secondary", use_container_width=True):
        init_db(reset=True)
        st.session_state.carrito = []
        st.success("Registros eliminados correctamente.")
        st.rerun()

# --- 4. MOTOR DE EXPORTACIÓN PDF ---
class PDF(FPDF):
    def header(self):
        if logo_data:
            with open("temp_logo_pro.png", "wb") as f: f.write(logo_data)
            self.image("temp_logo_pro.png", 10, 8, 30)
        
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, nombre_empresa.upper(), ln=True, align='R')
        self.set_font('Arial', '', 8)
        self.cell(0, 4, f"RFC: {rfc_empresa}", ln=True, align='R')
        self.multi_cell(0, 4, direccion, align='R')
        self.cell(0, 4, f"Tel: {telefono}", ln=True, align='R')
        self.ln(12)

def generar_pdf_bytes(info, items):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(100, 8, f"CLIENTE: {info['cliente'].upper()}")
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f"FECHA: {info['fecha']}", align='R', ln=True)
    pdf.cell(0, 8, f"FOLIO: {info['folio']}", align='R', ln=True)
    pdf.ln(8)

    # Encabezado tabla
    pdf.set_fill_color(30, 30, 30); pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(90, 10, " DESCRIPCION DEL EQUIPO / SERVICIO", 1, 0, 'L', True)
    pdf.cell(25, 10, "CANT/METROS", 1, 0, 'C', True)
    pdf.cell(35, 10, "P. UNITARIO", 1, 0, 'C', True)
    pdf.cell(40, 10, "TOTAL", 1, 1, 'C', True)

    # Contenido
    pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
    subtotal_gral = 0
    for it in items:
        pdf.cell(90, 9, f" {it['desc']}", 1)
        pdf.cell(25, 9, f"{it['cant']}", 1, 0, 'C')
        pdf.cell(35, 9, f"${it['prec']:,.2f}", 1, 0, 'C')
        linea = it['cant'] * it['prec']
        pdf.cell(40, 9, f"${linea:,.2f}", 1, 1, 'C')
        subtotal_gral += linea

    # Cierre
    pdf.ln(5)
    iva = subtotal_gral * (info['iva']/100)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(150, 7, "SUBTOTAL:", 0, 0, 'R')
    pdf.cell(40, 7, f"${subtotal_gral:,.2f}", 0, 1, 'R')
    pdf.cell(150, 7, f"IVA ({info['iva']}%):", 0, 0, 'R')
    pdf.cell(40, 7, f"${iva:,.2f}", 0, 1, 'R')
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 10, "TOTAL NETO:", 0, 0, 'R')
    pdf.cell(40, 10, f"${subtotal_gral + iva:,.2f}", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 5. INTERFAZ PRINCIPAL ---
st.markdown('<div class="main-title">Sistema de Gestión de Ventas e Instalaciones</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Generar Cotización/Nota", "Historial de Folios", "Reporte Consolidado (Excel)"])

with tab1:
    with st.container(border=True):
        c1, c2, c3 = st.columns([2.5, 1, 1])
        cliente = c1.text_input("Razón Social / Cliente", placeholder="Ej. Residencial Las Palmas")
        fecha_v = c2.date_input("Fecha", value=datetime.now())
        iva_p = c3.number_input("IVA %", min_value=0.0, value=16.0)

    # SECCIÓN DE AGREGAR PRODUCTOS
    st.markdown("#### Registro de Partidas")
    
    # Sub-tabs para diferenciar equipo de cableado
    sub_t1, sub_t2 = st.tabs(["Equipo (Cámaras, DVR, Antenas)", "Cableado (Por Metros)"])
    
    with sub_t1:
        col_d, col_c, col_p = st.columns([3, 1, 1])
        desc_e = col_d.text_input("Descripción del Equipo", placeholder="Ej. Cámara Turret 2MP Hikvision")
        cant_e = col_c.number_input("Cantidad", min_value=1, value=1, key="cant_e")
        prec_e = col_p.number_input("Precio Unitario", min_value=0.0, step=10.0, key="prec_e")
        if st.button("Añadir Equipo", use_container_width=True):
            if desc_e and prec_e > 0:
                st.session_state.carrito.append({"desc": desc_e, "cant": cant_e, "prec": prec_e})
                st.rerun()

    with sub_t2:
        col_cd, col_cm, col_cp = st.columns([3, 1, 1])
        desc_c = col_cd.selectbox("Tipo de Cable", ["Cable UTP Cat5e Exterior", "Cable UTP Cat6 Interior", "Bobina Fibra Óptica", "Cable Coaxial RG59"])
        metros = col_cm.number_input("Metros Totales", min_value=1.0, value=1.0, key="metros")
        prec_m = col_cp.number_input("Precio por Metro", min_value=0.0, value=15.0, key="prec_m")
        if st.button("Añadir Metraje", use_container_width=True):
            st.session_state.carrito.append({"desc": f"{desc_c} ({metros}m)", "cant": metros, "prec": prec_m})
            st.rerun()

    if st.session_state.carrito:
        st.markdown("---")
        st.table(st.session_state.carrito)
        total_acumulado = sum(p['cant'] * p['prec'] for p in st.session_state.carrito)
        total_iva = total_acumulado * (1 + (iva_p/100))
        
        st.metric("Total de la Operación (Con IVA)", f"${total_iva:,.2f} MXN")

        if st.button("GUARDAR REGISTRO Y GENERAR FOLIO", type="primary"):
            if cliente:
                folio_nuevo = generar_folio()
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("INSERT INTO ventas (folio, cliente, fecha, iva_porc, total) VALUES (?,?,?,?,?)",
                          (folio_nuevo, cliente, fecha_v.strftime("%Y-%m-%d"), iva_p, total_iva))
                v_id = cur.lastrowid
                for p in st.session_state.carrito:
                    cur.execute("INSERT INTO detalles (venta_id, descripcion, cant, precio, subtotal) VALUES (?,?,?,?,?)",
                              (v_id, p['desc'], p['cant'], p['prec'], p['cant']*p['prec']))
                conn.commit(); conn.close()
                st.session_state.carrito = []
                st.success(f"Venta registrada. Folio asignado: {folio_nuevo}")
                st.balloons()
            else:
                st.error("Se requiere el nombre del cliente.")

with tab2:
    busqueda = st.text_input("Buscador de Folios / Clientes", placeholder="Escriba aquí para filtrar...")
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM ventas WHERE folio LIKE ? OR cliente LIKE ? ORDER BY id DESC", (f'%{busqueda}%', f'%{busqueda}%'))
    ventas_list = cur.fetchall()
    
    for v in ventas_list:
        with st.expander(f"FOLIO: {v[1]} | {v[2]} | Total: ${v[5]:,.2f}"):
            cur.execute("SELECT descripcion, cant, precio FROM detalles WHERE venta_id = ?", (v[0],))
            detalles_db = cur.fetchall()
            items_pdf = []
            for d in detalles_db:
                st.text(f"• {d[1]}x {d[0]} | Unitario: ${d[2]:,.2f}")
                items_pdf.append({"desc": d[0], "cant": d[1], "prec": d[2]})
            
            pdf_data = generar_pdf_bytes({"folio": v[1], "cliente": v[2], "fecha": v[3], "iva": v[4]}, items_pdf)
            st.download_button(f"Descargar PDF {v[1]}", pdf_data, f"Cotizacion_{v[1]}.pdf", "application/pdf")
    conn.close()

with tab3:
    st.markdown("#### Consolidado General de Productos Vendidos")
    conn = sqlite3.connect(DB_NAME)
    # Query que agrupa por folio para que sea idéntico al PDF
    query_excel = """
        SELECT 
            v.folio AS 'Folio',
            v.fecha AS 'Fecha',
            v.cliente AS 'Cliente',
            d.descripcion AS 'Concepto/Equipo',
            d.cant AS 'Cantidad/Metros',
            d.precio AS 'P. Unitario',
            d.subtotal AS 'Subtotal'
        FROM detalles d
        JOIN ventas v ON d.venta_id = v.id
        ORDER BY v.id DESC
    """
    df_excel = pd.read_sql_query(query_excel, conn)
    conn.close()

    if not df_excel.empty:
        st.dataframe(df_excel, use_container_width=True, hide_index=True)
        
        # Generar Excel en memoria
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Reporte_Ventas_Seguridad')
        
        st.download_button(
            label="Descargar Reporte en Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"Reporte_Seguridad_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No hay datos registrados actualmente.")
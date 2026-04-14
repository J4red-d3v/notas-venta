import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string
import pandas as pd  # Para el manejo de tablas tipo Excel

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Hazard Corp | Sistema Pro", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stDownloadButton>button { background-color: #059669 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('hazard_v5_final.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ventas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, folio TEXT, cliente TEXT, fecha TEXT, iva_porc REAL, total REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS detalles 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, descripcion TEXT, cant REAL, precio REAL, subtotal REAL,
                  FOREIGN KEY(venta_id) REFERENCES ventas(id))''')
    conn.commit()
    conn.close()

def generar_folio():
    return f"HZ-{''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))}"

init_db()

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- 3. CONFIGURACIÓN DE EMPRESA (DATOS DE LA IMAGEN) ---
with st.sidebar:
    st.title("⚙️ Configuración")
    nombre_empresa = st.text_input("Nombre del Negocio", value="Hazard Corp")
    rfc_empresa = st.text_input("RFC", value="MODD9009069Q1")
    direccion = st.text_area("Dirección", value="Héroe de Nacozari #904, Col. Ampliación Bellavista C.P. 35058, Gómez Palacio Dgo.")
    telefono = st.text_input("Teléfono", value="87-18-45-71-17")
    
    logo_file = st.file_uploader("Cargar Logo", type=["png", "jpg", "jpeg"])
    logo_data = logo_file.getvalue() if logo_file else None
    
    if st.button("🗑️ Limpiar Formulario"):
        st.session_state.carrito = []
        st.rerun()

# --- 4. GENERADOR DE PDF ---
class PDF(FPDF):
    def header(self):
        if logo_data:
            with open("temp_logo.png", "wb") as f: f.write(logo_data)
            self.image("temp_logo.png", 10, 8, 30)
        
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, nombre_empresa.upper(), ln=True, align='R')
        self.set_font('Arial', '', 8)
        self.cell(0, 4, f"RFC: {rfc_empresa}", ln=True, align='R')
        self.multi_cell(0, 4, direccion, align='R')
        self.cell(0, 4, f"Tel: {telefono}", ln=True, align='R')
        self.ln(10)

def exportar_pdf(info_venta, items):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(100, 10, f"CLIENTE: {info_venta['cliente']}")
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f"FECHA: {info_venta['fecha']}", align='R', ln=True)
    pdf.cell(0, 10, f"FOLIO: {info_venta['folio']}", align='R', ln=True)
    pdf.ln(5)

    pdf.set_fill_color(0, 0, 0); pdf.set_text_color(255, 255, 255); pdf.set_font('Arial', 'B', 10)
    pdf.cell(90, 10, " DESCRIPCION", 1, 0, 'L', True)
    pdf.cell(20, 10, "CANT", 1, 0, 'C', True)
    pdf.cell(40, 10, "PRECIO U.", 1, 0, 'C', True)
    pdf.cell(40, 10, "TOTAL", 1, 1, 'C', True)

    pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 10)
    subtotal_gral = 0
    for it in items:
        pdf.cell(90, 10, f" {it['desc']}", 1)
        pdf.cell(20, 10, f"{it['cant']}", 1, 0, 'C')
        pdf.cell(40, 10, f"${it['prec']:,.2f}", 1, 0, 'C')
        linea = it['cant'] * it['prec']
        pdf.cell(40, 10, f"${linea:,.2f}", 1, 1, 'C')
        subtotal_gral += linea

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 8, "SUBTOTAL:", 0, 0, 'R')
    pdf.cell(40, 8, f"${subtotal_gral:,.2f}", 0, 1, 'R')
    iva_monto = subtotal_gral * (info_venta['iva'] / 100)
    pdf.cell(150, 8, f"IVA ({info_venta['iva']}%):", 0, 0, 'R')
    pdf.cell(40, 8, f"${iva_monto:,.2f}", 0, 1, 'R')
    pdf.set_text_color(20, 60, 180); pdf.set_font('Arial', 'B', 14)
    pdf.cell(150, 12, "TOTAL NETO:", 0, 0, 'R')
    pdf.cell(40, 12, f"${subtotal_gral + iva_monto:,.2f}", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 5. INTERFAZ ---
st.title(f"🚀 {nombre_empresa} | Terminal de Ventas")

tab1, tab2, tab3 = st.tabs(["🛒 Generar Venta", "📂 Panel de Rastreo", "📊 Reporte de Productos (Excel)"])

with tab1:
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        cliente = c1.text_input("Nombre del Cliente")
        fecha_v = c2.date_input("Fecha")
        iva_p = c3.number_input("IVA % (Manual)", min_value=0.0, value=16.0) # Ajustado a 16% común

    st.subheader("Agregar Items")
    with st.expander("Añadir producto/servicio", expanded=True):
        col_d, col_c, col_p = st.columns([3, 1, 1])
        desc = col_d.text_input("Descripción")
        cant = col_c.number_input("Cant.", min_value=0.1, value=1.0)
        prec = col_p.number_input("Precio Unitario", min_value=0.0)
        
        if st.button("➕ Agregar a la Lista"):
            if desc and prec > 0:
                st.session_state.carrito.append({"desc": desc, "cant": cant, "prec": prec})
                st.rerun()

    if st.session_state.carrito:
        st.markdown("### Resumen de Venta")
        st.table(st.session_state.carrito)
        sub = sum(p['cant'] * p['prec'] for p in st.session_state.carrito)
        total_v = sub * (1 + (iva_p/100))
        st.metric("TOTAL A COBRAR", f"${total_v:,.2f}")

        if st.button("🔥 REGISTRAR VENTA FINAL"):
            if cliente:
                folio = generar_folio()
                conn = sqlite3.connect('hazard_v5_final.db')
                cur = conn.cursor()
                cur.execute("INSERT INTO ventas (folio, cliente, fecha, iva_porc, total) VALUES (?,?,?,?,?)",
                          (folio, cliente, fecha_v.strftime("%Y-%m-%d"), iva_p, total_v))
                v_id = cur.lastrowid
                for p in st.session_state.carrito:
                    cur.execute("INSERT INTO detalles (venta_id, descripcion, cant, precio, subtotal) VALUES (?,?,?,?,?)",
                              (v_id, p['desc'], p['cant'], p['prec'], p['cant']*p['prec']))
                conn.commit(); conn.close()
                st.session_state.carrito = []
                st.success(f"Venta Guardada. Folio: {folio}")
                st.balloons()
            else:
                st.error("Por favor, ingresa el nombre del cliente.")

with tab2:
    st.subheader("Buscador de Folios")
    busqueda = st.text_input("Buscar por Folio o Cliente")
    conn = sqlite3.connect('hazard_v5_final.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM ventas WHERE folio LIKE ? OR cliente LIKE ? ORDER BY id DESC", (f'%{busqueda}%', f'%{busqueda}%'))
    ventas = cur.fetchall()
    
    for v in ventas:
        with st.expander(f"FOLIO: {v[1]} | {v[2]} | Total: ${v[5]:,.2f}"):
            cur.execute("SELECT descripcion, cant, precio FROM detalles WHERE venta_id = ?", (v[0],))
            items_db = cur.fetchall()
            listado_pdf = []
            for item in items_db:
                st.write(f"- {item[1]}x {item[0]} | ${item[2]:,.2f}")
                listado_pdf.append({"desc": item[0], "cant": item[1], "prec": item[2]})
            
            pdf_bytes = exportar_pdf({"folio": v[1], "cliente": v[2], "fecha": v[3], "iva": v[4]}, listado_pdf)
            st.download_button(f"📥 Descargar PDF {v[1]}", pdf_bytes, f"Nota_{v[1]}.pdf", "application/pdf", key=f"dl_{v[1]}")
    conn.close()

# --- NUEVA SECCIÓN: REPORTE EXCEL ---
with tab3:
    st.subheader("📊 Historial General de Productos")
    st.info("Aquí puedes ver todos los productos vendidos individualmente y descargarlos para tu control en Excel.")
    
    conn = sqlite3.connect('hazard_v5_final.db')
    # Esta consulta une las dos tablas para saber qué producto pertenece a qué folio y fecha
    query = """
        SELECT 
            v.fecha AS 'Fecha',
            v.folio AS 'Folio',
            v.cliente AS 'Cliente',
            d.descripcion AS 'Producto/Servicio',
            d.cant AS 'Cantidad',
            d.precio AS 'Precio Unitario',
            d.subtotal AS 'Subtotal'
        FROM detalles d
        JOIN ventas v ON d.venta_id = v.id
        ORDER BY v.id DESC
    """
    df_reporte = pd.read_sql_query(query, conn)
    conn.close()

    if not df_reporte.empty:
        # Mostrar tabla en el sitio
        st.dataframe(df_reporte, use_container_width=True)
        
        # Generar archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_reporte.to_excel(writer, index=False, sheet_name='Ventas_Detalladas')
        
        excel_data = output.getvalue()
        
        st.download_button(
            label="Excel 📗 Descargar Reporte Completo",
            data=excel_data,
            file_name=f"Reporte_Ventas_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Aún no hay ventas registradas para generar el reporte.")
import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string
import os

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="Hazard Corp | Sistema Pro", layout="wide", page_icon="🚀")

# Estilo para que se vea más profesional
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stDownloadButton>button { background-color: #059669 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS (NUEVA VERSIÓN V5) ---
def init_db():
    # Cambiamos el nombre del archivo para forzar una estructura limpia y sin errores
    conn = sqlite3.connect('hazard_v5_final.db')
    c = conn.cursor()
    # Tabla Maestra: Datos generales de la venta
    c.execute('''CREATE TABLE IF NOT EXISTS ventas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  folio TEXT, 
                  cliente TEXT, 
                  fecha TEXT, 
                  iva_porc REAL, 
                  total REAL)''')
    # Tabla de Detalles: Cada producto por separado
    c.execute('''CREATE TABLE IF NOT EXISTS detalles 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  venta_id INTEGER, 
                  descripcion TEXT, 
                  cant REAL, 
                  precio REAL, 
                  subtotal REAL,
                  FOREIGN KEY(venta_id) REFERENCES ventas(id))''')
    conn.commit()
    conn.close()

def generar_folio():
    return f"HZ-{''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))}"

init_db()

# --- 3. ESTADO DE LA APLICACIÓN (CARRITO) ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- 4. CONFIGURACIÓN DE EMPRESA (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ Configuración")
    nombre_empresa = st.text_input("Nombre del Negocio", value="Hazard Corp")
    logo_file = st.file_uploader("Cargar Logo", type=["png", "jpg", "jpeg"])
    logo_data = logo_file.getvalue() if logo_file else None
    
    if st.button("🗑️ Limpiar Formulario"):
        st.session_state.carrito = []
        st.rerun()

# --- 5. GENERADOR DE PDF ---
class PDF(FPDF):
    def header(self):
        if logo_data:
            with open("temp_logo.png", "wb") as f: f.write(logo_data)
            self.image("temp_logo.png", 10, 8, 35)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, nombre_empresa.upper(), ln=True, align='R')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, "DOCUMENTO DE VENTA", ln=True, align='R')
        self.ln(20)

def exportar_pdf(info_venta, items):
    pdf = PDF()
    pdf.add_page()
    
    # Datos de la Venta
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(100, 10, f"CLIENTE: {info_venta['cliente']}")
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f"FECHA: {info_venta['fecha']}", align='R', ln=True)
    pdf.cell(0, 10, f"FOLIO: {info_venta['folio']}", align='R', ln=True)
    pdf.ln(5)

    # Tabla de productos
    pdf.set_fill_color(0, 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(90, 10, " DESCRIPCION", 1, 0, 'L', True)
    pdf.cell(20, 10, "CANT", 1, 0, 'C', True)
    pdf.cell(40, 10, "PRECIO U.", 1, 0, 'C', True)
    pdf.cell(40, 10, "TOTAL", 1, 1, 'C', True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    subtotal_gral = 0
    for it in items:
        pdf.cell(90, 10, f" {it['desc']}", 1)
        pdf.cell(20, 10, f"{it['cant']}", 1, 0, 'C')
        pdf.cell(40, 10, f"${it['prec']:,.2f}", 1, 0, 'C')
        linea = it['cant'] * it['prec']
        pdf.cell(40, 10, f"${linea:,.2f}", 1, 1, 'C')
        subtotal_gral += linea

    # Cálculos Finales
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 10, "SUBTOTAL:", 0, 0, 'R')
    pdf.cell(40, 10, f"${subtotal_gral:,.2f}", 0, 1, 'R')
    
    iva_monto = subtotal_gral * (info_venta['iva'] / 100)
    pdf.cell(150, 10, f"IVA ({info_venta['iva']}%):", 0, 0, 'R')
    pdf.cell(40, 10, f"${iva_monto:,.2f}", 0, 1, 'R')
    
    pdf.set_text_color(20, 60, 180)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(150, 15, "TOTAL NETO:", 0, 0, 'R')
    pdf.cell(40, 15, f"${subtotal_gral + iva_monto:,.2f}", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 6. INTERFAZ ---
st.title(f"🚀 {nombre_empresa} | Terminal de Ventas")

tab1, tab2 = st.tabs(["🛒 Generar Venta", "📂 Panel de Rastreo"])

with tab1:
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        cliente = c1.text_input("Nombre del Cliente")
        fecha_v = c2.date_input("Fecha")
        iva_p = c3.number_input("IVA % (Manual)", min_value=0.0, value=0.0)

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
                # Guardar Venta
                cur.execute("INSERT INTO ventas (folio, cliente, fecha, iva_porc, total) VALUES (?,?,?,?,?)",
                          (folio, cliente, fecha_v.strftime("%Y-%m-%d"), iva_p, total_v))
                v_id = cur.lastrowid
                # Guardar Detalles
                for p in st.session_state.carrito:
                    cur.execute("INSERT INTO detalles (venta_id, descripcion, cant, precio, subtotal) VALUES (?,?,?,?,?)",
                              (v_id, p['desc'], p['cant'], p['prec'], p['cant']*p['prec']))
                conn.commit()
                conn.close()
                st.session_state.carrito = []
                st.success(f"Venta Guardada con éxito. Folio: {folio}")
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
            st.download_button(f"📥 Descargar Nota {v[1]}", pdf_bytes, f"Nota_{v[1]}.pdf", "application/pdf", key=f"dl_{v[1]}")
    conn.close()
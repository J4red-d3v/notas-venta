import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Hazard Corp - Gestión de Ventas", layout="wide")

# --- FUNCIONES DE BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('ventas_hazard.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ventas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  folio_rastreo TEXT,
                  cliente TEXT, fecha TEXT, concepto TEXT, 
                  cantidad REAL, precio REAL, iva REAL, total REAL)''')
    conn.commit()
    conn.close()

def generar_folio():
    letters = string.ascii_uppercase
    nums = string.digits
    return f"HZ-{''.join(random.choice(letters + nums) for _ in range(6))}"

init_db()

# --- SIDEBAR: IDENTIDAD CORPORATIVA ---
if 'config' not in st.session_state:
    st.session_state.config = {"nombre": "Hazard Corp", "logo": None}

with st.sidebar:
    st.header("🏢 Identidad de Empresa")
    st.session_state.config["nombre"] = st.text_input("Nombre de Empresa", value=st.session_state.config["nombre"])
    logo_file = st.file_uploader("Logo Corporativo (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if logo_file:
        st.session_state.config["logo"] = logo_file.getvalue()
        st.success("✅ Logo cargado")

# --- GENERADOR DE PDF PROFESIONAL ---
def generar_pdf_venta(nota):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado: Logo y Nombre
    if st.session_state.config["logo"]:
        with open("temp_logo.png", "wb") as f:
            f.write(st.session_state.config["logo"])
        pdf.image("temp_logo.png", 10, 8, 45)
    
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(33, 37, 41)
    pdf.cell(0, 15, st.session_state.config["nombre"].upper(), ln=True, align='R')
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "NOTA DE VENTA / FACTURA", ln=True, align='R')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"Folio de Rastreo: {nota['folio']}", ln=True, align='R')
    pdf.cell(0, 5, f"Fecha: {nota['fecha']}", ln=True, align='R')
    
    pdf.ln(25)
    
    # Datos del Cliente
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f" CLIENTE: {nota['cliente']}", ln=True, fill=True)
    pdf.ln(10)
    
    # Tabla de Productos/Servicios
    pdf.set_fill_color(0, 0, 0) # Negro para un look agresivo y elegante
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 12, " DESCRIPCIÓN", 1, 0, 'L', True)
    pdf.cell(25, 12, "CANT.", 1, 0, 'C', True)
    pdf.cell(30, 12, "PRECIO", 1, 0, 'C', True)
    pdf.cell(35, 12, "SUBTOTAL", 1, 1, 'C', True)
    
    # Contenido
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 11)
    subtotal = nota['cantidad'] * nota['precio']
    pdf.cell(100, 15, f" {nota['concepto']}", 1)
    pdf.cell(25, 15, f"{nota['cantidad']}", 1, 0, 'C')
    pdf.cell(30, 15, f"${nota['precio']:,.2f}", 1, 0, 'C')
    pdf.cell(35, 15, f"${subtotal:,.2f}", 1, 1, 'C')
    
    # Totales
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(155, 10, "SUBTOTAL:", 0, 0, 'R')
    pdf.cell(35, 10, f"${subtotal:,.2f}", 0, 1, 'C')
    
    pdf.cell(155, 10, f"IVA ({nota['iva']}%):", 0, 0, 'R')
    iva_monto = subtotal * (nota['iva']/100)
    pdf.cell(35, 10, f"${iva_monto:,.2f}", 0, 1, 'C')
    
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 100, 0) # Verde oscuro para el éxito de venta
    pdf.cell(155, 15, "TOTAL A PAGAR:", 0, 0, 'R')
    pdf.cell(35, 15, f"${nota['total']:,.2f}", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ PRINCIPAL ---
st.title(f"🚀 {st.session_state.config['nombre']} | Terminal de Venta")

tab1, tab2 = st.tabs(["⚡ Nueva Venta", "🔍 Buscador y Archivo"])

with tab1:
    with st.form("venta_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        cliente = c1.text_input("👤 Nombre del Cliente / Razón Social")
        fecha_vta = c2.date_input("📅 Fecha de Venta", value=datetime.now())
        
        concepto = st.text_area("📦 Descripción del Servicio o Producto")
        
        col_a, col_b, col_c = st.columns([1, 1, 2])
        cantidad = col_a.number_input("Cantidad", min_value=0.1, value=1.0)
        precio = col_b.number_input("Precio de Venta", min_value=0.0)
        
        iva_opcion = col_c.radio("Configuración de IVA", ["Automático (16%)", "Cero / Exento", "Manual"], horizontal=True)
        if iva_opcion == "Automático (16%)":
            iva_val = 16.0
        elif iva_opcion == "Cero / Exento":
            iva_val = 0.0
        else:
            iva_val = col_c.number_input("IVA % Personalizado", min_value=0.0, max_value=100.0)

        if st.form_submit_button("✅ REGISTRAR VENTA Y GENERAR FOLIO"):
            if cliente and concepto and precio > 0:
                folio = generar_folio()
                total_vta = (cantidad * precio) * (1 + (iva_val/100))
                
                conn = sqlite3.connect('ventas_hazard.db')
                c = conn.cursor()
                c.execute("INSERT INTO ventas (folio_rastreo, cliente, fecha, concepto, cantidad, precio, iva, total) VALUES (?,?,?,?,?,?,?,?)",
                          (folio, cliente, fecha_vta.strftime("%Y-%m-%d"), concepto, cantidad, precio, iva_val, total_vta))
                conn.commit()
                conn.close()
                st.success(f"Venta Registrada. Folio de Rastreo: {folio}")
            else:
                st.error("Datos incompletos.")

with tab2:
    st.header("🔎 Panel de Rastreo")
    busqueda = st.text_input("Ingresa el Folio de Rastreo (ej: HZ-XXXXXX) o nombre del cliente")
    
    conn = sqlite3.connect('ventas_hazard.db')
    c = conn.cursor()
    if busqueda:
        c.execute("SELECT * FROM ventas WHERE folio_rastreo LIKE ? OR cliente LIKE ? ORDER BY id DESC", (f'%{busqueda}%', f'%{busqueda}%'))
    else:
        c.execute("SELECT * FROM ventas ORDER BY id DESC LIMIT 20")
    
    registros = c.fetchall()
    conn.close()

    for r in registros:
        with st.expander(f"FOLIO: {r[1]} | CLIENTE: {r[2]} | TOTAL: ${r[8]:,.2f}"):
            col_det1, col_det2 = st.columns(2)
            col_det1.write(f"**Fecha:** {r[3]}")
            col_det1.write(f"**Descripción:** {r[4]}")
            col_det2.write(f"**Cantidad:** {r[5]}")
            col_det2.write(f"**P. Venta:** ${r[6]:,.2f}")
            
            datos_pdf = {
                "id": r[0], "folio": r[1], "cliente": r[2], "fecha": r[3],
                "concepto": r[4], "cantidad": r[5], "precio": r[6], "iva": r[7], "total": r[8]
            }
            
            pdf_bytes = generar_pdf_venta(datos_pdf)
            st.download_button(
                label=f"📥 Descargar PDF Venta {r[1]}",
                data=pdf_bytes,
                file_name=f"Venta_{r[1]}.pdf",
                mime="application/pdf",
                key=f"btn_{r[1]}"
            )
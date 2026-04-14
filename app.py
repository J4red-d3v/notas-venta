import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Hazard Corp - Elite System", layout="wide")

# --- INICIALIZACIÓN DE BASE DE DATOS (SQLite) ---
def init_db():
    conn = sqlite3.connect('notas.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  cliente TEXT, fecha TEXT, concepto TEXT, 
                  cantidad REAL, precio REAL, iva REAL, total REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- ESTADO DE CONFIGURACIÓN ---
if 'config' not in st.session_state:
    st.session_state.config = {"nombre": "Hazard Corp", "logo": None}

# --- SIDEBAR: BRANDING ---
with st.sidebar:
    st.header("🏢 Branding Elite")
    st.session_state.config["nombre"] = st.text_input("Nombre del Negocio", value=st.session_state.config["nombre"])
    logo_file = st.file_uploader("Cargar Logo (Alta Resolución)", type=["png", "jpg", "jpeg"])
    if logo_file:
        st.session_state.config["logo"] = logo_file.getvalue()
        st.success("✅ Logo vinculado al sistema")

# --- FUNCIÓN PDF ESTILO COTIZACIÓN ---
def generar_pdf_perro(nota):
    pdf = FPDF()
    pdf.add_page()
    
    # Header con Logo
    if st.session_state.config["logo"]:
        with open("temp_logo.png", "wb") as f:
            f.write(st.session_state.config["logo"])
        pdf.image("temp_logo.png", 10, 8, 40)
    
    # Datos del Negocio (Derecha)
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, st.session_state.config["nombre"].upper(), ln=True, align='R')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 5, "COTIZACIÓN PROFESIONAL", ln=True, align='R')
    pdf.ln(20)
    
    # Info Cliente y Nota
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f" CLIENTE: {nota['cliente']}", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 8, f"Fecha de emisión: {nota['fecha']}", ln=False)
    pdf.cell(0, 8, f"Folio: #00{nota['id']}", ln=True, align='R')
    pdf.ln(10)
    
    # Tabla de Contenido
    pdf.set_draw_color(50, 50, 50)
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 10, " DESCRIPCIÓN DEL SERVICIO / PRODUCTO", 1, 0, 'L', True)
    pdf.cell(25, 10, "CANT.", 1, 0, 'C', True)
    pdf.cell(30, 10, "P. UNIT", 1, 0, 'C', True)
    pdf.cell(35, 10, "SUBTOTAL", 1, 1, 'C', True)
    
    # Cuerpo de Tabla
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 11)
    subtotal_base = nota['cantidad'] * nota['precio']
    pdf.cell(100, 12, f" {nota['concepto']}", 1)
    pdf.cell(25, 12, f"{nota['cantidad']}", 1, 0, 'C')
    pdf.cell(30, 12, f"${nota['precio']:,.2f}", 1, 0, 'C')
    pdf.cell(35, 12, f"${subtotal_base:,.2f}", 1, 1, 'C')
    
    # Totales
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(155, 8, "SUBTOTAL:", 0, 0, 'R')
    pdf.cell(35, 8, f"${subtotal_base:,.2f}", 0, 1, 'C')
    pdf.cell(155, 8, f"IVA ({nota['iva']}%):", 0, 0, 'R')
    monto_iva = subtotal_base * (nota['iva']/100)
    pdf.cell(35, 8, f"${monto_iva:,.2f}", 0, 1, 'C')
    
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(155, 12, "TOTAL NETO:", 0, 0, 'R')
    pdf.cell(35, 12, f"${nota['total']:,.2f}", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ DE GENERACIÓN ---
st.title("💎 Hazard Corp: Sistema de Cotizaciones")

with st.form("form_perro", clear_on_submit=True):
    c1, c2 = st.columns(2)
    cliente = c1.text_input("👤 Nombre del Cliente")
    fecha_dt = c2.date_input("📅 Fecha", value=datetime.now())
    
    st.markdown("---")
    concepto = st.text_area("🛠️ Concepto o Descripción del Servicio")
    
    col_a, col_b, col_c = st.columns([1, 1, 2])
    cantidad = col_a.number_input("Cantidad", min_value=0.1, value=1.0)
    precio = col_b.number_input("Precio Unitario", min_value=0.0)
    
    # LÓGICA DE IVA AUTOMÁTICO/MANUAL
    tipo_iva = col_c.radio("Tipo de IVA", ["Automático (16%)", "Manual"], horizontal=True)
    if tipo_iva == "Automático (16%)":
        iva_val = 16.0
    else:
        iva_val = col_c.number_input("IVA Personalizado %", min_value=0.0, max_value=100.0, value=0.0)
    
    if st.form_submit_button("🔥 GENERAR Y GUARDAR EN DB"):
        if cliente and concepto and precio > 0:
            total_calc = (cantidad * precio) * (1 + (iva_val/100))
            
            # Guardar en SQLite
            conn = sqlite3.connect('notas.db')
            c = conn.cursor()
            c.execute("INSERT INTO notas (cliente, fecha, concepto, cantidad, precio, iva, total) VALUES (?,?,?,?,?,?,?)",
                      (cliente, fecha_dt.strftime("%Y-%m-%d"), concepto, cantidad, precio, iva_val, total_calc))
            conn.commit()
            conn.close()
            st.success("🚀 Nota guardada en la base de datos y lista para descargar.")
        else:
            st.warning("Faltan datos críticos para la cotización.")

# --- SISTEMA DE CONTROL (HISTORIAL DESDE DB) ---
st.header("📊 Sistema de Control (Base de Datos)")

conn = sqlite3.connect('notas.db')
df = sqlite3.connect('notas.db')
# Consultar todas las notas
c = conn.cursor()
c.execute("SELECT * FROM notas ORDER BY id DESC")
records = c.fetchall()
conn.close()

for r in records:
    # r[0]=id, r[1]=cliente, r[2]=fecha, r[3]=concepto, r[4]=cantidad, r[5]=precio, r[6]=iva, r[7]=total
    with st.expander(f"FOLIO #00{r[0]} | {r[1]} | ${r[7]:,.2f}"):
        st.write(f"**Descripción:** {r[3]}")
        st.write(f"**Detalle:** {r[4]} unidad(es) x ${r[5]:,.2f} (+ {r[6]}% IVA)")
        
        # Generar PDF desde los datos de la DB
        datos_nota = {
            "id": r[0], "cliente": r[1], "fecha": r[2], 
            "concepto": r[3], "cantidad": r[4], "precio": r[5], 
            "iva": r[6], "total": r[7]
        }
        
        pdf_bytes = generar_pdf_perro(datos_nota)
        st.download_button(
            label="📥 Descargar Cotización PDF",
            data=pdf_bytes,
            file_name=f"Cotizacion_{r[0]}_{r[1]}.pdf",
            mime="application/pdf",
            key=f"btn_{r[0]}"
        )
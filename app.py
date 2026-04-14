import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Hazard Corp - Notas", page_icon="📝")

# Inicialización de estados
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'config' not in st.session_state:
    st.session_state.config = {"nombre": "Hazard Corp", "logo": None}

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración")
    st.session_state.config["nombre"] = st.text_input("Nombre del negocio", value=st.session_state.config["nombre"])
    logo_file = st.file_uploader("Cargar logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if logo_file:
        st.session_state.config["logo"] = logo_file.getvalue()
        st.success("✅ Logo guardado")

# --- FUNCIÓN PDF ---
def generar_pdf(nota):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, st.session_state.config["nombre"], ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Cliente: {nota['cliente']}", ln=True)
    pdf.cell(0, 10, f"Fecha: {nota['fecha']}", ln=True)
    pdf.ln(10)
    
    # Encabezados de tabla
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 10, "Concepto", 1, 0, 'C', True)
    pdf.cell(30, 10, "Cant.", 1, 0, 'C', True)
    pdf.cell(40, 10, "Precio", 1, 0, 'C', True)
    pdf.cell(40, 10, "Total", 1, 1, 'C', True)
    
    for s in nota['servicios']:
        pdf.cell(80, 10, str(s['concepto']), 1)
        pdf.cell(30, 10, str(s['cantidad']), 1)
        pdf.cell(40, 10, f"${s['precio']:,.2f}", 1)
        pdf.cell(40, 10, f"${(s['cantidad'] * s['precio']):,.2f}", 1, 1)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"TOTAL: ${nota['total']:,.2f}", ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
st.title(f"Negocio: {st.session_state.config['nombre']}")

with st.form("nueva_nota", clear_on_submit=True):
    st.subheader("📝 Nueva Nota")
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Nombre del cliente *")
    fecha = col2.date_input("Fecha", value=datetime.now())
    
    concepto = st.text_input("Concepto")
    c1, c2, c3 = st.columns(3)
    cantidad = c1.number_input("Cantidad", min_value=1, step=1, value=1)
    precio = c2.number_input("Precio Unitario", min_value=0.0, step=0.01, format="%.2f")
    iva = c3.slider("IVA (%)", 0, 16, 16)
    
    if st.form_submit_button("Guardar Nota"):
        if cliente and concepto:
            subtotal = cantidad * precio
            total = subtotal * (1 + (iva/100))
            
            # Guardamos los datos asegurando que son números (float/int)
            st.session_state.historial.append({
                "id": len(st.session_state.historial) + 1,
                "cliente": cliente,
                "fecha": fecha.strftime("%d/%m/%Y"),
                "servicios": [{"cantidad": int(cantidad), "concepto": concepto, "precio": float(precio)}],
                "total": float(total)
            })
            st.success("✅ Nota guardada")
        else:
            st.error("⚠️ Llena los campos obligatorios")

# --- HISTORIAL (SIN ERRORES) ---
st.header("📋 Historial de Notas")

for nota in reversed(st.session_state.historial):
    with st.expander(f"Nota #{nota['id']} - {nota['cliente']} - ${nota.get('total', 0):,.2f}"):
        # El truco está en usar .get() para evitar el TypeError
        for svc in nota.get('servicios', []):
            c = svc.get('cantidad', 0)
            p = svc.get('precio', 0.0)
            con = svc.get('concepto', 'Sin concepto')
            # Multiplicación segura
            st.write(f"• {c}x {con} — **${(c * p):,.2f}**")
        
        pdf_bytes = generar_pdf(nota)
        st.download_button("📥 Descargar PDF", pdf_bytes, f"Nota_{nota['id']}.pdf", "application/pdf", key=f"btn_{nota['id']}")
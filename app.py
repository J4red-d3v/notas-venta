import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Hazard Corp - Sistema de Ventas", layout="wide")

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('ventas_hazard.db')
    c = conn.cursor()
    # Tabla de Ventas (Maestro)
    c.execute('''CREATE TABLE IF NOT EXISTS ventas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, folio TEXT, cliente TEXT, fecha TEXT, iva_porcentaje REAL, total REAL)''')
    # Tabla de Detalles (Productos)
    c.execute('''CREATE TABLE IF NOT EXISTS detalles 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, concepto TEXT, cantidad REAL, precio REAL)''')
    conn.commit()
    conn.close()

def generar_folio():
    return f"HZ-{''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))}"

init_db()

# --- SESIÓN PARA MULTI-PRODUCTOS ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("🏢 Configuración")
    nombre_empresa = st.text_input("Nombre de Empresa", value="Hazard Corp")
    logo_file = st.file_uploader("Logo", type=["png", "jpg", "jpeg"])
    logo_data = logo_file.getvalue() if logo_file else None

# --- PDF GENERATOR ---
def generar_pdf(venta_info, productos):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    if logo_data:
        with open("temp_logo.png", "wb") as f: f.write(logo_data)
        pdf.image("temp_logo.png", 10, 8, 40)
    
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, nombre_empresa.upper(), ln=True, align='R')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"FOLIO: {venta_info['folio']}", ln=True, align='R')
    pdf.cell(0, 5, f"FECHA: {venta_info['fecha']}", ln=True, align='R')
    pdf.ln(20)
    
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f" CLIENTE: {venta_info['cliente']}", ln=True, fill=True)
    pdf.ln(5)
    
    # Tabla
    pdf.set_fill_color(0, 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(90, 10, " DESCRIPCION", 1, 0, 'L', True)
    pdf.cell(20, 10, "CANT.", 1, 0, 'C', True)
    pdf.cell(40, 10, "P. UNIT", 1, 0, 'C', True)
    pdf.cell(40, 10, "TOTAL", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    subtotal_gral = 0
    for p in productos:
        pdf.cell(90, 10, f" {p['concepto']}", 1)
        pdf.cell(20, 10, f"{p['cantidad']}", 1, 0, 'C')
        pdf.cell(40, 10, f"${p['precio']:,.2f}", 1, 0, 'C')
        linea_total = p['cantidad'] * p['precio']
        pdf.cell(40, 10, f"${linea_total:,.2f}", 1, 1, 'C')
        subtotal_gral += linea_total
    
    # Totales
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(150, 8, "SUBTOTAL:", 0, 0, 'R')
    pdf.cell(40, 8, f"${subtotal_gral:,.2f}", 0, 1, 'C')
    
    iva_monto = subtotal_gral * (venta_info['iva'] / 100)
    pdf.cell(150, 8, f"IVA ({venta_info['iva']}%):", 0, 0, 'R')
    pdf.cell(40, 8, f"${iva_monto:,.2f}", 0, 1, 'C')
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(150, 12, "TOTAL NETO:", 0, 0, 'R')
    pdf.cell(40, 12, f"${subtotal_gral + iva_monto:,.2f}", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
st.title(f"🚀 {nombre_empresa} | Terminal de Venta")

tab1, tab2 = st.tabs(["🛒 Nueva Venta", "📂 Panel de Rastreo"])

with tab1:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        cliente_nombre = c1.text_input("Nombre del Cliente")
        fecha_vta = c2.date_input("Fecha", value=datetime.now())
        iva_input = st.number_input("IVA a aplicar (%)", min_value=0.0, value=0.0, step=0.1)

    st.subheader("Agregar Productos")
    with st.expander("➕ Añadir concepto a la nota", expanded=True):
        col_c, col_q, col_p = st.columns([3, 1, 1])
        con = col_c.text_input("Descripción del Producto/Servicio")
        can = col_q.number_input("Cant.", min_value=0.1, value=1.0)
        pre = col_p.number_input("Precio Unit.", min_value=0.0)
        
        if st.button("Agregar a la lista"):
            if con and pre > 0:
                st.session_state.carrito.append({"concepto": con, "cantidad": can, "precio": pre})
                st.rerun()

    if st.session_state.carrito:
        st.table(st.session_state.carrito)
        if st.button("❌ Vaciar Lista"):
            st.session_state.carrito = []
            st.rerun()
            
        if st.button("🔥 REGISTRAR VENTA FINAL"):
            if cliente_nombre:
                folio = generar_folio()
                sub = sum(p['cantidad'] * p['precio'] for p in st.session_state.carrito)
                tot = sub * (1 + (iva_input/100))
                
                conn = sqlite3.connect('ventas_hazard.db')
                cur = conn.cursor()
                cur.execute("INSERT INTO ventas (folio, cliente, fecha, iva_porcentaje, total) VALUES (?,?,?,?,?)",
                          (folio, cliente_nombre, fecha_vta.strftime("%Y-%m-%d"), iva_input, tot))
                v_id = cur.lastrowid
                for p in st.session_state.carrito:
                    cur.execute("INSERT INTO detalles (venta_id, concepto, cantidad, precio) VALUES (?,?,?,?)",
                              (v_id, p['concepto'], p['cantidad'], p['precio']))
                conn.commit()
                conn.close()
                st.session_state.carrito = []
                st.success(f"Venta Guardada. Folio: {folio}")
            else:
                st.warning("Pon el nombre del cliente.")

with tab2:
    busq = st.text_input("Buscar por Folio o Cliente")
    conn = sqlite3.connect('ventas_hazard.db')
    cur = conn.cursor()
    query = "SELECT * FROM ventas WHERE folio LIKE ? OR cliente LIKE ? ORDER BY id DESC"
    cur.execute(query, (f'%{busq}%', f'%{busq}%'))
    ventas = cur.fetchall()
    
    for v in ventas:
        with st.expander(f"Folio: {v[1]} | {v[2]} | Total: ${v[5]:,.2f}"):
            cur.execute("SELECT concepto, cantidad, precio FROM detalles WHERE venta_id = ?", (v[0],))
            prods = cur.fetchall()
            lista_prods = []
            for pr in prods:
                st.write(f"• {pr[1]}x {pr[0]} - ${pr[2]:,.2f}")
                lista_prods.append({"concepto": pr[0], "cantidad": pr[1], "precio": pr[2]})
            
            info_pdf = {"folio": v[1], "cliente": v[2], "fecha": v[3], "iva": v[4]}
            pdf_out = generar_pdf(info_pdf, lista_prods)
            st.download_button(f"📥 PDF {v[1]}", pdf_out, f"Venta_{v[1]}.pdf", "application/pdf", key=v[1])
    conn.close()
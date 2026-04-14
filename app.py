"""
Notas de Venta - Web App
Crea notas de venta profesionales en PDF con logo y branding personalizado.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

# ========== CONFIGURACIÓN DE PÁGINA ==========
st.set_page_config(
    page_title="Notas de Venta",
    page_icon="🧾"
)

# ========== ESTADOS DE SESIÓN ==========
if 'notas' not in st.session_state:
    st.session_state.notas = []

if 'logo_base64' not in st.session_state:
    st.session_state.logo_base64 = None

if 'nombre_negocio' not in st.session_state:
    st.session_state.nombre_negocio = "Mi Negocio"

# ========== FUNCIONES AUXILIARES ==========
def load_logo():
    """Carga el logo desde el archivo."""
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def save_logo(file):
    """Guarda el logo cargado."""
    with open("logo.png", "wb") as f:
        f.write(file.getbuffer())
    st.session_state.logo_base64 = load_logo()

def guardar_config(nombre):
    """Guarda el nombre del negocio."""
    st.session_state.nombre_negocio = nombre
    with open("config.txt", "w") as f:
        f.write(nombre)

def cargar_config():
    """Carga la configuración."""
    if os.path.exists("config.txt"):
        with open("config.txt", "r") as f:
            st.session_state.nombre_negocio = f.read().strip()
    st.session_state.logo_base64 = load_logo()

def cargar_notas():
    """Carga las notas desde CSV."""
    if os.path.exists("notas.csv"):
        try:
            df = pd.read_csv("notas.csv")
            st.session_state.notas = df.to_dict('records')
        except:
            st.session_state.notas = []

def guardar_notas():
    """Guarda las notas en CSV."""
    if st.session_state.notas:
        df = pd.DataFrame(st.session_state.notas)
        df.to_csv("notas.csv", index=False)

def generar_pdf(nota, logo_base64, nombre_negocio):
    """Genera el PDF de la nota de venta."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()
    elements = []

    # --- ENCABEZADO CON LOGO ---
    if logo_base64:
        try:
            logo_data = base64.b64decode(logo_base64)
            logo_buffer = BytesIO(logo_data)
            logo_img = Image(logo_buffer, width=1.5*inch, height=1.5*inch)
            logo_img.hAlign = 'CENTER'
        except:
            logo_img = None
    else:
        logo_img = None

    # Título del negocio
    titulo_style = ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#6200ee'),
        alignment=TA_CENTER,
        spaceAfter=6
    )

    elementos_header = []
    if logo_img:
        elementos_header.append(logo_img)
    elementos_header.append(Paragraph(nombre_negocio, titulo_style))
    elementos_header.append(Spacer(1, 12))

    header_table = Table([elementos_header], colWidths=[7*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(header_table)

    # --- NÚMERO DE NOTA ---
    nota_style = ParagraphStyle(
        'Nota',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.gray,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    elements.append(Paragraph(f"NOTA DE VENTA #{nota['numero']}", nota_style))

    # --- INFO DEL CLIENTE ---
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=4
    )

    fecha_formato = nota['fecha'].strftime('%d de %B del %Y') if isinstance(nota['fecha'], (datetime, date)) else nota['fecha']

    client_info = f"""
    <b>Cliente:</b> {nota['cliente']}<br/>
    <b>Fecha:</b> {fecha_formato}
    """
    elements.append(Paragraph(client_info, info_style))
    elements.append(Spacer(1, 20))

    # --- TABLA DE SERVICIOS ---
    table_data = [['Cantidad', 'Concepto', 'P. Unitario', 'Importe']]

    for servicio in nota['servicios']:
        cantidad = servicio['cantidad']
        concepto = servicio['concepto']
        precio = servicio['precio']
        importe = cantidad * precio
        table_data.append([
            str(cantidad),
            concepto,
            f"${precio:,.2f}",
            f"${importe:,.2f}"
        ])

    # Agregar filas vacías hasta tener al menos 3 filas de datos
    while len(table_data) < 4:
        table_data.append(['', '', '', ''])

    servicios_table = Table(table_data, colWidths=[1*inch, 3*inch, 1.5*inch, 1.5*inch])
    servicios_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6200ee')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    elements.append(servicios_table)
    elements.append(Spacer(1, 20))

    # --- TOTALES ---
    subtotal = nota['subtotal']
    iva = nota['iva']
    total = nota['total']

    totales_data = [
        ['', '', 'Subtotal:', f"${subtotal:,.2f}"],
        ['', '', f'IVA ({nota["iva_porcentaje"]}%):', f"${iva:,.2f}"],
        ['', '', 'TOTAL:', f"${total:,.2f}"]
    ]

    totales_table = Table(totales_data, colWidths=[4*inch, 0.5*inch, 1*inch, 1.5*inch])
    totales_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (2, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (2, 0), (-1, -1), 11),
        ('LINEABOVE', (2, 2), (-1, 2), 1.5, colors.HexColor('#6200ee')),
        ('FONTNAME', (2, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 2), (-1, 2), 14),
        ('TEXTCOLOR', (2, 2), (-1, 2), colors.HexColor('#6200ee')),
    ]))
    elements.append(totales_table)

    # --- FOOTER ---
    elements.append(Spacer(1, 40))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.gray,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Documento generado automaticamente - Gracias por su preferencia", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ========== CARGAR CONFIGURACIÓN ==========
cargar_config()
cargar_notas()

# ========== SIDEBAR - CONFIGURACIÓN ==========
with st.sidebar:
    st.header("Configuracion")

    # Logo upload
    st.subheader("Logo del negocio")
    logo_file = st.file_uploader("Cargar logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'], key="logo_uploader")
    if logo_file:
        save_logo(logo_file)
        st.success("Logo guardado")

    if st.session_state.logo_base64:
        st.image("logo.png", width=150)

    st.divider()

    # Nombre del negocio
    st.subheader("Nombre del negocio")
    nombre_input = st.text_input(
        "Nombre",
        value=st.session_state.nombre_negocio,
        key="nombre_input",
        label_visibility="collapsed"
    )
    if st.button("Guardar nombre"):
        guardar_config(nombre_input)
        st.success("Nombre guardado")

# ========== TÍTULO ==========
st.title("Notas de Venta")
st.markdown(f"**Negocio:** {st.session_state.nombre_negocio}")

# ========== FORMULARIO NUEVA NOTA ==========
st.header("Nueva Nota")

col1, col2 = st.columns(2)
with col1:
    cliente = st.text_input("Nombre del cliente *", placeholder="Juan Perez")
with col2:
    fecha = st.date_input("Fecha", value=datetime.now())

st.subheader("Servicios/Productos")

# Inicializar servicios si no existen
if 'servicios_temp' not in st.session_state:
    st.session_state.servicios_temp = [{'concepto': '', 'cantidad': 1, 'precio': 0.0}]

servicios = []
for i, svc in enumerate(st.session_state.servicios_temp):
    cols = st.columns([3, 1, 1, 0.5])
    with cols[0]:
        svc['concepto'] = st.text_input("Concepto", value=svc['concepto'], key=f"concepto_{i}", placeholder="Corte de cabello")
    with cols[1]:
        svc['cantidad'] = st.number_input("Cant.", value=svc['cantidad'], min_value=1, key=f"cantidad_{i}", label_visibility="collapsed")
    with cols[2]:
        svc['precio'] = st.number_input("Precio", value=float(svc['precio']), min_value=0.0, format="%.2f", key=f"precio_{i}", label_visibility="collapsed")
    with cols[3]:
        if len(st.session_state.servicios_temp) > 1:
            if st.button("X", key=f"del_{i}"):
                del st.session_state.servicios_temp[i]
                st.rerun()

if st.button("+ Agregar servicio"):
    st.session_state.servicios_temp.append({'concepto': '', 'cantidad': 1, 'precio': 0.0})
    st.rerun()

iva_porcentaje = st.number_input("IVA (%)", value=16.0, min_value=0.0, max_value=100.0, format="%.1f")

# ========== BOTÓN GENERAR ==========
st.divider()

if st.button("Generar Nota de Venta", type="primary", use_container_width=True):
    # Validar
    if not cliente:
        st.error("Ingresa el nombre del cliente")
    else:
        # Filtrar servicios vacíos
        servicios_validos = [s for s in st.session_state.servicios_temp if s['concepto'].strip() and s['precio'] > 0]

        if not servicios_validos:
            st.error("Agrega al menos un servicio con precio")
        else:
            # Calcular totales
            subtotal = sum(s['cantidad'] * s['precio'] for s in servicios_validos)
            iva = subtotal * (iva_porcentaje / 100)
            total = subtotal + iva

            # Crear nota
            numero = len(st.session_state.notas) + 1
            nota = {
                'numero': f"{numero:04d}",
                'cliente': cliente,
                'fecha': fecha,
                'servicios': servicios_validos,
                'subtotal': subtotal,
                'iva': iva,
                'iva_porcentaje': iva_porcentaje,
                'total': total
            }

            st.session_state.notas.append(nota)
            guardar_notas()

            # Generar PDF
            pdf_buffer = generar_pdf(nota, st.session_state.logo_base64, st.session_state.nombre_negocio)

            st.success(f"Nota #{nota['numero']} creada!")

            # Mostrar preview
            st.markdown("### Preview")
            cols_preview = st.columns([1, 1, 1, 1])
            headers = ['Cant.', 'Concepto', 'P.Unit.', 'Importe']
            for i, h in enumerate(headers):
                cols_preview[i].markdown(f"**{h}**")

            for svc in servicios_validos:
                cols = st.columns([1, 1, 1, 1])
                importe = svc['cantidad'] * svc['precio']
                cols[0].write(svc['cantidad'])
                cols[1].write(svc['concepto'])
                cols[2].write(f"${svc['precio']:,.2f}")
                cols[3].write(f"${importe:,.2f}")

            st.markdown(f"**Subtotal:** ${subtotal:,.2f}")
            st.markdown(f"**IVA ({iva_porcentaje}%):** ${iva:,.2f}")
            st.markdown(f"### **TOTAL: ${total:,.2f}**")

            # Descargar PDF
            st.download_button(
                "Descargar PDF",
                pdf_buffer,
                file_name=f"Nota_{nota['numero']}_{cliente}.pdf",
                mime="application/pdf",
                type="secondary"
            )

            # Compartir (solo funciona en movil)
            if st.button("Compartir", type="secondary"):
                st.info("En movil: Usa el boton de compartir del navegador")

            # Limpiar formulario
            st.session_state.servicios_temp = [{'concepto': '', 'cantidad': 1, 'precio': 0}]

# ========== HISTORIAL ==========
st.divider()
st.header("Historial de Notas")

if st.session_state.notas:
    # Filtro por semana
    semana_actual = datetime.now().isocalendar()[1]
    notas_semanales = [
        n for n in st.session_state.notas
        if hasattr(n['fecha'], 'isocalendar') and n['fecha'].isocalendar()[1] == semana_actual
    ] or st.session_state.notas[-5:]  # Si no hay de esta semana, mostrar últimos 5

    for nota in reversed(notas_semanales):
        with st.expander(f"Nota #{nota['numero']} - {nota['cliente']} - ${nota['total']:,.2f}"):
            col_info1, col_info2 = st.columns(2)
            col_info1.write(f"**Cliente:** {nota['cliente']}")
            col_info2.write(f"**Fecha:** {nota['fecha']}")

            st.write("**Servicios:**")
            for svc in nota['servicios']:
                st.write(f"  - {svc['cantidad']}x {svc['concepto']} - ${svc['cantidad'] * svc['precio']:,.2f}")

            st.write(f"**Subtotal:** ${nota['subtotal']:,.2f}")
            st.write(f"**IVA ({nota['iva_porcentaje']}%):** ${nota['iva']:,.2f}")
            st.write(f"### Total: ${nota['total']:,.2f}")

            # Regenerar PDF
            pdf = generar_pdf(nota, st.session_state.logo_base64, st.session_state.nombre_negocio)
            st.download_button(
                "Descargar PDF",
                pdf,
                file_name=f"Nota_{nota['numero']}_{nota['cliente']}.pdf",
                mime="application/pdf"
            )

            # Eliminar
            if st.button(f"Eliminar nota #{nota['numero']}", key=f"del_nota_{nota['numero']}"):
                st.session_state.notas = [n for n in st.session_state.notas if n['numero'] != nota['numero']]
                guardar_notas()
                st.rerun()
else:
    st.info("No hay notas guardadas. Crea tu primera nota arriba.")

# ========== FOOTER ==========
st.divider()
st.caption("App de Notas de Venta - Creado con Streamlit")
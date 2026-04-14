import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string
import pandas as pd
import hashlib

# --- 1. CONFIGURACIÓN DE SEGURIDAD Y ESTILO ---
st.set_page_config(page_title="Hazard Corp | Enterprise Portal", layout="wide", page_icon="🔒")

# Estilo de Interfaz de Alta Seguridad
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0B0E11; }
    
    /* Login Box */
    .login-container {
        max-width: 400px;
        margin: auto;
        padding: 40px;
        background: #161B22;
        border-radius: 10px;
        border: 1px solid #30363D;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    .header-status {
        background: #161B22;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #10B981;
        margin-bottom: 20px;
    }
    
    div[data-testid="stMetricValue"] { 
        font-family: 'JetBrains Mono', monospace; 
        color: #10B981; 
    }
    
    /* Glassmorphism effect for cards */
    .glass-card {
        background: rgba(22, 27, 34, 0.7);
        border-radius: 10px;
        border: 1px solid #30363D;
        padding: 20px;
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }
    
    /* Button styles */
    .stButton button {
        border: 1px solid #30363D;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(16, 185, 129, 0.2);
    }
    
    /* Table styles */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Remove item button */
    .remove-btn {
        background: linear-gradient(90deg, #ff6b6b 0%, #ee5a52 100%) !important;
        color: white !important;
        border: none !important;
        padding: 4px 8px !important;
        border-radius: 4px !important;
        font-size: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE BASE DE DATOS Y USUARIOS ---
DB_NAME = 'hazard_enterprise_v3.db'

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def init_db(reset=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if reset:
        c.execute("DROP TABLE IF EXISTS detalles")
        c.execute("DROP TABLE IF EXISTS ventas")
    
    # Tabla de Usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)''')
    
    # Tabla de Ventas
    c.execute('''CREATE TABLE极速赛车开奖直播 IF NOT EXISTS ventas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, folio TEXT, cliente TEXT, fecha TEXT, iva_porc REAL, total REAL, vendedor TEXT)''')
    
    # Tabla de Detalles
    c.execute('''CREATE TABLE IF NOT EXISTS detalles 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, descripcion TEXT, cant REAL, precio REAL, subtotal REAL,
                  FOREIGN KEY(venta_id) REFERENCES ventas(id))''')
    
    # Crear usuarios por defecto si no existen
    c.execute("SELECT * FROM usuarios WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (username, password, role) VALUES (?,?,?)", 
                  ('admin', make_hashes('admin123'), 'Admin'))
        c.execute("INSERT INTO usuarios (username, password, role) VALUES (?,?,?)", 
                  ('vendedor', make_hashes('ventas123'), 'Vendedor'))
        
    conn.commit()
    conn.close()

def generar_folio():
    return f"HZ-{datetime.now().strftime('%y%m')}-{''.join(random.choice(string.digits) for _ in range(4))}"

init_db()

# --- 3. LÓGICA DE AUTENTICACIÓN MEJORADA ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.auth = False  # Para control de acceso

def login_ui():
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image("Hazard.png", use_container_width=True)
            except:
                st.markdown("<div style='text-align: center; color: #10B981; font-size: 24px; font-weight: bold;'>HAZARD CORP</div>", unsafe_allow_html=True)
        st.title("🔐 Acceso Hazard Corp")
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        if st.button("Ingresar Sistema", use_container_width=True):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT password, role FROM usuarios WHERE username=?", (user,))
            res = c.fetchone()
            conn.close()
            
            if res and check_hashes(pw, res[0]):
                st.session_state.logged_in = True
                st.session_state.auth = True
                st.session_state.username = user
                st.session_state.role = res[1]
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. MOTOR DE PDF PROFESIONAL ---
class PDF(FPDF):
    def header(self):
        if 'logo_data' in st.session_state and st.session_state.logo_data:
            with open("temp_logo.png", "wb") as f: f.write(st.session_state.logo_data)
            self.image("极速赛车开奖直播temp_logo.png", 10, 8, 30)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, st.session_state.nombre_empresa.upper(), ln=True, align='R')
        self.set_font('Arial', '', 8)
        self.cell(0, 4, f"RFC: {st.session_state.rfc_empresa}", ln=True, align极速赛车开奖直播='R')
        self.multi_cell(0, 4, st.session_state.direccion, align='R')
        self.cell(0, 4, f"Tel: {st.session_state.telefono}", ln=True, align='极速赛车开奖直播R')
        self.ln(12)

# --- 5. APLICACIÓN PRINCIPAL (SI ESTÁ LOGUEADO) ---
if not st.session_state.auth:
    login_ui()
else:
    # Sidebar de Configuración y Usuario
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        st.info(f"Rol: {st.session_state.role}")
        
        if st.button("Cerrar Sesión"):
            st.session_state.logged_in = False
            st.session_state.auth = False
            st.rerun()
            
        st.divider()
        st.markdown("### Identidad Corporativa")
        logo_file = st.file_uploader("Actualizar Logo", type=["png", "jpg", "jpeg"])
        st.session_state.logo_data = logo_file.getvalue() if logo_file else None
        
        st.session_state.nombre_empresa = st.text_input("Razón Social", value="Hazard Corp")
        st.session_state.rfc_empresa = st.text_input("RFC", value="MODD9009069Q1")
        st.session_state.direccion = st.text_area("Domicilio Fiscal", value="Héroe de Nacozari #904, Col. Ampliación Bellavista C.P. 35058, Gómez Palacio Dgo.")
        st.session_state.telefono = st.text_input("Contacto", value="87-18-45-71-17")

        if st.session_state.role == "Admin":
            st.divider()
            if st.button("⚠️ LIMPIAR BASE DE DATOS"):
                init_db(reset=True)
                st.warning("Sistema reiniciado.")
                st.rerun()

    # Dashboard Principal
    st.markdown(f"""
        <div class="header-status">
            <strong>Panel de Control:</strong> {st.session_state.nombre_empresa} | 
            <strong>Usuario Activo:</strong> {st.session_state.username} ({st.session_state.role})
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 Generar Cotización/Venta", "🔍 Historial de Folios", "📊 Reporte Maestro (Admin)"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2.5, 1, 1])
        cliente = c1.text_input("Cliente / Razón Social")
        fecha_v = c2.date_input("Fecha de Emisión")
        iva_p = c3.number_input("IVA %", value=16.0)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("#### Configuración de Partidas")
        sub_t1, sub_t2 = st.tabs(["Equipamiento", "Cableado Estructurado"])
        
        if 'carrito' not in st.session_state: 
            st.session_state.carrito = []

        with sub_t1:
            col_d, col_c, col_p = st.columns([3, 1, 1])
            desc_e = col_d.text_input("Descripción del Producto", placeholder="Ej. Kit 4 Cámaras 1080p")
            cant_e = col_c.number_input("Cantidad", min_value=1.0, value=1.0, key="c_eq")
            prec_e = col_p.number_input("Precio Unitario", min_value=0.0, key="p_eq")
            if st.button("Agregar Equipo"):
                if desc_e and prec_e > 0:
                    st.session_state.carrito.append({"desc": desc极速赛车开奖直播_e, "cant": cant_e, "prec": prec_e})
                    st.rerun()

        with sub_t2:
            col_cd, col_cm, col_cp = st.columns([3, 1, 1])
            cable_tipo = col_cd.selectbox("Tipo de Cable", ["Cable UTP Cat5e Ext.", "Cable UTP Cat6 Int.", "Coaxial RG59 + Corriente"])
            metros = col_cm.number_input("Metros", min_value=1.0, value=1.0)
            precio_m = col_cp.number_input("Precio por Metro", value=18.0)
            if st.button("Agregar Cableado"):
                st.session_state.carrito.append({"desc": f"{cable_tipo} ({metros}m)", "cant": metros, "prec": precio_m})
                st.rerun()

        if st.session_state.carrito:
            st.markdown("#### 🛒 Carrito de Compra")
            
            # Crear DataFrame para el carrito con botones de eliminación
            carrito_data = []
            for idx, item in enumerate(st.session_state.carrito):
                carrito_data.append({
                    "Ítem": idx + 1,
                    "Descripción": item['desc'],
                    "Cantidad": item['cant'],
                    "Precio Unitario": f"${item['prec']:,.2f}",
                    "Subtotal": f"${item['cant'] * item['prec']:,.2f}",
                    "Acción": idx  # Guardamos el índice para el botón
                })
            
            carrito_df = pd.DataFrame(carrito_data)
            
            # Mostrar la tabla con botones de eliminación
            for _, row in carrito_df.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([0.5, 3, 1, 1, 1, 1])
                with col1:
                    st.write(row['Ítem'])
                with col2:
                    st.write(row['Descripción'])
                with col3:
                    st.write(row['Cantidad'])
                with col4:
                    st.write(row['Precio Unitario'])
                with col5:
                    st.write(row['Subtotal'])
                with col6:
                    if st.button("🗑️", key=f"del_{row['Acción']}", help="Eliminar ítem"):
                        del st.session_state.carrito[row['Acción']]
                        st.rerun()
            
            # Calcular totales
            subt = sum(p['cant'] * p['prec'] for p in st.session_state.carrito)
            iva = subt * (iva_p/100)
            total_v = subt + iva
            
            col1, col2, col3 = st.columns(3)
            col1.metric("SUBTOTAL", f"${subt:,.2f} MXN")
            col2.metric("IVA", f"${iva:,.2f} MXN")
            col3.metric("TOTAL", f"${total_v:,.2f} MXN", delta_color="off")

            if st.button("✅ REGISTRAR Y GENERAR FOLIO", type="primary", use_container_width=True):
                if cliente:
                    folio = generar_folio()
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    cur.execute("INSERT INTO ventas (folio, cliente, fecha, iva_porc, total, vendedor) VALUES (?,?,?,?,?,?)",
                              (folio, cliente, str(fecha_v), iva_p, total_v, st.session_state.username))
                    v_id = cur.lastrowid
                    for p in st.session_state.carrito:
                        cur.execute("INSERT INTO detalles (venta_id, descripcion, cant, precio, subtotal极速赛车开奖直播) VALUES (?,?,?,?,?)",
                                  (v_id, p['desc'], p['cant'], p['prec'], p['cant']*p['prec']))
                    conn.commit()
                    conn.close()
                    st.session_state.carrito = []
                    st.success(f"Registro exitoso. Folio: {folio}")
                    st.balloons()
                else: 
                    st.error("Falta el nombre del cliente.")

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        search = st.text_input("Buscar por Folio o Cliente...")
        st.markdown('</div>', unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_NAME)
        # Los vendedores solo ven lo suyo, el admin ve todo
        if st.session_state.role == "Admin":
            query = "SELECT * FROM ventas WHERE (folio LIKE ? OR cliente LIKE ?) ORDER BY id DESC"
            params = (f'%{search}%', f'%{search}%')
        else:
            query = "SELECT * FROM ventas WHERE vendedor=? AND (folio LIKE ? OR cliente LIKE ?) ORDER BY id DESC"
            params = (st.session_state.username, f'%{search}%', f'%{search}%')
            
        ventas_list = pd.read_sql_query(query, conn, params=params)
        conn.close()

        for index, row in ventas_list.iterrows():
            with st.expander(f"FOLIO: {row['folio']} | {row['cliente']} | Vendedor: {row['vendedor']}"):
                conn = sqlite3.connect(DB_NAME)
                items = pd.read_sql_query("SELECT descripcion, cant, precio FROM detalles WHERE venta_id=?", conn, params=(row['id'],))
                conn.close()
                
                # Formatear la tabla para mejor visualización
                items_display = items.copy()
                items_display['precio'] = items_display['precio'].apply(lambda x: f"${x:,.2f}")
                items_display['subtotal'] = items_display['cant'] * items_display['precio'].str.replace('$', '').str.replace(',', '').astype(float)
                items_display['subtotal'] = items_display['subtotal'].apply(lambda x: f"${x:,.2f}")
                items_display = items_display.rename(columns={
                    'descripcion': 'Descripción', 
                    'cant': 'Cantidad', 
                    'precio': 'Precio Unitario'
                })
                
                st.table(items_display)
                
                # Botón de PDF
                items_list = items.to_dict('records')
                # Adaptación para el generador de PDF (renombrar llaves)
                for i in items_list: 
                    i['desc'] = i['descripcion']
                    i['prec'] = i['precio']
                
                pdf = PDF()
                pdf.add_page()
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 10, f"CLIENTE: {row['cliente']}", ln=True)
                pdf.cell(0, 10, f"FOLIO: {row['folio']} | FECHA: {row['fecha']}", ln=True)
                pdf.ln(5)
                
                # Crear tabla en PDF
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(100, 8, 'DESCRIPCIÓN', 1)
                pdf.cell(30, 8, 'CANTIDAD', 1)
                pdf.cell(30, 8, 'PRECIO', 1)
                pdf.cell(30, 8, 'SUBTOTAL', 1)
                pdf.ln()
                
                pdf.set_font('Arial', '', 10)
                for item in items_list:
                    pdf.cell(100, 8, item['desc'][:40], 1)  # Limitar longitud
                    pdf.cell(30, 8, str(item['cant']), 1)
                    pdf.cell(30, 8, f"${item['prec']:,.2f}", 1)
                    pdf.cell(30, 8, f"${item['cant'] * item['prec']:,.2f}", 1)
                    pdf.ln()
                
                # Totales
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(160, 10, 'TOTAL:', 0, 0, 'R')
                pdf.cell(30, 10, f"${row['total']:,.2f}", 1, 1, 'R')
                
                # Guardar PDF en bytes
                pdf_bytes = pdf.output(dest='S').encode('latin1')
                
                st.download_button(
                    label="📄 Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"comprobante_{row['folio']}.pdf",
                    mime="application/pdf"
                )
                
    with tab3:
        if st.session_state.role == "Admin":
            st.markdown("#### Inteligencia de Negocio")
            
            conn = sqlite3.connect(DB_NAME)
            query_global = """
                SELECT v.folio, v.fecha, v.cliente, v.vendedor, d.descripcion, d.cant, d.precio, d.subtotal
                FROM detalles d JOIN ventas v ON d.venta_id = v.id ORDER BY v.id DESC
            """
            df_global = pd.read_sql_query(query_global, conn)
            
            # Gráfico de ventas por día
            st.markdown("##### Ventas Totales por Día")
            ventas_por_dia = df_global.groupby(pd.to_datetime(df_global['fecha']).dt.date)['subtotal'].sum().reset_index()
            ventas_por_dia.columns = ['Fecha', 'Total_Ventas']
            
            if not ventas_por_dia.empty:
                st.line_chart(ventas_por_dia.set_index('Fecha'))
            else:
                st.info("No hay datos suficientes para generar el gráfico.")
            
            # Resumen de ventas
            st.markdown("##### Resumen de Ventas")
            col1, col2, col3 = st.columns(3)
            total_ventas = df_global['subtotal'].sum()
            ventas_promedio = df_global['subtotal'].mean() if not df_global.empty else 0
            total_transacciones = df_global['folio'].nunique()
            
            col1.metric("Ventas Totales", f"${total_ventas:,.2f}")
            col2.metric("Ticket Promedio", f"${ventas_promedio:,.2f}")
            col3.metric("Total Transacciones", total_transacciones)
            
            # Tabla de datos
            st.markdown("##### Detalle de Ventas")
            if not df_global.empty:
                st.dataframe(df_global, use_container_width=True, hide_index=True)
                
                # Exportación Excel
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_global.to_excel(writer, index=False, sheet_name='Reporte_Master')
                st.download_button("Descargar Reporte Maestro (Excel)", buffer.getvalue(), 
                                 f"Reporte_Hazard_{datetime.now().strftime('%Y%m%d')}.xlsx", 
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("Sin registros globales.")
                
            conn.close()
        else:
            st.warning("Área restringida para Administradores.")

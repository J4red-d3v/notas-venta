import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import sqlite3
import random
import string
import pandas as pd
import hashlib
import time

# --- 1. CONFIGURACIÓN DE SEGURIDAD Y ESTILO MEJORADA ---
st.set_page_config(page_title="Hazard Corp | Enterprise Portal", layout="wide", page_icon="🔒")

# Estilo de Interfaz de Alta Seguridad Mejorado
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    }
    .stApp { 
        background: linear-gradient(135deg, #0B0E11 0%, #0D1117 100%);
    }
    
    /* Login Box Mejorado */
    .login-container {
        max-width: 420px;
        margin: 120px auto;
        padding: 40px 30px;
        background: rgba(22, 27, 34, 0.95);
        border-radius: 12px;
        border: 1px solid #2EA04330;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
    }
    
    .login-title {
        text-align: center;
        color: #10B981;
        font-weight: 700;
        font-size: 28px;
        margin-bottom: 8px;
        font-family: 'Inter', sans-serif;
    }
    
    .login-subtitle {
        text-align: center;
        color: #C9D1D9;
        font-size: 14px;
        margin-bottom: 32px;
        font-weight: 300;
    }
    
    .stTextInput input {
        background-color: #0D1117 !important;
        color: #C9D1D9 !important;
        border: 1px solid #30363D !important;
        border-radius: 6px !important;
        padding: 12px 14px !important;
    }
    
    .stTextInput input:focus {
        border-color: #10B981 !important;
        box-shadow: 0 0 0 2px #10B98140 !important;
    }
    
    .stButton button {
        width: 100%;
        background: linear-gradient(90deg, #10B981 0%, #0D9488 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 14px !important;
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3) !important;
    }
    
    .stButton button:active {
        transform: translateY(0);
    }
    
    /* Header mejorado */
    .header-status {
        background: linear-gradient(90deg, #161B22 0%, #0D1117 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #10B981;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar mejorado */
    .css-1d391kg, .css-1y4p3pa {
        background: linear-gradient(180deg, #161B22 0%, #0D1117 100%) !important;
    }
    
    /* Métricas mejoradas */
    div[data-testid="stMetricValue"] { 
        font-family: 'JetBrains Mono', monospace; 
        color: #10B981; 
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    
    /* Tabs mejorados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #161B22;
        border-radius: 8px 8px 0 0;
        padding: 16px 24px;
        border: 1px solid #30363D;
        border-bottom: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: #10B981 !important;
        color: white !important;
    }
    
    /* Tablas mejoradas */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Efectos de carga mejorados */
    .stSpinner > div {
        border: 3px solid #10B98130;
        border-top: 3px solid #10B981;
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
    c.execute('''CREATE TABLE IF NOT EXISTS ventas 
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
    st.session_state.auth_message = ""

def login_ui():
    # Fondo con efecto de partículas (simulado con CSS)
    st.markdown("""
        <div style='position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; 
                    background: radial-gradient(circle at 20% 30%, #0D948855 0%, transparent 40%),
                                radial-gradient(circle at 80% 70%, #10B98155 0%, transparent 40%),
                                #0B0E11;'>
        </div>
    """, unsafe_allow_html=True)
    
    # Contenedor principal del login
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Logo y título
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image("Hazard.png", use_container_width=True)
            except:
                st.markdown("<div style='text-align: center; color: #10B981; font-size: 24px; font-weight: bold; margin-bottom: 20px;'>HAZARD CORP</div>", unsafe_allow_html=True)
        
        st.markdown('<div class="login-title">Enterprise Portal</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Sistema de Gestión Comercial y Seguridad</div>', unsafe_allow_html=True)
        
        # Formulario de login
        user = st.text_input("Usuario", placeholder="Ingrese su usuario")
        pw = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
        
        # Botón de ingreso con animación
        if st.button("🔐 Ingresar al Sistema", use_container_width=True, type="primary"):
            with st.spinner("Verificando credenciales..."):
                time.sleep(0.5)  # Pequeña pausa para mejor UX
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT password, role FROM usuarios WHERE username=?", (user,))
                res = c.fetchone()
                conn.close()
                
                if res and check_hashes(pw, res[0]):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.role = res[1]
                    st.session_state.auth_message = "success"
                    st.rerun()
                else:
                    st.session_state.auth_message = "error"
                    st.error("Credenciales incorrectas. Intente nuevamente.")
        
        # Mensaje de estado
        if st.session_state.auth_message == "error":
            st.error("Acceso denegado. Verifique sus credenciales.")
        elif st.session_state.auth_message == "success":
            st.success("Acceso concedido. Redirigiendo...")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer del login
        st.markdown("""
            <div style='text-align: center; margin-top: 30px; color: #8B949E; font-size: 12px;'>
                Hazard Corp © 2023 | Sistema de Gestión Empresarial
            </div>
        """, unsafe_allow_html=True)

# --- 4. MOTOR DE PDF PROFESIONAL ---
class PDF(FPDF):
    def header(self):
        if 'logo_data' in st.session_state and st.session_state.logo_data:
            with open("temp_logo.png", "wb") as f: f.write(st.session_state.logo_data)
            self.image("temp_logo.png", 10, 8, 30)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, st.session_state.nombre_empresa.upper(), ln=True, align='R')
        self.set_font('Arial', '', 8)
        self.cell(0, 4, f"RFC: {st.session_state.rfc_empresa}", ln=True, align='R')
        self.multi_cell(0, 4, st.session_state.direccion, align='R')
        self.cell(0, 4, f"Tel: {st.session_state.telefono}", ln=True, align='R')
        self.ln(12)

# --- 5. APLICACIÓN PRINCIPAL (SI ESTÁ LOGUEADO) ---
if not st.session_state.logged_in:
    login_ui()
else:
    # Sidebar de Configuración y Usuario mejorado
    with st.sidebar:
        # Información de usuario
        st.markdown(f"""
            <div style='background: linear-gradient(90deg, #10B98120 0%, transparent 100%); 
                        padding: 16px; border-radius: 8px; margin-bottom: 24px;'>
                <div style='font-size: 18px; font-weight: 600; color: #10B981;'>👤 {st.session_state.username}</div>
                <div style='font-size: 14px; color: #8B949E;'>Rol: {st.session_state.role}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.auth_message = ""
            st.rerun()
            
        st.divider()
        
        # Identidad Corporativa
        st.markdown("### 🎨 Identidad Corporativa")
        logo_file = st.file_uploader("Actualizar Logo", type=["png", "jpg", "jpeg"], 
                                    help="Suba una imagen para personalizar el logo en los documentos")
        if logo_file:
            st.session_state.logo_data = logo_file.getvalue()
        else:
            # Logo por defecto si no se ha subido uno
            try:
                with open("Hazard.png", "rb") as f:
                    st.session_state.logo_data = f.read()
            except:
                st.session_state.logo_data = None
        
        st.session_state.nombre_empresa = st.text_input("Razón Social", value="Hazard Corp")
        st.session_state.rfc_empresa = st.text_input("RFC", value="MODD9009069Q1")
        st.session_state.direccion = st.text_area("Domicilio Fiscal", value="Héroe de Nacozari #904, Col. Ampliación Bellavista C.P. 35058, Gómez Palacio Dgo.")
        st.session_state.telefono = st.text_input("Contacto", value="87-18-45-71-17")

        if st.session_state.role == "Admin":
            st.divider()
            st.markdown("### ⚙️ Administración")
            if st.button("⚠️ LIMPIAR BASE DE DATOS", use_container_width=True):
                if st.checkbox("¿Está seguro? Esta acción no se puede deshacer"):
                    init_db(reset=True)
                    st.warning("Base de datos reiniciada correctamente.")
                    time.sleep(1.5)
                    st.rerun()

    # Dashboard Principal mejorado
    st.markdown(f"""
        <div class="header-status">
            <span style='font-size: 18px; font-weight: 600; color: #10B981;'>Panel de Control</span><br>
            <span style='color: #C9D1D9;'>{st.session_state.nombre_empresa} | Usuario: {st.session_state.username} ({st.session_state.role})</span>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 Generar Cotización/Venta", "🔍 Historial de Folios", "📊 Reporte Global (Admin)"])

    with tab1:
        # Formulario de venta/cotización
        c1, c2, c3 = st.columns([2.5, 1, 1])
        cliente = c1.text_input("Cliente / Razón Social", placeholder="Nombre completo o razón social del cliente")
        fecha_v = c2.date_input("Fecha de Emisión")
        iva_p = c3.number_input("IVA %", value=16.0, min_value=0.0, max_value=100.0)

        st.markdown("#### Configuración de Partidas")
        sub_t1, sub_t2 = st.tabs(["🖥️ Equipamiento", "🔌 Cableado Estructurado"])
        
        if 'carrito' not in st.session_state: 
            st.session_state.carrito = []

        with sub_t1:
            st.markdown("###### Agregar Equipos de Seguridad")
            col_d, col_c, col_p = st.columns([3, 1, 1])
            desc_e = col_d.text_input("Descripción del Producto", placeholder="Ej. Kit 4 Cámaras 1080p", key="desc_equipo")
            cant_e = col_c.number_input("Cantidad", min_value=1.0, value=1.0, key="c_eq")
            prec_e = col_p.number_input("Precio Unitario", min_value=0.0, key="p_eq")
            
            if st.button("➕ Agregar Equipo", key="add_equipo"):
                if desc_e and prec_e > 0:
                    st.session_state.carrito.append({"desc": desc_e, "cant": cant_e, "prec": prec_e})
                    st.success("Producto agregado al carrito")
                    st.rerun()
                else:
                    st.error("Complete todos los campos del producto")

        with sub_t2:
            st.markdown("###### Calculadora de Cableado")
            col_cd, col_cm, col_cp = st.columns([3, 1, 1])
            cable_tipo = col_cd.selectbox("Tipo de Cable", ["Cable UTP Cat5e Ext.", "Cable UTP Cat6 Int.", "Coaxial RG59 + Corriente"])
            metros = col_cm.number_input("Metros", min_value=1.0, value=1.0)
            precio_m = col_cp.number_input("Precio por Metro", value=18.0)
            
            if st.button("➕ Agregar Cableado", key="add_cable"):
                st.session_state.carrito.append({"desc": f"{cable_tipo} ({metros}m)", "cant": metros, "prec": precio_m})
                st.success("Cableado agregado al carrito")
                st.rerun()

        # Mostrar carrito de compras
        if st.session_state.carrito:
            st.markdown("---")
            st.markdown("#### 🛒 Carrito de Compra")
            
            # Crear DataFrame para mejor visualización
            carrito_df = pd.DataFrame(st.session_state.carrito)
            carrito_df['Subtotal'] = carrito_df['cant'] * carrito_df['prec']
            carrito_df.index = range(1, len(carrito_df) + 1)
            
            # Formatear columnas para mejor visualización
            carrito_display = carrito_df.copy()
            carrito_display['prec'] = carrito_display['prec'].apply(lambda x: f"${x:,.2f}")
            carrito_display['Subtotal'] = carrito_display['Subtotal'].apply(lambda x: f"${x:,.2f}")
            carrito_display = carrito_display.rename(columns={
                'desc': 'Descripción', 
                'cant': 'Cantidad', 
                'prec': 'Precio Unitario'
            })
            
            st.table(carrito_display)
            
            # Calculadora de totales
            subt = sum(p['cant'] * p['prec'] for p in st.session_state.carrito)
            iva = subt * (iva_p/100)
            total_v = subt + iva
            
            col1, col2, col3 = st.columns(3)
            col1.metric("SUBTOTAL", f"${subt:,.2f} MXN")
            col2.metric("IVA", f"${iva:,.2f} MXN")
            col3.metric("TOTAL", f"${total_v:,.2f} MXN", delta_color="off")

            # Botón de registro
            if st.button("✅ REGISTRAR Y GENERAR FOLIO", type="primary", use_container_width=True):
                if cliente:
                    with st.spinner("Procesando venta..."):
                        folio = generar_folio()
                        conn = sqlite3.connect(DB_NAME)
                        cur = conn.cursor()
                        cur.execute("INSERT INTO ventas (folio, cliente, fecha, iva_porc, total, vendedor) VALUES (?,?,?,?,?,?)",
                                  (folio, cliente, str(fecha_v), iva_p, total_v, st.session_state.username))
                        v_id = cur.lastrowid
                        for p in st.session_state.carrito:
                            cur.execute("INSERT INTO detalles (venta_id, descripcion, cant, precio, subtotal) VALUES (?,?,?,?,?)",
                                      (v_id, p['desc'], p['cant'], p['prec'], p['cant']*p['prec']))
                        conn.commit()
                        conn.close()
                        st.session_state.carrito = []
                        st.success(f"✅ Registro exitoso. Folio: **{folio}**")
                        st.balloons()
                else: 
                    st.error("❌ Debe especificar el nombre del cliente.")

    with tab2:
        # Búsqueda y visualización de historial
        st.markdown("#### Historial de Transacciones")
        search = st.text_input("Buscar por Folio o Cliente...", placeholder="Ingrese folio o nombre de cliente")
        
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

        if ventas_list.empty:
            st.info("No se encontraron transacciones con los criterios de búsqueda.")
        else:
            for index, row in ventas_list.iterrows():
                with st.expander(f"{row['folio']} | {row['cliente']} | ${row['total']:,.2f} | {row['fecha']}"):
                    conn = sqlite3.connect(DB_NAME)
                    items = pd.read_sql_query("SELECT descripcion, cant, precio, subtotal FROM detalles WHERE venta_id=?", 
                                            conn, params=(row['id'],))
                    conn.close()
                    
                    # Formatear la tabla para mejor visualización
                    items_display = items.copy()
                    items_display['precio'] = items_display['precio'].apply(lambda x: f"${x:,.2f}")
                    items_display['subtotal'] = items_display['subtotal'].apply(lambda x: f"${x:,.2f}")
                    items_display = items_display.rename(columns={
                        'descripcion': 'Descripción', 
                        'cant': 'Cantidad', 
                        'precio': 'Precio Unitario',
                        'subtotal': 'Subtotal'
                    })
                    
                    st.table(items_display)
                    
                    # Botones de acción
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📄 Generar PDF", key=f"pdf_{row['id']}"):
                            # Lógica para generar PDF (similar a la original)
                            st.info("Generando PDF...")
                    with col2:
                        if st.button("📊 Ver Detalles", key=f"det_{row['id']}"):
                            st.info("Mostrando detalles completos...")
                
    with tab3:
        if st.session_state.role == "Admin":
            st.markdown("#### Inteligencia de Negocio")
            conn = sqlite3.connect(DB_NAME)
            query_global = """
                SELECT v.folio, v.fecha, v.cliente, v.vendedor, d.descripcion, d.cant, d.precio, d.subtotal
                FROM detalles d JOIN ventas v ON d.venta_id = v.id ORDER BY v.id DESC
            """
            df_global = pd.read_sql_query(query_global, conn)
            conn.close()
            
            if not df_global.empty:
                # Mostrar métricas resumen
                total_ventas = df_global['subtotal'].sum()
                avg_venta = df_global['subtotal'].mean()
                num_transacciones = df_global['folio'].nunique()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Ventas", f"${total_ventas:,.2f} MXN")
                col2.metric("Transacciones", num_transacciones)
                col3.metric("Ticket Promedio", f"${avg_venta:,.2f} MXN")
                
                # Dataframe con los datos
                st.dataframe(df_global, use_container_width=True, hide_index=True)
                
                # Exportación Excel
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_global.to_excel(writer, index=False, sheet_name='Reporte_Master')
                
                st.download_button("💾 Descargar Reporte Maestro (Excel)", buffer.getvalue(), 
                                 f"Reporte_Hazard_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", 
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 use_container_width=True)
            else:
                st.info("No hay registros para mostrar.")
        else:
            st.warning("⛔ Área restringida para Administradores.")

# 🧾 Notas de Venta - Guía de Despliegue

## Archivos creados:
- `app.py` - Aplicación principal (Streamlit)
- `requirements.txt` - Dependencias de Python

---

## 🚀 OPCIÓN 1: Streamlit Cloud (GRATIS) - 15 min

### Paso 1: Preparar archivos locales
Crea una cuenta en [GitHub.com](https://github.com) (es gratis)

En tu computadora, crea una carpeta con estos archivos:
```
notas-venta/
├── app.py
├── requirements.txt
└── README.md  (opcional)
```

### Paso 2: Subir a GitHub
1. Ve a [github.com](https://github.com) y crea un nuevo repositorio llamado `notas-venta`
2. Sigue las instrucciones para subir tu código:
   ```bash
   git init
   git add .
   git commit -m "initial commit"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/notas-venta.git
   git push -u origin main
   ```

### Paso 3: Desplegar en Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con GitHub
3. Click "New app"
4. Selecciona tu repositorio `notas-venta`
5. Branch: `main`
6. Main file path: `app.py`
7. Click "Deploy!"

**Resultado:** Recibirás una URL como `https://TUUSUARIO-notas-venta.streamlit.app`

---

## 🖥️ OPCIÓN 2: Ejecución local (para probar)

### En tu computadora:

```bash
# 1. Crear entorno virtual (opcional pero recomendado)
python -m venv venv
venv\Scripts\activate  # En Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar
streamlit run app.py
```

Se abrirá en tu navegador en `http://localhost:8501`

---

## 📱 Cómo usar la app:

1. **Configura tu negocio** (sidebar izquierdo):
   - Carga el logo de tu negocio (PNG/JPG)
   - Escribe el nombre de tu negocio

2. **Crea una nota de venta:**
   - Ingresa el nombre del cliente
   - Selecciona la fecha
   - Agrega servicios/productos (concepto, cantidad, precio)
   - Ajusta el % de IVA si es diferente a 16%
   - Click "Generar Nota de Venta"

3. **Descarga o comparte el PDF:**
   - Botón "📥 Descargar PDF" para guardar
   - En celular, usa la función compartir del navegador

4. **Historial:**
   - Las notas se guardan automáticamente
   - Puedes descargar el PDF de cualquier nota anterior

---

## ⚠️ Notas importantes:

- El logo y la configuración se guardan en archivos locales (`logo.png`, `config.txt`)
- Las notas se guardan en `notas.csv`
- En Streamlit Cloud, los archivos no persisten entre sesiones
- Para persistencia real, necesitarías agregar una base de datos (pero para empezar está bien)

---

## 🔧 Si quieres agregar persistencia con Supabase (gratis):

1. Crea cuenta en [supabase.com](https://supabase.com)
2. Crea un proyecto
3. Obtén la URL y la key
4. Instala: `pip install supabase`
5. Modifica el código para guardar/leer de Supabase en lugar de archivos locales

El código actual funciona perfecto para empezar y probar. Después puedes agregar base de datos si necesitas que las notas persistan en la nube.
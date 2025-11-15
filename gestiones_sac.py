import streamlit as st
import pandas as pd
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# ==============================
# CONFIGURACIÓN GOOGLE SHEETS
# ==============================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

credenciales_dict = json.loads(st.secrets["GOOGLE_SHEETS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(credenciales_dict, scope)
client = gspread.authorize(creds)

# IMPORTANTE:
# Crea en tu Google Drive una planilla llamada "Gestiones_SAC"
# con estas columnas en la fila 1:
# Fecha | Gestor | Sitio | Actividad
sheet = client.open("Gestiones_SAC").sheet1

data = sheet.get_all_records()
df_existente = pd.DataFrame(data)

if not df_existente.empty and "Fecha" in df_existente.columns:
    df_existente["Fecha"] = pd.to_datetime(df_existente["Fecha"], errors="coerce")

# ==============================
# CONFIG VISUAL
# ==============================

st.set_page_config(page_title="GESTIONES SAC", layout="centered")

st.markdown(
    """
    <style>
    .stApp {background-color: #f9f5ff;}
    h1, h2, h3 {text-align: center; color: #2d004d;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1>GESTIONES SAC</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; color: #4b0082;'>Registro simplificado de actividades diarias de los gestores.</p>",
    unsafe_allow_html=True
)

st.markdown("----")

# ==============================
# LISTAS DESPLEGABLES
# ==============================

gestores = [
    "Hernán Aguilera", "Ignacio Basaure", "Francisco Barrios", "Felipe Camus",
    "Rodrigo Escandón", "Osvaldo Espinoza", "Juan Pablo Molina",
    "Marilin López", "Francisco Parra", "Roberto Severino",
    "Manuel Araus", "Christian Cifuentes", "Guillermo Angermeyer"
]

actividades = [
    "BÚSQUEDA DE ALTERNATIVAS",
    "TSS",
    "FIRMA DE DOCUMENTO",
    "PROCURACIÓN",
    "REUNIÓN CON PROPIETARIO",
    "ENERGÍA PROVISORIA",
    "SERVIDUMBRE",
    "GESTIONES VARIAS"
]

# ==============================
# FORMULARIO DE REGISTRO
# ==============================

st.markdown("### 📝 Nuevo registro de gestión")

with st.form("registro_gestiones"):
    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input("Fecha", value=date.today())
        gestor = st.selectbox("Gestor", gestores)

    with col2:
        sitio = st.text_input("Nombre del sitio / Site")

    actividad = st.selectbox("Actividad realizada", actividades)

    enviado = st.form_submit_button("✅ Guardar gestión")

    if enviado:
        if not sitio.strip():
            st.error("❌ Debes ingresar el nombre del sitio.")
        else:
            nueva_fila = [
                str(fecha),
                gestor,
                sitio.strip(),
                actividad
            ]
            try:
                sheet.append_row(nueva_fila)
                st.success("✅ Gestión registrada correctamente en Google Sheets.")
            except Exception as e:
                st.error(f"⚠️ Ocurrió un error al guardar la gestión: {e}")

st.markdown("---")

# ==============================
# GRÁFICA RESUMEN GENERAL
# ==============================

st.markdown("### 📊 Resumen general de actividades registradas")

data_resumen = sheet.get_all_records()
df_resumen = pd.DataFrame(data_resumen)

if df_resumen.empty or "Actividad" not in df_resumen.columns:
    st.info("Aún no hay actividades registradas en la planilla.")
else:
    actividad_counts = (
        df_resumen["Actividad"]
        .value_counts()
        .reset_index()
    )
    actividad_counts.columns = ["Actividad", "Cantidad"]
    actividad_counts["Porcentaje"] = (
        actividad_counts["Cantidad"] / actividad_counts["Cantidad"].sum() * 100
    ).round(1)

    st.write("Resumen de actividades (cantidad y porcentaje):")
    st.dataframe(actividad_counts, use_container_width=True)

    chart_data = actividad_counts.set_index("Actividad")[["Porcentaje"]]
    st.bar_chart(chart_data)

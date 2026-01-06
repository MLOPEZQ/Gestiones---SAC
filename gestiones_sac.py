import streamlit as st
import pandas as pd
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import altair as alt

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
    h2, h3 {text-align: center; color: #2d004d;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    </style>
    """,
    unsafe_allow_html=True
)

# Título con fondo morado sólido tipo WOM
st.markdown(
    """
    <div style="background-color:#5700A5;
                padding-top:14px;
                padding-bottom:14px;
                border-radius:12px;
                margin-bottom:10px;">
        <h1 style="color:white;
                   text-align:center;
                   margin:0;
                   letter-spacing:2px;">
            GESTIONES SAC
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# ==============================
# LISTAS DESPLEGABLES
# ==============================

gestores = [
    "Hernán Aguilera", "Ignacio Basaure", "Francisco Barrios", "Felipe Camus",
    "Rodrigo Escandón", "Osvaldo Espinoza", "Juan Pablo Molina",
    "Marilin López", "Francisco Parra", "Andrea Collao"
]

actividades = [
    "BÚSQUEDA DE ALTERNATIVAS",
    "TSS",
    "FIRMA DE DOCUMENTO",
    "PROCURACIÓN",
    "INGRESO DOM",
    "REUNIÓN CON PROPIETARIO",
    "ENERGÍA PROVISORIA",
    "SERVIDUMBRE",
    "APOYO A OTRAS ÁREAS"
]

# ==============================
# FORMULARIO DE REGISTRO
# ==============================

st.markdown("### 📝 Nuevo registro")

with st.form("registro_gestiones"):

    # Fila 1: Fecha / Gestor
    fila1_col1, fila1_col2 = st.columns(2)
    with fila1_col1:
        fecha = st.date_input("Fecha", value=date.today())
    with fila1_col2:
        gestor = st.selectbox("Gestor", gestores)

    # Fila 2: Código Subtel / Actividad
    fila2_col1, fila2_col2 = st.columns(2)
    with fila2_col1:
        sitio = st.text_input("Código Subtel")
    with fila2_col2:
        actividad = st.selectbox("Actividad realizada", actividades)

    enviado = st.form_submit_button("✅ Guardar gestión")

    if enviado:
        if not sitio.strip():
            st.error("❌ Debes ingresar el Código Subtel.")
        else:
            nueva_fila = [
                str(fecha),
                gestor,
                sitio.strip(),
                actividad
            ]
            try:
                sheet.append_row(nueva_fila)
                st.success("✅ Gestión registrada correctamente.")
            except Exception as e:
                st.error(f"⚠️ Ocurrió un error al guardar la gestión: {e}")

st.markdown("---")

# ==============================
# GRÁFICA RESUMEN GENERAL
# ==============================

st.markdown("### 📊 Resumen general de actividades")

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
    ).round(0).astype(int)

    st.dataframe(actividad_counts, use_container_width=True)

    # Orden explícito (mayor a menor) para que SIEMPRE quede bien
    orden_actividades = actividad_counts.sort_values("Cantidad", ascending=False)["Actividad"].tolist()

    chart = (
        alt.Chart(actividad_counts)
        .mark_bar(
            cornerRadiusTopRight=6,
            cornerRadiusBottomRight=6,
            color="#5700A5"
        )
        .encode(
            y=alt.Y("Actividad:N", sort=orden_actividades, title="Actividad"),
            x=alt.X(
    "Cantidad:Q",
    title="Cantidad",
    axis=alt.Axis(
        tickMinStep=1,
        format="d",
        grid=False
    )
),
            tooltip=[
                alt.Tooltip("Actividad:N"),
                alt.Tooltip("Cantidad:Q"),
                alt.Tooltip("Porcentaje:Q", title="Porcentaje (%)")
            ]
        )
        .properties(height=max(320, 28 * len(actividad_counts)))  # altura dinámica según items
    )

    # Etiqueta de % al final de cada barra
    labels = (
        alt.Chart(actividad_counts)
        .mark_text(align="left", baseline="middle", dx=6, fontSize=12, color="#2d004d")
        .encode(
            y=alt.Y("Actividad:N", sort=orden_actividades),
            x=alt.X("Cantidad:Q"),
            text=alt.Text("Porcentaje:Q", format=".0f")
        )
    )

    # Estilo "pro"
    final_chart = (
        (chart + labels)
        .configure_axis(
            labelFontSize=12,
            titleFontSize=12,
            grid=False
        )
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(final_chart, use_container_width=True)

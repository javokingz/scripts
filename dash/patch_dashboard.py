import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Configurar la página
st.set_page_config(
    page_title="EC2 Patch Management Dashboard",
    page_icon="🛠️",
    layout="wide"
)

# Título y descripción
st.title("🛠️ EC2 Patch Management Dashboard")
st.markdown("""
Este dashboard muestra información sobre la instalación de parches en instancias EC2.
Utiliza los filtros en la barra lateral para analizar los datos específicos.
""")

# Conectar a la base de datos
@st.cache_data
def load_data():
    conn = sqlite3.connect('patches.db')
    df = pd.read_sql_query("SELECT * FROM patches", conn)
    conn.close()
    
    # Convertir InstalledTime a datetime
    df['InstalledTime'] = pd.to_datetime(df['InstalledTime'])
    
    return df

# Cargar datos
df = load_data()

# Sidebar para filtros
st.sidebar.header("Filtros")

# Filtros por perfil
profiles = ['Todos'] + sorted(df['Profile'].unique().tolist())
selected_profile = st.sidebar.selectbox('Perfil AWS', profiles)

# Filtros por región
regions = ['Todas'] + sorted(df['Region'].unique().tolist())
selected_region = st.sidebar.selectbox('Región', regions)

# Filtros por severidad
severities = ['Todas'] + sorted(df['Severity'].unique().tolist())
selected_severity = st.sidebar.selectbox('Severidad', severities)

# Filtros por estado
states = ['Todos'] + sorted(df['State'].unique().tolist())
selected_state = st.sidebar.selectbox('Estado', states)

# Filtros por fecha
min_date = df['InstalledTime'].min()
max_date = df['InstalledTime'].max()
start_date = st.sidebar.date_input('Fecha inicial', min_date)
end_date = st.sidebar.date_input('Fecha final', max_date)

# Aplicar filtros
filtered_df = df.copy()
if selected_profile != 'Todos':
    filtered_df = filtered_df[filtered_df['Profile'] == selected_profile]
if selected_region != 'Todas':
    filtered_df = filtered_df[filtered_df['Region'] == selected_region]
if selected_severity != 'Todas':
    filtered_df = filtered_df[filtered_df['Severity'] == selected_severity]
if selected_state != 'Todos':
    filtered_df = filtered_df[filtered_df['State'] == selected_state]
filtered_df = filtered_df[
    (filtered_df['InstalledTime'].dt.date >= start_date) & 
    (filtered_df['InstalledTime'].dt.date <= end_date)
]

# Métricas principales
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Parches", len(filtered_df))
with col2:
    st.metric("Instancias Únicas", filtered_df['Instance_id'].nunique())
with col3:
    st.metric("Cuentas Únicas", filtered_df['Account_id'].nunique())
with col4:
    st.metric("KB IDs Únicos", filtered_df['KBId'].nunique())

# Gráfico de distribución de severidad
st.subheader("Distribución de Severidad de Parches")
severity_counts = filtered_df['Severity'].value_counts()
fig_severity = px.pie(
    values=severity_counts.values,
    names=severity_counts.index,
    title="Distribución de Severidad"
)
st.plotly_chart(fig_severity, use_container_width=True)

# Gráfico de parches por región
st.subheader("Parches por Región")
region_counts = filtered_df['Region'].value_counts()
fig_region = px.bar(
    x=region_counts.index,
    y=region_counts.values,
    title="Número de Parches por Región",
    labels={'x': 'Región', 'y': 'Número de Parches'}
)
st.plotly_chart(fig_region, use_container_width=True)

# Gráfico de evolución temporal
st.subheader("Evolución Temporal de Instalación de Parches")
daily_patches = filtered_df.groupby(filtered_df['InstalledTime'].dt.date).size()
fig_temporal = px.line(
    x=daily_patches.index,
    y=daily_patches.values,
    title="Parches Instalados por Día",
    labels={'x': 'Fecha', 'y': 'Número de Parches'}
)
st.plotly_chart(fig_temporal, use_container_width=True)

# Tabla de datos detallada
st.subheader("Detalles de Parches")
st.dataframe(
    filtered_df[[
        'Profile', 'Region', 'Instance_id', 'Title', 
        'KBId', 'Classification', 'Severity', 'State', 
        'InstalledTime'
    ]],
    use_container_width=True
)

# Exportar datos
if st.button("Exportar Datos Filtrados"):
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name="patches_data.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("Dashboard creado con Streamlit | Última actualización: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")) 
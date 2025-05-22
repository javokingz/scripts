import streamlit as st
import boto3
import pandas as pd
from datetime import datetime
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="EC2 Patch Management DynamoDB Dashboard",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ EC2 Patch Management Dashboard (DynamoDB)")
st.markdown("""
Este dashboard muestra información sobre la instalación de parches en instancias EC2 obtenida desde una tabla DynamoDB.
""")

# Parámetros de conexión
DYNAMO_TABLE = "<NOMBRE_DE_TU_TABLA>"  # <-- Cambia esto por el nombre real de tu tabla
REGION_NAME = "us-east-1"  # <-- Cambia esto si tu tabla está en otra región

@st.cache_data
def load_dynamo_data():
    dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
    table = dynamodb.Table(DYNAMO_TABLE)
    response = table.scan()
    data = response.get('Items', [])
    # Manejar paginación si hay más de 1MB de datos
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response.get('Items', []))
    df = pd.DataFrame(data)
    # Convertir fechas
    if 'CreationDate' in df.columns:
        df['CreationDate'] = pd.to_datetime(df['CreationDate'], errors='coerce')
    if 'LastUpdatePatching' in df.columns:
        df['LastUpdatePatching'] = pd.to_datetime(df['LastUpdatePatching'], errors='coerce')
    return df

# Cargar datos
try:
    df = load_dynamo_data()
    st.success(f"Datos cargados correctamente. Total registros: {len(df)}")
except Exception as e:
    st.error(f"Error al cargar datos de DynamoDB: {e}")
    st.stop()

# Filtros en la barra lateral
st.sidebar.header("Filtros")
account_ids = ['Todos'] + sorted(df['AccountId'].dropna().unique().tolist())
selected_account = st.sidebar.selectbox('Cuenta AWS', account_ids)
plataformas = ['Todas'] + sorted(df['PlataformaName'].dropna().unique().tolist())
selected_plataforma = st.sidebar.selectbox('Plataforma', plataformas)
versions = ['Todas'] + sorted(df['PlataformVersion'].dropna().unique().tolist())
selected_version = st.sidebar.selectbox('Versión de Plataforma', versions)

# Filtro por fecha de creación
if 'CreationDate' in df.columns:
    min_date = df['CreationDate'].min()
    max_date = df['CreationDate'].max()
    start_date = st.sidebar.date_input('Fecha inicial (CreationDate)', min_date)
    end_date = st.sidebar.date_input('Fecha final (CreationDate)', max_date)
else:
    start_date = end_date = None

# Aplicar filtros
filtered_df = df.copy()
if selected_account != 'Todos':
    filtered_df = filtered_df[filtered_df['AccountId'] == selected_account]
if selected_plataforma != 'Todas':
    filtered_df = filtered_df[filtered_df['PlataformaName'] == selected_plataforma]
if selected_version != 'Todas':
    filtered_df = filtered_df[filtered_df['PlataformVersion'] == selected_version]
if start_date and end_date:
    filtered_df = filtered_df[(filtered_df['CreationDate'] >= pd.to_datetime(start_date)) & (filtered_df['CreationDate'] <= pd.to_datetime(end_date))]

# Métricas principales
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Instancias", filtered_df['instanceId'].nunique())
with col2:
    st.metric("Cuentas Únicas", filtered_df['AccountId'].nunique())
with col3:
    st.metric("Plataformas Únicas", filtered_df['PlataformaName'].nunique())

# Gráficos
st.subheader("Instancias por Cuenta AWS")
if not filtered_df.empty:
    cuenta_counts = filtered_df['AccountId'].value_counts()
    fig_cuenta = px.bar(
        x=cuenta_counts.index,
        y=cuenta_counts.values,
        labels={'x': 'AccountId', 'y': 'Cantidad de Instancias'},
        title="Cantidad de Instancias por Cuenta AWS"
    )
    st.plotly_chart(fig_cuenta, use_container_width=True)

    st.subheader("Instancias por Plataforma")
    plataforma_counts = filtered_df['PlataformaName'].value_counts()
    fig_plataforma = px.pie(
        values=plataforma_counts.values,
        names=plataforma_counts.index,
        title="Distribución por Plataforma"
    )
    st.plotly_chart(fig_plataforma, use_container_width=True)

    st.subheader("Evolución de Creación de Instancias")
    if 'CreationDate' in filtered_df.columns:
        daily = filtered_df.groupby(filtered_df['CreationDate'].dt.date).size()
        fig_tiempo = px.line(
            x=daily.index,
            y=daily.values,
            labels={'x': 'Fecha', 'y': 'Nuevas Instancias'},
            title="Instancias creadas por día"
        )
        st.plotly_chart(fig_tiempo, use_container_width=True)
else:
    st.info("No hay datos para mostrar con los filtros seleccionados.")

# Tabla de datos detallada
st.subheader("Detalles de Instancias")
st.dataframe(
    filtered_df[[
        'instanceId', 'AccountId', 'InstanceName', 'PlataformaName',
        'PlataformVersion', 'CreationDate', 'LastUpdatePatching'
    ]],
    use_container_width=True
)

# Exportar datos
if st.button("Exportar Datos Filtrados"):
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name="dynamo_patches_data.csv",
        mime="text/csv"
    )

st.markdown("---")
st.markdown("Dashboard creado con Streamlit y DynamoDB | Última actualización: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")) 
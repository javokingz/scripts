import streamlit as st
import boto3
import pandas as pd
import plotly.express as px
from botocore.exceptions import ProfileNotFound, ClientError
import folium
from streamlit_folium import folium_static
import json

# Configurar la página
st.set_page_config(
    page_title="RDS Global Distribution",
    page_icon="🌍",
    layout="wide"
)

# Título y descripción
st.title("🌍 Distribución Global de Instancias RDS")
st.markdown("""
Este dashboard muestra la distribución global de las instancias RDS a través de todos los perfiles de AWS.
""")

# Diccionario de coordenadas para las regiones de AWS
region_coordinates = {
    'us-east-1': {'lat': 39.833333, 'lon': -98.583333},  # N. Virginia
    'us-east-2': {'lat': 40.367474, 'lon': -82.996216},  # Ohio
    'us-west-1': {'lat': 37.7749, 'lon': -122.4194},     # N. California
    'us-west-2': {'lat': 45.5231, 'lon': -122.6765},     # Oregon
    'eu-west-1': {'lat': 53.3498, 'lon': -6.2603},       # Ireland
    'eu-west-2': {'lat': 51.5074, 'lon': -0.1278},       # London
    'eu-west-3': {'lat': 48.8566, 'lon': 2.3522},        # Paris
    'eu-central-1': {'lat': 50.1109, 'lon': 8.6821},     # Frankfurt
    'ap-southeast-1': {'lat': 1.3521, 'lon': 103.8198},  # Singapore
    'ap-southeast-2': {'lat': -33.8688, 'lon': 151.2093},# Sydney
    'ap-northeast-1': {'lat': 35.6762, 'lon': 139.6503}, # Tokyo
    'ap-northeast-2': {'lat': 37.5665, 'lon': 126.9780}, # Seoul
    'ap-south-1': {'lat': 19.0760, 'lon': 72.8777},      # Mumbai
    'sa-east-1': {'lat': -23.5505, 'lon': -46.6333},     # São Paulo
    'ca-central-1': {'lat': 45.5017, 'lon': -73.5673},   # Canada
    'eu-north-1': {'lat': 59.3293, 'lon': 18.0686},      # Stockholm
    'me-south-1': {'lat': 25.2048, 'lon': 55.2708},      # Bahrain
    'af-south-1': {'lat': -33.9249, 'lon': 18.4241},     # Cape Town
    'ap-east-1': {'lat': 22.3193, 'lon': 114.1694},      # Hong Kong
    'eu-south-1': {'lat': 45.4642, 'lon': 9.1900},       # Milan
}

@st.cache_data
def get_rds_instances():
    """Obtener todas las instancias RDS de todos los perfiles"""
    all_instances = []
    profiles = boto3.Session().available_profiles
    
    for profile in profiles:
        try:
            session = boto3.Session(profile_name=profile)
            ec2_client = session.client('ec2')
            regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
            
            for region in regions:
                try:
                    rds_client = session.client('rds', region_name=region)
                    instances = rds_client.describe_db_instances()
                    
                    for instance in instances['DBInstances']:
                        all_instances.append({
                            'Profile': profile,
                            'Region': region,
                            'DBIdentifier': instance['DBInstanceIdentifier'],
                            'Engine': instance['Engine'],
                            'Status': instance['DBInstanceStatus'],
                            'Endpoint': instance['Endpoint']['Address'],
                            'Port': instance['Endpoint']['Port'],
                            'Latitude': region_coordinates.get(region, {}).get('lat', 0),
                            'Longitude': region_coordinates.get(region, {}).get('lon', 0)
                        })
                except ClientError as e:
                    st.warning(f"No se pudo acceder a la región {region} en el perfil {profile}: {str(e)}")
                    continue
                    
        except ProfileNotFound:
            st.warning(f"Perfil {profile} no encontrado")
            continue
        except Exception as e:
            st.error(f"Error al procesar el perfil {profile}: {str(e)}")
            continue
    
    return pd.DataFrame(all_instances)

# Cargar datos
df = get_rds_instances()

if not df.empty:
    # Mostrar tabla de datos
    st.subheader("Tabla de Instancias RDS")
    st.dataframe(df[['Profile', 'Region', 'DBIdentifier', 'Engine', 'Status', 'Endpoint', 'Port']], 
                use_container_width=True)
    
    # Crear mapa
    st.subheader("Distribución Global de Instancias RDS")
    
    # Agrupar por región para el tamaño de los marcadores
    region_counts = df.groupby(['Region', 'Latitude', 'Longitude']).size().reset_index(name='Count')
    
    # Crear mapa base
    m = folium.Map(location=[20, 0], zoom_start=2)
    
    # Agregar marcadores para cada región
    for idx, row in region_counts.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=row['Count'] * 2,  # Tamaño proporcional al número de instancias
            popup=f"Región: {row['Region']}<br>Instancias: {row['Count']}",
            color='blue',
            fill=True,
            fill_color='blue'
        ).add_to(m)
    
    # Mostrar mapa
    folium_static(m)
    
    # Gráfico de barras por región
    st.subheader("Número de Instancias por Región")
    fig = px.bar(
        region_counts,
        x='Region',
        y='Count',
        title="Distribución de Instancias RDS por Región",
        labels={'Region': 'Región', 'Count': 'Número de Instancias'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Exportar datos
    if st.button("Exportar Datos a CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name="rds_instances.csv",
            mime="text/csv"
        )
else:
    st.error("No se encontraron instancias RDS en ningún perfil.") 
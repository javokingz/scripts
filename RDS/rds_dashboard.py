import streamlit as st
import boto3
import pandas as pd
import plotly.express as px
from botocore.exceptions import ProfileNotFound, ClientError

# Configuración de la página
st.set_page_config(page_title="AWS RDS Dashboard", layout="wide")
st.title("AWS RDS Instances Dashboard")

# Lista de perfiles AWS
AWS_PROFILES = ["Profile1", "Profile2", "Profile3"]

def get_rds_instances(profile_name, region):
    """Obtiene la lista de instancias RDS para el perfil y región seleccionados"""
    try:
        session = boto3.Session(profile_name=profile_name, region_name=region)
        rds_client = session.client('rds')
        instances = rds_client.describe_db_instances()
        
        instance_list = []
        for instance in instances['DBInstances']:
            instance_list.append({
                'Profile': profile_name,
                'Region': region,
                'DBInstanceIdentifier': instance['DBInstanceIdentifier'],
                'Engine': instance['Engine'],
                'DBInstanceClass': instance['DBInstanceClass'],
                'Status': instance['DBInstanceStatus'],
                'Endpoint': instance.get('Endpoint', {}).get('Address', 'N/A'),
                'Port': instance.get('Endpoint', {}).get('Port', 'N/A'),
                'MultiAZ': instance.get('MultiAZ', False),
                'StorageType': instance.get('StorageType', 'N/A'),
                'AllocatedStorage': instance.get('AllocatedStorage', 'N/A'),
                'Latitude': get_region_coordinates(region)[0],
                'Longitude': get_region_coordinates(region)[1]
            })
        return instance_list
    except (ProfileNotFound, ClientError) as e:
        st.error(f"Error con el perfil {profile_name} en la región {region}: {str(e)}")
        return []

def get_region_coordinates(region):
    """Obtiene las coordenadas aproximadas para cada región AWS"""
    region_coordinates = {
        'us-east-1': (39.8283, -98.5795),  # Virginia
        'us-east-2': (40.4173, -82.9071),  # Ohio
        'us-west-1': (37.7749, -122.4194), # California
        'us-west-2': (45.5231, -122.6765), # Oregon
        'eu-west-1': (53.3498, -6.2603),   # Irlanda
        'eu-west-2': (51.5074, -0.1278),   # Londres
        'eu-central-1': (50.1109, 8.6821), # Frankfurt
        'ap-southeast-1': (1.3521, 103.8198), # Singapur
        'ap-southeast-2': (-33.8688, 151.2093), # Sydney
        'ap-northeast-1': (35.6762, 139.6503), # Tokyo
        'sa-east-1': (-23.5505, -46.6333), # São Paulo
    }
    return region_coordinates.get(region, (0, 0))

def main():
    # Obtener todas las instancias RDS
    all_instances = []
    for profile in AWS_PROFILES:
        # Obtener la región por defecto para el perfil
        session = boto3.Session(profile_name=profile)
        region = session.region_name
        instances = get_rds_instances(profile, region)
        all_instances.extend(instances)

    if not all_instances:
        st.warning("No se encontraron instancias RDS en los perfiles especificados.")
        return

    # Convertir a DataFrame
    df = pd.DataFrame(all_instances)

    # Mostrar tabla de instancias
    st.subheader("Instancias RDS")
    st.dataframe(df)

    # Crear mapa
    st.subheader("Ubicación de las Instancias RDS")
    fig = px.scatter_geo(
        df,
        lat='Latitude',
        lon='Longitude',
        color='Profile',
        hover_name='DBInstanceIdentifier',
        hover_data=['Engine', 'Status', 'Region'],
        title='Distribución de Instancias RDS por Región',
        projection='natural earth'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Mostrar estadísticas
    st.subheader("Estadísticas")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Instancias", len(df))
    
    with col2:
        st.metric("Motores Diferentes", df['Engine'].nunique())
    
    with col3:
        st.metric("Regiones Activas", df['Region'].nunique())

if __name__ == "__main__":
    main() 
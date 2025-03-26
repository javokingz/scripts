import streamlit as st
import boto3
from datetime import datetime, timedelta
import pandas as pd

def get_rds_instances(profile_name):
    """
    Obtiene la lista de instancias RDS para un perfil de AWS específico.
    """
    session = boto3.Session(profile_name=profile_name)
    rds_client = session.client('rds')
    
    try:
        response = rds_client.describe_db_instances()
        instances = [instance['DBInstanceIdentifier'] for instance in response['DBInstances']]
        return instances
    except Exception as e:
        st.error(f"Error al obtener instancias RDS: {e}")
        return []

def get_rds_metrics(profile_name, instance_identifier):
    """
    Recupera métricas de CloudWatch para una instancia RDS específica.
    """
    session = boto3.Session(profile_name=profile_name)
    cloudwatch = session.client('cloudwatch')
    
    # Métricas de ejemplo para RDS
    metrics_to_fetch = [
        'CPUUtilization',
        'DatabaseConnections',
        'FreeableMemory',
        'DMLLatency',
        'ReadIOPS',
        'WriteIOPS'
    ]
    
    metrics_data = {}
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=12)
    
    for metric_name in metrics_to_fetch:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': instance_identifier
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # Intervalos de 5 minutos
                Statistics=['Average', 'Maximum']
            )
            
            if response['Datapoints']:
                metrics_data[metric_name] = pd.DataFrame(response['Datapoints'])
        except Exception as e:
            st.warning(f"No se pudieron recuperar métricas para {metric_name}: {e}")
    
    return metrics_data

def get_rds_events(profile_name, instance_identifier):
    """
    Recupera eventos recientes para una instancia RDS.
    """
    session = boto3.Session(profile_name=profile_name)
    rds_client = session.client('rds')
    
    try:
        response = rds_client.describe_events(
            SourceType='DB_INSTANCE',
            SourceIdentifier=instance_identifier,
            Duration=720  # Eventos de las últimas 12 horas
        )
        
        events = response.get('Events', [])
        return pd.DataFrame(events)
    except Exception as e:
        st.error(f"Error al obtener eventos de RDS: {e}")
        return pd.DataFrame()

def main():
    st.title('Dashboard de Métricas de AWS RDS')
    
    # Selector de perfil de AWS
    aws_profiles = ['default', 'dev', 'prod']  # Personalizar según tus perfiles
    selected_profile = st.selectbox('Seleccionar Perfil de AWS', aws_profiles)
    
    # Obtener instancias RDS
    rds_instances = get_rds_instances(selected_profile)
    
    if not rds_instances:
        st.warning('No se encontraron instancias RDS')
        return
    
    # Selector de instancia RDS
    selected_instance = st.selectbox('Seleccionar Instancia RDS', rds_instances)
    
    # Botón para cargar métricas
    if st.button('Cargar Métricas y Eventos'):
        st.subheader(f'Métricas para {selected_instance}')
        
        # Obtener métricas
        metrics_data = get_rds_metrics(selected_profile, selected_instance)
        
        for metric_name, metric_df in metrics_data.items():
            st.write(f"Métrica: {metric_name}")
            st.dataframe(metric_df)
            
            # Opcional: Gráfico simple de la métrica
            st.line_chart(metric_df['Average'])
        
        # Mostrar eventos
        st.subheader('Eventos de RDS')
        events_df = get_rds_events(selected_profile, selected_instance)
        
        if not events_df.empty:
            st.dataframe(events_df)
        else:
            st.info('No se encontraron eventos recientes')

if __name__ == '__main__':
    main()
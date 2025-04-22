import streamlit as st
import boto3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import os
from rds_database import RDSDatabase

# Predefined AWS Profiles
AWS_PROFILES = [
    'XXXXXX',
    'xxxxxxxxx',
    '+++++++++++++'
]

class RDSDatabase:
    def __init__(self, db_path='rds_history.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database and create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create instances table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rds_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT,
                engine TEXT,
                instance_class TEXT,
                status TEXT,
                allocated_storage INTEGER,
                endpoint TEXT,
                multi_az INTEGER,
                publicly_accessible INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rds_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT,
                metric_name TEXT,
                value REAL,
                timestamp DATETIME,
                FOREIGN KEY (instance_id) REFERENCES rds_instances(instance_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_instances(self, instances_df):
        """Store RDS instances information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for _, row in instances_df.iterrows():
            cursor.execute('''
                INSERT INTO rds_instances (
                    instance_id, engine, instance_class, status,
                    allocated_storage, endpoint, multi_az, publicly_accessible
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['DBInstanceIdentifier'],
                row['Engine'],
                row['DBInstanceClass'],
                row['Status'],
                row['AllocatedStorage'],
                row['Endpoint'],
                int(row['MultiAZ']),
                int(row['PubliclyAccessible'])
            ))
        
        conn.commit()
        conn.close()
    
    def store_metrics(self, instance_id, metric_name, metrics_df):
        """Store metrics data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for _, row in metrics_df.iterrows():
            cursor.execute('''
                INSERT INTO rds_metrics (
                    instance_id, metric_name, value, timestamp
                ) VALUES (?, ?, ?, ?)
            ''', (
                instance_id,
                metric_name,
                row['Value'],
                row['Timestamp']
            ))
        
        conn.commit()
        conn.close()
    
    def get_historical_instances(self, days=7):
        """Get historical instances data"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM rds_instances 
            WHERE timestamp >= datetime('now', ?)
            ORDER BY timestamp DESC
        '''
        df = pd.read_sql_query(query, conn, params=[f'-{days} days'])
        conn.close()
        return df
    
    def get_historical_metrics(self, instance_id, metric_name, days=7):
        """Get historical metrics data"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM rds_metrics 
            WHERE instance_id = ? AND metric_name = ? 
            AND timestamp >= datetime('now', ?)
            ORDER BY timestamp DESC
        '''
        df = pd.read_sql_query(query, conn, params=[instance_id, metric_name, f'-{days} days'])
        conn.close()
        return df

class AWSRDS_Dashboard:
    def __init__(self):
        self.profiles = sorted(set(AWS_PROFILES))
        self.db = RDSDatabase()
        
    def get_session_for_profile(self, profile_name):
        """
        Crea una sesión de boto3 usando un perfil específico
        """
        try:
            session = boto3.Session(profile_name=profile_name)
            return session
        except Exception as e:
            st.error(f"Error creando sesión para {profile_name}: {e}")
            return None
    
    def get_rds_instances(self, session):
        """
        Obtiene las instancias RDS
        """
        try:
            rds = session.client('rds')
            response = rds.describe_db_instances()
            
            instances = []
            for instance in response['DBInstances']:
                instances.append({
                    'DBInstanceIdentifier': instance.get('DBInstanceIdentifier', 'N/A'),
                    'Engine': instance.get('Engine', 'N/A'),
                    'DBInstanceClass': instance.get('DBInstanceClass', 'N/A'),
                    'Status': instance.get('DBInstanceStatus', 'N/A'),
                    'AllocatedStorage': instance.get('AllocatedStorage', 0),
                    'Endpoint': instance.get('Endpoint', {}).get('Address', 'N/A'),
                    'MultiAZ': instance.get('MultiAZ', False),
                    'PubliclyAccessible': instance.get('PubliclyAccessible', False)
                })
            
            return pd.DataFrame(instances)
        except Exception as e:
            st.error(f"Error obteniendo instancias RDS: {e}")
            return pd.DataFrame()
    
    def get_cloudwatch_metrics(self, session, instance_id, metric_name, period=300, hours=24):
        """
        Obtiene métricas de CloudWatch para una instancia RDS específica
        """
        try:
            cloudwatch = session.client('cloudwatch')
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            response = cloudwatch.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'rds_metric',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/RDS',
                                'MetricName': metric_name,
                                'Dimensions': [
                                    {
                                        'Name': 'DBInstanceIdentifier',
                                        'Value': instance_id
                                    }
                                ]
                            },
                            'Period': period,
                            'Stat': 'Average'
                        }
                    }
                ],
                StartTime=start_time,
                EndTime=end_time
            )
            
            timestamps = response['MetricDataResults'][0]['Timestamps']
            values = response['MetricDataResults'][0]['Values']
            
            return pd.DataFrame({
                'Timestamp': timestamps,
                'Value': values
            }).sort_values('Timestamp')
        except Exception as e:
            st.error(f"Error obteniendo métricas para {instance_id} - {metric_name}: {e}")
            return pd.DataFrame()
    
    def get_rds_events(self, session, instance_id=None):
        """
        Obtiene eventos de RDS para una instancia específica o todas las instancias
        """
        try:
            rds = session.client('rds')
            
            kwargs = {
                'Duration': 24 * 7  # Últimos 7 días
            }
            
            if instance_id:
                kwargs['DBInstanceIdentifier'] = instance_id
            
            response = rds.describe_events(**kwargs)
            
            events = []
            for event in response['Events']:
                events.append({
                    'SourceIdentifier': event.get('SourceIdentifier', 'N/A'),
                    'Message': event.get('Message', 'N/A'),
                    'Date': event.get('Date', datetime.now()),
                    'SourceType': event.get('SourceType', 'N/A'),
                    'EventCategories': ', '.join(event.get('EventCategories', []))
                })
            
            return pd.DataFrame(events)
        except Exception as e:
            st.error(f"Error obteniendo eventos RDS: {e}")
            return pd.DataFrame()
    
    def get_cloudwatch_logs(self, session, instance_id, hours=24):
        """
        Obtiene los logs de CloudWatch para una instancia RDS específica
        """
        try:
            # Obtener el cliente de CloudWatch Logs
            logs = session.client('logs')
            
            # Calcular el tiempo de inicio y fin
            end_time = int(datetime.utcnow().timestamp() * 1000)
            start_time = int((datetime.utcnow() - timedelta(hours=hours)).timestamp() * 1000)
            
            # Obtener los grupos de logs relacionados con RDS
            log_groups = logs.describe_log_groups(
                logGroupNamePrefix=f'/aws/rds/instance/{instance_id}'
            )
            
            all_logs = []
            for group in log_groups.get('logGroups', []):
                group_name = group['logGroupName']
                
                # Obtener los streams de logs
                streams = logs.describe_log_streams(
                    logGroupName=group_name,
                    orderBy='LastEventTime',
                    descending=True
                )
                
                # Obtener los eventos de logs de cada stream
                for stream in streams.get('logStreams', [])[:5]:  # Limitamos a los 5 streams más recientes
                    try:
                        log_events = logs.get_log_events(
                            logGroupName=group_name,
                            logStreamName=stream['logStreamName'],
                            startTime=start_time,
                            endTime=end_time
                        )
                        
                        for event in log_events['events']:
                            all_logs.append({
                                'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000),
                                'message': event['message'],
                                'stream': stream['logStreamName']
                            })
                    except Exception as e:
                        st.warning(f"Error obteniendo logs del stream {stream['logStreamName']}: {e}")
                        continue
            
            return pd.DataFrame(all_logs)
        except Exception as e:
            st.error(f"Error obteniendo logs de CloudWatch para {instance_id}: {e}")
            return pd.DataFrame()

def main():
    st.set_page_config(page_title="AWS Monitoring Dashboard", layout="wide")
    
    # Sidebar menu for dashboard selection
    st.sidebar.title("Menú Principal")
    dashboard_type = st.sidebar.radio(
        "Seleccionar Dashboard",
        ["Patch Management", "RDS Monitoring"]
    )
    
    if dashboard_type == "Patch Management":
        # Aquí iría el código del dashboard de Patch Management
        st.title("Patch Management Dashboard")
        st.write("Contenido del dashboard de Patch Management")
        
    else:  # RDS Monitoring
        dashboard = AWSRDS_Dashboard()
        
        st.sidebar.title("Configuración RDS")
        selected_profile = st.sidebar.selectbox("Seleccionar Perfil AWS", dashboard.profiles)
        
        st.sidebar.markdown("---")
        hours = st.sidebar.slider("Periodo de Tiempo (horas)", 1, 72, 24)
        
        # Add historical data query section
        st.sidebar.markdown("---")
        st.sidebar.subheader("Consulta Histórica")
        historical_query = st.sidebar.checkbox("Mostrar Datos Históricos")
        
        if historical_query:
            # Date range selector
            col1, col2 = st.sidebar.columns(2)
            with col1:
                start_date = st.date_input("Fecha Inicio")
            with col2:
                end_date = st.date_input("Fecha Fin")
            
            # Convert dates to datetime
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Get available instances
            available_instances = dashboard.db.get_available_instances()
            if available_instances:
                selected_instance = st.sidebar.selectbox(
                    "Seleccionar Instancia",
                    available_instances
                )
                
                # Get available metrics for selected instance
                available_metrics = dashboard.db.get_available_metrics(selected_instance)
                if available_metrics:
                    selected_metric = st.sidebar.selectbox(
                        "Seleccionar Métrica",
                        available_metrics
                    )
                    
                    # Query and display historical data
                    historical_metrics = dashboard.db.get_historical_metrics(
                        selected_instance,
                        selected_metric,
                        start_datetime,
                        end_datetime
                    )
                    
                    if not historical_metrics.empty:
                        st.subheader(f"Historial de {selected_metric} para {selected_instance}")
                        fig = px.line(
                            historical_metrics,
                            x='timestamp',
                            y='value',
                            title=f'Historial de {selected_metric}'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show raw data
                        st.subheader("Datos Históricos")
                        st.dataframe(historical_metrics)
                    else:
                        st.info("No hay datos históricos disponibles para el período seleccionado")
                else:
                    st.info("No hay métricas disponibles para la instancia seleccionada")
            else:
                st.info("No hay instancias disponibles en el histórico")
        
        st.title(f"AWS RDS Monitoring Dashboard")
        st.markdown(f"Perfil: **{selected_profile}** | Periodo: **{hours} horas**")
        
        if st.sidebar.button("Cargar Datos"):
            session = dashboard.get_session_for_profile(selected_profile)
            
            if session:
                # Obtener instancias RDS
                instances_df = dashboard.get_rds_instances(session)
                
                if not instances_df.empty:
                    # Store instances in database
                    dashboard.db.store_instances(instances_df)
                    
                    # Mostrar resumen de instancias en tarjetas
                    st.subheader("Resumen de Instancias RDS")
                    
                    total_instances = len(instances_df)
                    instances_online = instances_df[instances_df['Status'] == 'available'].shape[0]
                    total_storage = instances_df['AllocatedStorage'].sum()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Instancias Totales", total_instances)
                    with col2:
                        st.metric("Instancias Online", instances_online)
                    with col3:
                        st.metric("Almacenamiento Total (GB)", total_storage)
                    
                    # Mostrar tabla de instancias
                    st.subheader("Instancias RDS")
                    st.dataframe(instances_df)
                    
                    # Seleccionar una instancia para métricas detalladas
                    selected_instance = st.selectbox(
                        "Seleccionar Instancia para Métricas", 
                        instances_df['DBInstanceIdentifier'].tolist()
                    )
                    
                    # Mostrar métricas en gráficos
                    st.subheader(f"Métricas de la Instancia: {selected_instance}")
                    
                    # Crear pestañas para diferentes métricas
                    tabs = st.tabs([
                        "CPU", "Memoria", "Conexiones", "Almacenamiento", "Eventos", "Logs"
                    ])
                    
                    # Pestaña de CPU
                    with tabs[0]:
                        cpu_metric = dashboard.get_cloudwatch_metrics(
                            session, selected_instance, 'CPUUtilization', hours=hours
                        )
                        
                        if not cpu_metric.empty:
                            # Store metrics in database
                            dashboard.db.store_metrics(selected_instance, 'CPUUtilization', cpu_metric)
                            
                            fig = px.line(
                                cpu_metric, 
                                x='Timestamp', 
                                y='Value', 
                                title='Utilización de CPU (%)'
                            )
                            fig.update_traces(line_color='#1f77b4')
                            fig.update_layout(
                                xaxis_title="Hora",
                                yaxis_title="CPU (%)",
                                height=400
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No hay datos de CPU disponibles para esta instancia.")
                    
                    # Pestaña de Memoria
                    with tabs[1]:
                        memory_metric = dashboard.get_cloudwatch_metrics(
                            session, selected_instance, 'FreeableMemory', hours=hours
                        )
                        
                        if not memory_metric.empty:
                            # Convertir a GB
                            memory_metric['Value'] = memory_metric['Value'] / (1024 * 1024 * 1024)
                            
                            fig = px.line(
                                memory_metric, 
                                x='Timestamp', 
                                y='Value', 
                                title='Memoria Disponible (GB)'
                            )
                            fig.update_traces(line_color='#ff7f0e')
                            fig.update_layout(
                                xaxis_title="Hora",
                                yaxis_title="Memoria (GB)",
                                height=400
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No hay datos de memoria disponibles para esta instancia.")
                    
                    # Pestaña de Conexiones
                    with tabs[2]:
                        conn_metric = dashboard.get_cloudwatch_metrics(
                            session, selected_instance, 'DatabaseConnections', hours=hours
                        )
                        
                        if not conn_metric.empty:
                            fig = px.line(
                                conn_metric, 
                                x='Timestamp', 
                                y='Value', 
                                title='Conexiones a la Base de Datos'
                            )
                            fig.update_traces(line_color='#2ca02c')
                            fig.update_layout(
                                xaxis_title="Hora",
                                yaxis_title="Conexiones",
                                height=400
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No hay datos de conexiones disponibles para esta instancia.")
                    
                    # Pestaña de Almacenamiento
                    with tabs[3]:
                        storage_metric = dashboard.get_cloudwatch_metrics(
                            session, selected_instance, 'FreeStorageSpace', hours=hours
                        )
                        
                        if not storage_metric.empty:
                            # Convertir a GB
                            storage_metric['Value'] = storage_metric['Value'] / (1024 * 1024 * 1024)
                            
                            fig = px.line(
                                storage_metric, 
                                x='Timestamp', 
                                y='Value', 
                                title='Espacio de Almacenamiento Libre (GB)'
                            )
                            fig.update_traces(line_color='#d62728')
                            fig.update_layout(
                                xaxis_title="Hora",
                                yaxis_title="Espacio Libre (GB)",
                                height=400
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No hay datos de almacenamiento disponibles para esta instancia.")
                    
                    # Pestaña de Eventos
                    with tabs[4]:
                        events = dashboard.get_rds_events(session, selected_instance)
                        
                        if not events.empty:
                            st.dataframe(events.sort_values(by='Date', ascending=False))
                        else:
                            st.info("No hay eventos recientes para esta instancia.")
                    
                    # Nueva pestaña de Logs (después de la pestaña de Eventos)
                    with tabs[5]:
                        st.subheader("Logs de CloudWatch")
                        logs_df = dashboard.get_cloudwatch_logs(session, selected_instance, hours=hours)
                        
                        if not logs_df.empty:
                            # Agregar filtros para los logs
                            col1, col2 = st.columns(2)
                            with col1:
                                selected_streams = st.multiselect(
                                    "Filtrar por Stream",
                                    options=sorted(logs_df['stream'].unique()),
                                    default=sorted(logs_df['stream'].unique())
                                )
                            
                            with col2:
                                search_term = st.text_input("Buscar en logs", "")
                            
                            # Aplicar filtros
                            filtered_logs = logs_df[logs_df['stream'].isin(selected_streams)]
                            if search_term:
                                filtered_logs = filtered_logs[
                                    filtered_logs['message'].str.contains(search_term, case=False, na=False)
                                ]
                            
                            # Mostrar los logs filtrados
                            st.dataframe(
                                filtered_logs.sort_values('timestamp', ascending=False),
                                use_container_width=True
                            )
                            
                            # Mostrar estadísticas básicas
                            st.metric("Total de logs encontrados", len(filtered_logs))
                        else:
                            st.info("No se encontraron logs para esta instancia. Asegúrate de que los logs de CloudWatch estén habilitados para esta instancia RDS.")
                else:
                    st.warning("No se encontraron instancias RDS para este perfil.")

if __name__ == "__main__":
    main()
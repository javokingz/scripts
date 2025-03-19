import streamlit as st
import boto3
import pandas as pd
from datetime import datetime, timedelta

# Configurar título
st.title("📊 Dashboard de Conexiones en RDS")

# Perfiles de AWS que se usarán para generar el reporte
AWS_PROFILES = ["default", "profile1", "profile2"]  # <-- Cambia esto por tus perfiles

# Cuadro de texto para ingresar la instancia
instance_id = st.text_input("🔍 Ingrese el ID de la instancia RDS:")

# Botón para consultar conexiones
if st.button("Consultar Conexiones"):
    if instance_id:
        # Función para obtener conexiones activas desde CloudWatch
        def get_rds_connections(instance_id):
            client = boto3.client("cloudwatch")
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)  # Última hora

            response = client.get_metric_statistics(
                Namespace="AWS/RDS",
                MetricName="DatabaseConnections",
                Dimensions=[{"Name": "DBInstanceIdentifier", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # Cada 5 minutos
                Statistics=["Average"],
                Unit="Count",
            )

            if response.get("Datapoints"):
                data = sorted(response["Datapoints"], key=lambda x: x["Timestamp"])
                timestamps = [dp["Timestamp"] for dp in data]
                values = [dp["Average"] for dp in data]
                return timestamps, values
            return [], []

        # Obtener conexiones
        timestamps, values = get_rds_connections(instance_id)

        if timestamps:
            df_connections = pd.DataFrame({"Tiempo": timestamps, "Conexiones": values})
            df_connections["Tiempo"] = df_connections["Tiempo"].dt.tz_localize(None)

            # Mostrar última métrica
            st.metric(label="🔹 Conexiones Activas (Último valor)", value=int(values[-1]))

            # Mostrar tabla de conexiones
            st.write("📊 Datos históricos de conexiones:")
            st.dataframe(df_connections)

            # Mostrar gráfica
            st.line_chart(df_connections.set_index("Tiempo"))
        else:
            st.warning("⚠ No se encontraron datos en CloudWatch para esta instancia.")
    else:
        st.error("⚠ Debe ingresar un ID de instancia RDS.")

# Botón para generar reporte de instancias en múltiples perfiles
if st.button("Generar Reporte RDS"):
    def get_rds_instances_from_profile(profile):
        try:
            session = boto3.Session(profile_name=profile)
            client = session.client("rds")
            response = client.describe_db_instances()
            instances = [
                {
                    "Perfil": profile,
                    "ID": db.get("DBInstanceIdentifier", "N/A"),
                    "Engine": db.get("Engine", "Desconocido"),
                    "Estado": db.get("DBInstanceStatus", "Desconocido"),
                    "Endpoint": db.get("Endpoint", {}).get("Address", "N/A"),
                    "Puerto": db.get("Endpoint", {}).get("Port", "N/A"),
                }
                for db in response.get("DBInstances", [])
            ]
            return instances
        except Exception as e:
            st.error(f"⚠ Error en perfil {profile}: {e}")
            return []

    # Obtener instancias de todos los perfiles
    all_instances = []
    for profile in AWS_PROFILES:
        all_instances.extend(get_rds_instances_from_profile(profile))

    if all_instances:
        df_report = pd.DataFrame(all_instances)
        st.write("📋 Reporte de todas las instancias RDS en los perfiles configurados:")
        st.dataframe(df_report)
    else:
        st.warning("⚠ No se encontraron instancias RDS en los perfiles configurados.")

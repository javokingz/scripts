import streamlit as st
import boto3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Configuración de AWS
st.title("📊 Dashboard de Conexiones Activas en RDS")

# Input del usuario para el ID de la instancia RDS
instance_id = st.text_input("Ingrese el ID de la instancia RDS", "my-rds-instance")

# Función para obtener datos de conexiones desde CloudWatch
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
        Unit="Count"
    )

    # Procesar datos
    if response["Datapoints"]:
        data = sorted(response["Datapoints"], key=lambda x: x["Timestamp"])
        timestamps = [dp["Timestamp"] for dp in data]
        values = [dp["Average"] for dp in data]
        return timestamps, values
    else:
        return [], []

# Obtener y mostrar datos
if instance_id:
    timestamps, values = get_rds_connections(instance_id)
    
    if timestamps:
        # Mostrar el valor más reciente
        st.metric(label="Conexiones Activas (Último valor)", value=int(values[-1]))

        # Crear DataFrame
        df = pd.DataFrame({"Tiempo": timestamps, "Conexiones": values})
        df["Tiempo"] = df["Tiempo"].dt.tz_localize(None)  # Quitar info de zona horaria

        # Mostrar DataFrame
        st.write("📌 Datos históricos de conexiones:")
        st.dataframe(df)

        # Crear gráfico de líneas
        fig, ax = plt.subplots()
        ax.plot(df["Tiempo"], df["Conexiones"], marker="o", linestyle="-", color="b")
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Conexiones Activas")
        ax.set_title("Tendencia de Conexiones en RDS")
        ax.grid(True)
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning("No se encontraron datos para esta instancia.")

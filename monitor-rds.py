import streamlit as st
import boto3
import pandas as pd
from datetime import datetime, timedelta

# Configuración de AWS
st.title("📊 Dashboard de Conexiones Activas en RDS")

# Función para obtener instancias RDS
@st.cache_data
def get_rds_instances():
    client = boto3.client("rds")
    response = client.describe_db_instances()
    instances = [
        {
            "Seleccionar": False,  # Checkbox
            "ID": db["DBInstanceIdentifier"],
            "Engine": db["Engine"],
            "Estado": db["DBInstanceStatus"],
            "Endpoint": db["Endpoint"]["Address"],
            "Puerto": db["Endpoint"]["Port"],
        }
        for db in response["DBInstances"]
    ]
    return pd.DataFrame(instances)

# Obtener lista de instancias
df_instances = get_rds_instances()

# Mostrar DataFrame con checkboxes
st.write("📌 Seleccione las instancias RDS:")
selected_rows = st.data_editor(df_instances, column_config={"Seleccionar": st.column_config.CheckboxColumn()}, hide_index=True)

# Filtrar las instancias seleccionadas
selected_instances = selected_rows[selected_rows["Seleccionar"]]["ID"].tolist()

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
        Unit="Count",
    )

    if response["Datapoints"]:
        data = sorted(response["Datapoints"], key=lambda x: x["Timestamp"])
        timestamps = [dp["Timestamp"] for dp in data]
        values = [dp["Average"] for dp in data]
        return timestamps, values
    return [], []

# Obtener y mostrar datos para las instancias seleccionadas
if selected_instances:
    all_data = []
    
    for instance_id in selected_instances:
        timestamps, values = get_rds_connections(instance_id)
        
        if timestamps:
            df_connections = pd.DataFrame({"Tiempo": timestamps, "Conexiones": values, "Instancia": instance_id})
            df_connections["Tiempo"] = df_connections["Tiempo"].dt.tz_localize(None)
            all_data.append(df_connections)

            # Mostrar la última métrica de conexiones activas
            st.metric(label=f"Conexiones Activas ({instance_id})", value=int(values[-1]))

    # Si hay datos, mostrar gráfica
    if all_data:
        df_final = pd.concat(all_data)
        st.write("📊 Datos históricos de conexiones:")
        st.dataframe(df_final)

        # Mostrar gráfica de líneas con múltiples instancias
        st.line_chart(df_final.pivot(index="Tiempo", columns="Instancia", values="Conexiones"))
    else:
        st.warning("No se encontraron datos para las instancias seleccionadas en CloudWatch.")
else:
    st.info("Seleccione al menos una instancia para visualizar sus conexiones.")

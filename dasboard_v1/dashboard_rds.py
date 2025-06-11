import streamlit as st
import boto3
from botocore.exceptions import ClientError
import pandas as pd

st.title('Dashboard de RDS Multi-Cuenta')

# Selección de cuenta (placeholder, se puede mejorar con perfiles o roles)
accounts = ['default']  # Aquí puedes agregar más perfiles o roles
selected_account = st.selectbox('Selecciona la cuenta AWS', accounts)

# Selección de región
regions = ['us-east-1', 'us-west-2', 'eu-west-1']
selected_region = st.selectbox('Selecciona la región', regions)

# Nombre de la tabla DynamoDB (puedes cambiarlo por el nombre real)
dynamo_table_name = st.text_input('Nombre de la tabla DynamoDB con histórico de RDS', 'rds_historico')

# Función para obtener datos históricos de DynamoDB
def get_rds_history(session, table_name):
    try:
        dynamodb = session.resource('dynamodb')
        table = dynamodb.Table(table_name)
        response = table.scan()
        items = response.get('Items', [])
        return items
    except Exception as e:
        st.error(f"Error al obtener datos de DynamoDB: {e}")
        return []

# Conexión a AWS usando boto3 y el perfil seleccionado
try:
    session = boto3.Session(profile_name=selected_account, region_name=selected_region)
    rds_client = session.client('rds')
    
    # Obtener información de instancias RDS
    response = rds_client.describe_db_instances()
    dbs = response['DBInstances']
    
    if dbs:
        st.write(f"Se encontraron {len(dbs)} instancias RDS:")
        for db in dbs:
            st.subheader(db['DBInstanceIdentifier'])
            st.write({
                'Engine': db['Engine'],
                'Status': db['DBInstanceStatus'],
                'Endpoint': db.get('Endpoint', {}).get('Address', 'N/A'),
                'Clase': db['DBInstanceClass'],
                'Zona': db['AvailabilityZone'],
            })
    else:
        st.info('No se encontraron instancias RDS en esta cuenta/región.')
except ClientError as e:
    st.error(f"Error al conectar con AWS: {e}")
except Exception as e:
    st.error(f"Error inesperado: {e}")

# Apartado para mostrar información histórica de RDS desde DynamoDB
st.header('Histórico de RDS (DynamoDB)')
history_data = get_rds_history(session, dynamo_table_name)
if history_data:
    df_history = pd.DataFrame(history_data)
    st.dataframe(df_history)
else:
    st.info('No se encontraron datos históricos en DynamoDB o la tabla está vacía.') 
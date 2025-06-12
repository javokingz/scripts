import streamlit as st
import boto3
from botocore.exceptions import ClientError
import pandas as pd
import os

st.title('Dashboard de RDS Multi-Cuenta')

# --- Configuración de cuentas y roles ---
# Lista de cuentas y roles de la landing zone (puedes cargar esto de un archivo, variable de entorno o DynamoDB)
LANDING_ZONE_ACCOUNTS = [
    {"account_id": "111111111111", "name": "Cuenta Producción", "role": "arn:aws:iam::111111111111:role/RoleParaDashboard"},
    {"account_id": "222222222222", "name": "Cuenta Desarrollo", "role": "arn:aws:iam::222222222222:role/RoleParaDashboard"},
    # Agrega más cuentas aquí
]

# --- Menú lateral ---
menu = st.sidebar.radio('Selecciona el dashboard', ['Histórico', 'Tiempo Real'])

# --- Selección de cuenta y región ---
account_names = [f"{acc['name']} ({acc['account_id']})" for acc in LANDING_ZONE_ACCOUNTS]
selected_account_idx = st.sidebar.selectbox('Cuenta AWS', range(len(account_names)), format_func=lambda i: account_names[i])
selected_account = LANDING_ZONE_ACCOUNTS[selected_account_idx]
regions = ['us-east-1', 'us-west-2', 'eu-west-1']
selected_region = st.sidebar.selectbox('Región', regions)

# --- Función para asumir rol en otra cuenta ---
def get_session_for_account(account):
    sts = boto3.client('sts')
    assumed = sts.assume_role(
        RoleArn=account['role'],
        RoleSessionName='DashboardSession'
    )
    creds = assumed['Credentials']
    session = boto3.Session(
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'],
        aws_session_token=creds['SessionToken'],
        region_name=selected_region
    )
    return session

# --- Dashboard Histórico ---
def dashboard_historico():
    # Nombre de la tabla DynamoDB (puedes cambiarlo por el nombre real)
    dynamo_table_name = st.text_input('Nombre de la tabla DynamoDB con histórico de RDS', 'rds_historico')
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
    try:
        session = get_session_for_account(selected_account)
        st.header('Histórico de RDS (DynamoDB)')
        history_data = get_rds_history(session, dynamo_table_name)
        if history_data:
            df_history = pd.DataFrame(history_data)
            st.dataframe(df_history)
        else:
            st.info('No se encontraron datos históricos en DynamoDB o la tabla está vacía.')
    except Exception as e:
        st.error(f"Error inesperado: {e}")

# --- Dashboard Tiempo Real ---
def dashboard_tiempo_real():
    try:
        session = get_session_for_account(selected_account)
        rds_client = session.client('rds')
        response = rds_client.describe_db_instances()
        dbs = response['DBInstances']
        st.header(f"Instancias RDS en tiempo real para {selected_account['name']}")
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

# --- Renderizado según menú ---
if menu == 'Histórico':
    dashboard_historico()
else:
    dashboard_tiempo_real() 
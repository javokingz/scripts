import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

def init_auth():
    # Configuración de usuarios (en un entorno real, esto debería estar en una base de datos)
    credentials = {
        'usernames': {
            'admin': {
                'name': 'Administrador',
                'password': stauth.Hasher(['admin123']).generate()[0]
            }
        }
    }

    # Guardar las credenciales en un archivo YAML
    with open('config.yaml', 'w') as file:
        yaml.dump(credentials, file, default_flow_style=False)

    # Cargar las credenciales
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    # Crear el autenticador
    authenticator = stauth.Authenticate(
        config['usernames'],
        'dashboard_cookie',
        'dashboard_key',
        cookie_expiry_days=30
    )

    return authenticator

def login():
    authenticator = init_auth()
    
    # Crear la interfaz de login
    name, authentication_status, username = authenticator.login('Iniciar Sesión', 'main')

    if authentication_status == False:
        st.error('Usuario/contraseña incorrectos')
        return False
    elif authentication_status == None:
        st.warning('Por favor ingresa tu usuario y contraseña')
        return False
    elif authentication_status:
        st.success(f'Bienvenido *{name}*')
        return True

def logout():
    authenticator = init_auth()
    authenticator.logout('Cerrar Sesión', 'main') 
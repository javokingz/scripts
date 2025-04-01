# Monitor de Instancias RDS de AWS

Esta aplicación web desarrollada con Streamlit permite monitorear las instancias RDS de AWS, mostrando información detallada y métricas en tiempo real.

## Características

- Selección de perfiles de AWS
- Lista de todas las instancias RDS con sus detalles básicos
- Visualización de métricas en tiempo real:
  - Utilización de CPU
  - Uso de memoria
  - Espacio de almacenamiento
  - Tamaño de logs
  - Número de conexiones
- Gráficos interactivos usando Plotly

## Requisitos Previos

- Python 3.8 o superior
- Cuenta de AWS con acceso a RDS y CloudWatch
- Credenciales de AWS configuradas localmente

## Configuración de Credenciales AWS

1. Asegúrate de tener el AWS CLI instalado
2. Configura tus credenciales usando uno de estos métodos:

   ```bash
   # Método 1: Usando AWS CLI
   aws configure --profile nombre_perfil

   # Método 2: Crear/editar manualmente el archivo de credenciales
   # Ubicación: ~/.aws/credentials (Linux/Mac) o %UserProfile%\.aws\credentials (Windows)
   [nombre_perfil]
   aws_access_key_id = TU_ACCESS_KEY
   aws_secret_access_key = TU_SECRET_KEY
   region = tu-region
   ```

## Instalación

1. Clona este repositorio o descarga los archivos

2. Crea un entorno virtual (recomendado):
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución

1. Activa el entorno virtual si no está activado:
   ```bash
   # Windows
   .\venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

2. Inicia la aplicación:
   ```bash
   streamlit run aws_rds_monitor.py
   ```

3. La aplicación se abrirá automáticamente en tu navegador predeterminado (generalmente en http://localhost:8501)

## Uso

1. Selecciona tu perfil de AWS en el menú desplegable
2. La tabla mostrará todas las instancias RDS disponibles
3. Selecciona una instancia específica para ver sus métricas
4. Navega entre las pestañas para ver diferentes métricas:
   - CPU Utilization
   - Memory Usage
   - Storage
   - Logs
   - Connections

## Solución de Problemas

- Si no ves perfiles de AWS, verifica que tus credenciales estén correctamente configuradas
- Si no hay instancias RDS, asegúrate de que el perfil seleccionado tenga acceso a RDS
- Si las métricas no se cargan, verifica que el perfil tenga permisos para CloudWatch

## Notas

- Las métricas se muestran para la última hora por defecto
- Los datos se actualizan automáticamente cada vez que cambias de pestaña
- Asegúrate de tener los permisos necesarios en AWS para acceder a RDS y CloudWatch 

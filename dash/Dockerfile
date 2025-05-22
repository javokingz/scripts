# Utiliza una imagen oficial de Python como base
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de la aplicación al contenedor
COPY . /app

# Instala las dependencias necesarias
RUN pip install --no-cache-dir streamlit boto3 pandas plotly

# Expone el puerto por defecto de Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación Streamlit
CMD ["streamlit", "run", "patch_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"] 
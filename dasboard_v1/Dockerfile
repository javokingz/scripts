# Utiliza una imagen oficial de Python como base
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de la aplicación y los requisitos
COPY ../requirements.txt ./
COPY ../dashboard_rds.py ./

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto por defecto de Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "dashboard_rds.py", "--server.port=8501", "--server.address=0.0.0.0"] 
# Conector de Instancias EC2 de AWS

Este script permite conectarse a instancias EC2 de AWS utilizando AWS Systems Manager Session Manager. Proporciona una interfaz de línea de comandos interactiva con tablas coloridas y mensajes informativos.

## Características

- Lista todas las instancias EC2 en una región específica
- Muestra información detallada de cada instancia:
  - Nombre (desde las etiquetas)
  - ID de instancia
  - Estado (running/stopped)
  - IP pública
  - IP privada
- Conexión directa a instancias usando AWS SSM Session Manager
- Interfaz de usuario colorida y amigable

## Requisitos Previos

- Python 3.8 o superior
- AWS CLI instalado y configurado
- Credenciales de AWS configuradas localmente
- Permisos necesarios para:
  - Describir instancias EC2
  - Usar Systems Manager Session Manager

## Instalación

1. Crea un entorno virtual (recomendado):
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Ejecuta el script:
   ```bash
   python connect_ec2.py
   ```

2. Sigue las instrucciones en pantalla:
   - Ingresa el nombre del perfil de AWS
   - Ingresa la región (ejemplo: us-east-1)
   - Selecciona el ID de la instancia a la que deseas conectarte

## Notas Importantes

- Asegúrate de que las instancias EC2 tengan el agente SSM instalado y configurado
- Las instancias deben tener los permisos IAM necesarios para Systems Manager
- El estado de las instancias se muestra en verde (running) o rojo (stopped)
- La conexión se realiza usando el comando `aws ssm start-session`

## Solución de Problemas

- Si no ves las instancias, verifica que:
  - El perfil de AWS sea correcto
  - La región sea la adecuada
  - Tengas los permisos necesarios
- Si la conexión falla, asegúrate de que:
  - La instancia esté en ejecución
  - El agente SSM esté instalado y funcionando
  - Los permisos IAM sean correctos

## Ejemplo de Uso

```bash
$ python connect_ec2.py
AWS EC2 Instance Connector
Enter AWS profile name: my-profile
Enter AWS region (e.g., us-east-1): us-east-1

# Se mostrará una tabla con las instancias
# Ingresa el ID de la instancia cuando se te solicite
``` 
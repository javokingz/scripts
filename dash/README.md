# Lambda Function para Iniciar Tareas Fargate

Esta función Lambda permite iniciar tareas en AWS Fargate de manera programática. Puede ser invocada directamente o mediante un EventBridge (CloudWatch Events) con un cron job diario.

## Requisitos

- Cuenta de AWS con acceso a:
  - AWS Lambda
  - Amazon ECS
  - Amazon EventBridge (CloudWatch Events)
  - VPC y subredes configuradas
  - Grupos de seguridad
- Rol IAM con los siguientes permisos:
  - `ecs:RunTask`
  - `ecs:DescribeTasks`
  - `logs:CreateLogGroup`
  - `logs:CreateLogStream`
  - `logs:PutLogEvents`
  - `events:PutRule`
  - `events:PutTargets`

## Configuración

1. Crear un rol IAM para la función Lambda con los permisos necesarios
2. Crear la función Lambda con el código proporcionado
3. Configurar las variables de entorno en la función Lambda:
   - `ECS_CLUSTER`: Nombre del clúster ECS
   - `TASK_DEFINITION`: Nombre y revisión de la definición de tarea (ejemplo: "my-task:1")
   - `SUBNETS`: IDs de subredes separados por comas
   - `SECURITY_GROUPS`: IDs de grupos de seguridad separados por comas
   - `ASSIGN_PUBLIC_IP`: "ENABLED" o "DISABLED" (opcional, por defecto "DISABLED")
4. Configurar el tiempo de espera y la memoria según sea necesario
5. Configurar la VPC y los grupos de seguridad

## Configuración de EventBridge

1. Crear una regla en EventBridge:
   ```bash
   aws events put-rule \
     --name "daily-fargate-task" \
     --schedule-expression "cron(0 0 * * ? *)" \
     --state ENABLED
   ```

2. Agregar la función Lambda como objetivo:
   ```bash
   aws events put-targets \
     --rule "daily-fargate-task" \
     --targets "Id"="1","Arn"="arn:aws:lambda:region:account:function:start-fargate-task"
   ```

## Uso

### Invocación mediante EventBridge
La función se ejecutará automáticamente todos los días a la medianoche (UTC) usando la configuración de las variables de entorno.

### Invocación Directa
La función también puede ser invocada directamente con un evento JSON:

```json
{
    "cluster": "nombre-del-cluster",
    "taskDefinition": "nombre-de-la-definicion:revision",
    "subnets": ["subnet-12345678", "subnet-87654321"],
    "securityGroups": ["sg-12345678"],
    "assignPublicIp": "ENABLED"
}
```

### Parámetros

- `cluster`: Nombre del clúster ECS donde se ejecutará la tarea
- `taskDefinition`: Nombre y revisión de la definición de tarea
- `subnets`: Lista de IDs de subredes
- `securityGroups`: Lista de IDs de grupos de seguridad (opcional)
- `assignPublicIp`: "ENABLED" o "DISABLED" (opcional)

### Respuesta

La función devuelve un objeto JSON con el siguiente formato:

```json
{
    "statusCode": 200,
    "body": {
        "message": "Fargate task started successfully",
        "taskArn": "arn:aws:ecs:region:account:task/cluster/task-id"
    }
}
```

## Manejo de Errores

La función incluye manejo de errores y logging. Los errores se registran en CloudWatch Logs y se devuelven en la respuesta con un código de estado 500.

## Ejemplo de Invocación Directa

```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='start-fargate-task',
    Payload=json.dumps({
        "cluster": "my-cluster",
        "taskDefinition": "my-task:1",
        "subnets": ["subnet-12345678"],
        "securityGroups": ["sg-12345678"],
        "assignPublicIp": "ENABLED"
    })
)
```

## Notas Importantes

1. Asegúrate de que la definición de tarea esté configurada para usar el tipo de lanzamiento FARGATE
2. Las subredes deben estar en la misma VPC que el clúster ECS
3. Los grupos de seguridad deben permitir el tráfico necesario para la tarea
4. El rol IAM de la función Lambda debe tener los permisos necesarios
5. La función está configurada para iniciar una sola tarea a la vez
6. Para el cron job diario, la función usa las variables de entorno para la configuración
7. El cron job se ejecuta a la medianoche UTC (0 0 * * ? *) 
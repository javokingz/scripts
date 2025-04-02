import json
import boto3
import logging
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to start a Fargate task.
    Can be triggered by EventBridge (CloudWatch Events) or direct invocation.
    
    For EventBridge trigger, the function uses environment variables for configuration.
    For direct invocation, it expects the following event format:
    {
        "cluster": "your-cluster-name",
        "taskDefinition": "your-task-definition:revision",
        "subnets": ["subnet-12345678", "subnet-87654321"],
        "securityGroups": ["sg-12345678"],
        "assignPublicIp": "ENABLED" or "DISABLED"
    }
    """
    try:
        # Initialize ECS client
        ecs_client = boto3.client('ecs')
        
        # Check if this is an EventBridge trigger
        if 'source' in event and event['source'] == 'aws.events':
            # Use environment variables for configuration
            cluster = os.environ.get('ECS_CLUSTER')
            task_definition = os.environ.get('TASK_DEFINITION')
            subnets = os.environ.get('SUBNETS', '').split(',')
            security_groups = os.environ.get('SECURITY_GROUPS', '').split(',')
            assign_public_ip = os.environ.get('ASSIGN_PUBLIC_IP', 'DISABLED')
            
            # Remove empty strings from lists
            subnets = [s for s in subnets if s]
            security_groups = [sg for sg in security_groups if sg]
        else:
            # Use parameters from direct invocation
            cluster = event.get('cluster')
            task_definition = event.get('taskDefinition')
            subnets = event.get('subnets', [])
            security_groups = event.get('securityGroups', [])
            assign_public_ip = event.get('assignPublicIp', 'DISABLED')
        
        # Validate required parameters
        if not all([cluster, task_definition, subnets]):
            raise ValueError("Missing required parameters: cluster, taskDefinition, or subnets")
        
        # Prepare network configuration
        network_configuration = {
            'awsvpcConfiguration': {
                'subnets': subnets,
                'securityGroups': security_groups,
                'assignPublicIp': assign_public_ip
            }
        }
        
        # Start the Fargate task
        response = ecs_client.run_task(
            cluster=cluster,
            taskDefinition=task_definition,
            launchType='FARGATE',
            networkConfiguration=network_configuration,
            count=1
        )
        
        # Check if task was started successfully
        if response['tasks']:
            task_arn = response['tasks'][0]['taskArn']
            logger.info(f"Successfully started Fargate task: {task_arn}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Fargate task started successfully',
                    'taskArn': task_arn
                })
            }
        else:
            logger.error("Failed to start Fargate task")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Failed to start Fargate task',
                    'failures': response.get('failures', [])
                })
            }
            
    except Exception as e:
        logger.error(f"Error starting Fargate task: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error starting Fargate task',
                'error': str(e)
            })
        } 
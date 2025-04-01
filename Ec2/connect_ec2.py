#!/usr/bin/env python3
import boto3
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich import print as rprint
import subprocess
import sys
from botocore.exceptions import ProfileNotFound, ClientError

def get_ec2_instances(profile_name, region):
    """Get list of EC2 instances for the selected profile and region"""
    try:
        session = boto3.Session(profile_name=profile_name, region_name=region)
        ec2_client = session.client('ec2')
        instances = ec2_client.describe_instances()
        
        instance_list = []
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                # Get instance name from tags
                name = "No Name"
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                
                instance_list.append({
                    'InstanceId': instance['InstanceId'],
                    'Name': name,
                    'State': instance['State']['Name'],
                    'PublicIp': instance.get('PublicIpAddress', 'N/A'),
                    'PrivateIp': instance.get('PrivateIpAddress', 'N/A')
                })
        return instance_list
    except ProfileNotFound:
        rprint("[red]Error: Profile not found[/red]")
        sys.exit(1)
    except ClientError as e:
        rprint(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)
    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

def display_instances(instances):
    """Display EC2 instances in a rich table"""
    table = Table(title="EC2 Instances")
    table.add_column("Name", style="cyan")
    table.add_column("Instance ID", style="magenta")
    table.add_column("State", style="bold")
    table.add_column("Public IP", style="green")
    table.add_column("Private IP", style="blue")

    for instance in instances:
        state_color = "green" if instance['State'] == 'running' else "red"
        table.add_row(
            instance['Name'],
            instance['InstanceId'],
            f"[{state_color}]{instance['State']}[/{state_color}]",
            instance['PublicIp'],
            instance['PrivateIp']
        )

    console = Console()
    console.print(table)

def connect_to_instance(instance_id, profile_name, region):
    """Connect to EC2 instance using AWS SSM Session Manager"""
    try:
        command = [
            'aws', 'ssm', 'start-session',
            '--target', instance_id,
            '--profile', profile_name,
            '--region', region
        ]
        subprocess.run(command)
    except subprocess.CalledProcessError as e:
        rprint(f"[red]Error connecting to instance: {str(e)}[/red]")
        sys.exit(1)
    except Exception as e:
        rprint(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

def main():
    console = Console()
    console.print("[bold blue]AWS EC2 Instance Connector[/bold blue]")
    
    # Get AWS profile and region
    profile_name = Prompt.ask("Enter AWS profile name")
    region = Prompt.ask("Enter AWS region (e.g., us-east-1)")
    
    # Get and display instances
    instances = get_ec2_instances(profile_name, region)
    if not instances:
        rprint("[yellow]No EC2 instances found in the selected profile and region[/yellow]")
        sys.exit(0)
    
    display_instances(instances)
    
    # Get instance ID to connect to
    instance_id = Prompt.ask("Enter the Instance ID to connect to")
    
    # Validate instance ID
    if not any(instance['InstanceId'] == instance_id for instance in instances):
        rprint("[red]Invalid Instance ID[/red]")
        sys.exit(1)
    
    # Connect to the instance
    rprint(f"[green]Connecting to instance {instance_id}...[/green]")
    connect_to_instance(instance_id, profile_name, region)

if __name__ == "__main__":
    main() 
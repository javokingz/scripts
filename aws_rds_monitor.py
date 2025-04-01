import streamlit as st
import boto3
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from botocore.exceptions import ProfileNotFound

def get_aws_profiles():
    """Get list of AWS profiles from credentials file"""
    try:
        profiles = boto3.Session().available_profiles
        return profiles
    except Exception as e:
        st.error(f"Error getting AWS profiles: {str(e)}")
        return []

def get_rds_instances(profile_name):
    """Get list of RDS instances for the selected profile"""
    try:
        session = boto3.Session(profile_name=profile_name)
        rds_client = session.client('rds')
        instances = rds_client.describe_db_instances()
        return instances['DBInstances']
    except ProfileNotFound:
        st.error(f"Profile '{profile_name}' not found")
        return []
    except Exception as e:
        st.error(f"Error getting RDS instances: {str(e)}")
        return []

def get_rds_metrics(profile_name, instance_id, metric_name, period=3600):
    """Get CloudWatch metrics for a specific RDS instance"""
    try:
        session = boto3.Session(profile_name=profile_name)
        cloudwatch = session.client('cloudwatch')
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(seconds=period)
        
        response = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'm1',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/RDS',
                            'MetricName': metric_name,
                            'Dimensions': [
                                {
                                    'Name': 'DBInstanceIdentifier',
                                    'Value': instance_id
                                }
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    },
                    'StartTime': start_time,
                    'EndTime': end_time
                }
            ]
        )
        
        if response['MetricDataResults']:
            return response['MetricDataResults'][0]['Values']
        return []
    except Exception as e:
        st.error(f"Error getting metrics for {metric_name}: {str(e)}")
        return []

def plot_metric(metric_data, title, y_label):
    """Create a line plot for metric data"""
    if not metric_data:
        st.warning(f"No data available for {title}")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=metric_data,
        mode='lines',
        name=title
    ))
    fig.update_layout(
        title=title,
        xaxis_title='Time',
        yaxis_title=y_label,
        height=400
    )
    st.plotly_chart(fig)

def main():
    st.title("AWS RDS Monitor")
    
    # Get AWS profiles
    profiles = get_aws_profiles()
    if not profiles:
        st.error("No AWS profiles found. Please configure your AWS credentials.")
        return
    
    # Profile selection
    selected_profile = st.selectbox("Select AWS Profile", profiles)
    
    # Get RDS instances
    instances = get_rds_instances(selected_profile)
    if not instances:
        st.warning("No RDS instances found in the selected profile.")
        return
    
    # Create a DataFrame with instance information
    instance_data = []
    for instance in instances:
        instance_data.append({
            'DBIdentifier': instance['DBInstanceIdentifier'],
            'Engine': instance['Engine'],
            'Endpoint': instance['Endpoint']['Address'],
            'Port': instance['Endpoint']['Port'],
            'Status': instance['DBInstanceStatus']
        })
    
    df = pd.DataFrame(instance_data)
    
    # Display instances table
    st.subheader("RDS Instances")
    st.dataframe(df)
    
    # Instance selection for detailed metrics
    selected_instance = st.selectbox(
        "Select an instance to view metrics",
        df['DBIdentifier'].tolist()
    )
    
    if selected_instance:
        st.subheader(f"Metrics for {selected_instance}")
        
        # Create tabs for different metrics
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "CPU Utilization",
            "Memory Usage",
            "Storage",
            "Logs",
            "Connections"
        ])
        
        with tab1:
            cpu_data = get_rds_metrics(selected_profile, selected_instance, 'CPUUtilization')
            plot_metric(cpu_data, "CPU Utilization", "Percentage")
        
        with tab2:
            memory_data = get_rds_metrics(selected_profile, selected_instance, 'FreeableMemory')
            plot_metric(memory_data, "Freeable Memory", "Bytes")
        
        with tab3:
            storage_data = get_rds_metrics(selected_profile, selected_instance, 'FreeStorageSpace')
            plot_metric(storage_data, "Free Storage Space", "Bytes")
        
        with tab4:
            log_data = get_rds_metrics(selected_profile, selected_instance, 'LogFileSize')
            plot_metric(log_data, "Log File Size", "Bytes")
        
        with tab5:
            connections_data = get_rds_metrics(selected_profile, selected_instance, 'DatabaseConnections')
            plot_metric(connections_data, "Database Connections", "Count")

if __name__ == "__main__":
    main() 
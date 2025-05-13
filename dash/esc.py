import streamlit as st
import boto3
import pandas as pd
from datetime import datetime

# Configure the page
st.set_page_config(
    page_title="AWS ECS Dashboard",
    page_icon="🚀",
    layout="wide"
)

# Initialize AWS clients
@st.cache_resource
def get_aws_clients():
    ecs_client = boto3.client('ecs')
    return ecs_client

def get_clusters(ecs_client):
    try:
        response = ecs_client.list_clusters()
        clusters = response['clusterArns']
        return clusters
    except Exception as e:
        st.error(f"Error getting clusters: {str(e)}")
        return []

def get_cluster_services(ecs_client, cluster_name):
    try:
        response = ecs_client.list_services(cluster=cluster_name)
        services = response['serviceArns']
        return services
    except Exception as e:
        st.error(f"Error getting services for cluster {cluster_name}: {str(e)}")
        return []

def get_service_details(ecs_client, cluster_name, service_name):
    try:
        response = ecs_client.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        return response['services'][0]
    except Exception as e:
        st.error(f"Error getting service details: {str(e)}")
        return None

def get_task_definitions(ecs_client, family_prefix=None):
    try:
        if family_prefix:
            response = ecs_client.list_task_definitions(familyPrefix=family_prefix)
        else:
            response = ecs_client.list_task_definitions()
        return response['taskDefinitionArns']
    except Exception as e:
        st.error(f"Error getting task definitions: {str(e)}")
        return []

def get_task_definition_details(ecs_client, task_definition_arn):
    try:
        response = ecs_client.describe_task_definition(taskDefinition=task_definition_arn)
        return response['taskDefinition']
    except Exception as e:
        st.error(f"Error getting task definition details: {str(e)}")
        return None

# Main dashboard
st.title("AWS ECS Dashboard")
st.markdown("---")

# Initialize AWS client
ecs_client = get_aws_clients()

# Get clusters
clusters = get_clusters(ecs_client)

if not clusters:
    st.warning("No ECS clusters found or unable to access AWS resources.")
else:
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Clusters & Services", "Task Definitions"])
    
    with tab1:
        st.header("ECS Clusters and Services")
        
        # Display clusters in a selectbox
        selected_cluster = st.selectbox(
            "Select a Cluster",
            clusters,
            format_func=lambda x: x.split('/')[-1]
        )
        
        if selected_cluster:
            # Get services for selected cluster
            services = get_cluster_services(ecs_client, selected_cluster)
            
            if services:
                st.subheader("Services in Cluster")
                
                # Create columns for service details
                for service in services:
                    service_details = get_service_details(ecs_client, selected_cluster, service)
                    
                    if service_details:
                        with st.expander(f"Service: {service.split('/')[-1]}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Service Details:**")
                                st.write(f"Status: {service_details.get('status', 'N/A')}")
                                st.write(f"Desired Count: {service_details.get('desiredCount', 'N/A')}")
                                st.write(f"Running Count: {service_details.get('runningCount', 'N/A')}")
                                st.write(f"Pending Count: {service_details.get('pendingCount', 'N/A')}")
                            
                            with col2:
                                st.write("**Task Definition:**")
                                st.write(f"Task Definition: {service_details.get('taskDefinition', 'N/A').split('/')[-1]}")
                                st.write(f"Launch Type: {service_details.get('launchType', 'N/A')}")
                                st.write(f"Platform Version: {service_details.get('platformVersion', 'N/A')}")
            else:
                st.info("No services found in this cluster.")
    
    with tab2:
        st.header("Task Definitions")
        
        # Search box for task definition family prefix
        family_prefix = st.text_input("Search Task Definitions (Family Prefix)")
        
        # Get task definitions
        task_definitions = get_task_definitions(ecs_client, family_prefix if family_prefix else None)
        
        if task_definitions:
            st.subheader("Available Task Definitions")
            
            # Display task definitions in a selectbox
            selected_task_def = st.selectbox(
                "Select a Task Definition",
                task_definitions,
                format_func=lambda x: x.split('/')[-1]
            )
            
            if selected_task_def:
                task_def_details = get_task_definition_details(ecs_client, selected_task_def)
                
                if task_def_details:
                    with st.expander("Task Definition Details", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Basic Information:**")
                            st.write(f"Family: {task_def_details.get('family', 'N/A')}")
                            st.write(f"Revision: {task_def_details.get('revision', 'N/A')}")
                            st.write(f"Status: {task_def_details.get('status', 'N/A')}")
                            st.write(f"CPU: {task_def_details.get('cpu', 'N/A')}")
                            st.write(f"Memory: {task_def_details.get('memory', 'N/A')}")
                        
                        with col2:
                            st.write("**Container Definitions:**")
                            for container in task_def_details.get('containerDefinitions', []):
                                st.write(f"Container: {container.get('name', 'N/A')}")
                                st.write(f"Image: {container.get('image', 'N/A')}")
                                st.write("---")
        else:
            st.info("No task definitions found.")

# Add footer
st.markdown("---")
st.markdown("Dashboard last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

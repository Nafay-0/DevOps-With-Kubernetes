#!/usr/bin/env python3
"""
DummySite Controller
Watches for DummySite resources and creates deployments/services to serve HTML from the website_url
"""

import os
import time
import urllib3
import requests
from kubernetes import client, config, watch

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Kubernetes API configuration
try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
custom_api = client.CustomObjectsApi()

GROUP = "stable.dwk"
VERSION = "v1"
PLURAL = "dummysites"
# Watch all namespaces (set to None) or specific namespace
WATCH_NAMESPACE = os.getenv("WATCH_NAMESPACE", None)  # None = all namespaces


def fetch_website_content(url):
    """Fetch HTML content from a URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return f"<html><body><h1>Error loading website</h1><p>{str(e)}</p></body></html>"


def create_deployment(name, namespace, html_content):
    """Create a Deployment that serves the HTML content"""
    # Create a ConfigMap with the HTML content
    configmap = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name=f"{name}-html",
            namespace=namespace
        ),
        data={"index.html": html_content}
    )
    
    try:
        v1.create_namespaced_config_map(namespace=namespace, body=configmap)
        print(f"Created ConfigMap {name}-html in namespace {namespace}")
    except client.exceptions.ApiException as e:
        if e.status == 409:  # Already exists
            v1.patch_namespaced_config_map(
                name=f"{name}-html",
                namespace=namespace,
                body=configmap
            )
            print(f"Updated ConfigMap {name}-html in namespace {namespace}")
        else:
            raise
    
    # Create Deployment
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name=name,
            namespace=namespace,
            labels={"app": name, "managed-by": "dummysite-controller"}
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(
                match_labels={"app": name}
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={"app": name}
                ),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="webserver",
                            image="nginx:alpine",
                            ports=[client.V1ContainerPort(container_port=80)],
                            volume_mounts=[
                                client.V1VolumeMount(
                                    name="html-content",
                                    mount_path="/usr/share/nginx/html"
                                )
                            ]
                        )
                    ],
                    volumes=[
                        client.V1Volume(
                            name="html-content",
                            config_map=client.V1ConfigMapVolumeSource(
                                name=f"{name}-html"
                            )
                        )
                    ]
                )
            )
        )
    )
    
    try:
        apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
        print(f"Created Deployment {name} in namespace {namespace}")
    except client.exceptions.ApiException as e:
        if e.status == 409:  # Already exists
            apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            print(f"Updated Deployment {name} in namespace {namespace}")
        else:
            raise


def create_service(name, namespace):
    """Create a Service for the deployment"""
    service = client.V1Service(
        metadata=client.V1ObjectMeta(
            name=name,
            namespace=namespace,
            labels={"app": name, "managed-by": "dummysite-controller"}
        ),
        spec=client.V1ServiceSpec(
            selector={"app": name},
            ports=[client.V1ServicePort(port=80, target_port=80)],
            type="ClusterIP"
        )
    )
    
    try:
        v1.create_namespaced_service(namespace=namespace, body=service)
        print(f"Created Service {name} in namespace {namespace}")
    except client.exceptions.ApiException as e:
        if e.status == 409:  # Already exists
            v1.patch_namespaced_service(
                name=name,
                namespace=namespace,
                body=service
            )
            print(f"Updated Service {name} in namespace {namespace}")
        else:
            raise


def handle_dummysite_added(dummysite):
    """Handle when a DummySite is created"""
    name = dummysite['metadata']['name']
    namespace = dummysite['metadata'].get('namespace', 'default')
    website_url = dummysite['spec']['website_url']
    
    print(f"Processing DummySite {name} in namespace {namespace} with URL {website_url}")
    
    # Fetch website content
    html_content = fetch_website_content(website_url)
    
    # Create resources
    create_deployment(name, namespace, html_content)
    create_service(name, namespace)
    
    print(f"Successfully created resources for DummySite {name}")


def handle_dummysite_deleted(dummysite):
    """Handle when a DummySite is deleted"""
    name = dummysite['metadata']['name']
    namespace = dummysite['metadata'].get('namespace', 'default')
    
    print(f"Deleting resources for DummySite {name} in namespace {namespace}")
    
    # Delete Deployment
    try:
        apps_v1.delete_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=client.V1DeleteOptions(propagation_policy="Foreground")
        )
        print(f"Deleted Deployment {name}")
    except client.exceptions.ApiException as e:
        if e.status != 404:
            print(f"Error deleting Deployment {name}: {e}")
    
    # Delete Service
    try:
        v1.delete_namespaced_service(
            name=name,
            namespace=namespace,
            body=client.V1DeleteOptions()
        )
        print(f"Deleted Service {name}")
    except client.exceptions.ApiException as e:
        if e.status != 404:
            print(f"Error deleting Service {name}: {e}")
    
    # Delete ConfigMap
    try:
        v1.delete_namespaced_config_map(
            name=f"{name}-html",
            namespace=namespace,
            body=client.V1DeleteOptions()
        )
        print(f"Deleted ConfigMap {name}-html")
    except client.exceptions.ApiException as e:
        if e.status != 404:
            print(f"Error deleting ConfigMap {name}-html: {e}")


def watch_dummysites():
    """Watch for DummySite resource changes"""
    w = watch.Watch()
    
    try:
        if WATCH_NAMESPACE:
            print(f"Starting to watch DummySite resources in namespace {WATCH_NAMESPACE}...")
            stream = w.stream(
                custom_api.list_namespaced_custom_object,
                GROUP,
                VERSION,
                WATCH_NAMESPACE,
                PLURAL,
                timeout_seconds=60
            )
        else:
            print("Starting to watch DummySite resources in all namespaces...")
            stream = w.stream(
                custom_api.list_cluster_custom_object,
                GROUP,
                VERSION,
                PLURAL,
                timeout_seconds=60
            )
        
        for event in stream:
            event_type = event['type']
            dummysite = event['object']
            name = dummysite['metadata']['name']
            namespace = dummysite['metadata'].get('namespace', 'default')
            
            print(f"Received {event_type} event for DummySite {name} in namespace {namespace}")
            
            if event_type == 'ADDED' or event_type == 'MODIFIED':
                handle_dummysite_added(dummysite)
            elif event_type == 'DELETED':
                handle_dummysite_deleted(dummysite)
                
    except Exception as e:
        print(f"Error watching DummySite resources: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(5)
        watch_dummysites()  # Retry


def main():
    """Main entry point"""
    print("DummySite Controller starting...")
    if WATCH_NAMESPACE:
        print(f"Watching namespace: {WATCH_NAMESPACE}")
    else:
        print("Watching all namespaces")
    
    # Process existing DummySites
    try:
        if WATCH_NAMESPACE:
            existing = custom_api.list_namespaced_custom_object(
                GROUP, VERSION, WATCH_NAMESPACE, PLURAL
            )
        else:
            existing = custom_api.list_cluster_custom_object(GROUP, VERSION, PLURAL)
        
        for item in existing.get('items', []):
            name = item['metadata']['name']
            namespace = item['metadata'].get('namespace', 'default')
            print(f"Processing existing DummySite: {name} in namespace {namespace}")
            handle_dummysite_added(item)
    except Exception as e:
        print(f"Error processing existing DummySites: {e}")
    
    # Start watching for changes
    while True:
        try:
            watch_dummysites()
        except Exception as e:
            print(f"Error in watch loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()


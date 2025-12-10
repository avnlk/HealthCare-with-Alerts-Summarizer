#!/bin/bash
# Healthcare AIOps Kubernetes Deployment Script
# This script deploys all Kubernetes resources in the correct order

set -e

NAMESPACE="healthcare"
K8S_DIR="$(dirname "$0")"

echo "========================================="
echo "Healthcare AIOps Kubernetes Deployment"
echo "========================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Check cluster connection
echo ""
echo "Step 1: Checking cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Cannot connect to Kubernetes cluster"
    echo "Make sure your cluster is running and kubeconfig is configured"
    exit 1
fi
echo "✓ Connected to cluster"

# Create namespace
echo ""
echo "Step 2: Creating namespace..."
kubectl apply -f "$K8S_DIR/namespace.yaml"
echo "✓ Namespace '$NAMESPACE' created"

# Deploy ConfigMaps
echo ""
echo "Step 3: Deploying ConfigMaps..."
kubectl apply -f "$K8S_DIR/configmaps/"
echo "✓ ConfigMaps deployed"

# Deploy Secrets
echo ""
echo "Step 4: Deploying Secrets..."
kubectl apply -f "$K8S_DIR/secrets/"
echo "✓ Secrets deployed"

# Deploy ELK Stack (Elasticsearch first)
echo ""
echo "Step 5: Deploying ELK Stack..."
kubectl apply -f "$K8S_DIR/elk/"
echo "✓ ELK Stack deployed"

# Wait for Elasticsearch to be ready
echo ""
echo "Step 6: Waiting for Elasticsearch to be ready..."
kubectl rollout status statefulset/elasticsearch -n $NAMESPACE --timeout=300s || {
    echo "Warning: Elasticsearch not ready yet, continuing..."
}

# Deploy application services
echo ""
echo "Step 7: Deploying application services..."
kubectl apply -f "$K8S_DIR/deployments/"
echo "✓ Application services deployed"

# Deploy HPA
echo ""
echo "Step 8: Deploying Horizontal Pod Autoscalers..."
kubectl apply -f "$K8S_DIR/hpa/"
echo "✓ HPAs deployed"

# Deploy Ingress
echo ""
echo "Step 9: Deploying Ingress..."
kubectl apply -f "$K8S_DIR/ingress/"
echo "✓ Ingress deployed"

# Summary
echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Check status with:"
echo "  kubectl get all -n $NAMESPACE"
echo ""
echo "Watch pods:"
echo "  kubectl get pods -n $NAMESPACE -w"
echo ""
echo "Access services locally:"
echo "  kubectl port-forward svc/frontend 3000:80 -n $NAMESPACE"
echo "  kubectl port-forward svc/kibana 5601:5601 -n $NAMESPACE"
echo ""

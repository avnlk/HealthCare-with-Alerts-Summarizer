#!/bin/bash
# Healthcare AIOps Kubernetes Cleanup Script
# This script removes all Kubernetes resources

set -e

NAMESPACE="healthcare"
K8S_DIR="$(dirname "$0")"

echo "========================================="
echo "Healthcare AIOps Kubernetes Cleanup"
echo "========================================="

read -p "Are you sure you want to delete all resources in namespace '$NAMESPACE'? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deleting all resources..."

    # Delete in reverse order
    kubectl delete -f "$K8S_DIR/ingress/" --ignore-not-found
    kubectl delete -f "$K8S_DIR/hpa/" --ignore-not-found
    kubectl delete -f "$K8S_DIR/deployments/" --ignore-not-found
    kubectl delete -f "$K8S_DIR/elk/" --ignore-not-found
    kubectl delete -f "$K8S_DIR/secrets/" --ignore-not-found
    kubectl delete -f "$K8S_DIR/configmaps/" --ignore-not-found
    kubectl delete -f "$K8S_DIR/namespace.yaml" --ignore-not-found

    echo ""
    echo "✓ All resources deleted"
else
    echo "Cleanup cancelled"
fi

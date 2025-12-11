# Dockerfile for running Ansible with Kubernetes capabilities
FROM python:3.11-slim

# Install dependencies for Ansible, Kubernetes Python client, and kubectl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    && pip install ansible kubernetes \
    && curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg \
    && echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list \
    && apt-get update \
    && apt-get install -y kubectl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set up a working directory
WORKDIR /ansible

# Dockerfile for running Ansible
FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ansible \
    openssh-client \
    python3 \
    python3-pip \
    kubectl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set up a working directory
WORKDIR /ansible

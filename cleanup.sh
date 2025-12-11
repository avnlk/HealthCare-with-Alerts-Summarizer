#!/bin/bash

# This script cleans up old containers and Docker image versions to free up disk space on the CI agent.

set -e # Exit immediately if a command exits with a non-zero status.

# Arguments passed from the Jenkins pipeline
DOCKER_USERNAME=$1
APP_VERSION=$2


SERVICES_TO_CLEANUP=(
    "alert-engine" "auth-service" "summarizer-service"
    "vitals-generator" "frontend"
)

for service in "${SERVICES_TO_CLEANUP[@]}"; do
    repoName="${DOCKER_USERNAME}/${service}"
    echo "Cleaning up old images for ${repoName}..."
    # This command finds all versioned images for a repo, excludes the current version, and deletes the rest.
    docker images --format '{{.Repository}}:{{.Tag}}' "$repoName" | \
        grep -E ':[0-9]+\.[0-9]+\.[0-9]+$' | \
        grep -v ":${APP_VERSION}" | \
        xargs -r docker rmi || true
done

echo "--- Cleanup complete."
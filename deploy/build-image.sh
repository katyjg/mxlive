#!/bin/bash

IMAGE_REPO=${IMAGE_REPO:-"localhost"}
IMAGE_NAME="${IMAGE_REPO}/mxlive"

# Build a docker image
# Check if buildah exists, then build the image
echo "Building the Docker/Podman image... ${IMAGE_NAME}"
if command -v buildah &> /dev/null; then
  buildah bud -t "${IMAGE_NAME}:$(git describe)" -t "${IMAGE_NAME}:latest" .
  buildah rmi --prune
elif command -v podman &> /dev/null; then
  podman build -t "${IMAGE_NAME}:$(git describe)" -t "${IMAGE_NAME}:latest" .
  podman image prune -f
elif command -v docker &> /dev/null; then
  docker build -t "${IMAGE_NAME}:$(git describe)" -t "${IMAGE_NAME}:latest" .
  docker image prune -f
else
  echo "Neither podman, buildah nor docker are installed. Exiting!"
  exit 1
fi
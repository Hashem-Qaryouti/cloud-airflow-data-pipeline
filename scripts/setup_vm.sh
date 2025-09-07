#!/bin/bash

# ====================================================================
# Setup script for Docker + Apache Airflow (v3.0.6) on a GCP VM (Ubuntu)
# ====================================================================
# Prerequisites:
# 1. A running GCP VM with Ubuntu (tested on Ubuntu 20.04/22.04).
# 2. SSH access to the VM.
# 3. Run this script on the VM after connecting via SSH.
# ====================================================================

set -e  # Exit immediately if a command fails

# Step 1. Update apt and install required dependencies
echo ">>> Updating apt and installing dependencies..."
sudo apt-get update
sudo apt-get install ca-certificates curl

# Step 2. Add Docker’s official GPG key
echo ">>> Adding Docker's GPG key..."
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Step 3. Setup Docker repository
echo ">>> Adding Docker apt repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Step 4. Install Docker Engine and plugins
echo ">>> Installing Docker Engine and plugins..."
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Step 5. Verify Docker installation
echo ">>> Verifying Docker installation..."
sudo docker run hello-world

# Step 6. Install Apache Airflow via Docker Compose
echo ">>> Setting up Apache Airflow 3.0.6..."
mkdir airflow
cd airflow
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.0.6/docker-compose.yaml'

# Create folders required by Airflow
mkdir ./dags ./plugins ./logs

# Create .env file for Airflow
echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env

# Step 7. Initialize Airflow database
echo ">>> Initializing Airflow..."
sudo docker compose up airflow-init

# Step 8. Start all Airflow services
echo ">>> Starting Airflow services..."
sudo docker compose up

echo ">>> Setup complete! Access Airflow web UI at http://<VM_IP>:8080"
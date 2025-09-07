# A Data Pipeline using Apache Airflow Hosted on Google Cloud Platform Virtual Machine


## Architecture
1. Developer pushes code -> GitHub Repo.
2. GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs.
3. Workflow connected to the GCP VM via SSH.
4. Repository is cloned/pulled on the VM.
5. DAGs are copied into the Airflow instance (`~/airflow/dags`).
6. Airflow automatically loads new/updated DAGs.

## Setup
1. Prerequisites
    * Google Cloud Platform (GCP) account.
    * A running Ubuntu VM instance in GCP
    * Open firwall ports:
        * 22 -> SHH
        * 8080 -> Airflow Web UI
    * GitHub Repository with you DAGs and pipeline code.

2. Install Docker & Airflow on the VM
SSH into your VM:
`ssh <your-username>@<your-vm-external-ip>`
Then run the installation script:
`dd`
This will:
    * Install Docker Engine and Docker Compose
    * Download Airflow 3.0.6 docker-compose.yaml.
    * Creates folders (`/dags`, `./plugins`, `/logs`).
    * Initialize Airflow and start services.

After installation, open Airflow UI in your browser:
`http://<your-vm-external-ip>:8080`

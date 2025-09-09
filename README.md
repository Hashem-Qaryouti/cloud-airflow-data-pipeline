# A Data Pipeline using Apache Airflow Hosted on Google Cloud Platform Virtual Machine ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)


![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white)
![GCP](https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=Google%20Cloud&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=Docker&logoColor=white)

## 🚀 Architecture
1. Developer pushes code -> GitHub Repo.
2. GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs.
3. Workflow connected to the GCP VM via SSH.
4. Repository is cloned/pulled on the VM.
5. DAGs are copied into the Airflow instance (`~/airflow/dags`).
6. Airflow automatically loads new/updated DAGs.

## ⚙️ Setup
1. Prerequisites
    * Google Cloud Platform (GCP) account.
    * A running Ubuntu VM instance in GCP
    * Open firwall ports:
        * 22 -> SHH
        * 8080 -> Airflow Web UI
    * GitHub Repository with you DAGs and pipeline code.

2. Install Docker & Airflow on the VM
    - SSH into your VM:
    `ssh <your-username>@<your-vm-external-ip>` 
    - Then run the installation script:
    ```
    chmod +x ./scripts/setup_vm.sh
    ./scripts/setup_vm.sh
    ```  
    - This will:
        * Install Docker Engine and Docker Compose
        * Download Airflow 3.0.6 docker-compose.yaml.
        * Creates folders (`/dags`, `./plugins`, `/logs`).
        * Initialize Airflow and start services.

    - After installation, open Airflow UI in your browser:
    `http://<your-vm-external-ip>:8080`
![Alt text](assets/images/demo_dag.png)

3. Setup SSH Keys for CI/CD
    - On your local machine:\
    `ssh-keygen -t rsa -b 4096 -C "your_email@example.com"`

    * `id_rsa` → private key (add as GitHub secret: `GCP_SSH_KEY`).
    * `id_rsa.pub` → public key (add to VM: `~/.ssh/authorized_keys`).

    - Also add the following GitHub repo secrets:

    * `GCP_VM_HOST` = \<your-vm-ip\>
    * `GCP_VM_USER` = \<your-vm-username\>

## 📂 Repository Structure
```
cloud-airflow-data-pipeline/
│── dags/               # Airflow DAGs
│── plugins/            # Airflow custom plugins
│── scripts/            # Helper scripts
│── docker-compose.yml  # Docker setup for Airflow
│── install_airflow.sh  # Setup script for Docker + Airflow
│── .github/workflows/  # CI/CD definitions

```
## ▶️ Usage

* Add new DAGs to dags/ folder.

* Push changes to main branch.

* GitHub Actions deploys automatically.

* Check Airflow UI (http://\<vm-ip>\:8080) for new DAGs.



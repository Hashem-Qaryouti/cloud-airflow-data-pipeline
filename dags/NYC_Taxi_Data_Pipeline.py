from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from datetime import datetime, timedelta
import requests

BUCKET_NAME = 'gcp_storage_service'
BUCKET_RAW_DATA_FOLDER='green_taxi_data'

def download_green_taxi_data():    
    """ This function downloads raw green taxi data into S3
        
        Args:
            None
        
        Return:
            None
    """
    base_url='https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_'
    gcs = GCSHook(gcp_conn_id="gcp_bucket_connection") 
    today = datetime.today()

    for i in range(12):
        # Compute year-month
        date = today.replace(day=1) - timedelta(days=30*i)
        year = date.year
        month = f"{date.month:02d}"

        # File details
        url = f"{base_url}{year}-{month}.parquet"
        blob_name = f"{BUCKET_RAW_DATA_FOLDER}/green_tripdata_{year}-{month}.parquet"

        # Skip if file already exists (avoid duplicates)
        if gcs.exists(bucket_name=BUCKET_NAME, object_name=blob_name):
            print(f"{blob_name} already exists, skipping")
            continue

        # Download file
        print(f"Downloading {url}")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to download {url}")
            continue

        # Upload to GCS
        print(f"Uploading to gs://{BUCKET_NAME}/{blob_name}")
        gcs.upload(
            bucket_name=BUCKET_NAME,
            object_name=blob_name,
            data=response.content,
        )

# Define default args
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
}

with DAG(
    dag_id='NYC_Taxi_Data_DAG',
    default_args=default_args,
    description='A pipeline to process NYC Data',
    schedule='@daily',  # runs daily
    start_date=datetime(2025, 9, 7),
    catchup=False,
) as dag:
    
    

    download_raw_data = PythonOperator(
        task_id='download_green_taxi_data',
        python_callable=download_green_taxi_data
    )
    download_raw_data
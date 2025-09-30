from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.sdk import Variable
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from datetime import datetime, timedelta
import pyarrow.parquet as pq
import pandas as pd
import requests
import io
import paths

DEBUG = True
BUCKET_NAME = Variable.get("BUCKET_NAME")
BUCKET_RAW_DATA_FOLDER= paths.BUCKET_RAW_DATA_FOLDER

def connect_2_google_cloud():
    """ This funciton connects to google cloud platform using airflow connections
    """
    return GCSHook(gcp_conn_id="gcp_bucket_connection")

def download_green_taxi_data():    
    """ This function downloads raw green taxi data into Google Cloud Storage
        
        Args:
            None
        
        Return:
            None
    """
    base_url=paths.NYC_Green_Taxi_Data_URL
    gcp_connection = connect_2_google_cloud()

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
        if gcp_connection.exists(bucket_name=BUCKET_NAME, object_name=blob_name):
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
        gcp_connection.upload(
            bucket_name=BUCKET_NAME,
            object_name=blob_name,
            data=response.content,
        )

def check_dataset_schema():
    """ This function checks for anomalies in column names or types.
        Then, and based on the anomaly types, they should be handled correclty  
    """
    gcp_connection = connect_2_google_cloud() 
    files = gcp_connection.list(bucket_name=BUCKET_NAME, prefix=BUCKET_RAW_DATA_FOLDER)
    parquet_files = [parquet_file for parquet_file in files if parquet_file.endswith(".parquet")]
    
    if DEBUG:
        print(f"Batch files in the cloud {parquet_files}")

    # Get schemas for all files
    schemas = {}
    df_dict = {}
    for file in parquet_files:
        try:
            file_bytes = gcp_connection.download(bucket_name=BUCKET_NAME, object_name=file)
        except Exception as e:
            print(f"[check_dataset_schema]\t Unable to download files from the cloud")
        # Read schema using PyArrow (faster than loading whole DF)
        table = pq.read_table(io.BytesIO(file_bytes))
        schema = {col: str(table.schema.field(col).type) for col in table.schema.names}
        
        schemas[file] = schema

        # Load all DataFrames at once
        df_dict[file] = table.to_pandas()
    
    # Print schemas
    for file, schema in schemas.items():
        print(f"{file}")
        for col, dtype in schema.items():
            print(f"  {col}: {dtype}")
    
    # Compare schemas to find anomalies
    all_columns = set().union(*[s.keys() for s in schemas.values()])

    print("\n--- ANOMALIES ---")
    for col in all_columns:
        types = {}
        for file, schema in schemas.items():
            dtype = schema.get(col, "MISSING")
            types.setdefault(dtype, []).append(file)
        
        if len(types) > 1:  # mismatch found
            # Check if anomaly is only MISSING
            if "MISSING" in types and len(types) == 2:  
                # Only one other type and some missing → treat as missing column
                missing_files = types["MISSING"]
                handle_missing_columns(col, missing_files, df_dict)
            else:
                # Type mismatch
                handle_type_mismatch(col, types, df_dict)

    final_df = pd.concat(df_dict.values(), ignore_index=True)
    # Save data to Google Cloud Storage
    save_processed_dataframe_to_gcp(dataframe=final_df,
                                    bucket_name=BUCKET_NAME,
                                    object_name=paths.processed_data_path,
                                    gcp_connection=gcp_connection)
    # Save data to Google Cloud BigQuery
    save_processed_df_to_bigquery(dataframe=final_df,
                                  dataset_id=Variable.get("dataset_id"),
                                  table_id=Variable.get("table_id"),
                                  gcp_connection="gcp_bucket_connection")
    

def handle_missing_columns(col, missing_files,df_dict):
    for file in missing_files:
        df = df_dict[file]
        if col not in df.columns:
            df[col] = pd.NA
            print(f"Added missing column '{col}' with NaN in {file}")

def handle_type_mismatch(col, types, df_dict):
    """ Cast mismatched column types to a common type (default: string)
    """
    for dtype, files in types.items():
        for file in files:
            df = df_dict[file]
            if col in df.columns:
                df[col] = df[col].astype(str)
                print(f"Converted {col} in {file} from {dtype} to string")

def save_processed_dataframe_to_gcp(dataframe: pd.DataFrame,
                                    bucket_name:str,
                                    object_name:str,
                                    gcp_connection:str):
    try:
        csv_buffer = io.StringIO()
        dataframe.to_csv(csv_buffer, index=False)

        gcp_connection.upload(
            bucket_name=BUCKET_NAME,
            object_name=object_name,
            data=csv_buffer.getvalue(),
            mime_type="text/csv"
        )
        if DEBUG:
            print(f"Dataframe saved to the cloud: {bucket_name}/{object_name}")
        
    except Exception as e:
        print(f"Failed to upload CSV to the cloud: {e}")

def save_processed_df_to_bigquery(dataframe: pd.DataFrame,
                                  dataset_id: str,
                                  table_id:str,
                                  gcp_connection:str):
    """ This function saves final dataset to GCP BigQuery for further analysis

        Args:
            dataframe (pd.DataFrame): represents the processed dataframe
            dataset_id (str): represents the dataset id in Google Query
            table_id (str): represents the table id/name to save data
            gcp_connection (str): represents GCP connection object

        Return:
            None
    """
    big_query_hook = BigQueryHook(gcp_conn_id=gcp_connection, use_legacy_sql=False)

    # Upload pandas DataFrame to BigQuery
    big_query_hook.insert_rows_dataframe(
        dataset_id=dataset_id,
        table_id=table_id,
        rows=dataframe,
        project_id=None,
        chunk_size=5000,
        replace=True
    )
    if DEBUG:
        print(f"DataFrame saved to BigQuery: {dataset_id}.{table_id}")

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
    check_columns_anomalies = PythonOperator(
        task_id='check_for_anomalies_columns_types_names',
        python_callable=check_dataset_schema
    )
    

    download_raw_data >> check_columns_anomalies
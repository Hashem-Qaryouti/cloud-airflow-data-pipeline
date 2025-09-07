# Filename: dags/simple_dag.py

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

# Define default args
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
}

# Define the DAG
with DAG(
    dag_id='demo_dag',
    default_args=default_args,
    description='A simple example DAG',
    schedule='@daily',  # runs daily
    start_date=datetime(2025, 9, 6),
    catchup=False,
    tags=['example']
) as dag:

    # Task 1: Print current date
    def print_date():
        from datetime import datetime
        print(f"Current date: {datetime.now()}")

    task1 = PythonOperator(
        task_id='print_date',
        python_callable=print_date
    )

    # Task 2: Print Hello Airflow
    def hello_airflow():
        print("Hello Airflow 3.0.6!")

    task2 = PythonOperator(
        task_id='hello_airflow',
        python_callable=hello_airflow
    )

    # Set task order
    task1 >> task2

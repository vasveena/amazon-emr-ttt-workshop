# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from airflow import DAG
from airflow.operators.python_operator import PythonOperator

from time import sleep
from datetime import datetime

import boto3, time
from builtins import range
from pprint import pprint

from airflow.operators.sensors import BaseSensorOperator
from airflow.contrib.operators.emr_create_job_flow_operator import EmrCreateJobFlowOperator
from airflow.contrib.operators.emr_terminate_job_flow_operator import EmrTerminateJobFlowOperator
from airflow.contrib.sensors.emr_job_flow_sensor import EmrJobFlowSensor
from airflow.contrib.sensors.emr_step_sensor import EmrStepSensor
from airflow.contrib.hooks.emr_hook import EmrHook
from airflow.contrib.sensors.emr_base_sensor import EmrBaseSensor
from airflow.models import Variable
from airflow.utils import apply_defaults
from airflow.utils.dates import days_ago


# Available categories:
#
# Apparel,Automotive,Baby,Beauty,Books,Camera,Digital_Ebook_Purchase,Digital_Music_Purchase,
# Digital_Software,Digital_Video_Download,Digital_Video_Games,Electronics,Furniture,Gift_Card,
# Grocery,Health_&_Personal_Care,Home,Home_Entertainment,Home_Improvement,Jewelry,Kitchen,
# Lawn_and_Garden,Luggage,Major_Appliances,Mobile_Apps,Mobile_Electronics,Music,Musical_Instruments,
# Office_Products,Outdoors,PC,Personal_Care_Appliances,Pet_Products,Shoes,Software,Sports,Tools,
# Toys,Video,Video_DVD,Video_Games,Watches,Wireless


# =============== VARIABLES ===============
NOTEBOOK_ID = Variable.get('NOTEBOOK_ID')
NOTEBOOK_FILE_NAME = Variable.get('NOTEBOOK_FILE_NAME')
CATEGORIES_CSV = Variable.get('CATEGORIES_CSV')
REGION = Variable.get('REGION')
SUBNET_ID = Variable.get('SUBNET_ID')
EMR_LOG_URI = Variable.get('EMR_LOG_URI')
OUTPUT_LOCATION = Variable.get('OUTPUT_LOCATION')
FROM_DATE = Variable.get('FROM_DATE')
TO_DATE = Variable.get('TO_DATE')
# =========================================


JOB_FLOW_OVERRIDES = {
    'Name': 'Test-Cluster',
    'ReleaseLabel': 'emr-6.2.0',
    'Applications': [{'Name':'Spark'}, {'Name':'Hive'}, {'Name':'Livy'}, {'Name':'JupyterEnterpriseGateway'}],
    'Configurations': [
          {
            "Classification": "hive-site",
            "Properties": {
                "hive.execution.engine": "spark"
            }
        }
    ],
    'Instances': {
        'Ec2SubnetId': SUBNET_ID,
        'InstanceGroups': [
            {
                'Name': 'Master node',
                'Market': 'ON_DEMAND',
                'InstanceRole': 'MASTER',
                'InstanceType': 'm5.xlarge',
                'InstanceCount': 1,
            },
            {
                'Name': 'Core node',
                'Market': 'ON_DEMAND',
                'InstanceRole': 'CORE',
                'InstanceType': 'm5.xlarge',
                'InstanceCount': 2,
            }
        ],
        'KeepJobFlowAliveWhenNoSteps': True,
        'TerminationProtected': False,
    },
    'JobFlowRole': 'EMR_EC2_DefaultRole',
    'ServiceRole': 'EMR_DefaultRole',
    'LogUri': EMR_LOG_URI
}



class CustomEmrJobFlowSensor(EmrJobFlowSensor):
    NON_TERMINAL_STATES = ['STARTING', 'BOOTSTRAPPING', 'TERMINATING']


class NotebookExecutionSensor(EmrBaseSensor):
    NON_TERMINAL_STATES = ['START_PENDING', 'STARTING', 'RUNNING', 'FINISHING', 'STOP_PENDING', 'STOPPING']
    FAILED_STATE = ['FAILING', 'FAILED']
    template_fields = ['notebook_execution_id']
    template_ext = ()

    @apply_defaults
    def __init__(self, notebook_execution_id, *args, **kwargs):
        super(NotebookExecutionSensor, self).__init__(*args, **kwargs)
        self.notebook_execution_id = notebook_execution_id

    def get_emr_response(self):
        emr = EmrHook(aws_conn_id=self.aws_conn_id).get_conn()
        self.log.info('Poking notebook execution %s', self.notebook_execution_id)
        return emr.describe_notebook_execution(NotebookExecutionId=self.notebook_execution_id)

    @staticmethod
    def state_from_response(response):
        return response['NotebookExecution']['Status']

    @staticmethod
    def failure_message_from_response(response):
        state_change_reason = response['NotebookExecution']['LastStateChangeReason']
        if state_change_reason:
            return 'Execution failed with reason: ' + state_change_reason
        return None


def start_execution(**context):
    ti = context['task_instance']
    cluster_id = ti.xcom_pull(key='return_value', task_ids='create_cluster_task')

    print("Starting an execution using cluster: " + cluster_id)

    # generate a JSON key-pair of <String : String Array>, e.g. 
    # "\"CATEGORIES\": [\"Apparel\", \"Automotive\", \"Baby\", \"Books\"]"
    categories_escaped_quotes = ""
    for category in CATEGORIES_CSV.split(','):
        categories_escaped_quotes = categories_escaped_quotes + "\"" + category + "\","

    categories_escaped_quotes = categories_escaped_quotes[:-1]
    categories_parameter = "\"CATEGORIES\" : [" + categories_escaped_quotes + "]"


    output_location_parameter = "\"OUTPUT_LOCATION\": \"" + OUTPUT_LOCATION + "\""
    from_date_parameter = "\"FROM_DATE\": \"" + FROM_DATE + "\""
    to_date_parameter = "\"TO_DATE\": \"" + TO_DATE + "\""

    parameters = f"{{ {categories_parameter}, {output_location_parameter}, {from_date_parameter}, {to_date_parameter} }}"

    emr = boto3.client('emr', region_name=REGION)
    start_resp = emr.start_notebook_execution(
        EditorId=NOTEBOOK_ID,
        RelativePath=NOTEBOOK_FILE_NAME,
        ExecutionEngine={'Id': cluster_id, 'Type': 'EMR'},
        NotebookParams=parameters,
        ServiceRole='EMR_Notebooks_DefaultRole'
    )

    execution_id = start_resp['NotebookExecutionId']
    print("Started an execution: " + execution_id)
    return execution_id




with DAG('test_dag', description='test dag', schedule_interval='0 * * * *', start_date=datetime(2020,3,30), catchup=False) as dag:

    create_cluster = EmrCreateJobFlowOperator(
        task_id='create_cluster_task',
        job_flow_overrides=JOB_FLOW_OVERRIDES,
        aws_conn_id='aws_default',
        emr_conn_id='emr_default',
    )

    cluster_sensor = CustomEmrJobFlowSensor(
        task_id='check_cluster_task',
        job_flow_id="{{ task_instance.xcom_pull(task_ids='create_cluster_task', key='return_value') }}",
        aws_conn_id='aws_default',
    )

    start_execution = PythonOperator(
        task_id='start_execution_task', 
        python_callable=start_execution,
        provide_context=True
    )

    execution_sensor = NotebookExecutionSensor(
        task_id='check_execution_task',
        notebook_execution_id="{{ task_instance.xcom_pull(task_ids='start_execution_task', key='return_value') }}",
        aws_conn_id='aws_default',
    )


    cluster_remover = EmrTerminateJobFlowOperator(
        task_id='terminate_cluster',
        job_flow_id="{{ task_instance.xcom_pull(task_ids='create_cluster_task', key='return_value') }}",
        aws_conn_id='aws_default',
    )

    create_cluster >> cluster_sensor >> start_execution >> execution_sensor >> cluster_remover

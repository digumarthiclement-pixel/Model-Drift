import boto3
import sagemaker
from sagemaker.sklearn import SKLearn
from sagemaker.model_monitor import DataCaptureConfig
import time

# Delete old endpoint if exists
client = boto3.client('sagemaker')
try:
    client.delete_endpoint(EndpointName='drift-detection-endpoint')
    print("Deleted old endpoint, waiting...")
    time.sleep(15)
except:
    print("No existing endpoint found, continuing...")

# Start session
session = sagemaker.Session()

# Your IAM Role ARN
role = "arn:aws:iam::452379802272:role/service-role/AmazonSageMaker-ExecutionRole-20260402T094405"

# Use default S3 bucket
bucket = session.default_bucket()

# Upload training data (baseline.csv)
train_input = session.upload_data(
    path='baseline.csv',
    bucket=bucket,
    key_prefix='train-data'
)

# Enable data capture (needed for drift detection)
data_capture_config = DataCaptureConfig(
    enable_capture=True,
    sampling_percentage=100,
    destination_s3_uri=f's3://{bucket}/captured-data/'
)

# Train model
estimator = SKLearn(
    entry_point='train.py',
    role=role,
    instance_count=1,
    instance_type='ml.m5.large',
    framework_version='0.23-1',
    py_version='py3'
)

estimator.fit({'train': train_input})

# Deploy endpoint
predictor = estimator.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.large',
    endpoint_name='drift-detection-endpoint',
    data_capture_config=data_capture_config
)

print(f"✅ Endpoint deployed: {predictor.endpoint_name}")
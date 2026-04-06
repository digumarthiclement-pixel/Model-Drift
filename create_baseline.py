import sagemaker
from sagemaker.model_monitor import DefaultModelMonitor
from sagemaker.model_monitor.dataset_format import DatasetFormat

# Start session
session = sagemaker.Session()

# Your IAM Role ARN
role = "arn:aws:iam::452379802272:role/service-role/AmazonSageMaker-ExecutionRole-20260402T094405"

# Use default S3 bucket
bucket = session.default_bucket()

# Create Model Monitor (using allowed instance type)
monitor = DefaultModelMonitor(
    role=role,
    instance_count=1,
    instance_type='ml.t3.large',   # ✅ FIXED (more memory)
    volume_size_in_gb=20,
    max_runtime_in_seconds=3600
)

# Run baseline job
monitor.suggest_baseline(
    baseline_dataset=f's3://{bucket}/train-data/baseline.csv',
    dataset_format=DatasetFormat.csv(header=True),
    output_s3_uri=f's3://{bucket}/baseline-results/',
    wait=True,
    logs=True
)

print("✅ Baseline created successfully!")
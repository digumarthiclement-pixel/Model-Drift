import sagemaker
from sagemaker.model_monitor import DefaultModelMonitor, CronExpressionGenerator
from sagemaker.model_monitor.dataset_format import DatasetFormat

session = sagemaker.Session()

role = "arn:aws:iam::452379802272:role/service-role/AmazonSageMaker-ExecutionRole-20260402T094405"

bucket = session.default_bucket()

monitor = DefaultModelMonitor(
    role=role,
    instance_count=1,
    instance_type='ml.t3.medium',
    volume_size_in_gb=20,
    max_runtime_in_seconds=3600
)

monitor.create_monitoring_schedule(
    monitor_schedule_name="drift-monitor-schedule",

    endpoint_input=sagemaker.model_monitor.EndpointInput(
        endpoint_name="drift-detection-endpoint",
        destination="/opt/ml/processing/input"
    ),

    output_s3_uri=f"s3://{bucket}/monitoring-results/",

    statistics=f"s3://{bucket}/baseline-results/statistics.json",
    constraints=f"s3://{bucket}/baseline-results/constraints.json",

    schedule_cron_expression=CronExpressionGenerator.daily()
)

print("✅ Monitoring schedule created!")
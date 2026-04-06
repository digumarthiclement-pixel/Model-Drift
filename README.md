# Model Drift Detection with SageMaker Model Monitor

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![AWS](https://img.shields.io/badge/AWS-SageMaker-orange?logo=amazon-aws)
![Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=amazon-aws)
![S3](https://img.shields.io/badge/AWS-S3-blue?logo=amazon-aws)
![SNS](https://img.shields.io/badge/AWS-SNS-teal?logo=amazon-aws)
![MLOps](https://img.shields.io/badge/MLOps-Project%20%2341-green)

An automated cloud system that detects when a deployed ML model starts degrading
due to data drift — and alerts you via email before it causes business damage.

---

## What is Model Drift?

Model drift occurs when the statistical properties of real-world inference data
start diverging from the training data a model was originally trained on. This
causes prediction quality to silently degrade over time — often with no error
messages or visible warnings.

**Real-world example:** A fraud detection model trained in 2022 may perform well
initially. But if fraudsters change their behaviour patterns by 2023, the model
starts missing new fraud cases without anyone noticing — until revenue takes a hit.

---

## How This System Works

```
Your App → SageMaker Endpoint → Model Monitor → S3
                                                  ↓
                              EventBridge (6am) → Lambda
                                                  ↓
                                         KS Test on Features
                                                  ↓
                                     Drift Detected? → SNS Alert → Email
```

1. **SageMaker Endpoint** serves real-time predictions 24/7
2. **Model Monitor** captures 100% of inference inputs to S3 automatically
3. **EventBridge** triggers Lambda at 6:00 AM UTC every day
4. **Lambda** runs the Kolmogorov-Smirnov test on every feature column
5. **SNS** delivers an email alert within seconds if drift is detected

---

## AWS Services Used

| Service | Purpose |
|---------|---------|
| Amazon SageMaker | Trains and hosts the ML model as a live endpoint |
| SageMaker Model Monitor | Captures all inference data and creates statistical baseline |
| Amazon S3 | Stores training data, captured data, baseline stats, reports |
| AWS Lambda | Runs drift detection code daily — serverless, no maintenance |
| Amazon SNS | Sends email/SMS alert the moment drift is detected |
| Amazon EventBridge | Triggers Lambda at 6am UTC every day automatically |

---

## Project Structure

```
drift-project/
├── train.py                    # Trains RandomForest model, generates baseline.csv
├── deploy.py                   # Uploads to S3, trains on SageMaker, deploys endpoint
├── create_baseline.py          # Statistical analysis of training data
├── schedule_monitor.py         # Creates daily SageMaker monitoring schedule
├── test_endpoint.py            # Sends normal + drifted test traffic to verify
├── baseline.csv                # Auto-generated training data (1,000 rows, 10 features)
├── drift_lambda.zip            # Auto-generated Lambda deployment package
├── .gitignore                  # Excludes credentials and cache files
├── README.md                   # This file
└── lambda_package/
    └── lambda_function.py      # KS test engine — the heart of drift detection
```

---

## Prerequisites

- Python 3.9+
- AWS Account with billing enabled
- IAM user with: SageMakerFullAccess, S3FullAccess, LambdaFullAccess, SNSFullAccess
- AWS CLI installed and configured (`aws configure`)

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/model-drift-detection.git
cd model-drift-detection
```

### 2. Install Python dependencies
```bash
pip install boto3 sagemaker scikit-learn pandas scipy numpy joblib
```

### 3. Configure AWS credentials
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region (us-east-1)
```

### 4. Create your S3 bucket
```bash
aws s3 mb s3://your-drift-detection-bucket --region us-east-1
```

### 5. Update bucket name in all files
Replace `my-drift-detection-bucket` with your actual bucket name in:
- `deploy.py`
- `create_baseline.py`
- `schedule_monitor.py`
- Lambda environment variables

---

## Running the Project

Run each file in this exact order:

```bash
# Step 1: Train and deploy the model (5–10 minutes)
python deploy.py

# Step 2: Create statistical baseline (5–10 minutes)
python create_baseline.py

# Step 3: Schedule daily monitoring
python schedule_monitor.py

# Step 4: Create SNS alert topic
aws sns create-topic --name model-drift-alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:model-drift-alerts \
  --protocol email \
  --notification-endpoint your@email.com

# Step 5: Deploy Lambda function
cd lambda_package
pip install pandas scipy numpy -t .
cd ..
zip -r drift_lambda.zip lambda_package/
aws lambda create-function \
  --function-name model-drift-detector \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/LambdaExecutionRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://drift_lambda.zip \
  --timeout 300 --memory-size 512 \
  --environment "Variables={BUCKET_NAME=your-bucket,SNS_TOPIC_ARN=your-sns-arn,KS_THRESHOLD=0.05}"

# Step 6: Schedule daily trigger
aws events put-rule --name daily-drift-check \
  --schedule-expression "cron(0 6 * * ? *)" --state ENABLED

# Step 7: Test the full pipeline
python test_endpoint.py
aws lambda invoke --function-name model-drift-detector \
  --payload '{}' --cli-binary-format raw-in-base64-out output.json
cat output.json
```

---

## How Drift Is Detected — The KS Test

The **Kolmogorov-Smirnov (KS) test** compares two distributions:

- **KS Statistic**: 0.0 = identical distributions, 1.0 = completely different
- **p-value**: < 0.05 = drift detected, > 0.05 = distributions are similar

The Lambda function runs this test independently on every feature column and
alerts if any feature's p-value falls below the configured threshold (default: 0.05).

---

## Sample Alert Email

```
Subject: [Model Drift] 2 features drifted — 2024-01-15

DRIFT ALERT — 2024-01-15
2 of 10 features (20%) have statistically significant drift:

  Feature  : feature_2
  KS Stat  : 0.7823  (0=identical, 1=completely different)
  p-value  : 0.0000009  (threshold: 0.05)

  Feature  : feature_4
  KS Stat  : 0.5241
  p-value  : 0.0032000

Recommended Action: Review drifted features. Consider retraining.
```

---

## Cleanup (Avoid AWS Charges)

```bash
# SageMaker endpoints charge ~$0.13/hr even when idle — always delete after testing!
aws sagemaker delete-monitoring-schedule --monitoring-schedule-name drift-daily-monitor
aws sagemaker delete-endpoint --endpoint-name drift-detection-endpoint
aws lambda delete-function --function-name model-drift-detector
aws events remove-targets --rule daily-drift-check --ids 1
aws events delete-rule --name daily-drift-check
```

---

## Estimated Cost

| Service | Cost |
|---------|------|
| SageMaker Endpoint | ~$0.13/hr (delete when done!) |
| Training Job | ~$0.02 total |
| Lambda (1 run/day) | Free tier |
| SNS Alerts | Free tier |
| S3 Storage | ~$0.01/month |
| **Total (1 day test)** | **~$3–5** |

---

## Tech Stack

- **Language**: Python 3.11
- **ML Library**: scikit-learn (RandomForestClassifier)
- **Statistical Test**: scipy.stats.ks_2samp
- **Cloud**: AWS (SageMaker, Lambda, S3, SNS, EventBridge)
- **SDK**: boto3, sagemaker

---

## Author

Built as MLOps Project #41 — Medium Difficulty

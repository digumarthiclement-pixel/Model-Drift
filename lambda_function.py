import json
import boto3

sns = boto3.client('sns')

TOPIC_ARN = "arn:aws:sns:us-east-1:452379802272:drift-alerts"

def lambda_handler(event, context):

    message = "⚠️ Drift detected in your ML model!"

    sns.publish(
        TopicArn=TOPIC_ARN,
        Message=message,
        Subject="Model Drift Alert 🚨"
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Alert sent!')
    }
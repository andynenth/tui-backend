#\!/bin/bash
# Setup AWS Billing Alerts

echo "Setting up billing alerts..."

# Create SNS topic for alerts
TOPIC_ARN=$(aws sns create-topic --name billing-alerts --query TopicArn --output text)

# Subscribe email
echo -n "Enter your email for billing alerts: "
read EMAIL
aws sns subscribe --topic-arn $TOPIC_ARN --protocol email --notification-endpoint $EMAIL

# Create CloudWatch alarms
for THRESHOLD in 1 5 10; do
    aws cloudwatch put-metric-alarm \
        --alarm-name "Billing-Alert-${THRESHOLD}USD" \
        --alarm-description "Alert when bill exceeds $${THRESHOLD}" \
        --metric-name EstimatedCharges \
        --namespace AWS/Billing \
        --statistic Maximum \
        --period 86400 \
        --threshold $THRESHOLD \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 1 \
        --alarm-actions $TOPIC_ARN \
        --dimensions Name=Currency,Value=USD
done

echo "Billing alerts created\! Check your email to confirm subscription."

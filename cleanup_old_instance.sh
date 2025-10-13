#!/bin/bash
# Run this AFTER confirming new t2.micro instance works

echo "This will TERMINATE the old t3.medium instance. Are you sure? (yes/no)"
read CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled"
    exit 1
fi

echo "Terminating old instance i-00f537b8ed58a15de..."
aws ec2 terminate-instances --region ap-northeast-1 --instance-ids i-00f537b8ed58a15de

echo "✅ Old instance terminated - you'll save ~$39/month!"

#!/bin/bash
# rollback.sh - Rollback to previous task definition

set -e

ECS_CLUSTER="liap-tui-cluster"
ECS_SERVICE="liap-tui-service"
ECS_TASK_FAMILY="liap-tui"

# Get current task definition revision
CURRENT_REVISION=$(aws ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE} --query 'services[0].taskDefinition' --output text | cut -d':' -f7)
PREVIOUS_REVISION=$((CURRENT_REVISION - 1))

echo "🔄 Rolling back from revision ${CURRENT_REVISION} to ${PREVIOUS_REVISION}..."

# Update service to previous revision
aws ecs update-service \
  --cluster ${ECS_CLUSTER} \
  --service ${ECS_SERVICE} \
  --task-definition ${ECS_TASK_FAMILY}:${PREVIOUS_REVISION} \
  --force-new-deployment

echo "⏳ Waiting for rollback to complete..."
aws ecs wait services-stable --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE}

echo "✅ Rollback complete!"

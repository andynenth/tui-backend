#\!/bin/bash
# Monitor AWS costs and Free Tier usage

echo "AWS Cost & Free Tier Monitor"
echo "============================"
echo "Date: $(date)"
echo ""

# Your EC2 instance details
INSTANCE_ID="i-031f0be2cfed1ff2f"
INSTANCE_START="2025-08-13"  # When you launched it

# Calculate hours used
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CURRENT_EPOCH=$(date +%s)
    START_EPOCH=$(date -j -f "%Y-%m-%d" "$INSTANCE_START" +%s 2>/dev/null || echo 0)
else
    # Linux
    CURRENT_EPOCH=$(date +%s)
    START_EPOCH=$(date -d "$INSTANCE_START" +%s)
fi

if [ "$START_EPOCH" -ne 0 ]; then
    HOURS_USED=$(( (CURRENT_EPOCH - START_EPOCH) / 3600 ))
    DAYS_USED=$(( HOURS_USED / 24 ))
    echo "EC2 Instance Usage:"
    echo "  • Instance running for: $DAYS_USED days ($HOURS_USED hours)"
    echo "  • Free tier limit: 750 hours/month"
    echo "  • Hours remaining: $(( 750 - HOURS_USED ))"
    echo "  • Days remaining at 24/7: $(( (750 - HOURS_USED) / 24 )) days"
else
    echo "Could not calculate instance hours"
fi

echo ""
echo "Free Tier Limits (per month):"
echo "  • EC2: 750 hours t2.micro ✓"
echo "  • EBS: 30 GB storage ✓"
echo "  • Data Transfer: 15 GB out ✓"
echo "  • S3: 5 GB storage, 20k GET, 2k PUT ✓"

echo ""
echo "Cost Optimization Tips:"
echo "  1. Your t2.micro can run 24/7 all month (720-744 hours < 750)"
echo "  2. Monitor data transfer if hosting public content"
echo "  3. Delete old snapshots and unattached volumes"
echo "  4. Stop instance when not needed to save hours"

echo ""
echo "To check actual AWS charges:"
echo "  Visit: https://console.aws.amazon.com/billing/"

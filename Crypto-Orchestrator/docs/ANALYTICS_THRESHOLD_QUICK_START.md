# Analytics Threshold Notification System - Quick Start Guide

## 🚀 Quick Start

Get started with analytics threshold notifications in 5 minutes!

### Step 1: Run Database Migration

```bash
cd Crypto-Orchestrator
alembic upgrade head
```

This creates the `analytics_thresholds` table in your database.

### Step 2: Start Background Worker (Optional but Recommended)

The background job automatically checks thresholds every 15 minutes. Start Celery worker:

```bash
# In a separate terminal
celery -A server_fastapi.celery_app worker --loglevel=info
celery -A server_fastapi.celery_app beat --loglevel=info
```

### Step 3: Access the UI

1. **For Marketplace Analytics:**
   - Navigate to `/admin-analytics` (admin users) or marketplace analytics page
   - Click on the **"Thresholds"** tab

2. **For Provider Analytics:**
   - Navigate to `/provider-analytics` or your provider dashboard
   - Scroll to the **"Analytics Thresholds"** section

### Step 4: Create Your First Threshold

1. Click **"Create Threshold"** button
2. Fill in the form:
   - **Name**: "Low Return Alert"
   - **Threshold Type**: "Provider"
   - **Metric**: "Total Return (%)"
   - **Operator**: "Less Than (<)"
   - **Threshold Value**: `-10` (alert when return drops below -10%)
   - **Provider ID**: Your provider ID (if applicable)
   - **Cooldown**: 60 minutes
3. Click **"Create Threshold"**

### Step 5: Test Your Threshold

1. Click the **play button (▶)** next to your threshold
2. The system will check if the condition is currently met
3. You'll see a toast notification with the result

## 📋 Common Use Cases

### Alert When Revenue Drops

**Use Case**: Get notified when your provider revenue drops below a certain amount.

**Configuration:**
- Threshold Type: `Provider`
- Metric: `Total Return (%)`
- Operator: `Less Than (<)`
- Threshold Value: `-5` (alert when return is below -5%)
- Context: `{"provider_id": YOUR_PROVIDER_ID}`

### Monitor Follower Count Changes

**Use Case**: Alert when you lose followers.

**Configuration:**
- Threshold Type: `Provider`
- Metric: `Follower Count Change`
- Operator: `Less Than (<)`
- Threshold Value: `-10` (alert when you lose 10+ followers)
- Context: `{"provider_id": YOUR_PROVIDER_ID}`

### Track Marketplace Performance

**Use Case**: Monitor overall marketplace revenue.

**Configuration:**
- Threshold Type: `Marketplace Overview`
- Metric: `Platform Revenue Drop (%)`
- Operator: `Less Than (<)`
- Threshold Value: `1000` (alert when revenue drops below $1000)

### Developer Revenue Monitoring

**Use Case**: Alert when indicator sales drop.

**Configuration:**
- Threshold Type: `Developer`
- Metric: `Revenue Drop (%)`
- Operator: `Less Than (<)`
- Threshold Value: `500` (alert when revenue drops below $500)
- Context: `{"developer_id": YOUR_DEVELOPER_ID}`

## 🎯 Best Practices

1. **Set Realistic Thresholds**: Don't set thresholds too sensitive or you'll get alert fatigue
2. **Use Cooldowns**: Set cooldown periods (60+ minutes) to prevent spam
3. **Name Your Thresholds**: Use descriptive names like "Critical Revenue Drop" or "Low Win Rate Alert"
4. **Test First**: Always test your threshold after creating it
5. **Monitor Regularly**: Check your thresholds periodically to ensure they're still relevant

## 🔧 API Usage

### Create Threshold via API

```bash
curl -X POST "http://localhost:8000/api/marketplace/analytics/thresholds" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold_type": "provider",
    "metric": "total_return",
    "operator": "lt",
    "threshold_value": -10.0,
    "context": {"provider_id": 1},
    "name": "Low Return Alert",
    "cooldown_minutes": 60
  }'
```

### List Your Thresholds

```bash
curl -X GET "http://localhost:8000/api/marketplace/analytics/thresholds" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test a Threshold

```bash
curl -X POST "http://localhost:8000/api/marketplace/analytics/thresholds/1/test" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🐛 Troubleshooting

### Threshold Not Triggering

1. **Check if enabled**: Ensure the threshold is enabled
2. **Check cooldown**: Verify the cooldown period has passed
3. **Check metric value**: Use the test function to see current metric value
4. **Check logs**: Look for errors in the application logs

### Notifications Not Sending

1. **Check notification channels**: Ensure at least one channel is enabled
2. **Check user email**: Verify user has a valid email address
3. **Check notification service**: Ensure notification service is properly configured
4. **Check logs**: Look for notification errors in logs

### Background Job Not Running

1. **Check Celery worker**: Ensure Celery worker is running
2. **Check Celery beat**: Ensure Celery beat scheduler is running
3. **Check task registration**: Verify task is registered in `celery_app.py`
4. **Check logs**: Look for task execution logs

## 📊 Monitoring

### Check Threshold Status

View all your thresholds in the UI:
- **Enabled**: Green badge - threshold is active
- **Disabled**: Gray badge - threshold is inactive
- **Last Triggered**: Shows when threshold last triggered (or "Never")

### View Triggered Alerts

When a threshold triggers:
1. You'll receive a notification (email/push/in-app)
2. The threshold's "Last Triggered" timestamp updates
3. Check application logs for detailed information

## 🔗 Related Documentation

- [Full System Documentation](./ANALYTICS_THRESHOLD_SYSTEM.md)
- [Marketplace Analytics API](../server_fastapi/routes/marketplace.py)
- [Threshold Service](../server_fastapi/services/marketplace_threshold_service.py)

## 💡 Tips

- Start with conservative thresholds and adjust based on your needs
- Use descriptive names to easily identify thresholds
- Group related thresholds by type for easier management
- Regularly review and update thresholds as your metrics change
- Use the test function to verify thresholds work before relying on them

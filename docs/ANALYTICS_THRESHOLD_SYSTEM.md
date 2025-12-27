# Analytics Threshold Notification System

## Overview

The Analytics Threshold Notification System allows users to configure alerts for marketplace analytics metrics. When metrics exceed configured thresholds, users receive notifications via email, push notifications, or in-app alerts.

## Features

- **Configurable Thresholds**: Set thresholds for various analytics metrics
- **Multiple Threshold Types**: Provider, Developer, Copy Trading, Indicator Marketplace, Marketplace Overview
- **Flexible Operators**: Greater than, less than, equals, percent change, etc.
- **Cooldown Periods**: Prevent alert fatigue with configurable cooldown periods
- **Notification Channels**: Configure email, push, and in-app notifications
- **Background Monitoring**: Automatic threshold checking every 15 minutes
- **Manual Testing**: Test thresholds on-demand

## Architecture

### Backend Components

1. **Database Model** (`models/analytics_threshold.py`)
   - `AnalyticsThreshold` model with all configuration fields
   - Supports user-specific and global thresholds
   - JSON context field for provider/developer IDs

2. **Service Layer** (`services/marketplace_threshold_service.py`)
   - `MarketplaceThresholdService` for threshold monitoring
   - Integrates with `MarketplaceAnalyticsService` for metric values
   - Integrates with `NotificationService` for alerts

3. **API Routes** (`routes/marketplace.py`)
   - `POST /api/marketplace/analytics/thresholds` - Create threshold
   - `GET /api/marketplace/analytics/thresholds` - List thresholds
   - `GET /api/marketplace/analytics/thresholds/{id}` - Get threshold
   - `PUT /api/marketplace/analytics/thresholds/{id}` - Update threshold
   - `DELETE /api/marketplace/analytics/thresholds/{id}` - Delete threshold
   - `POST /api/marketplace/analytics/thresholds/{id}/test` - Test threshold

4. **Background Job** (`tasks/marketplace_tasks.py`)
   - `check_analytics_thresholds_task` - Runs every 15 minutes
   - Checks all enabled thresholds
   - Triggers notifications when thresholds are exceeded

### Frontend Components

1. **React Component** (`components/AnalyticsThresholdManager.tsx`)
   - Full CRUD interface for threshold management
   - Form validation and error handling
   - Table view with status indicators
   - Test threshold functionality

2. **React Query Hooks** (`hooks/useMarketplace.ts`)
   - `useAnalyticsThresholds()` - List thresholds
   - `useAnalyticsThreshold()` - Get single threshold
   - `useCreateAnalyticsThreshold()` - Create threshold
   - `useUpdateAnalyticsThreshold()` - Update threshold
   - `useDeleteAnalyticsThreshold()` - Delete threshold
   - `useTestAnalyticsThreshold()` - Test threshold

3. **Integration**
   - Added to `MarketplaceAnalyticsDashboard` as a tab
   - Added to `ProviderAnalyticsDashboard` as a section

## Usage

### Creating a Threshold

1. Navigate to Analytics Dashboard
2. Click on "Thresholds" tab (Marketplace Analytics) or scroll to Thresholds section (Provider Analytics)
3. Click "Create Threshold"
4. Fill in the form:
   - **Name**: Descriptive name for the threshold
   - **Threshold Type**: Provider, Developer, Copy Trading, etc.
   - **Metric**: Select the metric to monitor
   - **Operator**: Comparison operator (>, <, =, etc.)
   - **Threshold Value**: The value to compare against
   - **Context**: Provider ID or Developer ID (if applicable)
   - **Cooldown**: Minutes between alerts
   - **Description**: Optional description
5. Click "Create Threshold"

### Testing a Threshold

1. Click the play button (▶) next to a threshold
2. The system will check if the threshold condition is currently met
3. A toast notification will show the result

### Available Metrics

**Provider Metrics:**
- Total Return (%)
- Sharpe Ratio
- Win Rate (%)
- Max Drawdown (%)
- Profit Factor
- Average Rating
- Follower Count Change

**Developer Metrics:**
- Revenue Drop (%)
- Purchase Count Change
- Average Rating

**Marketplace Metrics:**
- Platform Revenue Drop (%)
- Total Providers Change
- Total Indicators Change

## Database Migration

Run the migration to create the `analytics_thresholds` table:

```bash
alembic upgrade head
```

Migration file: `alembic/versions/20251212_add_analytics_thresholds.py`

## Testing

Comprehensive tests are available in `tests/test_analytics_thresholds.py`:

- Model tests
- Service tests (threshold evaluation)
- API tests (CRUD operations)
- Authorization tests
- Filtering tests

Run tests with:
```bash
pytest server_fastapi/tests/test_analytics_thresholds.py -v
```

## Background Job Configuration

The threshold checking job runs every 15 minutes via Celery Beat:

```python
"check-analytics-thresholds": {
    "task": "marketplace.check_analytics_thresholds",
    "schedule": 900.0,  # Every 15 minutes
}
```

## Notification Channels

Thresholds support multiple notification channels:
- **Email**: Sends email notification (requires email service)
- **Push**: Sends push notification (requires push service)
- **In-App**: Shows in-app notification (always enabled)

Configure channels when creating/editing a threshold.

## Cooldown Periods

Cooldown periods prevent alert fatigue by limiting how often a threshold can trigger. Default is 60 minutes. Once a threshold triggers, it won't trigger again until the cooldown period has passed.

## Future Enhancements

- Historical threshold trigger tracking
- Percentage change calculations with historical data
- Email templates for threshold alerts
- Webhook notifications
- Threshold groups and dependencies
- Advanced filtering and search

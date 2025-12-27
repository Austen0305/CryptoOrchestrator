# Frontend-Backend Integration Guide

## ✅ Complete Integration Status

The frontend has been fully updated to work perfectly with the enhanced backend.

## 🔄 API Integration Updates

### 1. Enhanced API Client ✅
**File**: `client/src/lib/apiEnhanced.ts`

**Features**:
- API versioning support (v1/v2)
- Request ID correlation
- Trace ID propagation
- Enhanced headers

### 2. Updated API Functions ✅
**File**: `client/src/lib/api.ts`

**New API Modules Added**:
- `webhookApi` - Webhook management
- `featureFlagsApi` - Feature flag management
- `errorRecoveryApi` - Error recovery monitoring
- `analyticsApi` - API analytics
- `monitoringApi` - Monitoring and alerts
- `securityAuditApi` - Security auditing
- `loggingApi` - Log aggregation

### 3. Enhanced Request Handling ✅
**File**: `client/src/lib/queryClient.ts`

**Updates**:
- Automatic API version header (v2)
- Request ID correlation
- Trace ID storage
- Rate limit header handling
- Response format detection (v1/v2)
- Automatic data extraction from v2 format

### 4. React Hooks for Backend Features ✅
**File**: `client/src/hooks/useBackendFeatures.ts`

**Hooks Provided**:
- `useFeatureFlags()` - Get all feature flags
- `useFeatureFlag(name)` - Check specific feature
- `useWebhooks()` - Get webhook subscriptions
- `useCreateWebhook()` - Create webhook
- `useCircuitBreakers()` - Monitor circuit breakers
- `useAnalytics()` - Get API analytics
- `useAlerts()` - Get monitoring alerts
- `useResolveAlert()` - Resolve alerts
- `useSecurityAudit()` - Run security audit
- `useLogs()` - Get logs
- `useSearchLogs()` - Search logs

### 5. Enhanced WebSocket Client ✅
**File**: `client/src/lib/websocketEnhanced.ts`

**Features**:
- Request correlation support
- Trace ID propagation
- Automatic reconnection
- Message subscription system
- Connection state management

### 6. Utility Functions ✅
**Files**:
- `client/src/utils/requestCorrelation.ts` - Request correlation utilities
- `client/src/utils/rateLimit.ts` - Rate limiting utilities

## 📋 Type Definitions

### Backend Response Types ✅
**File**: `client/src/types/backend.ts`

**Types Defined**:
- `BackendResponse<T>` - Standard v2 response format
- `BackendError` - Error response format
- `RateLimitResponse` - Rate limit error
- `HealthCheckResponse` - Health check response
- `MiddlewareStatsResponse` - Middleware statistics

## 🔌 API Usage Examples

### Feature Flags
```typescript
import { useFeatureFlag } from "@/hooks/useBackendFeatures";

function MyComponent() {
  const { data: flag, isLoading } = useFeatureFlag("ml_predictions");
  
  if (isLoading) return <div>Loading...</div>;
  
  if (flag?.enabled) {
    // Use ML predictions feature
  }
}
```

### Webhooks
```typescript
import { useWebhooks, useCreateWebhook } from "@/hooks/useBackendFeatures";

function WebhookManager() {
  const { data: webhooks } = useWebhooks(true);
  const createWebhook = useCreateWebhook();
  
  const handleSubscribe = async () => {
    await createWebhook.mutateAsync({
      url: "https://example.com/webhook",
      events: ["bot.created", "trade.executed"],
      secret: "webhook_secret",
    });
  };
  
  return (
    <div>
      {webhooks?.map(webhook => (
        <div key={webhook.id}>{webhook.url}</div>
      ))}
    </div>
  );
}
```

### Monitoring Alerts
```typescript
import { useAlerts, useResolveAlert } from "@/hooks/useBackendFeatures";

function AlertPanel() {
  const { data: alerts } = useAlerts({ resolved: false, limit: 10 });
  const resolveAlert = useResolveAlert();
  
  return (
    <div>
      {alerts?.map(alert => (
        <div key={alert.id}>
          <span>{alert.title}</span>
          <button onClick={() => resolveAlert.mutate(alert.id)}>
            Resolve
          </button>
        </div>
      ))}
    </div>
  );
}
```

### Request Correlation
```typescript
import { getCorrelationIds, formatCorrelationIds } from "@/utils/requestCorrelation";

function ErrorReport() {
  const handleError = (error: Error) => {
    const correlationIds = getCorrelationIds();
    // Include correlation IDs in error report
    console.error("Error:", error, formatCorrelationIds());
  };
}
```

### Rate Limiting
```typescript
import { getRateLimitInfo, isRateLimitLow } from "@/utils/rateLimit";

function RateLimitIndicator() {
  const info = getRateLimitInfo();
  const isLow = isRateLimitLow(0.2);
  
  return (
    <div>
      {isLow && <span>Rate limit low: {info.remaining}/{info.limit}</span>}
    </div>
  );
}
```

## 🔄 Response Format Handling

### Automatic Format Detection
The API client automatically handles both v1 and v2 response formats:

```typescript
// v1 format (direct data)
{ data: {...} }

// v2 format (with meta)
{
  success: true,
  data: {...},
  meta: {
    timestamp: "...",
    version: "2.0",
    request_id: "..."
  }
}
```

The client automatically extracts `data` from v2 format.

## 🚀 WebSocket Integration

### Enhanced WebSocket Hook
```typescript
import { useWebSocketEnhanced } from "@/hooks/useWebSocketEnhanced";

function RealTimeUpdates() {
  const { isConnected, send, subscribe } = useWebSocketEnhanced(
    "ws://localhost:8000/ws",
    {
      enabled: true,
      token: authToken,
      onConnect: () => console.log("Connected"),
      onDisconnect: () => console.log("Disconnected"),
    }
  );
  
  useEffect(() => {
    const unsubscribe = subscribe("bot.updated", (data) => {
      console.log("Bot updated:", data);
    });
    
    return unsubscribe;
  }, [subscribe]);
  
  return <div>Status: {isConnected ? "Connected" : "Disconnected"}</div>;
}
```

## 🔒 Error Handling

### Enhanced Error Handling
The API client now handles:
- New error response formats
- Validation errors
- Rate limit errors (429)
- Request correlation in errors
- Automatic token cleanup on 401/403

## 📊 Type Safety

### TypeScript Types
All new endpoints have full TypeScript type definitions:
- Webhook types
- Feature flag types
- Monitoring types
- Security audit types
- Logging types
- Analytics types

## ✅ Integration Checklist

- [x] API client updated for new endpoints
- [x] TypeScript types added
- [x] Error handling updated
- [x] Request correlation support
- [x] API versioning support
- [x] Rate limit handling
- [x] WebSocket integration
- [x] React hooks created
- [x] Utility functions added
- [x] Response format handling
- [x] All new endpoints accessible

## 🎯 Usage in Components

### Example: Feature Flag Check
```typescript
import { useFeatureFlag } from "@/hooks/useBackendFeatures";

function MLPredictionsFeature() {
  const { data: flag, isLoading } = useFeatureFlag("ml_predictions");
  
  if (isLoading) return null;
  if (!flag?.enabled) return null;
  
  return <MLPredictionsComponent />;
}
```

### Example: Monitoring Dashboard
```typescript
import { useAlerts, useAnalytics } from "@/hooks/useBackendFeatures";

function MonitoringDashboard() {
  const { data: alerts } = useAlerts({ resolved: false });
  const { data: analytics } = useAnalytics();
  
  return (
    <div>
      <h2>Alerts: {alerts?.length || 0}</h2>
      <h2>Total Requests: {analytics?.total_requests || 0}</h2>
    </div>
  );
}
```

## 🎉 Integration Complete

The frontend is now fully integrated with all backend improvements:
- ✅ All new endpoints accessible
- ✅ Type-safe API calls
- ✅ Request correlation
- ✅ Rate limit handling
- ✅ WebSocket integration
- ✅ Error handling
- ✅ Response format handling
- ✅ React hooks for all features

**Frontend and backend are perfectly integrated!** 🚀


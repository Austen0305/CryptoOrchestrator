# 📊 Performance Attribution API Endpoint Documentation

**Purpose:** API endpoint specification for Performance Attribution component  
**Status:** 📋 Specification - Ready for Implementation  
**Component:** `client/src/components/PerformanceAttribution.tsx`

---

## Endpoint Specification

### GET `/api/analytics/performance/attribution`

Returns performance attribution data including alpha/beta decomposition, factor analysis, and cumulative returns.

#### Authentication
- **Required:** Yes
- **Method:** JWT Bearer token
- **Header:** `Authorization: Bearer <token>`

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `period` | string | No | `30d` | Time period: `1d`, `7d`, `30d`, `90d`, `1y` |
| `mode` | string | No | `paper` | Trading mode: `paper`, `real` |

#### Response Format

```typescript
interface PerformanceAttributionResponse {
  attribution: AttributionData[];
  cumulativeReturns: CumulativeReturn[];
  factorAnalysis: FactorAnalysis[];
}

interface AttributionData {
  strategy: string;           // Strategy name
  alpha: number;              // Alpha (excess return)
  beta: number;               // Beta (market correlation)
  sharpe: number;             // Sharpe ratio
  informationRatio: number;   // Information ratio
  contribution: number;       // Contribution percentage (0-100)
  trades: number;             // Number of trades
  winRate: number;            // Win rate percentage (0-100)
  avgReturn: number;          // Average return percentage
}

interface CumulativeReturn {
  month: string;              // Month identifier (e.g., "Jan", "Feb")
  returns: number;            // Portfolio returns percentage
  benchmark: number;          // Benchmark returns percentage
  alpha: number;              // Alpha generation percentage
}

interface FactorAnalysis {
  factor: string;             // Factor name (e.g., "Momentum", "Value")
  exposure: number;           // Factor exposure (-1 to 1)
  contribution: number;       // Contribution percentage
  color: string;              // Display color (hex code)
}
```

#### Example Response

```json
{
  "attribution": [
    {
      "strategy": "ML Enhanced",
      "alpha": 8.5,
      "beta": 1.2,
      "sharpe": 2.1,
      "informationRatio": 1.8,
      "contribution": 45,
      "trades": 120,
      "winRate": 68,
      "avgReturn": 3.2
    }
  ],
  "cumulativeReturns": [
    {
      "month": "Jan",
      "returns": 0,
      "benchmark": 0,
      "alpha": 0
    },
    {
      "month": "Feb",
      "returns": 2.5,
      "benchmark": 1.8,
      "alpha": 0.7
    }
  ],
  "factorAnalysis": [
    {
      "factor": "Momentum",
      "exposure": 0.65,
      "contribution": 12.5,
      "color": "#8884d8"
    }
  ]
}
```

#### Error Responses

**401 Unauthorized**
```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Failed to calculate performance attribution"
}
```

---

## Implementation Notes

### Backend Implementation

1. **Route Location:** `server_fastapi/routes/analytics.py`
2. **Service:** Use `AdvancedAnalyticsEngine` for calculations
3. **Data Sources:**
   - Trade history from database
   - Strategy performance metrics
   - Market benchmark data

### Frontend Integration

The component (`PerformanceAttribution.tsx`) is already prepared:
- ✅ React Query integration ready
- ✅ Loading/error states implemented
- ✅ Mock data fallback until API ready
- ✅ TypeScript interfaces defined

When endpoint is implemented:
1. Remove mock data fallback
2. Update `queryFn` to use real API
3. Remove error catch that returns mock data

---

## Calculation Guidelines

### Alpha Calculation
- Compare portfolio returns vs benchmark
- Risk-adjusted excess return
- Formula: `Alpha = Portfolio Return - (Risk-free Rate + Beta × (Market Return - Risk-free Rate))`

### Beta Calculation
- Measure of market correlation
- Calculate from covariance/covariance of returns
- Range typically 0-2

### Sharpe Ratio
- Risk-adjusted return measure
- Formula: `(Return - Risk-free Rate) / Standard Deviation`
- Higher is better (typically 1+ is good)

### Information Ratio
- Active return per unit of tracking error
- Formula: `(Portfolio Return - Benchmark Return) / Tracking Error`
- Measures consistency of outperformance

### Factor Analysis
- Analyze risk factor exposures
- Common factors: Momentum, Value, Size, Volatility, Quality
- Calculate exposure and contribution to returns

---

## Performance Considerations

### Caching
- Cache attribution calculations (5-10 minutes)
- Cache is user-specific
- Invalidate on new trades

### Optimization
- Calculate asynchronously
- Use database aggregations
- Batch calculations for multiple strategies
- Consider materialized views for complex queries

---

## Testing

### Unit Tests
- Test calculation formulas
- Test data transformation
- Test edge cases (no trades, negative returns)

### Integration Tests
- Test with real trade data
- Test with different time periods
- Test authentication/authorization
- Test error handling

---

## Future Enhancements

### Potential Additions
- [ ] Custom time period selection
- [ ] Strategy-specific attribution
- [ ] Real-time updates via WebSocket
- [ ] Export to CSV/PDF
- [ ] Historical comparison
- [ ] Risk decomposition

---

**Status:** Ready for backend implementation. Frontend component is prepared and will automatically work when endpoint is available.


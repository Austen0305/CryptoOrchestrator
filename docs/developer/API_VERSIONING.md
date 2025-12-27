# API Versioning Guide

**Last Updated**: December 12, 2025

## Overview

This guide covers the API versioning strategy, deprecation policy, migration guides, and best practices for using CryptoOrchestrator APIs.

---

## Versioning Strategy

### URL-Based Versioning (Primary)

**Current Versions**:
- **v1** (Default): `/api/` - Stable production version
- **v2** (Beta): `/api/v2/` - Enhanced features, improved responses

**Example**:
```bash
# v1 (default)
GET /api/bots/

# v2
GET /api/v2/bots/
```

### Header-Based Versioning (Alternative)

**Headers**:
- `X-API-Version: 2.0`
- `Accept: application/vnd.cryptoorchestrator.v2+json`

**Example**:
```bash
GET /api/bots/
X-API-Version: 2.0
```

---

## Version Detection

The API automatically detects the requested version in this order:

1. **URL Path**: `/api/v2/bots/` → Uses v2
2. **X-API-Version Header**: `X-API-Version: 2.0` → Uses v2
3. **Accept Header**: `Accept: application/vnd.cryptoorchestrator.v2+json` → Uses v2
4. **Default**: `/api/bots/` → Uses v1

---

## Version Differences

### v1 Response Format

```json
{
  "success": true,
  "data": {
    "id": "bot_123",
    "name": "My Bot"
  }
}
```

### v2 Response Format

```json
{
  "success": true,
  "data": {
    "id": "bot_123",
    "name": "My Bot"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "2.0",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Key Differences**:
- v2 includes `meta` object with timestamp, version, and request_id
- v2 provides better error messages
- v2 includes pagination metadata
- v2 supports field selection

---

## Deprecation Policy

### Support Lifecycle

**Active Support**: 12 months after release
- Full feature support
- Security updates
- Bug fixes
- New features

**Deprecated**: 6 months before sunset
- Security updates only
- Critical bug fixes
- No new features
- Deprecation warnings in headers

**Sunset**: After 12 months of deprecation
- No support
- API returns 410 Gone
- Migration required

### Deprecation Timeline

| Version | Release Date | Deprecation Date | Sunset Date | Status |
|---------|-------------|------------------|-------------|--------|
| v1 | 2024-01-01 | TBD | TBD | ✅ Active |
| v2 | 2024-06-01 | TBD | TBD | 🚧 Beta |

### Deprecation Warnings

**Response Headers**:
```
X-API-Deprecated: true
X-API-Deprecation-Date: 2025-12-31
X-API-Sunset-Date: 2026-06-30
X-API-Migration-Guide: https://docs.cryptoorchestrator.com/api/migration/v1-to-v2
```

**Example**:
```python
import requests

response = requests.get("https://api.cryptoorchestrator.com/api/v1/bots/")
if response.headers.get("X-API-Deprecated") == "true":
    print(f"Warning: API version deprecated. Sunset: {response.headers.get('X-API-Sunset-Date')}")
```

---

## Migration Guides

### Migrating from v1 to v2

#### 1. Update Base URL

**Python**:
```python
# v1
BASE_URL = "https://api.cryptoorchestrator.com/api"

# v2
BASE_URL = "https://api.cryptoorchestrator.com/api/v2"
```

**JavaScript/TypeScript**:
```typescript
// v1
const BASE_URL = "https://api.cryptoorchestrator.com/api";

// v2
const BASE_URL = "https://api.cryptoorchestrator.com/api/v2";
```

#### 2. Handle Enhanced Response Format

**Python**:
```python
# v1 response handling
response = requests.get(f"{BASE_URL}/bots/", headers=headers)
bots = response.json()  # Direct array or object

# v2 response handling
response = requests.get(f"{BASE_URL}/bots/", headers=headers)
data = response.json()
bots = data["data"]  # Extract from "data" field
meta = data.get("meta", {})  # Access metadata
request_id = meta.get("request_id")  # Get request ID
```

**JavaScript/TypeScript**:
```typescript
// v1 response handling
const response = await fetch(`${BASE_URL}/bots/`, { headers });
const bots = await response.json();

// v2 response handling
const response = await fetch(`${BASE_URL}/bots/`, { headers });
const data = await response.json();
const bots = data.data;  // Extract from "data" field
const meta = data.meta;  // Access metadata
const requestId = meta?.request_id;  // Get request ID
```

#### 3. Use Request IDs for Debugging

**Python**:
```python
response = requests.get(f"{BASE_URL}/bots/", headers=headers)
data = response.json()

if not response.ok:
    request_id = data.get("meta", {}).get("request_id")
    print(f"Error - Request ID: {request_id}")
    # Include request_id in error reports
```

**JavaScript/TypeScript**:
```typescript
const response = await fetch(`${BASE_URL}/bots/`, { headers });
const data = await response.json();

if (!response.ok) {
    const requestId = data.meta?.request_id;
    console.error(`Error - Request ID: ${requestId}`);
    // Include request_id in error reports
}
```

#### 4. Handle Field Selection (v2 only)

**Python**:
```python
# v2 supports field selection
response = requests.get(
    f"{BASE_URL}/bots/",
    headers=headers,
    params={"fields": "id,name,status"}  # Only return specified fields
)
```

**JavaScript/TypeScript**:
```typescript
// v2 supports field selection
const response = await fetch(
    `${BASE_URL}/bots/?fields=id,name,status`,
    { headers }
);
```

---

## Compatibility Testing

### Automated Compatibility Checks

**Test Suite**:
```python
# tests/test_api_compatibility.py
import pytest
import requests

def test_v1_compatibility():
    """Test that v1 endpoints still work"""
    response = requests.get("https://api.cryptoorchestrator.com/api/bots/")
    assert response.status_code == 200
    assert "data" in response.json()

def test_v2_compatibility():
    """Test that v2 endpoints work"""
    response = requests.get("https://api.cryptoorchestrator.com/api/v2/bots/")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data

def test_deprecation_warnings():
    """Test deprecation warnings in headers"""
    response = requests.get("https://api.cryptoorchestrator.com/api/v1/bots/")
    # Check for deprecation headers if version is deprecated
    if response.headers.get("X-API-Deprecated") == "true":
        assert "X-API-Sunset-Date" in response.headers
```

### Manual Testing Checklist

- [ ] Test all endpoints in v1
- [ ] Test all endpoints in v2
- [ ] Verify response formats match documentation
- [ ] Check deprecation warnings (if applicable)
- [ ] Test error handling in both versions
- [ ] Verify backward compatibility

---

## Client Migration Support

### SDK Updates

**Python SDK**:
```python
from cryptoorchestrator import CryptoOrchestratorClient

# v1 client
client_v1 = CryptoOrchestratorClient(version="v1")

# v2 client (recommended)
client_v2 = CryptoOrchestratorClient(version="v2")
```

**JavaScript/TypeScript SDK**:
```typescript
import { CryptoOrchestratorClient } from '@cryptoorchestrator/sdk';

// v1 client
const clientV1 = new CryptoOrchestratorClient({ version: 'v1' });

// v2 client (recommended)
const clientV2 = new CryptoOrchestratorClient({ version: 'v2' });
```

### Migration Checklist

1. **Review Changes**: Check changelog for breaking changes
2. **Update SDK**: Use latest SDK version
3. **Test in Staging**: Test migration in staging environment
4. **Update Code**: Update API calls to new version
5. **Handle Deprecations**: Update deprecated endpoints
6. **Test Thoroughly**: Run full test suite
7. **Deploy**: Deploy to production
8. **Monitor**: Monitor for errors and deprecation warnings

---

## Best Practices

### Version Selection

1. **Use Latest Stable**: Use latest stable version for new projects
2. **Stay Updated**: Monitor deprecation notices
3. **Plan Migrations**: Plan migrations before sunset dates
4. **Test Early**: Test new versions in staging

### Error Handling

```python
import requests

def make_api_request(url, headers):
    try:
        response = requests.get(url, headers=headers)
        
        # Check for deprecation warnings
        if response.headers.get("X-API-Deprecated") == "true":
            logger.warning(
                f"API version deprecated. Sunset: {response.headers.get('X-API-Sunset-Date')}"
            )
        
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        if e.response.status_code == 410:
            # API version sunset
            logger.error("API version no longer supported. Migration required.")
        raise
```

### Request ID Tracking

```python
def make_api_request(url, headers):
    response = requests.get(url, headers=headers)
    data = response.json()
    
    # Extract request ID for support
    request_id = data.get("meta", {}).get("request_id")
    if request_id:
        logger.info(f"Request ID: {request_id}")
    
    return data
```

---

## Sunset Dates

### Current Sunset Schedule

| Version | Sunset Date | Status |
|---------|-------------|--------|
| v1 | TBD | ✅ Active |
| v2 | TBD | 🚧 Beta |

**Note**: Sunset dates are announced 6 months in advance via:
- Email notifications
- API deprecation headers
- Documentation updates
- Release notes

---

## Support

### Getting Help

- **Documentation**: https://docs.cryptoorchestrator.com/api
- **Migration Support**: support@cryptoorchestrator.com
- **GitHub Issues**: https://github.com/cryptoorchestrator/api/issues
- **Community Forum**: https://community.cryptoorchestrator.com

### Reporting Issues

When reporting API version issues, include:
- API version used
- Request ID (if available)
- Full request/response details
- Error messages
- SDK version (if applicable)

---

## Changelog

### v2.0.0 (2024-06-01)
- Added `meta` object to responses
- Added request ID tracking
- Enhanced error messages
- Field selection support
- Improved pagination

### v1.0.0 (2024-01-01)
- Initial stable release
- Core trading operations
- Market data
- Portfolio management
- Bot management
- Analytics

---

**Last Updated**: December 12, 2025

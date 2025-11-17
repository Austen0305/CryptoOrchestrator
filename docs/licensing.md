# Licensing and Monetization System

Complete guide to the Stripe payment processing and licensing system implementation in CryptoOrchestrator.

## Overview

CryptoOrchestrator implements a dual monetization system:
1. **Stripe Subscriptions** - Recurring subscription payments
2. **License Keys** - Software licensing with machine binding

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Client Application                      │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  Frontend UI │  │  Electron    │                    │
│  │  React App   │  │  Desktop App │                    │
│  └──────┬───────┘  └──────┬───────┘                    │
└─────────┼──────────────────┼────────────────────────────┘
          │                  │
          └──────────┬───────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────┐
│              FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │   Stripe     │  │  Licensing   │                    │
│  │   Service    │  │  Service     │                    │
│  └──────┬───────┘  └──────┬───────┘                    │
└─────────┼──────────────────┼────────────────────────────┘
          │                  │
          └──────────┬───────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              External Services                         │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │    Stripe    │  │  Database    │                    │
│  │    API       │  │  (Licenses)  │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## Stripe Integration

### Setup

1. **Get Stripe API Keys:**
   - Sign up at [Stripe Dashboard](https://dashboard.stripe.com/)
   - Get your API keys from the Dashboard → Developers → API keys
   - Test keys start with `sk_test_` and `pk_test_`

2. **Configure Environment Variables:**
   ```env
   STRIPE_SECRET_KEY=sk_test_your_secret_key
   STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
   ```

3. **Set Up Webhook:**
   - In Stripe Dashboard → Developers → Webhooks
   - Add endpoint: `https://yourdomain.com/api/payments/webhook`
   - Select events: `customer.subscription.*`, `invoice.payment.*`

### Subscription Tiers

```python
# Defined in server_fastapi/services/payments/stripe_service.py

PRICE_CONFIGS = {
    "free": {
        "amount": 0,
        "features": ["Basic trading", "Paper trading", "5 bots max"]
    },
    "basic": {
        "amount": 4900,  # $49.00/month
        "features": ["All Free features", "Live trading", "20 bots max"]
    },
    "pro": {
        "amount": 9900,  # $99.00/month
        "features": ["All Basic features", "Unlimited bots", "Advanced ML", "API access"]
    },
    "enterprise": {
        "amount": 29900,  # $299.00/month
        "features": ["All Pro features", "Dedicated support", "Custom integrations"]
    }
}
```

### API Endpoints

**Create Customer:**
```http
POST /api/payments/customers
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe"
}
```

**Create Subscription:**
```http
POST /api/payments/subscriptions
Authorization: Bearer <token>

{
  "tier": "pro",
  "payment_method_id": "pm_xxx"
}
```

**Webhook Handler:**
```http
POST /api/payments/webhook
X-Stripe-Signature: <signature>

{ Stripe event payload }
```

### Webhook Events Handled

- `customer.subscription.created` - New subscription
- `customer.subscription.updated` - Subscription changed
- `customer.subscription.deleted` - Subscription canceled
- `invoice.payment_succeeded` - Payment successful
- `invoice.payment_failed` - Payment failed

## Licensing System

### License Types

```python
# Defined in server_fastapi/services/licensing/license_service.py

LICENSE_CONFIG = {
    "trial": {
        "duration_days": 14,
        "max_bots": 3,
        "features": ["paper_trading", "basic_strategies"]
    },
    "basic": {
        "duration_days": None,  # No expiration
        "max_bots": 10,
        "features": ["paper_trading", "live_trading", "basic_strategies"]
    },
    "pro": {
        "duration_days": None,
        "max_bots": 100,
        "features": ["paper_trading", "live_trading", "all_strategies", "advanced_ml"]
    },
    "enterprise": {
        "duration_days": None,
        "max_bots": -1,  # Unlimited
        "features": ["all_features"]
    }
}
```

### License Key Format

```
CO-XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX
     │         │         │         │
     └─────────┴─────────┴─────────┘
          Encrypted payload
```

### Machine Binding

Licenses can be bound to a specific machine:

1. **Machine ID Generation:**
   ```python
   # Unique per machine (hardware-based)
   machine_id = generate_machine_id()  # CPU, MAC address, etc.
   ```

2. **License Activation:**
   ```http
   POST /api/licensing/activate
   Authorization: Bearer <token>

   {
     "license_key": "CO-XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX",
     "machine_id": "<machine_id>"
   }
   ```

3. **License Validation:**
   ```http
   GET /api/licensing/validate
   Authorization: Bearer <token>
   ```

### API Endpoints

**Generate License:**
```http
POST /api/licensing/generate
Authorization: Bearer <admin_token>

{
  "user_id": "123",
  "license_type": "pro",
  "expires_at": null
}
```

**Activate License:**
```http
POST /api/licensing/activate

{
  "license_key": "CO-XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX",
  "machine_id": "<machine_id>"
}
```

**Validate License:**
```http
GET /api/licensing/validate
Authorization: Bearer <token>
```

**Check Features:**
```http
GET /api/licensing/features
Authorization: Bearer <token>
```

## Demo Mode

Demo mode provides a feature-limited version:

```python
# Defined in server_fastapi/services/licensing/demo_mode.py

FEATURE_FLAGS = {
    "live_trading": {"enabled": False, "message": "Upgrade to Basic"},
    "advanced_ml": {"enabled": False, "message": "Upgrade to Pro"},
    "api_access": {"enabled": False, "message": "Upgrade to Pro"},
    "unlimited_bots": {"enabled": False, "message": "Upgrade to Pro"}
}
```

## Integration Flow

### User Registration → Subscription

```
1. User registers account
2. User selects subscription tier
3. Frontend calls Stripe to create payment intent
4. User completes payment
5. Stripe sends webhook to backend
6. Backend creates subscription record
7. Backend generates license key
8. User activates license on device
```

### License Validation Flow

```
1. Application startup
2. Check for existing license
3. If no license → show demo mode
4. If license exists → validate:
   - Check expiration
   - Verify machine binding
   - Check features
5. Enable features based on license tier
```

## Security Considerations

1. **API Keys:**
   - Never commit keys to version control
   - Use environment variables
   - Rotate keys regularly

2. **Webhook Signatures:**
   - Always verify Stripe webhook signatures
   - Store webhook secret securely

3. **License Keys:**
   - Encrypt license payload
   - Use secure random generation
   - Implement expiration checks

4. **Machine Binding:**
   - Use hardware-based machine IDs
   - Allow re-activation with admin approval
   - Log all activation attempts

## Environment Variables

```env
# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Licensing
LICENSE_SECRET_KEY=<32-byte-hex-string>

# Feature Flags
ENABLE_DEMO_MODE=true
DEMO_MODE_MAX_BOTS=3
```

## Testing

### Stripe Test Mode

```bash
# Use test API keys
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx

# Use Stripe CLI for webhook testing
stripe listen --forward-to http://localhost:8000/api/payments/webhook
stripe trigger customer.subscription.created
```

### License Testing

```python
# Generate test license
python -c "
from server_fastapi.services.licensing.license_service import LicenseService
service = LicenseService()
key = service.generate_license_key('test_user', 'pro')
print(key)
"
```

## Troubleshooting

### Common Issues

**Webhook Not Receiving Events:**
- Check webhook URL is accessible
- Verify webhook secret matches
- Check Stripe Dashboard → Webhooks → Events

**License Validation Fails:**
- Check license hasn't expired
- Verify machine_id matches
- Check license database record

**Subscription Not Activating:**
- Verify payment succeeded
- Check webhook was received
- Review server logs

## Related Documentation

- [API Reference](api.md) - Complete API documentation
- [Deployment Guide](deployment.md) - Production setup
- [Stripe Documentation](https://stripe.com/docs) - Official Stripe docs


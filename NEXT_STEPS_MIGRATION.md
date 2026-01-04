# Next Steps: Complete Migration to Free Services

## ✅ Completed
- [x] Created free crypto price service (CoinLore API)
- [x] Created free subscription service
- [x] Updated MCP configuration (removed CoinGecko & Stripe)
- [x] Updated environment files
- [x] Removed Stripe from requirements.txt

## 🔧 Required Next Steps

### 1. Update Backend Routes (HIGH PRIORITY)

**File:** `server_fastapi/routes/billing.py`
- Update to use `free_subscription_service` instead of `stripe_service`
- Modify checkout endpoint to immediately create subscription (no payment needed)
- Update portal endpoint to return billing page URL

**File:** `server_fastapi/routes/payments.py`
- Update all endpoints to use `free_subscription_service`
- Remove Stripe-specific webhook handling
- Simplify subscription creation (no payment method needed)

**File:** `server_fastapi/billing/subscription_service.py`
- Update import from `stripe_service` to `free_subscription_service`
- Remove Stripe-specific logic

### 2. Update Frontend (MEDIUM PRIORITY)

**File:** `client/src/pages/Billing.tsx`
- Remove references to `stripe_price_id_monthly` and `stripe_price_id_yearly`
- Update checkout flow to handle free subscriptions (no redirect to Stripe)
- Show "Free" or "$0" for all plans
- Update UI to indicate all plans are free

**File:** `client/src/hooks/usePayments.ts`
- Update checkout to handle free subscriptions (no Stripe redirect)
- Simplify flow - subscriptions activate immediately

**File:** `client/src/components/PricingPlans.tsx`
- Remove Stripe references
- Update to show all plans as free
- Update subscription button text

**File:** `client/src/components/PaymentMethods.tsx`
- Either remove this component or update to show "No payment methods needed - all subscriptions are free"

### 3. Test the New Services (HIGH PRIORITY)

**Test Crypto Price Service:**
```python
# Test script
from server_fastapi.services.crypto_price_service import get_crypto_price_service

service = get_crypto_price_service()
price = await service.get_price("BTC/USD")
print(f"BTC Price: ${price}")
```

**Test Free Subscription Service:**
```python
# Test script
from server_fastapi.services.payments.free_subscription_service import free_subscription_service

customer = free_subscription_service.create_customer("test@example.com")
subscription = free_subscription_service.create_subscription(
    customer["id"], 
    tier=SubscriptionTier.PRO
)
print(f"Subscription: {subscription}")
```

### 4. Update Database (OPTIONAL)

The database schema can stay as-is since Stripe fields are nullable. However, you may want to:

- Add a migration to set all existing subscriptions to "active" and "free" tier
- Update any existing subscriptions to use the free service

### 5. Update Documentation

**Files to update:**
- `docs/guides/API_KEYS_SETUP.md` - Remove CoinGecko and Stripe sections
- `docs/core/LOCAL_DEVELOPMENT.md` - Update price service info
- `README.md` - Update setup instructions
- Any deployment guides

### 6. Clean Up (LOW PRIORITY)

- Remove unused Stripe imports if any remain
- Update comments that reference Stripe
- Remove Stripe webhook endpoints (or keep for backward compatibility)
- Update error messages that mention Stripe

## 🚀 Quick Start Guide

### Immediate Actions:

1. **Test the new services work:**
   ```bash
   # Start your backend
   python -m server_fastapi.main
   
   # Test crypto prices endpoint
   curl http://localhost:8000/api/markets/price/BTC/USD
   
   # Test subscription endpoint
   curl http://localhost:8000/api/billing/plans
   ```

2. **Update billing routes:**
   - Open `server_fastapi/routes/billing.py`
   - Replace `stripe_service` with `free_subscription_service`
   - Update checkout to create subscription immediately

3. **Update frontend:**
   - Open `client/src/pages/Billing.tsx`
   - Remove Stripe checkout redirect
   - Show "Activate Free Plan" button instead

## ⚠️ Important Notes

1. **Backward Compatibility:** The old service classes (`CoinGeckoService`, `StripeService`) still exist as wrappers, so existing code won't break immediately.

2. **Database:** Stripe fields in the database are nullable, so existing data won't break. You can migrate existing subscriptions later.

3. **Frontend:** The frontend will need updates to remove Stripe checkout flows, but the API endpoints can be updated first.

4. **Testing:** Test thoroughly before deploying to production, especially:
   - Subscription creation
   - Subscription upgrades/downgrades
   - Price fetching for various cryptocurrencies

## 📋 Checklist

- [ ] Update `server_fastapi/routes/billing.py`
- [ ] Update `server_fastapi/routes/payments.py`
- [ ] Update `server_fastapi/billing/subscription_service.py`
- [ ] Update `client/src/pages/Billing.tsx`
- [ ] Update `client/src/hooks/usePayments.ts`
- [ ] Update `client/src/components/PricingPlans.tsx`
- [ ] Test crypto price service
- [ ] Test subscription service
- [ ] Test full subscription flow (create, upgrade, cancel)
- [ ] Update documentation
- [ ] Deploy and verify

## 🆘 Need Help?

If you encounter issues:
1. Check `MIGRATION_TO_FREE_SERVICES.md` for migration details
2. Verify the new services are imported correctly
3. Check that backward compatibility wrappers are working
4. Test each service individually before integrating

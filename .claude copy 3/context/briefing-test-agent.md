# Test Agent Briefing
## Stripe Integration Testing Guide

**Components to Test:** 4 API routes, 1 middleware, 1 client page
**Testing Environment:** Development with Stripe test mode

---

## TEST SCOPE

### Critical Path Testing (Must Pass)

1. **Unauthenticated Access Protection**
2. **Checkout Session Creation**
3. **Webhook Event Processing**
4. **Subscription Status Checks**
5. **Portal Session Creation**

---

## TEST CASES

### TC-001: Unauthenticated User Redirect
**Endpoint:** `/` (landing page)
**Expected:** Redirect to `/auth`
**Verification:**
```bash
curl -I http://localhost:3000/
# Expected: 307 redirect to /auth
```

### TC-002: Unauthenticated API Access
**Endpoint:** `POST /api/generate`
**Expected:** 401 Unauthorized
**Verification:**
```bash
curl -X POST http://localhost:3000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"imageBase64": "test"}'
# Expected: {"error": "Unauthorized - Please sign in"}
```

### TC-003: Checkout Session Creation (Authenticated)
**Endpoint:** `POST /api/create-checkout-session`
**Requires:** Valid Supabase access token
**Expected:** JSON with `url` field pointing to Stripe checkout
**Verification:**
```bash
curl -X POST http://localhost:3000/api/create-checkout-session \
  -H "Authorization: Bearer <access_token>"
# Expected: {"url": "https://checkout.stripe.com/..."}
```

### TC-004: Checkout Session - No Auth
**Endpoint:** `POST /api/create-checkout-session`
**Expected:** 401 Unauthorized
**Verification:**
```bash
curl -X POST http://localhost:3000/api/create-checkout-session
# Expected: {"error": "Unauthorized"}
```

### TC-005: Webhook - Valid Signature
**Endpoint:** `POST /api/webhooks`
**Requires:** Valid Stripe signature
**Expected:** 200 with `{"received": true}`
**Test with Stripe CLI:**
```bash
stripe listen --forward-to localhost:3000/api/webhooks
stripe trigger checkout.session.completed
```

### TC-006: Webhook - Invalid Signature
**Endpoint:** `POST /api/webhooks`
**Expected:** 400 Bad Request
**Verification:**
```bash
curl -X POST http://localhost:3000/api/webhooks \
  -H "stripe-signature: invalid_sig" \
  -d '{"type": "test"}'
# Expected: {"error": "Invalid signature"}
```

### TC-007: Webhook - Missing Signature
**Endpoint:** `POST /api/webhooks`
**Expected:** 400 Bad Request
**Verification:**
```bash
curl -X POST http://localhost:3000/api/webhooks \
  -d '{"type": "test"}'
# Expected: {"error": "Missing signature"}
```

### TC-008: Portal Session - With Subscription
**Endpoint:** `POST /api/portal`
**Requires:** User with existing subscription
**Expected:** JSON with `url` field pointing to Stripe portal

### TC-009: Portal Session - No Subscription
**Endpoint:** `POST /api/portal`
**Requires:** User without subscription record
**Expected:** 404 with `{"error": "No subscription found"}`

### TC-010: Subscription Status Check - Active
**Function:** `hasActiveSubscription()`
**Setup:** User with `status = 'active'`
**Expected:** Returns `true`

### TC-011: Subscription Status Check - Canceled (In Period)
**Function:** `hasActiveSubscription()`
**Setup:** User with `status = 'canceled'`, `current_period_end` in future
**Expected:** Returns `true`

### TC-012: Subscription Status Check - Canceled (Expired)
**Function:** `hasActiveSubscription()`
**Setup:** User with `status = 'canceled'`, `current_period_end` in past
**Expected:** Returns `false`

### TC-013: Subscription Status Check - Past Due (Grace Period)
**Function:** `hasActiveSubscription()`
**Setup:** User with `status = 'past_due'`, `current_period_end` + 3 days in future
**Expected:** Returns `true`

### TC-014: Generate API - With Active Subscription
**Endpoint:** `POST /api/generate`
**Requires:** User with active subscription + valid image
**Expected:** 200 with generated images

### TC-015: Generate API - Without Subscription
**Endpoint:** `POST /api/generate`
**Requires:** Authenticated user without subscription
**Expected:** 403 with `{"error": "Active subscription required", "redirect": "/auth"}`

---

## STRIPE TEST DATA

### Test Cards
| Card Number | Result |
|-------------|--------|
| 4242424242424242 | Success |
| 4000000000000002 | Decline |
| 4000002500003155 | 3D Secure required |

### Stripe CLI Commands
```bash
# Start webhook forwarding
stripe listen --forward-to localhost:3000/api/webhooks

# Trigger test events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.updated
stripe trigger customer.subscription.deleted
stripe trigger invoice.payment_failed
```

---

## DATABASE VERIFICATION QUERIES

### Check Subscription Created
```sql
SELECT * FROM subscriptions
WHERE user_id = '<supabase_user_id>'
ORDER BY created_at DESC
LIMIT 1;
```

### Check Subscription Status Updated
```sql
SELECT status, current_period_end, updated_at
FROM subscriptions
WHERE stripe_subscription_id = '<sub_xxx>';
```

---

## KNOWN TESTING CHALLENGES

1. **Webhook Testing Requires Stripe CLI**
   - Cannot test webhooks via simple curl due to signature verification
   - Use `stripe listen` for local development

2. **Session Tokens Expire**
   - Supabase access tokens have limited lifetime
   - May need to refresh during extended testing

3. **Rate Limits**
   - Stripe test mode has rate limits
   - Avoid rapid-fire testing

---

## ACCEPTANCE CRITERIA

All of the following must pass:
- [ ] TC-001 through TC-015 pass
- [ ] No console errors during webhook processing
- [ ] Subscription record created within 5s of checkout completion
- [ ] User can access `/` after successful payment
- [ ] User redirected to `/auth` without active subscription

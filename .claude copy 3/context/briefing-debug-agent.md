# Debug Agent Briefing
## Stripe Integration - Common Issues and Solutions

**Focus Areas:** Webhook failures, Auth errors, Subscription state issues
**Key Files:** 6 files across `app/api/` and `app/lib/`

---

## COMMON ISSUES CHECKLIST

### Issue 1: Webhook Signature Verification Fails

**Symptoms:**
- Webhook returns 400 "Invalid signature"
- Console shows "Webhook signature verification failed"
- Subscriptions not activating after payment

**Causes:**
1. Wrong `STRIPE_WEBHOOK_SECRET` value
2. Request body modified before verification (e.g., JSON parsing)
3. Using test webhook secret in production (or vice versa)

**Solutions:**
```typescript
// CORRECT: Read raw body FIRST
const body = await request.text();  // RAW text, not JSON
const signature = request.headers.get('stripe-signature');

// WRONG: This breaks signature
const body = await request.json();  // Parsed - signature will fail!
```

**Verification:**
```bash
# Get the correct webhook secret
stripe listen --print-secret

# Compare with your .env.local
echo $STRIPE_WEBHOOK_SECRET
```

---

### Issue 2: Supabase User Not Found in Webhook

**Symptoms:**
- Webhook succeeds but subscription not created
- Error: "Missing user_id in metadata"

**Causes:**
1. `supabase_user_id` not included in checkout session metadata
2. Metadata key misspelled

**Solution Check:**
```typescript
// In create-checkout-session/route.ts, verify:
const session = await stripe.checkout.sessions.create({
  // ...
  metadata: {
    supabase_user_id: user.id,  // Must be present
  },
  subscription_data: {
    metadata: {
      supabase_user_id: user.id,  // Also here for subscription events
    },
  },
});
```

---

### Issue 3: Auth Callback Import Error

**Symptoms:**
- Error: "Cannot use supabase client in server component"
- Auth callback fails silently
- Users stuck in auth loop

**Root Cause:**
`app/auth/callback/route.ts` imports client-side Supabase:
```typescript
// WRONG - line 3
import { supabase } from '@/app/lib/supabaseClient';
```

**Fix:**
```typescript
// CORRECT
import { createClient } from '@/app/lib/supabase-server';

export async function GET(request: NextRequest) {
  const supabase = await createClient();
  // ...
}
```

---

### Issue 4: Middleware Subscription Query Fails

**Symptoms:**
- Users with subscriptions still redirected to /auth
- Middleware logs show null subscription

**Causes:**
1. Supabase RLS blocking the query
2. Cookie not being sent properly
3. User ID mismatch

**Debug Steps:**
```typescript
// Add logging to middleware.ts
console.log('User:', user?.id);
console.log('Subscription query result:', subscription);
console.log('Has active:', hasActiveSubscription);
```

**RLS Policy Check:**
```sql
-- Ensure this policy exists
CREATE POLICY "Users can view own subscription" ON subscriptions
  FOR SELECT USING (auth.uid() = user_id);
```

---

### Issue 5: Access Token Not Passed to API Routes

**Symptoms:**
- API returns 401 despite user being logged in
- Works in browser but fails in programmatic calls

**Cause:**
Missing `Authorization` header in fetch calls.

**Fix in Client Code:**
```typescript
const { data: sessionData } = await supabase.auth.getSession();

const response = await fetch('/api/create-checkout-session', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${sessionData.session?.access_token}`,
  },
});
```

---

### Issue 6: Stripe Customer Created But Not Linked

**Symptoms:**
- Stripe shows customer created
- Supabase has no subscription record
- Portal returns "No subscription found"

**Cause:**
Webhook failed or customer ID not saved.

**Debug Query:**
```sql
-- Check if customer ID exists
SELECT stripe_customer_id FROM subscriptions
WHERE user_id = '<user_id>';
```

**Stripe Dashboard Check:**
1. Go to Customers > [Customer] > Metadata
2. Verify `supabase_user_id` is present

---

### Issue 7: Past Due Status Not Handled

**Symptoms:**
- Payment fails but user still has access
- Or: User loses access immediately on first failure

**Expected Behavior:**
3-day grace period for `past_due` status.

**Code Location:**
`app/lib/subscription.ts` lines 29-34:
```typescript
if (data.status === 'past_due' && data.current_period_end) {
  const gracePeriod = new Date(data.current_period_end);
  gracePeriod.setDate(gracePeriod.getDate() + 3);
  return gracePeriod > new Date();
}
```

---

### Issue 8: Checkout Redirect URL Wrong

**Symptoms:**
- After payment, user lands on wrong page
- Or: Redirect fails with invalid URL

**Config Check:**
```typescript
// In create-checkout-session/route.ts
success_url: `${process.env.NEXT_PUBLIC_APP_URL}/auth?success=true`,
cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/auth?canceled=true`,
```

**Environment Check:**
```bash
# Verify this is set correctly
echo $NEXT_PUBLIC_APP_URL
# Should be: http://localhost:3000 (dev) or https://yourdomain.com (prod)
```

---

## DEBUGGING TOOLS

### Stripe CLI
```bash
# Listen to webhooks locally
stripe listen --forward-to localhost:3000/api/webhooks

# View recent events
stripe events list --limit 10

# Trigger test event
stripe trigger checkout.session.completed
```

### Supabase Logs
```sql
-- Check auth.users for user existence
SELECT id, email, created_at FROM auth.users
WHERE email = 'test@example.com';

-- Check subscriptions table
SELECT * FROM subscriptions ORDER BY created_at DESC LIMIT 5;
```

### Next.js Debug Mode
```bash
# Run with verbose logging
DEBUG=* npm run dev
```

---

## ERROR CODE REFERENCE

| HTTP Code | Location | Meaning |
|-----------|----------|---------|
| 400 | /api/webhooks | Invalid or missing Stripe signature |
| 401 | Any API route | Missing or invalid auth token |
| 403 | /api/generate | No active subscription |
| 404 | /api/portal | No subscription record for user |
| 500 | Any | Internal error (check console logs) |

---

## QUICK FIXES

### Force Subscription Activation (Dev Only)
```sql
INSERT INTO subscriptions (user_id, stripe_customer_id, status, current_period_end)
VALUES (
  '<supabase_user_id>',
  'cus_test123',
  'active',
  NOW() + INTERVAL '30 days'
);
```

### Reset Subscription State
```sql
DELETE FROM subscriptions WHERE user_id = '<user_id>';
```

### Check Current State
```sql
SELECT
  u.email,
  s.status,
  s.stripe_customer_id,
  s.current_period_end
FROM auth.users u
LEFT JOIN subscriptions s ON u.id = s.user_id
WHERE u.email = 'test@example.com';
```

---

## ESCALATION TRIGGERS

Escalate to senior review if:
1. Webhook signature fails with correct secret
2. Supabase RLS policies seem correct but queries return null
3. Stripe events show success but database not updated
4. Multiple users reporting same issue

# Stripe Integration Context Document
## YachtGenius - Payment System Implementation

**Document Version:** 1.0.0
**Last Updated:** 2025-12-17
**Status:** In Progress - Missing Critical Components

---

## 1. EXECUTIVE SUMMARY

### Current State
The Stripe payment integration for YachtGenius is **partially implemented**. Core API routes exist but the critical **webhook handler is missing**, which means subscription status updates from Stripe cannot be processed.

### Architecture Overview
```
User Flow:
[Auth Page] -> [Sign Up/In] -> [Payment Mode] -> [Stripe Checkout] -> [Webhook] -> [DB Update] -> [Access Granted]
                                                         ^                  ^
                                                         |                  |
                                                   IMPLEMENTED          MISSING!
```

### Critical Gap
**The webhook handler (`/api/webhooks/route.ts`) does not exist.** This is a blocking issue that prevents:
- Subscription activation after successful payment
- Subscription cancellation processing
- Payment failure handling
- Subscription renewal tracking

---

## 2. COMPONENT STATUS MATRIX

| Component | File Path | Status | Notes |
|-----------|-----------|--------|-------|
| Stripe Client | `app/lib/stripe.ts` | COMPLETE | Uses API version 2024-11-20.acacia |
| Subscription Helper | `app/lib/subscription.ts` | COMPLETE | Handles active/canceled/past_due states |
| Supabase Server Client | `app/lib/supabase-server.ts` | COMPLETE | Async cookies API for Next.js 16+ |
| Auth Middleware | `middleware.ts` | COMPLETE | Protects `/` and `/api/generate` |
| Checkout Session API | `app/api/create-checkout-session/route.ts` | COMPLETE | Creates Stripe checkout sessions |
| Portal API | `app/api/portal/route.ts` | COMPLETE | Creates customer portal sessions |
| Webhook Handler | `app/api/webhooks/route.ts` | **MISSING** | Critical gap |
| Auth Callback | `app/auth/callback/route.ts` | HAS BUG | Uses client-side supabase import |
| Auth Page | `app/auth/page.tsx` | COMPLETE | Includes payment mode UI |

---

## 3. DATABASE SCHEMA REQUIREMENTS

### Supabase Table: `subscriptions`

The code expects this schema (inferred from implementation):

```sql
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_customer_id TEXT NOT NULL,
  stripe_subscription_id TEXT,
  status TEXT NOT NULL, -- 'active', 'canceled', 'past_due', 'trialing', 'incomplete'
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT unique_user_subscription UNIQUE (user_id)
);

-- RLS Policies needed
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own subscription" ON subscriptions
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all" ON subscriptions
  FOR ALL USING (auth.role() = 'service_role');
```

---

## 4. ENVIRONMENT VARIABLES

### Required (Server-side)
```env
STRIPE_SECRET_KEY=sk_test_...           # Stripe secret key
STRIPE_WEBHOOK_SECRET=whsec_...         # Webhook signing secret (MISSING!)
SUPABASE_SERVICE_ROLE_KEY=eyJ...        # For server-side DB operations
```

### Required (Client-side / Public)
```env
NEXT_PUBLIC_STRIPE_PRICE_ID=price_...   # Subscription price ID
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

---

## 5. CRITICAL DECISIONS NEEDED

### Decision 1: Webhook Events to Handle
**Question:** Which Stripe webhook events should be processed?

**Recommended Events:**
1. `checkout.session.completed` - Initial subscription created
2. `customer.subscription.updated` - Status changes (renewal, changes)
3. `customer.subscription.deleted` - Subscription canceled
4. `invoice.payment_succeeded` - Successful payment (for tracking)
5. `invoice.payment_failed` - Payment failure (trigger grace period)

### Decision 2: Grace Period Policy
**Current Implementation:** 3-day grace period for `past_due` status
**Question:** Is this acceptable, or should it be configurable?

### Decision 3: Price Configuration
**Question:** Is there a single subscription tier at 12EUR/month, or are there multiple tiers planned?
**Current:** Single tier assumed based on auth page UI

### Decision 4: Trial Period
**Question:** Should there be a free trial period?
**Current:** No trial period implemented

---

## 6. DEPENDENCIES MAP

```
middleware.ts
    |
    +---> app/lib/supabase-server.ts (createClient)
    |         |
    |         +---> @supabase/ssr
    |
    +---> supabase.from('subscriptions') [direct query]

app/api/create-checkout-session/route.ts
    |
    +---> app/lib/stripe.ts (stripe client)
    |         |
    |         +---> stripe (npm package v20.1.0)
    |
    +---> app/lib/supabase-server.ts

app/api/generate/route.ts
    |
    +---> app/lib/supabase-server.ts
    +---> app/lib/subscription.ts (hasActiveSubscription)
    +---> @google/genai (Gemini AI)

app/auth/page.tsx
    |
    +---> app/lib/supabaseClient.ts (client-side)
    +---> /api/create-checkout-session (fetch)

app/auth/callback/route.ts  [BUG: uses client-side import]
    |
    +---> app/lib/supabaseClient.ts (WRONG - should use server client)
```

---

## 7. KNOWN ISSUES

### Issue 1: Missing Webhook Handler (CRITICAL)
**File:** `app/api/webhooks/route.ts`
**Impact:** Subscriptions cannot be activated after Stripe payment
**Solution:** Create webhook handler with signature verification

### Issue 2: Auth Callback Uses Wrong Supabase Client
**File:** `app/auth/callback/route.ts` (line 3)
**Current:** `import { supabase } from '@/app/lib/supabaseClient';`
**Problem:** Uses client-side Supabase in a server route
**Solution:** Use `createClient` from `app/lib/supabase-server.ts`

### Issue 3: No Subscription Record Creation on Checkout
**Problem:** When a user checks out, no initial subscription record is created
**Current Flow:** Relies entirely on webhook to create record
**Risk:** If webhook fails, user is stuck in limbo
**Mitigation:** Auth page polls for subscription, but timeout is 30s

---

## 8. IMPLEMENTATION PRIORITY

1. **P0 (Blocking):** Create webhook handler
2. **P1 (High):** Fix auth callback import
3. **P2 (Medium):** Add error handling for webhook failures
4. **P3 (Low):** Add subscription management UI (cancel, upgrade)

---

## 9. QUICK CONTEXT (< 500 tokens)

**Current Task:** Complete Stripe payment integration
**Immediate Goal:** Create webhook handler to process subscription events
**Recent Decisions:** Using Stripe API 2024-11-20.acacia, 3-day grace period for past_due
**Active Blockers:** Missing webhook handler prevents subscription activation
**Dependencies:** Supabase `subscriptions` table must exist with proper schema

---

## 10. ARCHIVED PATTERNS

### Pattern: Bearer Token Authentication
All API routes use consistent auth pattern:
```typescript
const authHeader = request.headers.get('authorization');
const accessToken = authHeader?.toLowerCase().startsWith('bearer ')
  ? authHeader.slice(7)
  : undefined;
```

### Pattern: Subscription Status Check
Three valid states for access:
1. `status === 'active'`
2. `status === 'canceled' && current_period_end > now`
3. `status === 'past_due' && current_period_end + 3 days > now`

### Pattern: Supabase User ID Linking
Stripe metadata always includes `supabase_user_id` for:
- Customer creation
- Checkout session
- Subscription data

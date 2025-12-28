# Implementation Agent Briefing
## Stripe Webhook Handler Implementation

**Priority:** P0 - Critical Blocker
**Estimated Effort:** 2-3 hours
**Files to Create/Modify:** 2

---

## YOUR TASK

Create the missing Stripe webhook handler at `app/api/webhooks/route.ts` and fix a bug in `app/auth/callback/route.ts`.

---

## TASK 1: Create Webhook Handler

### Location
`D:\Projects\yachtinterior\app\api\webhooks\route.ts`

### Requirements

1. **Verify Stripe Signature**
   - Use `stripe.webhooks.constructEvent()` with `STRIPE_WEBHOOK_SECRET`
   - Return 400 if signature invalid

2. **Handle These Events:**
   - `checkout.session.completed` - Create/activate subscription
   - `customer.subscription.updated` - Update subscription status
   - `customer.subscription.deleted` - Mark as canceled
   - `invoice.payment_failed` - Update status to past_due

3. **Database Operations:**
   - Use `upsertSubscription()` from `app/lib/subscription.ts`
   - Extract `supabase_user_id` from metadata

### Code Template
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { stripe } from '@/app/lib/stripe';
import { upsertSubscription } from '@/app/lib/subscription';
import Stripe from 'stripe';

export async function POST(request: NextRequest) {
  const body = await request.text();
  const signature = request.headers.get('stripe-signature');

  if (!signature) {
    return NextResponse.json({ error: 'Missing signature' }, { status: 400 });
  }

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }

  // Handle events here...

  return NextResponse.json({ received: true });
}
```

### Event Handling Logic

**checkout.session.completed:**
```typescript
const session = event.data.object as Stripe.Checkout.Session;
const userId = session.metadata?.supabase_user_id;
const customerId = session.customer as string;
const subscriptionId = session.subscription as string;

// Fetch full subscription details
const subscription = await stripe.subscriptions.retrieve(subscriptionId);

await upsertSubscription(userId, customerId, {
  stripe_subscription_id: subscriptionId,
  status: subscription.status,
  current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
  cancel_at_period_end: subscription.cancel_at_period_end,
});
```

---

## TASK 2: Fix Auth Callback Import

### Location
`D:\Projects\yachtinterior\app\auth\callback\route.ts`

### Current Code (BROKEN)
```typescript
import { supabase } from '@/app/lib/supabaseClient';
```

### Fixed Code
```typescript
import { createClient } from '@/app/lib/supabase-server';

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get('code');

  if (code) {
    const supabase = await createClient();
    await supabase.auth.exchangeCodeForSession(code);
  }

  return NextResponse.redirect(new URL('/auth', request.url));
}
```

**Note:** Redirect to `/auth` instead of `/` so user can complete subscription if needed.

---

## EXISTING CODE REFERENCES

### Stripe Client (`app/lib/stripe.ts`)
```typescript
import Stripe from 'stripe';
export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-11-20.acacia',
  typescript: true,
});
```

### Upsert Function (`app/lib/subscription.ts`)
```typescript
export async function upsertSubscription(
  userId: string,
  stripeCustomerId: string,
  subscriptionData: any
)
```

---

## ENVIRONMENT VARIABLE NEEDED

Add to `.env.local`:
```
STRIPE_WEBHOOK_SECRET=whsec_...
```

Get this from Stripe Dashboard > Developers > Webhooks > Add endpoint > Signing secret

---

## VERIFICATION CHECKLIST

After implementation:
- [ ] Webhook returns 200 for valid signatures
- [ ] Webhook returns 400 for invalid signatures
- [ ] `checkout.session.completed` creates subscription record
- [ ] `customer.subscription.updated` updates status
- [ ] `customer.subscription.deleted` marks as canceled
- [ ] Auth callback uses server-side Supabase client

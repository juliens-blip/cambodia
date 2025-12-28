# Context Index
## YachtGenius Stripe Integration

**Last Updated:** 2025-12-17
**Project:** Stripe Payment Integration for YachtGenius
**Branch:** main (uncommitted changes)

---

## QUICK LINKS

| Document | Purpose | Token Size |
|----------|---------|------------|
| [stripe-integration-context.md](./stripe-integration-context.md) | Full context | ~2000 |
| [briefing-implementation-agent.md](./briefing-implementation-agent.md) | What to build | ~800 |
| [briefing-test-agent.md](./briefing-test-agent.md) | What to verify | ~900 |
| [briefing-debug-agent.md](./briefing-debug-agent.md) | Common issues | ~1000 |

---

## CURRENT STATUS

**Phase:** Implementation
**Blocking Issue:** Missing webhook handler
**Next Action:** Create `app/api/webhooks/route.ts`

---

## FILE MAP

### Implemented (Ready)
- `app/lib/stripe.ts` - Stripe client initialization
- `app/lib/subscription.ts` - Subscription status helpers
- `app/lib/supabase-server.ts` - Server-side Supabase client
- `app/api/create-checkout-session/route.ts` - Checkout API
- `app/api/portal/route.ts` - Customer portal API
- `middleware.ts` - Route protection
- `app/auth/page.tsx` - Auth + payment UI

### Missing (To Create)
- `app/api/webhooks/route.ts` - **CRITICAL**

### Needs Fix
- `app/auth/callback/route.ts` - Wrong import (client vs server)

---

## KEY DECISIONS LOG

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-17 | 3-day grace period for past_due | Balance user experience vs revenue protection |
| 2025-12-17 | Single price tier (12 EUR/mo) | MVP simplicity |
| 2025-12-17 | No trial period | Direct monetization approach |

---

## CONTEXT RETRIEVAL GUIDE

**For new implementation work:**
1. Read `stripe-integration-context.md` sections 1-3
2. Read `briefing-implementation-agent.md`

**For testing:**
1. Read `briefing-test-agent.md`
2. Reference `stripe-integration-context.md` section 6

**For debugging:**
1. Start with `briefing-debug-agent.md`
2. Reference `stripe-integration-context.md` section 7

**For architecture questions:**
1. Read `stripe-integration-context.md` sections 4-6

---

## SESSION HANDOFF

If continuing this work in a new session:

1. **Current state:** Webhook handler not created
2. **Next step:** Implement webhook at `app/api/webhooks/route.ts`
3. **Then:** Fix auth callback import
4. **Then:** Test full flow with Stripe CLI
5. **Finally:** Commit changes

**Environment needed:**
- STRIPE_WEBHOOK_SECRET (get from Stripe CLI or dashboard)
- Supabase `subscriptions` table created

---

## COMPRESSION CHECKPOINT

This context was captured at commit: `ce3f755` (main branch)

Uncommitted files related to Stripe:
- `app/api/create-checkout-session/route.ts` (new)
- `app/api/portal/route.ts` (new)
- `app/lib/stripe.ts` (new)
- `app/lib/subscription.ts` (new)
- `app/lib/supabase-server.ts` (new)
- `middleware.ts` (new)

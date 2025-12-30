# Document Indexation on Railway.app - Complete Guide

This guide explains how to implement document indexation with embeddings on Railway.app with limited memory (~512MB).

## Problem Analysis

The original approach using FastAPI's `BackgroundTasks` fails because:

1. **Railway kills CPU-intensive processes after ~30s** - Embedding generation blocks the main thread
2. **Health checks fail during embedding** - The uvicorn worker can't respond to `/health`
3. **Memory is limited to 512MB** - `multilingual-e5-small` takes ~470MB just for the model

## Solution Options

### Option 1: CLI Script (Recommended for Railway)

Run indexation as a one-off command or Railway cron job:

```bash
# Run locally
python scripts/index_documents_railway.py

# On Railway - via cron or one-off dyno
python scripts/index_documents_railway.py --batch-size 3 --delay 2

# Dry run (check documents without processing)
python scripts/index_documents_railway.py --dry-run
```

**Advantages:**
- Doesn't affect the main API
- Health checks always pass
- Can be resumed if interrupted
- Memory is fully dedicated to indexation

### Option 2: API with ThreadPoolExecutor (For Web UI Trigger)

Use the improved admin routes (`admin_v2.py`) that:
- Run embeddings in a separate thread pool
- Allow health checks to pass during indexation
- Track progress via global state

**To enable:**

1. In `app/main.py`, change the import:
```python
# Before
from app.api.routes import admin

# After
from app.api.routes import admin_v2 as admin
```

2. Or rename files:
```bash
mv app/api/routes/admin.py app/api/routes/admin_backup.py
mv app/api/routes/admin_v2.py app/api/routes/admin.py
```

## Database Setup

### Check Embedding Dimension

The `multilingual-e5-small` model produces **384-dimensional** embeddings. If your database was set up for `e5-large` (1024D), you need to migrate:

```sql
-- Run in Supabase SQL Editor
-- WARNING: This will delete existing embeddings!

-- 1. Clear existing embeddings
DELETE FROM document_embeddings;

-- 2. Run migration
-- See: supabase/migrations/006_update_embedding_dimension_384.sql
```

Or run the migration file:
```bash
# Via Supabase CLI
supabase db push
```

### Verify Setup

```sql
-- Check embedding dimension
SELECT
    column_name,
    udt_name,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'document_embeddings'
AND column_name = 'embedding';

-- Should show: vector(384)
```

## Memory Optimization

### Key Optimizations in the Solution

1. **Single-chunk embedding** - Process one chunk at a time instead of batching
2. **Aggressive garbage collection** - `gc.collect()` after each document
3. **Singleton model** - Only load the model once via `get_embedding_service()`
4. **Small DB inserts** - Insert 20 chunks at a time to avoid timeouts
5. **Delay between documents** - Allow memory to be freed between operations

### Memory Usage

| Component | Memory |
|-----------|--------|
| Base Python | ~50MB |
| FastAPI + uvicorn | ~30MB |
| sentence-transformers | ~50MB |
| multilingual-e5-small model | ~370MB |
| **Total** | **~500MB** |

This leaves minimal headroom in 512MB, which is why single-chunk processing is essential.

## API Endpoints

### Start Indexation
```
POST /api/v1/admin/index-documents
```

Response:
```json
{
    "status": "started",
    "message": "Document indexation started in background",
    "documents_available": 34,
    "note": "Use /indexation-status to check progress"
}
```

### Check Status
```
GET /api/v1/admin/indexation-status
```

Response:
```json
{
    "documents_in_context": 34,
    "chunks_indexed": 150,
    "indexation_complete": false,
    "is_running": true,
    "progress": {
        "current": 10,
        "total": 34,
        "current_document": "Cashew Report 2024",
        "chunks_created_this_run": 45
    },
    "errors": []
}
```

### Clear Embeddings
```
DELETE /api/v1/admin/clear-embeddings
```

### Clear Search Cache
```
DELETE /api/v1/admin/clear-cache
```

### Test Search
```
GET /api/v1/admin/test-search?query=cashew+prices&commodity=cashew
```

## Railway Deployment

### Railway Settings

In `railway.toml`:
```toml
[build]
builder = "dockerfile"

[deploy]
healthcheckTimeout = 300
startupDelaySeconds = 300
restartPolicyType = "ON_FAILURE"
```

### Environment Variables

Required:
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
EMBEDDING_MODEL=intfloat/multilingual-e5-small
```

### Running Indexation on Railway

**Option A: Via Cron (Recommended)**

1. Create a Railway cron job
2. Command: `python scripts/index_documents_railway.py`
3. Schedule: Once, or as needed

**Option B: Via Railway CLI**

```bash
railway run python scripts/index_documents_railway.py
```

**Option C: Via Web UI**

1. Open Admin page (`/Admin`)
2. Click "Start Indexation"
3. Monitor progress (auto-refresh available)

## Troubleshooting

### "Process killed" on Railway

Cause: Out of memory or CPU timeout

Fix:
1. Use CLI script instead of API
2. Increase delay: `--delay 3`
3. Reduce batch size: `--batch-size 1`

### Health checks failing

Cause: Embedding generation blocking event loop

Fix: Use `admin_v2.py` which uses ThreadPoolExecutor

### Embedding dimension mismatch

Error: `dimension mismatch: expected 384, got 1024`

Fix: Run migration `006_update_embedding_dimension_384.sql`

### No results from search

Causes:
1. Embeddings not generated
2. Wrong dimension in database
3. Similarity threshold too high

Debug:
```
GET /api/v1/admin/test-search?query=test
```

## Files Created/Modified

| File | Purpose |
|------|---------|
| `scripts/index_documents_railway.py` | CLI indexation script |
| `app/api/routes/admin_v2.py` | Improved admin routes |
| `supabase/migrations/006_update_embedding_dimension_384.sql` | Fix embedding dimension |
| `DOCUMENT_INDEXATION_GUIDE.md` | This guide |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Railway Container                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │  Streamlit  │────▶│   FastAPI   │────▶│  Supabase   │   │
│  │    (UI)     │     │    (API)    │     │ (PostgreSQL) │   │
│  └─────────────┘     └──────┬──────┘     └─────────────┘   │
│                             │                               │
│                    ┌────────▼────────┐                     │
│                    │ ThreadPoolExecutor │                   │
│                    │   (Embeddings)   │                    │
│                    └─────────────────┘                     │
│                             │                               │
│                    ┌────────▼────────┐                     │
│                    │ sentence-transformers │               │
│                    │ multilingual-e5-small │               │
│                    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## Performance

Expected times on Railway (512MB, shared CPU):

| Documents | Chunks | Time |
|-----------|--------|------|
| 10 | ~50 | 5-10 min |
| 34 | ~150 | 15-30 min |
| 100 | ~500 | 1-2 hours |

## Summary

For Railway.app with limited resources:

1. **Use the CLI script** for initial indexation or bulk updates
2. **Use admin_v2.py** if you need web UI triggers
3. **Run migration 006** to fix embedding dimension to 384D
4. **Monitor via /indexation-status** endpoint
5. **Clear cache after re-indexing** for fresh search results

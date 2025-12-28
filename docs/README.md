# Documentation - Cambodia Agri Analytics

This directory contains comprehensive documentation for the Cambodia Agri Analytics project.

## Upsert Implementation (2025-12-25)

Documentation for the duplicate prevention implementation:

### Quick Start
- **[UPSERT_QUICK_START.md](UPSERT_QUICK_START.md)** - Get started in 60 seconds
- **[UPSERT_VISUAL_GUIDE.txt](UPSERT_VISUAL_GUIDE.txt)** - Visual ASCII diagrams and examples

### Detailed Documentation
- **[UPSERT_IMPLEMENTATION.md](UPSERT_IMPLEMENTATION.md)** - Complete technical implementation guide
- **[../IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md)** - Executive summary of changes
- **[../CHANGELOG_UPSERT.md](../CHANGELOG_UPSERT.md)** - Detailed changelog

### Database Migrations
- **[../scripts/migrations/README.md](../scripts/migrations/README.md)** - Migration instructions
- **[../scripts/migrations/001_add_unique_constraint_prices.sql](../scripts/migrations/001_add_unique_constraint_prices.sql)** - Migration SQL

## Document Guide

### For Users/Operators
1. Start with **UPSERT_QUICK_START.md** for immediate implementation
2. Review **UPSERT_VISUAL_GUIDE.txt** for conceptual understanding
3. Check **migrations/README.md** for database setup

### For Developers
1. Read **UPSERT_IMPLEMENTATION.md** for full technical details
2. Review **IMPLEMENTATION_SUMMARY.md** for changes overview
3. Check **CHANGELOG_UPSERT.md** for detailed change history
4. Examine code in `app/services/supabase_service.py` and `app/scheduler/jobs.py`

### For Project Managers
1. Read **IMPLEMENTATION_SUMMARY.md** for overview
2. Review success criteria and testing procedures
3. Check rollback plan if needed

## Key Concepts

### Natural Key
```
commodity_id + date + source + destination_country
```

### Upsert Behavior
- **Existing record:** UPDATE with new data
- **New record:** INSERT into database
- **Result:** No duplicates created

### Files Modified
- `app/services/supabase_service.py` - Added `upsert_price()` method
- `app/scheduler/jobs.py` - Changed to use upsert
- `scripts/supabase_schema.sql` - Added unique indexes

## Quick Links

| Task | Document |
|------|----------|
| Apply migration to existing DB | [migrations/README.md](../scripts/migrations/README.md) |
| Understand implementation | [UPSERT_IMPLEMENTATION.md](UPSERT_IMPLEMENTATION.md) |
| Quick setup guide | [UPSERT_QUICK_START.md](UPSERT_QUICK_START.md) |
| Visual examples | [UPSERT_VISUAL_GUIDE.txt](UPSERT_VISUAL_GUIDE.txt) |
| See all changes | [CHANGELOG_UPSERT.md](../CHANGELOG_UPSERT.md) |

## Testing

### Verify No Duplicates
```sql
SELECT
    commodity_id, date, source,
    COALESCE(destination_country, 'NULL') as destination,
    COUNT(*) as count
FROM prices
GROUP BY commodity_id, date, source, COALESCE(destination_country, 'NULL')
HAVING COUNT(*) > 1;
```

### Test Re-seeding
```bash
# First seed
python scripts/seed_collectors.py
# Note count

# Second seed
python scripts/seed_collectors.py
# Count should be same
```

## Support

For issues or questions:
1. Check troubleshooting section in [UPSERT_IMPLEMENTATION.md](UPSERT_IMPLEMENTATION.md)
2. Review migration logs in Supabase SQL Editor
3. Verify unique indexes exist in database
4. Check application logs for upsert messages

## Status

- **Implementation:** ✅ Complete
- **Documentation:** ✅ Complete
- **Testing:** ⏳ Awaiting user testing
- **Production:** ⏳ Ready to deploy

---

**Last Updated:** 2025-12-25
**Version:** 1.0.0

---\r\nPrerequisite: 00_system_exploration.md
description: Safe database schema change process.
---\r\nPrerequisite: 00_system_exploration.md

# Database Migration Workflow

1. **Backup**
   - Run python scripts/backup_database.py.

2. **Draft Migration**
   - Create migration: 
pm run migrate:create -- -m "description".
   - Review the generated script in lembic/versions/.

3. **Verification**
   - Test upgrade: lembic upgrade head.
   - Test downgrade: lembic downgrade -1.
   - Verify performance indexes ( composite indexes if needed).

4. **Deployment**
   - Update docs/developer/DATABASE_SCHEMA.md.



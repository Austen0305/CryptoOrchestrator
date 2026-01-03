# Database Migration

Handle database migrations using Alembic.

## Run Migrations

Apply all pending migrations:
```bash
alembic upgrade head
```

Or use npm script:
```bash
npm run migrate
```

## Create New Migration

Create a new migration from model changes:
```bash
alembic revision --autogenerate -m "description of changes"
```

Or use npm script:
```bash
npm run migrate:create "description of changes"
```

**Important**: Always review auto-generated migrations before applying!

## Rollback Migration

Rollback the last migration:
```bash
alembic downgrade -1
```

Or use npm script:
```bash
npm run migrate:rollback
```

## Check Migration Status

View current migration status:
```bash
alembic current
```

View migration history:
```bash
alembic history
```

## Best Practices

1. **Review Auto-Generated Migrations**: Always check `alembic/versions/` files before applying
2. **Test on Staging First**: Never apply migrations directly to production
3. **Backup Before Migrating**: Run `npm run db:backup` before major migrations
4. **Use Descriptive Messages**: Write clear migration descriptions
5. **Never Edit Existing Migrations**: Create new migrations instead

## Troubleshooting

If migrations fail:
1. Check database connection in `.env`
2. Verify Alembic is configured: `alembic.ini`
3. Check for conflicting migrations: `alembic history`
4. Restore from backup if needed: `npm run db:restore`

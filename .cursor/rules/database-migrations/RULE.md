---
description: Database migration patterns and best practices using Alembic
globs: ["alembic/**/*", "**/migrations/**/*", "**/*migration*.py"]
alwaysApply: false
---

# Database Migration Rules

## Alembic Migration Patterns

### Creating Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "add_user_preferences_table"

# Create an empty migration (for data migrations)
alembic revision -m "migrate_user_data"
```

### Migration File Structure
```python
"""add_user_preferences_table

Revision ID: abc123def456
Revises: xyz789
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'abc123def456'
down_revision = 'xyz789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration changes."""
    # ✅ Good: Use op.create_table for new tables
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(50), nullable=True),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # ✅ Good: Create indexes
    op.create_index('idx_user_preferences_user_id', 'user_preferences', ['user_id'])
    
    # ✅ Good: Add columns to existing tables
    op.add_column('users', sa.Column('preferences_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_users_preferences',
        'users', 'user_preferences',
        ['preferences_id'], ['id']
    )


def downgrade() -> None:
    """Revert migration changes."""
    # ✅ Good: Reverse operations in opposite order
    op.drop_constraint('fk_users_preferences', 'users', type_='foreignkey')
    op.drop_column('users', 'preferences_id')
    op.drop_index('idx_user_preferences_user_id', table_name='user_preferences')
    op.drop_table('user_preferences')
```

## Best Practices

### 1. Always Review Auto-Generated Migrations
```python
# ❌ Bad: Blindly accepting auto-generated migrations
# Always review and modify as needed

# ✅ Good: Review and optimize
def upgrade() -> None:
    # Auto-generated might create index separately
    # Combine operations when possible
    op.create_table(
        'trading_bots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),  # Index inline
        sa.PrimaryKeyConstraint('id'),
    )
```

### 2. Use Transactions for Data Migrations
```python
def upgrade() -> None:
    """Migrate user data to new structure."""
    connection = op.get_bind()
    
    # ✅ Good: Use transactions for data migrations
    with connection.begin():
        # Migrate existing data
        connection.execute(
            sa.text("""
                UPDATE users 
                SET preferences_id = (
                    SELECT id FROM user_preferences 
                    WHERE user_preferences.user_id = users.id
                )
            """)
        )
```

### 3. Handle Large Data Migrations
```python
def upgrade() -> None:
    """Migrate large dataset in batches."""
    connection = op.get_bind()
    
    # ✅ Good: Process in batches to avoid memory issues
    batch_size = 1000
    offset = 0
    
    while True:
        result = connection.execute(
            sa.text(f"""
                SELECT id, old_data FROM large_table 
                LIMIT {batch_size} OFFSET {offset}
            """)
        )
        
        rows = result.fetchall()
        if not rows:
            break
        
        # Process batch
        for row in rows:
            # Transform and update data
            pass
        
        offset += batch_size
```

### 4. Add Indexes for Performance
```python
def upgrade() -> None:
    """Add indexes for frequently queried columns."""
    # ✅ Good: Add indexes for foreign keys and frequently queried columns
    op.create_index('idx_trades_user_id', 'trades', ['user_id'])
    op.create_index('idx_trades_created_at', 'trades', ['created_at'])
    
    # ✅ Good: Composite indexes for common query patterns
    op.create_index(
        'idx_trades_user_created',
        'trades',
        ['user_id', 'created_at']
    )
```

### 5. Never Edit Existing Migration Files
```python
# ❌ Bad: Editing existing migration
# revision = 'abc123'  # DON'T CHANGE THIS

# ✅ Good: Create a new migration to fix issues
# alembic revision -m "fix_user_preferences_constraint"
```

### 6. Test Migrations
```python
# ✅ Good: Test migrations in test environment first
# Always test both upgrade and downgrade paths

def test_migration_upgrade():
    """Test migration upgrade."""
    from alembic import command
    from alembic.config import Config
    
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    
    # Verify migration applied correctly
    # Check tables, indexes, constraints, etc.

def test_migration_downgrade():
    """Test migration downgrade."""
    from alembic import command
    from alembic.config import Config
    
    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, "-1")
    
    # Verify rollback worked correctly
```

## Common Patterns

### Adding a Column with Default
```python
def upgrade() -> None:
    # ✅ Good: Add column with server default for existing rows
    op.add_column(
        'users',
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false')
    )

def downgrade() -> None:
    op.drop_column('users', 'is_verified')
```

### Renaming a Column
```python
def upgrade() -> None:
    # ✅ Good: Use op.alter_column for renaming
    op.alter_column('users', 'email_address', new_column_name='email')

def downgrade() -> None:
    op.alter_column('users', 'email', new_column_name='email_address')
```

### Changing Column Type
```python
def upgrade() -> None:
    # ✅ Good: Handle type changes carefully
    # For PostgreSQL, may need to cast data
    op.execute("""
        ALTER TABLE trades 
        ALTER COLUMN amount TYPE DECIMAL(18, 8) 
        USING amount::DECIMAL(18, 8)
    """)

def downgrade() -> None:
    op.execute("""
        ALTER TABLE trades 
        ALTER COLUMN amount TYPE FLOAT 
        USING amount::FLOAT
    """)
```

### Adding Foreign Key Constraint
```python
def upgrade() -> None:
    # ✅ Good: Add foreign key with proper ondelete behavior
    op.create_foreign_key(
        'fk_bots_user',
        'trading_bots', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'  # Delete bots when user is deleted
    )

def downgrade() -> None:
    op.drop_constraint('fk_bots_user', 'trading_bots', type_='foreignkey')
```

## Migration Naming Conventions

- Use descriptive names: `add_user_preferences_table`
- Use action verbs: `add_`, `remove_`, `update_`, `rename_`
- Be specific: `add_index_to_trades_user_id` not `add_index`
- Include table name: `add_email_column_to_users`

## Running Migrations

### Development
```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific revision
alembic upgrade abc123

# Show current revision
alembic current

# Show migration history
alembic history
```

### Production
```bash
# Always backup database before migrations
pg_dump database_name > backup.sql

# Run migrations
alembic upgrade head

# Verify migration applied
alembic current
```

### Rollback
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade xyz789

# Rollback all migrations (use with caution!)
alembic downgrade base
```

## Environment-Specific Considerations

### SQLite vs PostgreSQL
```python
def upgrade() -> None:
    """Handle differences between SQLite and PostgreSQL."""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # PostgreSQL-specific operations
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    elif bind.dialect.name == 'sqlite':
        # SQLite-specific operations
        pass
```

## Migration Checklist

Before committing a migration:
- [ ] Reviewed auto-generated code
- [ ] Tested upgrade path
- [ ] Tested downgrade path
- [ ] Added appropriate indexes
- [ ] Handled existing data (if needed)
- [ ] Used descriptive migration message
- [ ] Verified on staging environment
- [ ] Documented any special considerations

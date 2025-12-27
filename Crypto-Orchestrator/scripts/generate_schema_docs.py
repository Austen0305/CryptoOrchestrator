#!/usr/bin/env python3
"""
Generate Database Schema Documentation
Auto-generates documentation from SQLAlchemy models
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect
from sqlalchemy.schema import MetaData
from server_fastapi.database import engine
from server_fastapi.models import Base

def generate_schema_docs():
    """Generate database schema documentation."""
    
    # Get all tables from metadata
    metadata = Base.metadata
    tables = metadata.tables
    
    docs = []
    docs.append("# Database Schema Documentation\n")
    docs.append("Auto-generated from SQLAlchemy models.\n")
    docs.append("**Last Updated**: Auto-generated on schema inspection\n\n")
    docs.append("## Table of Contents\n\n")
    
    # Generate table of contents
    for table_name in sorted(tables.keys()):
        anchor = table_name.lower().replace("_", "-")
        docs.append(f"- [{table_name}](#{anchor})\n")
    
    docs.append("\n---\n\n")
    
    # Generate documentation for each table
    for table_name in sorted(tables.keys()):
        table = tables[table_name]
        inspector = inspect(engine.sync_engine)
        
        docs.append(f"## {table_name}\n\n")
        
        # Table description (if available)
        if table.comment:
            docs.append(f"*{table.comment}*\n\n")
        
        # Columns
        docs.append("### Columns\n\n")
        docs.append("| Column Name | Type | Nullable | Default | Description |\n")
        docs.append("|------------|------|----------|---------|-------------|\n")
        
        for column in table.columns:
            col_type = str(column.type)
            nullable = "Yes" if column.nullable else "No"
            default = str(column.default.arg) if column.default else "-"
            description = column.comment or "-"
            
            docs.append(f"| `{column.name}` | {col_type} | {nullable} | {default} | {description} |\n")
        
        # Primary Key
        if table.primary_key:
            pk_columns = [col.name for col in table.primary_key.columns]
            docs.append(f"\n**Primary Key**: {', '.join(pk_columns)}\n\n")
        
        # Foreign Keys
        fks = [fk for fk in table.foreign_keys]
        if fks:
            docs.append("### Foreign Keys\n\n")
            for fk in fks:
                target_table = fk.column.table.name
                target_column = fk.column.name
                docs.append(f"- `{fk.parent.name}` → `{target_table}.{target_column}`\n")
            docs.append("\n")
        
        # Indexes
        indexes = [idx for idx in table.indexes]
        if indexes:
            docs.append("### Indexes\n\n")
            for idx in indexes:
                idx_columns = [col.name for col in idx.columns]
                unique = "UNIQUE" if idx.unique else ""
                docs.append(f"- `{idx.name}` {unique}: {', '.join(idx_columns)}\n")
            docs.append("\n")
        
        docs.append("---\n\n")
    
    # Write to file
    output_path = Path(__file__).parent.parent / "docs" / "developer" / "DATABASE_SCHEMA.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("".join(docs))
    
    print(f"✅ Schema documentation generated: {output_path}")

if __name__ == "__main__":
    generate_schema_docs()

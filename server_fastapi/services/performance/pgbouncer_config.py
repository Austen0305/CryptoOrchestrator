"""
PgBouncer Configuration Service
Provides PgBouncer configuration templates and management for connection pooling
"""

import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PgBouncerConfigGenerator:
    """
    Generates PgBouncer configuration for enterprise-grade connection pooling
    
    PgBouncer provides:
    - Connection pooling at the database level (vs application level)
    - Reduced connection overhead
    - Better resource utilization
    - Support for transaction pooling mode
    """
    
    def __init__(self):
        self.default_config = {
            "database": {
                "pool_mode": "transaction",  # transaction, session, statement
                "max_client_conn": 1000,
                "default_pool_size": 25,
                "min_pool_size": 5,
                "reserve_pool_size": 5,
                "reserve_pool_timeout": 3,
                "max_db_connections": 100,
                "max_user_connections": 100,
            },
            "performance": {
                "server_round_robin": 0,
                "ignore_startup_parameters": "extra_float_digits",
                "application_name_add_host": 1,
            },
            "logging": {
                "log_connections": 1,
                "log_disconnections": 1,
                "log_pooler_errors": 1,
                "verbose": 0,
            },
        }
    
    def generate_config(
        self,
        database_url: str,
        pool_mode: str = "transaction",
        max_client_conn: int = 1000,
        default_pool_size: int = 25,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate PgBouncer configuration file
        
        Args:
            database_url: PostgreSQL connection URL
            pool_mode: transaction, session, or statement
            max_client_conn: Maximum client connections
            default_pool_size: Default pool size per database
            output_path: Optional path to save config file
        
        Returns:
            Configuration file content as string
        """
        # Parse database URL
        from urllib.parse import urlparse
        
        parsed = urlparse(database_url)
        db_name = parsed.path.lstrip("/")
        db_host = parsed.hostname or "localhost"
        db_port = parsed.port or 5432
        db_user = parsed.username or "postgres"
        
        config_lines = [
            "[databases]",
            f"{db_name} = host={db_host} port={db_port} dbname={db_name} user={db_user}",
            "",
            "[pgbouncer]",
            f"pool_mode = {pool_mode}",
            f"max_client_conn = {max_client_conn}",
            f"default_pool_size = {default_pool_size}",
            "min_pool_size = 5",
            "reserve_pool_size = 5",
            "reserve_pool_timeout = 3",
            "max_db_connections = 100",
            "max_user_connections = 100",
            "",
            "# Performance settings",
            "server_round_robin = 0",
            "ignore_startup_parameters = extra_float_digits",
            "",
            "# Logging",
            "log_connections = 1",
            "log_disconnections = 1",
            "log_pooler_errors = 1",
            "verbose = 0",
            "",
            "# Admin console",
            "admin_users = postgres",
            "stats_users = postgres",
            "",
            "# Connection settings",
            "listen_addr = 127.0.0.1",
            "listen_port = 6432",
            "auth_type = md5",
            "auth_file = /etc/pgbouncer/userlist.txt",
        ]
        
        config_content = "\n".join(config_lines)
        
        if output_path:
            try:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w") as f:
                    f.write(config_content)
                logger.info(f"PgBouncer config saved to {output_path}")
            except Exception as e:
                logger.error(f"Failed to save PgBouncer config: {e}")
        
        return config_content
    
    def get_connection_string(self, original_url: str, pgbouncer_port: int = 6432) -> str:
        """
        Convert database URL to use PgBouncer
        
        Args:
            original_url: Original PostgreSQL connection URL
            pgbouncer_port: PgBouncer port (default 6432)
        
        Returns:
            Connection string pointing to PgBouncer
        """
        from urllib.parse import urlparse, urlunparse
        
        parsed = urlparse(original_url)
        
        # Replace host/port with PgBouncer
        new_netloc = f"{parsed.hostname or 'localhost'}:{pgbouncer_port}"
        
        # For transaction pooling, add pool_mode parameter
        query = parsed.query
        if query:
            query += "&pool_mode=transaction"
        else:
            query = "pool_mode=transaction"
        
        new_url = urlunparse((
            parsed.scheme,
            new_netloc,
            parsed.path,
            parsed.params,
            query,
            parsed.fragment,
        ))
        
        return new_url


# Global instance
pgbouncer_config_generator = PgBouncerConfigGenerator()

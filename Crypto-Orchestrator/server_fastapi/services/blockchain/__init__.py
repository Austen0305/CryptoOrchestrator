"""
Blockchain Services Package
Services for blockchain interaction, transaction execution, and monitoring
"""

# Export key services for easier imports
try:
    from .web3_service import get_web3_service, Web3Service
    from .balance_service import get_balance_service, BalanceService
    from .transaction_service import get_transaction_service, TransactionService
    from .key_management import get_key_management_service, KeyManagementService
except ImportError:
    # Optional dependencies - allow import even if web3 is not installed
    pass

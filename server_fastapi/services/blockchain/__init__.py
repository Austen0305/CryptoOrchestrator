"""
Blockchain Services Package
Services for blockchain interaction, transaction execution, and monitoring
"""

# Export key services for easier imports
try:
    from .balance_service import BalanceService, get_balance_service
    from .key_management import KeyManagementService, get_key_management_service
    from .transaction_service import TransactionService, get_transaction_service
    from .web3_service import Web3Service, get_web3_service
except ImportError:
    # Optional dependencies - allow import even if web3 is not installed
    pass

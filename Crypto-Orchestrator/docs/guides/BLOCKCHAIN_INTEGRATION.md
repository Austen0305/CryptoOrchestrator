# Blockchain Integration Guide

Complete guide for blockchain integration, RPC providers, and wallet management in CryptoOrchestrator.

**Last Updated:** December 5, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [RPC Provider Setup](#rpc-provider-setup)
3. [Supported Blockchains](#supported-blockchains)
4. [Wallet Management](#wallet-management)
5. [Deposit & Withdrawal](#deposit--withdrawal)
6. [DEX Trading Integration](#dex-trading-integration)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting](#troubleshooting)

---

## Overview

CryptoOrchestrator supports direct blockchain interaction for:
- **Custodial Trading**: Users deposit funds to platform-managed wallets
- **Non-Custodial Trading**: Users connect their own wallets (MetaMask, WalletConnect, etc.)
- **DEX Trading**: Trade directly on decentralized exchanges without exchange API keys
- **Deposits & Withdrawals**: Send and receive funds on multiple blockchains

### Architecture

- **Backend**: Web3.py for blockchain interaction, async RPC connections
- **Frontend**: Wagmi v2 + Viem for wallet connections
- **RPC Providers**: Support for Alchemy, Infura, QuickNode, and public RPCs
- **Multi-Chain**: Ethereum, Base, Arbitrum, Polygon, Optimism, Avalanche, BNB Chain

---

## RPC Provider Setup

### Environment Variables

Add these to your `.env` file:

```env
# RPC Provider Configuration
RPC_PROVIDER_TYPE=alchemy  # Options: alchemy, infura, quicknode, public
RPC_API_KEY=your-rpc-api-key  # Required for alchemy/infura/quicknode
RPC_TIMEOUT=30  # Timeout in seconds (default: 30)
RPC_MAX_RETRIES=3  # Maximum retry attempts (default: 3)

# Chain-Specific RPC URLs (optional - overrides provider type)
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_KEY
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
OPTIMISM_RPC_URL=https://opt-mainnet.g.alchemy.com/v2/YOUR_KEY
AVALANCHE_RPC_URL=https://api.avax.network/ext/bc/C/rpc
BNB_CHAIN_RPC_URL=https://bsc-dataseed.binance.org
```

### Provider Options

#### 1. Alchemy (Recommended for Production)

**Pros:**
- High reliability and uptime
- Generous free tier (300M compute units/month)
- Excellent documentation and support
- WebSocket support

**Setup:**
1. Sign up at https://www.alchemy.com/
2. Create an app for each chain you want to support
3. Copy the API key from the dashboard
4. Set `RPC_PROVIDER_TYPE=alchemy` and `RPC_API_KEY=your-alchemy-key`

**URL Format:**
- Ethereum: `https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY`
- Base: `https://base-mainnet.g.alchemy.com/v2/YOUR_KEY`
- Arbitrum: `https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY`
- Polygon: `https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY`
- Optimism: `https://opt-mainnet.g.alchemy.com/v2/YOUR_KEY`
- Avalanche: `https://avax-mainnet.g.alchemy.com/v2/YOUR_KEY`

#### 2. Infura

**Pros:**
- Reliable service
- Good free tier (100k requests/day)
- Multi-chain support

**Setup:**
1. Sign up at https://infura.io/
2. Create a project
3. Copy the API key
4. Set `RPC_PROVIDER_TYPE=infura` and `RPC_API_KEY=your-infura-key`

**URL Format:**
- Ethereum: `https://mainnet.infura.io/v3/YOUR_KEY`
- Base: `https://base-mainnet.infura.io/v3/YOUR_KEY`
- Arbitrum: `https://arbitrum-mainnet.infura.io/v3/YOUR_KEY`
- Polygon: `https://polygon-mainnet.infura.io/v3/YOUR_KEY`
- Optimism: `https://optimism-mainnet.infura.io/v3/YOUR_KEY`

#### 3. QuickNode

**Pros:**
- Fast response times
- Custom endpoints
- Good for high-volume applications

**Setup:**
1. Sign up at https://www.quicknode.com/
2. Create an endpoint for each chain
3. Copy the endpoint URL
4. Set chain-specific `*_RPC_URL` environment variables

#### 4. Public RPCs (Development Only)

**Pros:**
- No API key required
- Free

**Cons:**
- Rate limits
- Lower reliability
- Not recommended for production

**Usage:**
- Set `RPC_PROVIDER_TYPE=public` or leave unset
- System will use public RPC endpoints as fallback

---

## Supported Blockchains

| Chain ID | Name | Symbol | Status |
|----------|------|--------|--------|
| 1 | Ethereum | ETH | ✅ Fully Supported |
| 8453 | Base | ETH | ✅ Fully Supported |
| 42161 | Arbitrum One | ETH | ✅ Fully Supported |
| 137 | Polygon | MATIC | ✅ Fully Supported |
| 10 | Optimism | ETH | ✅ Fully Supported |
| 43114 | Avalanche | AVAX | ✅ Fully Supported |
| 56 | BNB Chain | BNB | ✅ Fully Supported |

### Adding New Chains

To add support for a new blockchain:

1. **Add RPC URL** to `server_fastapi/config/settings.py`:
   ```python
   new_chain_rpc_url: Optional[str] = Field(default=None, alias="NEW_CHAIN_RPC_URL")
   ```

2. **Update Chain Mapping** in `server_fastapi/services/blockchain/web3_service.py`:
   ```python
   CHAIN_NAMES = {
       # ... existing chains
       250: "Fantom",  # Example
   }
   
   DEFAULT_PUBLIC_RPCS = {
       # ... existing chains
       250: "https://rpc.ftm.tools",  # Example
   }
   ```

3. **Update Frontend** in `client/src/lib/wagmiConfig.ts`:
   ```typescript
   import { fantom } from 'wagmi/chains';
   
   export const chains = [
     // ... existing chains
     fantom,
   ];
   ```

---

## Wallet Management

### Custodial Wallets

**What are they?**
- Platform-managed wallets where users deposit funds
- Private keys stored securely (AWS KMS, HashiCorp Vault in production)
- Users can trade without managing their own keys

**Creating a Custodial Wallet:**

```typescript
// Frontend
const createWallet = useCreateCustodialWallet();
await createWallet.mutateAsync(1); // Chain ID (1 = Ethereum)
```

**API Endpoint:**
```http
POST /api/wallets/custodial
Content-Type: application/json

{
  "chain_id": 1,
  "label": "My Ethereum Wallet" // Optional
}
```

### External Wallets

**What are they?**
- User's own wallets (MetaMask, WalletConnect, etc.)
- User controls private keys
- Used for non-custodial trading

**Registering an External Wallet:**

```typescript
// Frontend
const registerWallet = useRegisterExternalWallet();
await registerWallet.mutateAsync({
  wallet_address: "0x...",
  chain_id: 1,
  label: "My MetaMask" // Optional
});
```

**API Endpoint:**
```http
POST /api/wallets/external
Content-Type: application/json

{
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "chain_id": 1,
  "label": "My MetaMask Wallet"
}
```

### Getting Deposit Address

**API Endpoint:**
```http
GET /api/wallets/deposit-address/{chain_id}
```

Returns the user's custodial wallet address for deposits.

---

## Deposit & Withdrawal

### Deposits

**How it works:**
1. User gets deposit address from `/api/wallets/deposit-address/{chain_id}`
2. User sends funds to that address
3. Background Celery task monitors blockchain for deposits
4. System automatically updates user balance when deposit detected

**Monitoring:**
- Deposit monitoring runs as a Celery background task
- Checks for new transactions every block
- Supports ETH and ERC-20 token deposits
- Waits for confirmations before crediting balance

**Celery Task:**
```bash
# Start deposit monitor worker
celery -A server_fastapi.celery_app worker -Q deposit_monitor
```

### Withdrawals

**Security Features:**
- 2FA token required
- Address validation
- Daily/weekly withdrawal limits
- Multi-signature support (future)

**API Endpoint:**
```http
POST /api/withdrawals
Content-Type: application/json

{
  "chain_id": 1,
  "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "amount": "0.1",
  "currency": "ETH",
  "mfa_token": "123456"
}
```

**Withdrawal Limits:**
- Default daily limit: $10,000 USD
- Default weekly limit: $50,000 USD
- Minimum withdrawal: 0.001 ETH
- Configurable per user tier

**Status Check:**
```http
GET /api/withdrawals/status/{chain_id}/{tx_hash}
```

---

## DEX Trading Integration

### Overview

DEX trading allows users to trade tokens directly on decentralized exchanges without requiring exchange API keys. The platform:

1. Aggregates quotes from multiple DEX aggregators (0x, OKX, Rubic)
2. Routes to the best price
3. Executes swaps on-chain
4. Charges platform trading fees

### Supported Aggregators

- **0x Protocol**: 150+ liquidity sources, affiliate fees
- **OKX DEX**: 500+ DEXs, competitive rates
- **Rubic**: Cross-chain swaps, 100+ blockchains

### Trading Modes

#### Custodial Trading
- User deposits funds to platform wallet
- Platform executes swaps on user's behalf
- Higher fees (0.2% default) but simpler UX

#### Non-Custodial Trading
- User connects their own wallet
- User signs transactions themselves
- Lower fees (0.15% default) but requires wallet connection

### API Endpoints

**Get Quote:**
```http
POST /api/dex/quote
Content-Type: application/json

{
  "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
  "buy_token": "ETH",
  "sell_amount": "1000000000", // 1000 USDC (6 decimals)
  "chain_id": 1,
  "slippage_percentage": 0.5
}
```

**Execute Swap:**
```http
POST /api/dex/swap
Content-Type: application/json

{
  "sell_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "buy_token": "ETH",
  "sell_amount": "1000000000",
  "chain_id": 1,
  "slippage_percentage": 0.5,
  "custodial": true, // or false for non-custodial
  "user_wallet_address": "0x...", // Required for non-custodial
  "signature": "0x..." // Required for non-custodial
}
```

---

## Security Considerations

### Private Key Management

**⚠️ CRITICAL: Never store private keys in the database or code!**

**Production Setup:**
1. Use AWS KMS, HashiCorp Vault, or similar
2. Store only key IDs in database
3. Retrieve keys at runtime, never cache
4. Use hardware security modules (HSM) for high-value wallets

**Current Implementation:**
- `server_fastapi/services/blockchain/key_management.py` provides interface
- Placeholder implementation needs to be replaced with actual KMS/Vault integration
- See TODO comments in code

### Transaction Security

- **Nonce Management**: Database-backed nonces prevent replay attacks
- **Signature Verification**: EIP-712 signatures for non-custodial trades
- **Gas Estimation**: Automatic gas estimation with 20% buffer
- **Transaction Monitoring**: Automatic status tracking and confirmation

### Withdrawal Security

- **2FA Required**: All withdrawals require 2FA token
- **Address Validation**: Strict Ethereum address format validation
- **Rate Limiting**: Daily/weekly withdrawal limits
- **Audit Trail**: All withdrawals logged to database

---

## Troubleshooting

### RPC Connection Issues

**Problem:** "No Web3 connection for chain X"

**Solutions:**
1. Check RPC URL is correct in `.env`
2. Verify API key is valid (for Alchemy/Infura)
3. Check network connectivity
4. Try public RPC as fallback: `RPC_PROVIDER_TYPE=public`

**Debug:**
```python
# In Python shell
from server_fastapi.services.blockchain.web3_service import get_web3_service
service = get_web3_service()
w3 = await service.get_connection(1)  # Ethereum
is_connected = await w3.is_connected()
print(f"Connected: {is_connected}")
```

### Balance Not Updating

**Problem:** Deposits not detected

**Solutions:**
1. Check deposit monitor Celery task is running
2. Verify transaction has enough confirmations
3. Check wallet address is correct
4. Review logs: `logs/fastapi.log`

**Manual Check:**
```python
from server_fastapi.services.blockchain.balance_service import get_balance_service
service = get_balance_service()
balance = await service.get_eth_balance(1, "0x...", use_cache=False)
print(f"Balance: {balance} ETH")
```

### Transaction Failures

**Problem:** Transactions failing

**Common Causes:**
1. Insufficient gas
2. Insufficient balance
3. Invalid calldata
4. Network congestion

**Debug:**
- Check transaction receipt status
- Verify gas price is reasonable
- Check error messages in logs
- Use transaction status endpoint: `GET /api/withdrawals/status/{chain_id}/{tx_hash}`

### Circuit Breaker Open

**Problem:** Aggregator API calls failing

**Solutions:**
1. Check aggregator API keys are valid
2. Verify rate limits not exceeded
3. Wait for circuit breaker recovery (60s default)
4. Check aggregator service health

**Status Check:**
```python
from server_fastapi.services.integrations.zeroex_service import ZeroExService
service = ZeroExService()
status = service.circuit_breaker.get_status()
print(status)  # Shows state, failure_count, last_failure_time
```

---

## Best Practices

### Development

1. **Use Public RPCs**: For local development, public RPCs are sufficient
2. **Test on Testnets**: Use Sepolia, Base Sepolia, etc. for testing
3. **Mock Services**: Use mocks for blockchain services in unit tests
4. **Rate Limiting**: Be mindful of RPC rate limits during development

### Production

1. **Use Paid RPC Providers**: Alchemy or Infura for reliability
2. **Multiple Providers**: Configure fallback RPCs for redundancy
3. **Monitor Usage**: Track RPC usage to avoid hitting limits
4. **Secure Key Management**: Use AWS KMS or HashiCorp Vault
5. **Transaction Monitoring**: Set up alerts for failed transactions
6. **Balance Caching**: Use caching to reduce RPC calls (already implemented)

### Security

1. **Never Log Private Keys**: Use LogSanitizer middleware
2. **Validate All Inputs**: Address validation, amount checks
3. **2FA for Withdrawals**: Always require 2FA
4. **Rate Limiting**: Implement withdrawal rate limits
5. **Audit Logging**: Log all blockchain transactions

---

## API Reference

### Wallet Endpoints

- `POST /api/wallets/custodial` - Create custodial wallet
- `POST /api/wallets/external` - Register external wallet
- `GET /api/wallets` - List user wallets
- `GET /api/wallets/deposit-address/{chain_id}` - Get deposit address

### Withdrawal Endpoints

- `POST /api/withdrawals` - Create withdrawal
- `GET /api/withdrawals/status/{chain_id}/{tx_hash}` - Get withdrawal status

### DEX Trading Endpoints

- `POST /api/dex/quote` - Get DEX quote
- `POST /api/dex/swap` - Execute DEX swap
- `GET /api/dex/supported-chains` - List supported chains

### Metrics Endpoints

- `GET /api/metrics/dex/volume` - Get DEX trade volume
- `GET /api/metrics/dex/fees` - Get fee collection metrics
- `GET /api/metrics/dex/aggregators` - Get aggregator performance
- `GET /api/metrics/dex/errors` - Get error rates
- `GET /api/metrics/dex/chains` - Get volume by chain
- `GET /api/metrics/dex/all` - Get all DEX metrics

---

## Next Steps

1. **Set up RPC providers** (Alchemy recommended)
2. **Configure environment variables** (see above)
3. **Test wallet creation** via `/api/wallets/custodial`
4. **Test deposit monitoring** (send test transaction)
5. **Test withdrawal flow** (with 2FA)
6. **Monitor metrics** via `/api/metrics/dex/all`

---

**For more information:**
- See `docs/DEX_TRADING_GUIDE.md` for DEX trading details
- See `docs/API_KEYS_SETUP.md` for API key configuration
- See `server_fastapi/services/blockchain/` for implementation details

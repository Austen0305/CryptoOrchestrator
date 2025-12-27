#!/usr/bin/env python3
"""
Test Data Generator for CryptoOrchestrator
Generates realistic test data for development and testing
"""
import random
import string
import json
from datetime import datetime, timedelta
from typing import List, Dict
import argparse


class TestDataGenerator:
    """Generate realistic test data"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.trading_pairs = [
            'BTC/USD', 'ETH/USD', 'BNB/USD', 'ADA/USD', 'SOL/USD',
            'XRP/USD', 'DOT/USD', 'DOGE/USD', 'AVAX/USD', 'MATIC/USD'
        ]
        self.strategies = [
            'ma_crossover', 'rsi_strategy', 'bollinger_bands',
            'macd_strategy', 'momentum', 'mean_reversion'
        ]
        self.first_names = [
            'John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah',
            'Robert', 'Lisa', 'William', 'Jennifer', 'James', 'Mary'
        ]
        self.last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
            'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez'
        ]
    
    def generate_email(self, first_name: str, last_name: str, domain: str = 'example.com') -> str:
        """Generate realistic email"""
        return f"{first_name.lower()}.{last_name.lower()}@{domain}"
    
    def generate_user(self, user_id: int) -> Dict:
        """Generate a user"""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        created_date = datetime.now() - timedelta(days=random.randint(1, 365))
        
        return {
            'id': user_id,
            'email': self.generate_email(first_name, last_name),
            'first_name': first_name,
            'last_name': last_name,
            'balance_usd': round(random.uniform(100, 50000), 2),
            'balance_btc': round(random.uniform(0.001, 5), 6),
            'balance_eth': round(random.uniform(0.01, 50), 6),
            'created_at': created_date.isoformat(),
            'last_login': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            'email_verified': random.choice([True, True, True, False]),  # 75% verified
            'two_factor_enabled': random.choice([True, False, False]),  # 33% 2FA
        }
    
    def generate_bot(self, bot_id: int, user_id: int) -> Dict:
        """Generate a trading bot"""
        strategy = random.choice(self.strategies)
        pair = random.choice(self.trading_pairs)
        created_date = datetime.now() - timedelta(days=random.randint(1, 180))
        
        return {
            'id': bot_id,
            'user_id': user_id,
            'name': f"{strategy.replace('_', ' ').title()} Bot {bot_id}",
            'strategy': strategy,
            'trading_pair': pair,
            'amount': round(random.uniform(10, 5000), 2),
            'status': random.choice(['running', 'stopped', 'paused', 'error']),
            'paper_trading': random.choice([True, False]),
            'created_at': created_date.isoformat(),
            'updated_at': (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
            'total_trades': random.randint(0, 1000),
            'win_rate': round(random.uniform(0.3, 0.8), 3),
            'profit_loss': round(random.uniform(-500, 2000), 2),
        }
    
    def generate_trade(self, trade_id: int, user_id: int, bot_id: int = None) -> Dict:
        """Generate a trade"""
        pair = random.choice(self.trading_pairs)
        side = random.choice(['buy', 'sell'])
        amount = round(random.uniform(0.001, 1), 6)
        price = round(random.uniform(100, 50000), 2)
        executed_date = datetime.now() - timedelta(hours=random.randint(0, 720))
        
        return {
            'id': trade_id,
            'user_id': user_id,
            'bot_id': bot_id,
            'trading_pair': pair,
            'side': side,
            'amount': amount,
            'price': price,
            'total': round(amount * price, 2),
            'fee': round(amount * price * 0.001, 2),  # 0.1% fee
            'status': random.choice(['completed', 'completed', 'completed', 'pending', 'failed']),
            'executed_at': executed_date.isoformat(),
        }
    
    def generate_market_data(self, pair: str, days: int = 30) -> List[Dict]:
        """Generate historical market data (OHLCV)"""
        data = []
        base_price = random.uniform(100, 50000)
        
        for i in range(days * 24):  # Hourly data
            timestamp = datetime.now() - timedelta(hours=days * 24 - i)
            
            # Random walk price
            change = random.uniform(-0.02, 0.02)
            base_price *= (1 + change)
            
            open_price = base_price
            close_price = base_price * (1 + random.uniform(-0.01, 0.01))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
            volume = random.uniform(1000, 100000)
            
            data.append({
                'timestamp': timestamp.isoformat(),
                'pair': pair,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 2),
            })
        
        return data
    
    def generate_test_scenarios(self) -> Dict:
        """Generate Stripe test scenarios"""
        return {
            'successful_payment': {
                'card_number': '4242424242424242',
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123',
                'amount': 100.00,
                'expected_status': 'succeeded'
            },
            'declined_payment': {
                'card_number': '4000000000000002',
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123',
                'amount': 100.00,
                'expected_status': 'declined'
            },
            '3d_secure': {
                'card_number': '4000002500003155',
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123',
                'amount': 100.00,
                'expected_status': 'requires_action'
            },
            'insufficient_funds': {
                'card_number': '4000000000009995',
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123',
                'amount': 100.00,
                'expected_status': 'declined'
            }
        }
    
    def generate_complete_dataset(self, num_users: int, num_bots: int, num_trades: int) -> Dict:
        """Generate a complete dataset"""
        print(f"🎲 Generating test data...")
        print(f"   Users: {num_users}")
        print(f"   Bots: {num_bots}")
        print(f"   Trades: {num_trades}")
        
        users = [self.generate_user(i + 1) for i in range(num_users)]
        
        bots = []
        bot_id = 1
        for user in users:
            num_user_bots = random.randint(0, max(1, num_bots // num_users))
            for _ in range(num_user_bots):
                bots.append(self.generate_bot(bot_id, user['id']))
                bot_id += 1
        
        trades = []
        for i in range(num_trades):
            user = random.choice(users)
            user_bots = [b for b in bots if b['user_id'] == user['id']]
            bot = random.choice(user_bots) if user_bots else None
            trades.append(self.generate_trade(i + 1, user['id'], bot['id'] if bot else None))
        
        market_data = {}
        for pair in self.trading_pairs[:5]:  # Generate for first 5 pairs
            market_data[pair] = self.generate_market_data(pair, days=7)
        
        return {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'seed': 42,
                'counts': {
                    'users': len(users),
                    'bots': len(bots),
                    'trades': len(trades),
                    'market_data_pairs': len(market_data)
                }
            },
            'users': users,
            'bots': bots,
            'trades': trades,
            'market_data': market_data,
            'stripe_test_scenarios': self.generate_test_scenarios()
        }


def main():
    """Main CLI"""
    parser = argparse.ArgumentParser(description='Generate test data for CryptoOrchestrator')
    parser.add_argument('--users', type=int, default=10, help='Number of users to generate')
    parser.add_argument('--bots', type=int, default=20, help='Number of bots to generate')
    parser.add_argument('--trades', type=int, default=100, help='Number of trades to generate')
    parser.add_argument('--output', type=str, default='test_data.json', help='Output file')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    generator = TestDataGenerator(seed=args.seed)
    dataset = generator.generate_complete_dataset(args.users, args.bots, args.trades)
    
    # Save to file
    with open(args.output, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"\n✅ Test data generated successfully!")
    print(f"   Output file: {args.output}")
    print(f"   File size: {len(json.dumps(dataset)) / 1024:.1f} KB")
    print(f"\n📊 Summary:")
    print(f"   Users: {len(dataset['users'])}")
    print(f"   Bots: {len(dataset['bots'])}")
    print(f"   Trades: {len(dataset['trades'])}")
    print(f"   Market data pairs: {len(dataset['market_data'])}")
    print(f"   Stripe scenarios: {len(dataset['stripe_test_scenarios'])}")
    print(f"\n💡 Usage:")
    print(f"   Load data in tests: json.load(open('{args.output}'))")
    print(f"   Seed database: python scripts/seed_database.py --file {args.output}")


if __name__ == "__main__":
    main()

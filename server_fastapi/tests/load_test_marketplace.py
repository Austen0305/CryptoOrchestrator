"""
Load Testing Script for Marketplace Endpoints
Run with: locust -f server_fastapi/tests/load_test_marketplace.py
"""

from locust import HttpUser, task, between
import random
import json


class MarketplaceUser(HttpUser):
    """Simulates user interactions with marketplace endpoints"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Login and get auth token"""
        # Register/login (simplified for load testing)
        self.token = None
        try:
            response = self.client.post(
                "/api/auth/register",
                json={
                    "email": f"loadtest_{random.randint(1000, 9999)}@test.com",
                    "password": "TestPassword123!",
                    "username": f"loadtest_{random.randint(1000, 9999)}",
                },
            )
            if response.status_code == 201:
                data = response.json()
                self.token = data.get("access_token")
        except:
            pass
        
        # If registration failed, try login
        if not self.token:
            try:
                response = self.client.post(
                    "/api/auth/login",
                    json={
                        "email": "test@test.com",
                        "password": "TestPassword123!",
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
            except:
                pass
    
    def _get_headers(self):
        """Get headers with auth token"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(3)
    def browse_traders(self):
        """Browse marketplace traders (most common action)"""
        params = {
            "skip": random.randint(0, 10) * 20,
            "limit": 20,
            "sort_by": random.choice(["total_return", "sharpe_ratio", "win_rate", "rating"]),
        }
        self.client.get("/api/marketplace/traders", params=params, headers=self._get_headers())
    
    @task(2)
    def view_trader_profile(self):
        """View a specific trader profile"""
        trader_id = random.randint(1, 100)  # Assume traders exist
        self.client.get(f"/api/marketplace/traders/{trader_id}", headers=self._get_headers())
    
    @task(1)
    def browse_indicators(self):
        """Browse indicator marketplace"""
        params = {
            "skip": random.randint(0, 5) * 20,
            "limit": 20,
            "category": random.choice(["trend", "momentum", "volatility", "volume", None]),
        }
        self.client.get("/api/indicators/marketplace", params=params, headers=self._get_headers())
    
    @task(1)
    def view_indicator(self):
        """View a specific indicator"""
        indicator_id = random.randint(1, 100)  # Assume indicators exist
        self.client.get(f"/api/indicators/{indicator_id}", headers=self._get_headers())
    
    @task(1)
    def rate_trader(self):
        """Rate a trader (less frequent)"""
        if self.token:
            trader_id = random.randint(1, 100)
            self.client.post(
                f"/api/marketplace/traders/{trader_id}/rate",
                json={
                    "rating": random.randint(1, 5),
                    "comment": "Load test rating",
                },
                headers=self._get_headers(),
            )
    
    @task(1)
    def apply_as_provider(self):
        """Apply as signal provider (rare)"""
        if self.token:
            self.client.post(
                "/api/marketplace/apply",
                json={"profile_description": "Load test application"},
                headers=self._get_headers(),
            )


class AdminUser(HttpUser):
    """Simulates admin interactions"""
    
    wait_time = between(2, 5)
    weight = 1  # Fewer admin users
    
    def on_start(self):
        """Login as admin"""
        # This would need actual admin credentials
        self.token = None
    
    def _get_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(1)
    def verify_providers(self):
        """Verify provider performance"""
        if self.token:
            self.client.post(
                "/api/marketplace/traders/verify-all",
                params={"period_days": 90},
                headers=self._get_headers(),
            )
    
    @task(1)
    def get_flagged_providers(self):
        """Get flagged providers"""
        if self.token:
            self.client.get(
                "/api/marketplace/traders/flagged",
                params={"threshold_days": 30},
                headers=self._get_headers(),
            )

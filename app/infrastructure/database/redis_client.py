import json
import redis
from app.shared.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )

    def set_latest_price(self, pair, price):
        key = f"price:{pair}"
        self.client.set(key, str(price))
    
    def get_latest_price(self, pair):
        key = f"price:{pair}"
        price_str = self.client.get(key)

        if price_str is None:
            return None
        return float(price_str)

    def set_account_state(self, state):
        """
        Store the current account state as JSON.
        
        Args:
            state (dict): Account state dictionary containing balance, equity, etc.
        """
        key = "account:state"
        self.client.set(key, json.dumps(state))

    def get_account_state(self):
        """
        Retrieve the current account state.
        
        Returns:
            dict: Account state if found, otherwise None
        """
        key = "account:state"
        state_json = self.client.get(key)

        if state_json is None:
            return None
        return json.loads(state_json)
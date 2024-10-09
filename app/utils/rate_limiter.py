from collections import defaultdict
from time import time

class RateLimiter:
    def __init__(self, limit=10, per=60):
        self.limit = limit
        self.per = per
        self.user_requests = defaultdict(list)

    def check_limits(self, user_id):
        now = time()
        user_reqs = self.user_requests[user_id]
        user_reqs = [req for req in user_reqs if now - req < self.per]
        self.user_requests[user_id] = user_reqs
        
        if len(user_reqs) >= self.limit:
            return False
        
        self.user_requests[user_id].append(now)
        return True

    def update_usage(self, user_id, request_size):
        # This method could be used to implement more sophisticated rate limiting
        pass

    def get_current_usage(self, user_id):
        now = time()
        user_reqs = self.user_requests[user_id]
        user_reqs = [req for req in user_reqs if now - req < self.per]
        return len(user_reqs)
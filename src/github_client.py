import requests
import time
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _handle_rate_limit(self, response: requests.Response):
        """Checks rate limit headers and sleeps if necessary."""
        remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
        reset_time = int(response.headers.get("X-RateLimit-Reset", time.time()))

        if remaining <= 1:
            sleep_time = max(reset_time - time.time(), 0) + 1
            logger.warning(f"Rate limit reached. Sleeping for {sleep_time} seconds until reset.")
            time.sleep(sleep_time)

        # Handle secondary rate limits (Abuse mechanism)
        if response.status_code in [403, 429]:
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning(f"Secondary rate limit hit (HTTP {response.status_code}). Sleeping for {retry_after} seconds.")
            time.sleep(retry_after)
            return True # Indicates we should retry
        return False

    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """Wrapper for GET requests handling pagination and rate limits."""
        url = f"{self.base_url}{endpoint}"
        
        while True:
            response = self.session.get(url, params=params)
            needs_retry = self._handle_rate_limit(response)
            
            if needs_retry:
                continue

            response.raise_for_status()
            return response

    def fetch_all_pages(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """Fetches all pages of a paginated API endpoint."""
        if params is None:
            params = {}
        params['per_page'] = 100
        
        all_results = []
        url = f"{self.base_url}{endpoint}"

        while url:
            logger.debug(f"Fetching: {url}")
            response = self.session.get(url, params=params)
            
            if self._handle_rate_limit(response):
                continue
                
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                # If it's not a list, it's not paginated in the standard way
                return [data]

            all_results.extend(data)
            
            # Check for next page
            if 'next' in response.links:
                url = response.links['next']['url']
                params = None # Params are included in the 'next' URL
            else:
                url = None

        return all_results

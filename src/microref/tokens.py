import os
import threading
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from .constants import constants
from .logger import logger

class Token:
    """Represents a single GitHub token and its individual rate limit status."""
    def __init__(self, token_str: str):
        self.token = token_str
        self.remaining = 5000
        self.reset_time = datetime.now(timezone.utc)

    def is_available(self) -> bool:
        """Checks if the token has a safe number of requests or if its penalty time is over."""
        # We use a small buffer (e.g., 10) to be safe.
        return self.remaining > 10 or datetime.now(timezone.utc) >= self.reset_time

    def update_rate_limit(self, headers):
        """Updates the token's status from the API response headers."""
        if headers and 'X-RateLimit-Remaining' in headers:
            self.remaining = int(headers['X-RateLimit-Remaining'])
        if headers and 'X-RateLimit-Reset' in headers:
            self.reset_time = datetime.fromtimestamp(
                int(headers['X-RateLimit-Reset']), tz=timezone.utc
            )

class TokenManager:
    """An intelligent, thread-safe manager for multiple, distinct GitHub tokens."""
    def __init__(self):
        load_dotenv()
        tokens_list = self._load_tokens_from_env()
        self.tokens = [Token(t) for t in tokens_list]
        self._lock = threading.Lock() # Protects token access
        self._pause_event = threading.Event() # The global "stop sign"
        self._pause_event.set() # Start in the "go" state
        self._print_lock = threading.Lock() # Ensures the pause message is only printed once

    def _load_tokens_from_env(self) -> list[str]:
        tokens_list = []
        i = 1
        while True:
            token_str = os.getenv(f"GITHUB_TOKEN_{i}")
            if token_str:
                tokens_list.append(token_str)
                i += 1
            else:
                break
        if not tokens_list:
            print(constants["TokensNotFound"])
            logger.error("No GitHub tokens found in .env file.")
        else:
             print(f"✅ TokenManager initialized with {len(tokens_list)} tokens (assumed from separate accounts).")
             logger.info(f"TokenManager initialized with {len(tokens_list)} tokens.")
        return tokens_list

    def get_token(self) -> Token | None:
        """
        Gets the next available token. If all are exhausted, it will ensure
        only one thread manages the pause while others wait quietly.
        """
        if not self.tokens:
            return None

        while True:
            # All threads must wait here if the "stop sign" is up.
            self._pause_event.wait()

            with self._lock:
                # Find the first token that is ready to be used.
                available_tokens = [t for t in self.tokens if t.is_available()]
                if available_tokens:
                    return available_tokens[0]

                # If we get here, ALL tokens are rate-limited.
                # The first thread to notice this becomes the "leader" for pausing.
                if self._print_lock.acquire(blocking=False):
                    try:
                        # 1. Put up the "stop sign" for all other threads.
                        self._pause_event.clear()

                        soonest_reset_time = min(t.reset_time for t in self.tokens)
                        now = datetime.now(timezone.utc)
                        wait_time = (soonest_reset_time - now).total_seconds()

                        if wait_time > 0:
                            print(f"\n🚨 All tokens are rate-limited. Pausing all threads for {wait_time:.2f} seconds... 🚨")
                            logger.warning(f"All tokens exhausted. Pausing for {wait_time:.2f} seconds.")
                            
                            # The leader sleeps on behalf of everyone.
                            time.sleep(wait_time + 1)
                        
                        # 2. Take down the "stop sign" so everyone can work again.
                        self._pause_event.set()

                    finally:
                        # 3. Release the print lock so a new leader can be chosen next time.
                        self._print_lock.release()
                
                # Other threads that didn't become the leader will loop again
                # and be caught by self._pause_event.wait() at the top.

    def __len__(self):
        return len(self.tokens)
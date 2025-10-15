
from pathlib import Path
import json
import time
from threading import RLock

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PORTFOLIO_PATH = DATA_DIR / "portfolio.json"
LAST_USER_PATH = DATA_DIR / "last_user.json"
FIRST_RUN_PATH = DATA_DIR / "first_run.json"

_lock = RLock()

class PortfolioStorage:
    """
    Centralized portfolio + metadata storage with in-memory caching.
    Use load()/save() rarely — the cache auto-serves reads.
    """
    def __init__(self):
        self._cache = None
        self._last_user_cache = None
        self._first_run_cache = None

    def _read_json(self, path, default):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _write_json(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    # portfolio operations
    def load_portfolios(self):
        with _lock:
            if self._cache is None:
                self._cache = self._read_json(PORTFOLIO_PATH, {})
            return self._cache

    def save_portfolios(self):
        with _lock:
            if self._cache is None:
                self._cache = {}
            self._write_json(PORTFOLIO_PATH, self._cache)

    def get_user(self, username):
        portfolios = self.load_portfolios()
        return portfolios.get(username)

    def ensure_user(self, username):
        portfolios = self.load_portfolios()
        if username not in portfolios:
            portfolios[username] = {"name": username, "cash_balance": 10000, "holdings": {}}
            self.save_portfolios()
        return portfolios[username]

    def create_user_if_missing(self, username):
        return self.ensure_user(username)

    def update_user(self, username, user_obj):
        portfolios = self.load_portfolios()
        portfolios[username] = user_obj
        self.save_portfolios()

    def reset_user(self, username):
        portfolios = self.load_portfolios()
        portfolios[username] = {"name": username, "cash_balance": 10000, "holdings": {}}
        self.save_portfolios()

    # last user operations
    def set_last_user(self, username):
        with _lock:
            self._last_user_cache = {"last_user": username}
            self._write_json(LAST_USER_PATH, self._last_user_cache)

    def get_last_user(self):
        with _lock:
            if self._last_user_cache is None:
                self._last_user_cache = self._read_json(LAST_USER_PATH, {})
            return self._last_user_cache.get("last_user")

    # first_run operations
    def is_first_run(self):
        with _lock:
            if self._first_run_cache is None:
                self._first_run_cache = self._read_json(FIRST_RUN_PATH, {"first_run": True})
            return self._first_run_cache.get("first_run", True)

    def set_first_run_false(self):
        with _lock:
            self._first_run_cache = {"first_run": False}
            self._write_json(FIRST_RUN_PATH, self._first_run_cache)

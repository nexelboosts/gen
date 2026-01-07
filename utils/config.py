"""
Config Module
Centralized configuration loading from config.json
"""

import json
import os
from typing import Any, Optional
from utils.logger import log


class Config:
    """Configuration manager singleton"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self, config_path: str = "config.json"):
        """Load configuration from JSON file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            else:
                self._config = {}
                log.warning(f"Config file {config_path} not found, using defaults")
        except Exception as e:
            log.error(f"Error loading config: {e}")
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a config value (in memory only)"""
        self._config[key] = value
    
    def __getitem__(self, key: str) -> Any:
        return self._config.get(key)
    
    def __contains__(self, key: str) -> bool:
        return key in self._config


# Global config instance
config = Config()


def load_config(path: str = "config.json") -> dict:
    """Load config from file and return as dict"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Error loading config: {e}")
        return {}

"""
Proxy Manager Module
Handles loading, parsing, and rotating proxies from proxies.txt
"""

import os
import random
import threading
from typing import Optional, List, Dict
from utils.logger import log


class ProxyManager:
    """Manages proxy rotation for browser instances"""
    
    def __init__(self, proxy_file: str = "proxies.txt"):
        self.proxy_file = proxy_file
        self.proxies: List[Dict[str, str]] = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.load_proxies()

    def load_proxies(self) -> None:
        """Load and parse proxies from file"""
        try:
            if not os.path.exists(self.proxy_file):
                log.warning(f"Proxy file {self.proxy_file} not found")
                return
            
            with open(self.proxy_file, "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
                
                for line in lines:
                    try:
                        proxy = self._parse_proxy_line(line)
                        if proxy:
                            self.proxies.append(proxy)
                    except Exception as e:
                        log.debug(f"Invalid proxy format: {line} ({str(e)})")
                        continue
            
            if self.proxies:
                log.info(f"Loaded {len(self.proxies)} proxies")
            else:
                log.warning("No valid proxies loaded")
                
        except Exception as e:
            log.error(f"Error loading proxies: {str(e)}")

    def _parse_proxy_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        Parse a proxy line in various formats:
        - http://user:pass@host:port
        - user:pass@host:port
        - host:port:user:pass
        - host:port
        """
        line = line.strip()
        if not line:
            return None

        # Handle protocol
        protocol = "http"
        if "://" in line:
            protocol, line = line.split("://", 1)
        
        # Format 1 & 2: user:pass@host:port
        if "@" in line:
            try:
                credentials, host_port = line.split("@", 1)
                if ":" in credentials:
                    username, password = credentials.split(":", 1)
                else:
                    username = credentials
                    password = ""
                
                if ":" in host_port:
                    host, port = host_port.split(":", 1)
                else:
                    host = host_port
                    port = "8080"
                    
                return {
                    "protocol": protocol.lower(),
                    "host": host,
                    "port": port,
                    "username": username,
                    "password": password
                }
            except Exception:
                pass

        # Format 3 & 4: host:port:user:pass OR host:port
        parts = line.split(":")
        
        if len(parts) == 2:
            # host:port
            return {
                "protocol": protocol.lower(),
                "host": parts[0],
                "port": parts[1],
                "username": None,
                "password": None
            }
        elif len(parts) == 4:
            # host:port:user:pass
            return {
                "protocol": protocol.lower(),
                "host": parts[0],
                "port": parts[1],
                "username": parts[2],
                "password": parts[3]
            }
            
        return None

    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """Get the next proxy in rotation"""
        if not self.proxies:
            return None
        
        with self.lock:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
        
        return proxy

    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random proxy"""
        if not self.proxies:
            return None
        
        with self.lock:
            proxy = random.choice(self.proxies)
        
        return proxy

    def get_proxy_dict(self, proxy: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Convert proxy to Playwright-compatible format"""
        if not proxy:
            return None

        protocol = proxy['protocol']
        if protocol not in ['http', 'https', 'socks4', 'socks5']:
            protocol = 'http'

        proxy_url = f"{protocol}://{proxy['host']}:{proxy['port']}"

        if proxy['username'] and proxy['password']:
            return {
                "server": proxy_url,
                "username": proxy['username'],
                "password": proxy['password']
            }
        
        return {"server": proxy_url}

    def get_proxy_for_camoufox(self, proxy: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Convert proxy to Camoufox-compatible format"""
        if not proxy:
            return None

        result = {
            "http": f"http://{proxy['host']}:{proxy['port']}",
            "https": f"http://{proxy['host']}:{proxy['port']}"
        }

        if proxy['username'] and proxy['password']:
            auth_http = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
            result = {
                "http": auth_http,
                "https": auth_http
            }

        return result

    def get_working_proxy_dict(self) -> Optional[Dict[str, str]]:
        """Get next proxy in Camoufox format"""
        proxy = self.get_next_proxy()
        return self.get_proxy_for_camoufox(proxy) if proxy else None

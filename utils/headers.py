import time
import uuid
from base64 import b64encode
from json import dumps
from platform import system, release, version
from typing import Optional, Dict, Any, Union

class HeaderGenerator:
    def __init__(self) -> None:
        self.base_chrome_version: int = 120
        self.ua_details: Dict[str, Any] = self._generate_ua_details()

    def _generate_ua_details(self) -> Dict[str, Any]:
        chrome_major: int = self.base_chrome_version
        full_version: str = f"{chrome_major}.0.0.0"

        os_spec: str = self._get_os_string()
        platform_ua: str = f"Windows NT {release()}; Win64; x64" if "Windows" in os_spec else os_spec

        return {
            "user_agent": (
                f"Mozilla/5.0 ({platform_ua}) AppleWebKit/537.36 "
                f"(KHTML, like Gecko) Chrome/{full_version} Safari/537.36 Edg/{full_version}"
            ),
            "chrome_version": full_version,
            "sec_ch_ua": [
                f'"Google Chrome";v="{chrome_major}"',
                f'"Chromium";v="{chrome_major}"',
                '"Not/A)Brand";v="99"'
            ]
        }

    def _get_os_string(self) -> str:
        os_map: Dict[str, str] = {
            "Windows": f"Windows NT 10.0; Win64; x64",
            "Linux": "X11; Linux x86_64",
            "Darwin": "Macintosh; Intel Mac OS X 10_15_7"
        }
        return os_map.get(system(), "Windows NT 10.0; Win64; x64")

    def generate_super_properties(self) -> str:
        sp: Dict[str, Any] = {
            "os": system(),
            "browser": "Chrome",
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": self.ua_details["user_agent"],
            "browser_version": self.ua_details["chrome_version"].split(".0.")[0] + ".0.0.0",
            "os_version": str(release()),
            "referrer": "https://discord.com/",
            "referring_domain": "discord.com",
            "search_engine": "google",
            "release_channel": "stable",
            "client_build_number": 438971,
            "client_event_source": None,
            "has_client_mods": False,
            "client_launch_id": str(uuid.uuid4()),
            "launch_signature": str(uuid.uuid4()),
            "client_heartbeat_session_id": str(uuid.uuid4()),
            "client_app_state": "focused"
        }
        return b64encode(dumps(sp, separators=(',', ':')).encode()).decode()

    def get_headers(self) -> Dict[str, str]:
        return {
            'authority': 'discord.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://discord.com',
            'referer': 'https://discord.com/register',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': self.ua_details['user_agent'],
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'en-US',
            'x-discord-timezone': 'America/Los_Angeles',
            'x-super-properties': self.generate_super_properties()
        }

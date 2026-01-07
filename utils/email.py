"""
Email Module
Handles temporary email creation and verification link retrieval
"""

import re
import random
import string
import asyncio
import requests
from typing import Optional, Tuple, Set

from utils.logger import log


# Session for email API requests
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Accept": "application/json",
    "Content-Type": "application/json"
})

# Track used emails to prevent duplicates
used_email_ids: Set[str] = set()


def _get_proxy_url(proxy_dict: Optional[dict]) -> Optional[str]:
    """Convert proxy dict to requests-compatible URL"""
    if not proxy_dict:
        return None
    
    server = proxy_dict.get("server", "")
    username = proxy_dict.get("username")
    password = proxy_dict.get("password")
    
    if username and password:
        if "://" in server:
            protocol, host_port = server.split("://", 1)
            return f"{protocol}://{username}:{password}@{host_port}"
        return f"http://{username}:{password}@{server}"
    return server


async def create_temp_email(proxy: Optional[dict] = None) -> Tuple[str, str]:
    """
    Create a temporary email account.
    Returns: (email_address, auth_token)
    """
    base_url = "http://103.114.203.91:8080"
    domain = "@tempmail.katxd.xyz"
    
    proxies = None
    proxy_url = _get_proxy_url(proxy)
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    
    for _ in range(3):
        try:
            random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            username = f"{random_string}{random.randint(100000, 999999)}"
            email = f"{username}{domain}"
            password = f"pass{random.randint(1000, 9999)}"
            header = {"X-API-Key": "0228e946-0e4f-4851-a781-bcddc5e19276"}
            payload = {"email": email, "password": password}
            
            r = session.post(
                f"{base_url}/api/create_account", 
                json=payload, 
                timeout=12, 
                headers=header,
                proxies=proxies
            )
            
            if r.status_code in [200, 201]:
                log.success(f"Created temp email: {email}")
                return email, f"{email}:{password}"
            else:
                log.debug(f"Failed to create account: {r.status_code}")
                
        except Exception as e:
            log.debug(f"Temp mail generate error: {e}")
            await asyncio.sleep(2)
    
    # Fallback
    fallback = f"user{random.randint(100000,999999)}{domain}"
    log.warning(f"Using fallback email: {fallback}")
    return fallback, f"{fallback}:secret"


async def get_verification_link(token: str, proxy: Optional[dict] = None) -> Optional[str]:
    """
    Fetch Discord verification link from email inbox.
    Args:
        token: Format "email:password"
    """
    if not token or ":" not in token:
        return None
    
    try:
        email, password = token.split(":", 1)
    except:
        return None
    
    base_url = "http://103.114.203.91:8080"
    
    proxies = None
    proxy_url = _get_proxy_url(proxy)
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    
    for _ in range(40):
        try:
            payload = {"email": email, "password": password}
            r = session.post(f"{base_url}/api/get_inbox", json=payload, timeout=12, proxies=proxies)
            
            if r.status_code != 200:
                await asyncio.sleep(3)
                continue
            
            data = r.json()
            mails = data if isinstance(data, list) else data.get("emails", [])
            
            for mail in mails:
                mail_id = mail.get("id") or str(hash(mail.get("subject", "") + mail.get("timestamp", "")))
                
                if mail_id in used_email_ids:
                    continue
                
                subject = mail.get("subject", "")
                if "Discord" in subject and ("verify" in subject.lower() or "ยืนยัน" in subject):
                    body = mail.get("body", "") + mail.get("html", "")
                    
                    # Extract verification link
                    patterns = [
                        r'https://click\.discord\.com/ls/click\?[^\s"\')]+',
                        r'https://click\.discord\.com/ls/click\?[^\s"]+',
                        r'https://[^\s"\']*discord[^\s"\']*'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, body)
                        if match and "click.discord.com" in match.group(0):
                            link = match.group(0)
                            used_email_ids.add(mail_id)
                            log.success("Verification link found!")
                            return link
                            
        except Exception as e:
            log.debug(f"Inbox check error: {e}")
        
        await asyncio.sleep(3)
    
    log.warning("No verification email received within 120 seconds")
    return None


async def get_verification_upn(token: str, proxy: Optional[dict] = None) -> Optional[str]:
    """
    Fetch Discord verification UPN from email inbox.
    Args:
        token: Format "email:password"
    """
    if not token or ":" not in token:
        return None
    
    try:
        email, password = token.split(":", 1)
    except:
        return None
    
    base_url = "http://103.114.203.91:8080"
    
    proxies = None
    proxy_url = _get_proxy_url(proxy)
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    
    for _ in range(40):
        try:
            payload = {"email": email, "password": password}
            r = session.post(f"{base_url}/api/get_inbox", json=payload, timeout=12, proxies=proxies)
            
            if r.status_code != 200:
                await asyncio.sleep(3)
                continue
            
            data = r.json()
            mails = data if isinstance(data, list) else data.get("emails", [])
            
            for mail in mails:
                mail_id = mail.get("id") or str(hash(mail.get("subject", "") + mail.get("timestamp", "")))
                
                if mail_id in used_email_ids:
                    continue
                
                subject = mail.get("subject", "")
                if "Discord" in subject and ("verify" in subject.lower() or "ยืนยัน" in subject):
                    body = mail.get("body", "") + mail.get("html", "")
                    
                    # Extract UPN
                    match = re.search(r'upn=([^\s&]+)', body)
                    if match:
                        upn = match.group(1)
                        used_email_ids.add(mail_id)
                        log.success("Verification UPN found!")
                        return upn
                            
        except Exception as e:
            log.debug(f"Inbox check error: {e}")
        
        await asyncio.sleep(3)
    
    log.warning("No verification email received within 120 seconds")
    return None


# Compatibility alias
async def get_email(proxy: Optional[dict] = None) -> Tuple[str, str]:
    """Alias for create_temp_email"""
    return await create_temp_email(proxy)

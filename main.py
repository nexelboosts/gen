import asyncio
import random
import string
import time
from utils.logger import log
from utils.config import config
from utils.email import get_email
from core.solver_service import SolverService
from utils.proxy import ProxyManager

def generate_random_username():
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(10))

def generate_password():
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choice(chars) for _ in range(12))

def generate_dob():
    year = random.randint(1995, 2003)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"

async def main():
    log.info("Start Generating")
    
    # Initialize Proxy Manager
    proxy_manager = ProxyManager()
    
    gen_count = 0
    
    while True:
        try:
            start_time = time.time()
            gen_count += 1
            log.info(f"--- Generation Run #{gen_count} ---")
            
            # --- 1. Proxy Setup ---
            proxy_playwright = None
            if config.get("proxies", False):
                proxy_data = proxy_manager.get_next_proxy()
                if proxy_data:
                    # For Solver (Playwright/Camoufox)
                    proxy_playwright = proxy_manager.get_proxy_dict(proxy_data)
                    # log.info(f"Using proxy: {proxy_data.get('host', 'unknown')[:15]}...")
            
            # --- 2. Email (Retry Loop) ---
            email = None
            mail_token = None
            for attempt in range(3):
                try:
                    log.info(f"Getting email (Attempt {attempt+1})...")
                    email, mail_token = await get_email(proxy_playwright)
                    if email:
                        log.success(f"Got email: {email}")
                        break
                    await asyncio.sleep(1.5)
                except Exception as e:
                    log.warning(f"Email fetch error: {e}")
                    await asyncio.sleep(1.5)
            
            if not email:
                log.error("Failed to get email after 3 attempts. Skipping run.")
                await asyncio.sleep(2)
                continue

            # --- 3. Prepare Registration Data ---
            username = generate_random_username()
            password = config.get("password") or generate_password()
            dob = generate_dob()
            
            registration_data = {
                "email": email,
                "username": username,
                "password": password,
                "dob": dob,
                "mail_token": mail_token
            }

            # --- 4. Execute Registration ---
            log.info(f"Processing user: {username}")
            
            solver_service = SolverService()
            
            # Use the browser to solve captcha AND register in the same session
            try:
                result = await solver_service.solve_and_register(
                    registration_data, 
                    proxy=proxy_playwright, 
                    headless=config.get("headless", True)
                )
            except Exception as e:
                log.error(f"Solver crashed: {e}")
                await asyncio.sleep(3)
                continue
            
            # --- 5. Handle Result ---
            elapsed = time.time() - start_time
            
            if result["success"]:
                token = result['body'].get('token')
                # Use the fancy new logger method
                log.token_generated(
                    token=token,
                    gen_time=elapsed,
                    display_name=username,
                    status="Success"
                )
                
                # Save to tokens.txt
                with open("tokens.txt", "a") as f:
                    f.write(f"{email}:{password}:{token}\n")
            else:
                error_msg = result.get('error') or result.get('status')
                log.error(f"Registration failed: {error_msg}")
                if 'body' in result:
                     log.debug(f"Details: {result['body']}")
            
            # Cool down slightly between runs to avoid spamming CPU if things fail fast
            await asyncio.sleep(2)

        except KeyboardInterrupt:
            log.info("Stopping Ryzen Gen...")
            break
        except Exception as e:
            log.critical(f"Critical Loop Error: {e}")
            await asyncio.sleep(5) # Wait a bit before restarting loop to avoid fast-fail loops

if __name__ == "__main__":
    asyncio.run(main())

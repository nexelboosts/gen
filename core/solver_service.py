from camoufox.async_api import AsyncCamoufox
import asyncio
import json
from solver import Solver
from utils.logger import log
from utils.config import config

class SolverService:
    def __init__(self):
        self.solver = Solver()

    async def verify_email(self, page, verify_link):
        log.info(f"Visiting verification link: {verify_link}")
        try:
            await page.goto(verify_link, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            # Check for success indicators
            # Discord usually redirects to a page saying "Email Verified!" or launches the app.
            # We can check page title or specific text.
            try:
                content = await page.content()
                if "Email Verified" in content or "Continue to Discord" in content:
                    log.success("Email verified successfully!")
                    return True
            except:
                pass
            
            # Sometimes there is a "Verify" button on the landing page if it's a click tracking link
            try:
                verify_btn = await page.query_selector('button:has-text("Verify")')
                if verify_btn:
                    await verify_btn.click()
                    await asyncio.sleep(3)
            except:
                pass

            return True
        except Exception as e:
            log.error(f"Error visiting verification link: {e}")
            return False

    async def solve_and_register(self, registration_data: dict, proxy: dict = None, headless: bool = True):
        browser_kwargs = {
            "headless": headless,
            "window": (1280, 720),
            "disable_coop": True,
            "i_know_what_im_doing": True,
            "humanize": config.get("humanize", False),
            "geoip": bool(proxy)
        }
        
        if proxy:
            browser_kwargs["proxy"] = proxy

        async with AsyncCamoufox(**browser_kwargs) as browser:
            page = await browser.new_page()
            
            log.info("Navigating to Discord registration page...")
            await page.goto("https://discord.com/register", wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # Fill Form Data
            log.info("Filling registration form...")
            try:
                # Email
                await page.fill('input[name="email"]', registration_data['email'])
                
                # Display Name (using username as display name)
                try:
                    await page.fill('input[name="global_name"]', registration_data['username'])
                except:
                    await page.fill('input[name="display_name"]', registration_data['username'])

                # Username
                await page.fill('input[name="username"]', registration_data['username'])
                
                # Password
                await page.fill('input[name="password"]', registration_data['password'])

                # Date of Birth
                # Parse DOB (YYYY-MM-DD)
                dob_parts = registration_data['dob'].split('-')
                year, month, day = dob_parts[0], dob_parts[1], dob_parts[2]
                
                # Year
                await page.click('[class*="year"] div[class*="control"]') 
                await page.click(f'div[class*="option"]:has-text("{year}")')
                
                # Month
                months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                month_name = months[int(month) - 1]
                await page.click('[class*="month"] div[class*="control"]')
                await page.click(f'div[class*="option"]:has-text("{month_name}")')
                
                # Day
                await page.click('[class*="day"] div[class*="control"]')
                await page.click(f'div[class*="option"]:has-text("{int(day)}")') # remove leading zero

                # Checkbox for Terms
                try:
                    await page.click('input[type="checkbox"]', timeout=2000)
                except:
                    pass

                log.info("Clicking Continue...")
                # Try multiple selectors for the continue button
                clicked = False
                submit_selectors = [
                    'button[type="submit"]',
                    'div[role="button"]:has-text("Continue")',
                    'div[class*="button"]:has-text("Continue")',
                    'button:has-text("Continue")'
                ]
                
                for selector in submit_selectors:
                    try:
                        if await page.is_visible(selector):
                            await page.click(selector)
                            clicked = True
                            break
                    except:
                        continue
                
                if not clicked:
                    # Last resort: press Enter
                    await page.keyboard.press("Enter")

                
            except Exception as e:
                log.error(f"Error filling form: {e}")
                return {"success": False, "error": f"Form fill error: {e}"}

            # Wait for Captcha to appear
            log.info("Waiting for Captcha...")
            
            # Solve Captcha
            # Solver will wait for frames to appear
            result = await self.solver.solve_captcha(page)
            
            if not result['success']:
                 log.error(f"Captcha solution failed: {result.get('error')}")
                 return {"success": False, "error": "Captcha failed"}
            
            log.success("Captcha solved! Waiting for token...")

            # Wait for token extraction
            # We loop and check webpack/localStorage
            token = None
            for i in range(20):
                await asyncio.sleep(1)
                token = await page.evaluate("""
                    () => {
                        try {
                            // Method 1: Webpack
                            if (window.webpackChunkdiscord_app) {
                                let token = null;
                                window.webpackChunkdiscord_app.push([
                                    [Math.random()], {}, (req) => {
                                        for (const m of Object.values(req.c)) {
                                            if (m.exports?.default?.getToken) {
                                                token = m.exports.default.getToken();
                                            }
                                        }
                                    }
                                ]);
                                if (token) return token;
                            }
                            // Method 2: LocalStorage
                            return localStorage.getItem('token')?.replace(/"/g, '');
                        } catch(e) { return null; }
                    }
                """)
                if token:
                    break
            
            if not token:
                return {"success": False, "error": "Token not found after captcha solve"}

            # --- Email Verification Step ---
            log.info("Registration success! Waiting for verification email...")
            mail_token = registration_data.get('mail_token')
            if mail_token:
                from utils.email import get_verification_link
                link = await get_verification_link(mail_token, proxy)
                if link:
                    await self.verify_email(page, link)
                else:
                    log.warning("Could not get verification link.")
            else:
                log.warning("No mail token provided for verification.")

            return {"success": True, "body": {"token": token}}

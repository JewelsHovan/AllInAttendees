#!/usr/bin/env python3
"""
Browser automation script to extract bearer token from All In 2025
Uses Playwright to navigate to the site and capture API calls
"""

import asyncio
import json
import base64
import re
import shutil
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from config import COOKIES, HEADERS

class BearerTokenExtractor:
    def __init__(self, headless=False, verbose=True):
        self.headless = headless
        self.verbose = verbose
        self.bearer_token = None
        self.token_found = False
        self.graphql_url = "https://app.swapcard.com/api/graphql"
        self.event_url = "https://app.swapcard.com/event/all-in-2025/people/RXZlbnRWaWV3XzEwNTU5ODE="
        
    def log(self, message):
        """Print log messages if verbose mode is enabled"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def decode_jwt(self, token):
        """Decode JWT token to check expiry"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception as e:
            self.log(f"Error decoding JWT: {e}")
            return None
    
    def validate_token(self, token):
        """Validate that the token is valid and not expired"""
        payload = self.decode_jwt(token)
        if not payload:
            return False, "Could not decode token"
        
        exp = payload.get('exp')
        if not exp:
            return False, "No expiry in token"
        
        expiry_date = datetime.fromtimestamp(exp)
        now = datetime.now()
        
        if now > expiry_date:
            return False, f"Token expired at {expiry_date}"
        
        time_left = expiry_date - now
        return True, f"Token valid until {expiry_date} ({time_left.days} days, {time_left.seconds//3600} hours)"
    
    async def handle_request(self, request):
        """Intercept and analyze requests to extract bearer token"""
        if self.graphql_url in request.url:
            auth_header = request.headers.get('authorization', '')
            
            if auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '')
                
                # Check if this is a new token
                current_token = HEADERS.get('authorization', '').replace('Bearer ', '')
                
                if token and token != current_token:
                    self.log(f"✓ Found new bearer token in GraphQL request!")
                    self.log(f"  First 50 chars: {token[:50]}...")
                    
                    # Validate the token
                    is_valid, message = self.validate_token(token)
                    if is_valid:
                        self.log(f"  {message}")
                        self.bearer_token = token
                        self.token_found = True
                    else:
                        self.log(f"  ⚠️ Token validation failed: {message}")
                elif token == current_token:
                    self.log("  (Same as current token, looking for a fresh one...)")
    
    async def extract_token(self):
        """Main function to extract bearer token using browser automation"""
        async with async_playwright() as p:
            self.log("Starting browser...")
            
            # Launch browser
            browser = await p.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # Create context with cookies
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
            )
            
            # Add cookies to maintain session
            self.log("Adding cookies to browser context...")
            cookies_to_add = []
            
            # Add regular cookies
            for name, value in COOKIES.items():
                cookies_to_add.append({
                    'name': name,
                    'value': value,
                    'domain': '.swapcard.com',
                    'path': '/'
                })
            
            await context.add_cookies(cookies_to_add)
            
            # Create page and set up request interception
            page = await context.new_page()
            
            # Listen for all requests
            page.on('request', self.handle_request)
            
            self.log(f"Navigating to: {self.event_url}")
            
            try:
                # Navigate to the page
                await page.goto(self.event_url, wait_until='networkidle', timeout=30000)
                self.log("Page loaded, waiting for GraphQL calls...")
                
                # Wait a moment for initial API calls
                await page.wait_for_timeout(3000)
                
                # If no token found yet, try scrolling to trigger more API calls
                if not self.token_found:
                    self.log("Scrolling to trigger more API calls...")
                    for i in range(3):
                        await page.evaluate('window.scrollBy(0, 500)')
                        await page.wait_for_timeout(1000)
                        
                        if self.token_found:
                            break
                
                # If still no token, try clicking on filters or refreshing the list
                if not self.token_found:
                    self.log("Trying to interact with page elements...")
                    
                    # Try clicking on a filter or search box if present
                    try:
                        # Look for common interactive elements
                        search_selectors = [
                            'input[type="search"]',
                            'input[placeholder*="Search"]',
                            'button:has-text("Filter")',
                            'button:has-text("Load")',
                            '[data-testid*="search"]'
                        ]
                        
                        for selector in search_selectors:
                            try:
                                element = await page.wait_for_selector(selector, timeout=2000)
                                if element:
                                    await element.click()
                                    await page.wait_for_timeout(2000)
                                    if self.token_found:
                                        break
                            except:
                                continue
                                
                    except Exception as e:
                        self.log(f"Could not interact with elements: {e}")
                
                # Final wait for any pending requests
                await page.wait_for_timeout(2000)
                
            except Exception as e:
                self.log(f"Error during page navigation: {e}")
                
                # Try alternative: check if we're redirected to login
                current_url = page.url
                if 'login' in current_url.lower() or 'auth' in current_url.lower():
                    self.log("⚠️ Redirected to login page. Session might have expired.")
                    self.log("Please login manually and update the cookies in config.py")
            
            finally:
                await browser.close()
        
        return self.bearer_token
    
    def update_config_file(self, new_token):
        """Update the config.py file with the new bearer token"""
        config_path = Path('config.py')
        backup_path = Path('config.py.backup')
        
        # Create backup
        self.log(f"Creating backup: {backup_path}")
        shutil.copy(config_path, backup_path)
        
        # Read current config
        with open(config_path, 'r') as f:
            lines = f.readlines()
        
        # Find and replace the authorization line
        updated = False
        for i, line in enumerate(lines):
            if "'authorization':" in line and 'Bearer' in line:
                # Extract indentation
                indent = len(line) - len(line.lstrip())
                lines[i] = f"{' ' * indent}'authorization': 'Bearer {new_token}',\n"
                updated = True
                self.log(f"Updated authorization header at line {i + 1}")
                break
        
        if updated:
            # Write updated config
            with open(config_path, 'w') as f:
                f.writelines(lines)
            self.log(f"✓ Successfully updated {config_path}")
            return True
        else:
            self.log("⚠️ Could not find authorization line in config.py")
            return False

async def main(auto_update=False):
    """Main function to run the token extraction"""
    print("=" * 60)
    print("Bearer Token Refresh Script")
    print("=" * 60)
    
    # Check current token status
    current_token = HEADERS.get('authorization', '').replace('Bearer ', '')
    if current_token:
        print(f"\nCurrent token (first 50 chars): {current_token[:50]}...")
        
        # Decode and check expiry
        try:
            parts = current_token.split('.')
            if len(parts) == 3:
                payload = parts[1]
                padding = 4 - len(payload) % 4
                if padding != 4:
                    payload += '=' * padding
                decoded = base64.urlsafe_b64decode(payload)
                token_data = json.loads(decoded)
                
                exp = token_data.get('exp')
                if exp:
                    expiry = datetime.fromtimestamp(exp)
                    now = datetime.now()
                    if now > expiry:
                        print(f"⚠️ Current token EXPIRED at {expiry}")
                    else:
                        time_left = expiry - now
                        print(f"Current token expires: {expiry}")
                        print(f"Time remaining: {time_left.days} days, {time_left.seconds//3600} hours")
        except:
            pass
    
    print("\n" + "-" * 60)
    
    # Initialize extractor
    extractor = BearerTokenExtractor(headless=True, verbose=True)
    
    # Extract token
    print("\nExtracting new bearer token from browser session...")
    new_token = await extractor.extract_token()
    
    print("\n" + "=" * 60)
    
    if new_token:
        print("✅ SUCCESS! New bearer token extracted!")
        print("=" * 60)
        
        # Auto-update if flag is set, otherwise ask
        if auto_update:
            print("\nAuto-update mode: Updating config.py...")
            if extractor.update_config_file(new_token):
                print("\n✅ Config file updated successfully!")
                print("Your scraper will now use the new bearer token.")
                return True
            else:
                print("\n⚠️ Failed to update config file automatically.")
                print("Please update manually by replacing the 'authorization' value with:")
                print(f"Bearer {new_token}")
                return False
        else:
            # Interactive mode
            print("\nDo you want to update config.py with the new token?")
            print("(This will create a backup at config.py.backup)")
            
            try:
                response = input("\nUpdate config.py? [y/N]: ").strip().lower()
                
                if response == 'y':
                    if extractor.update_config_file(new_token):
                        print("\n✅ Config file updated successfully!")
                        print("Your scraper will now use the new bearer token.")
                        return True
                    else:
                        print("\n⚠️ Failed to update config file automatically.")
                        print("Please update manually by replacing the 'authorization' value with:")
                        print(f"Bearer {new_token}")
                        return False
                else:
                    print("\nTo manually update, replace the 'authorization' header in config.py with:")
                    print(f"Bearer {new_token}")
                    return False
            except EOFError:
                # Non-interactive environment
                print("\nNon-interactive environment detected.")
                print("To auto-update, run with: python3 refresh_bearer_token.py --auto")
                print("\nTo manually update, replace the 'authorization' header in config.py with:")
                print(f"Bearer {new_token}")
                return False
    else:
        print("❌ Failed to extract bearer token")
        print("=" * 60)
        print("\nPossible reasons:")
        print("1. Session expired - need to login manually")
        print("2. Page structure changed")
        print("3. No GraphQL calls were made")
        print("\nTry running with headless=False to see what's happening:")
        print("  Edit this script and change: BearerTokenExtractor(headless=False)")
        return False

if __name__ == "__main__":
    import sys
    auto_update = '--auto' in sys.argv or '-a' in sys.argv
    asyncio.run(main(auto_update=auto_update))
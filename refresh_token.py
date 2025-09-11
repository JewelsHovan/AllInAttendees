#!/usr/bin/env python3
"""
Token refresh utility for All In 2025 scraping
Checks if the current token is expired and attempts to refresh it
"""

import base64
import json
import requests
from datetime import datetime
import sys

def decode_jwt(token):
    """Decode JWT token to check expiration"""
    if token.startswith('Bearer '):
        token = token[7:]
    
    parts = token.split('.')
    payload = parts[1]
    
    # Add padding if needed
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += '=' * padding
    
    decoded = base64.urlsafe_b64decode(payload)
    return json.loads(decoded)

def check_token_validity(token):
    """Check if token is still valid"""
    try:
        payload = decode_jwt(token)
        exp_time = datetime.fromtimestamp(payload['exp'])
        now = datetime.now()
        
        if now < exp_time:
            hours_remaining = (exp_time - now).total_seconds() / 3600
            print(f"✅ Token is valid. Expires in {hours_remaining:.1f} hours")
            print(f"   Expires at: {exp_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        else:
            print(f"❌ Token expired at: {exp_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return False
    except Exception as e:
        print(f"❌ Error checking token: {e}")
        return False

def update_config_token(new_token):
    """Update the Bearer token in config.py"""
    import config
    
    # Read the current config file
    with open('config.py', 'r') as f:
        lines = f.readlines()
    
    # Find and update the authorization line
    updated = False
    for i, line in enumerate(lines):
        if "'authorization': 'Bearer " in line:
            # Extract the indentation and format
            indent = line[:line.index("'")]
            lines[i] = f"{indent}'authorization': '{new_token}',\n"
            updated = True
            break
    
    if updated:
        # Write back to config
        with open('config.py', 'w') as f:
            f.writelines(lines)
        print("✅ Updated config.py with new token")
        return True
    else:
        print("❌ Could not find authorization line in config.py")
        return False

def main():
    import config
    
    print("=" * 60)
    print("TOKEN VALIDATION CHECK")
    print("=" * 60)
    
    current_token = config.HEADERS.get('authorization', '')
    
    if not current_token:
        print("❌ No token found in config")
        sys.exit(1)
    
    # Check if current token is valid
    if check_token_validity(current_token):
        print("\n✅ Token is still valid. No action needed.")
        sys.exit(0)
    else:
        print("\n⚠️ Token has expired or will expire soon.")
        print("\nTo get a new token:")
        print("1. Open https://app.swapcard.com/event/all-in-2025/people")
        print("2. Open Developer Tools (F12) > Network tab")
        print("3. Refresh the page")
        print("4. Find a GraphQL request")
        print("5. Copy the 'authorization: Bearer ...' header")
        print("\nThen run: python3 refresh_token.py --update 'Bearer YOUR_NEW_TOKEN'")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Check and update authentication token')
    parser.add_argument('--update', help='Update config with new Bearer token', type=str)
    args = parser.parse_args()
    
    if args.update:
        if update_config_token(args.update):
            print("✅ Token updated successfully")
            # Verify the new token
            check_token_validity(args.update)
        else:
            print("❌ Failed to update token")
            sys.exit(1)
    else:
        main()
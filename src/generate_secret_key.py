# Copyright (c) 2024 Nomomo
# Copyright (c) 2024 Kevin Perez - Modified work
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

"""
Helper script to generate a secure secret key for session encryption
and automatically insert it into settings.json.
"""

import secrets
import json
import os
import sys

def generate_secret_key():
    """Generate a secure random secret key."""
    return secrets.token_hex(32)

def update_settings_json(secret_key):
    """Update settings.json with the generated secret key."""
    settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
    
    # Check if settings.json exists
    if not os.path.exists(settings_path):
        print(f"❌ Error: settings.json not found at {settings_path}")
        print(f"💡 Tip: Copy settings.json.example to settings.json first:")
        print(f"   cp src/settings.json.example src/settings.json")
        return False
    
    try:
        # Read existing settings
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        
        # Check if sessionSecretKey already exists and is not empty
        if settings.get('sessionSecretKey') and settings['sessionSecretKey'] not in [None, '', 'GENERATE_WITH_PYTHON_SECRETS_TOKEN_HEX_32']:
            print("⚠️  Warning: sessionSecretKey already exists in settings.json")
            print(f"   Current value: {settings['sessionSecretKey'][:16]}...")
            response = input("   Do you want to replace it? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("❌ Cancelled. Keeping existing secret key.")
                return False
        
        # Update the secret key
        settings['sessionSecretKey'] = secret_key
        
        # Write back to file with nice formatting
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=4)
        
        print("✅ Success! sessionSecretKey has been updated in settings.json")
        print(f"   Secret key: {secret_key[:16]}...{secret_key[-8:]}")
        print(f"   File: {settings_path}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in settings.json: {e}")
        print(f"💡 Tip: Fix the JSON syntax errors in settings.json")
        return False
    except Exception as e:
        print(f"❌ Error updating settings.json: {e}")
        return False

def main():
    print("=" * 70)
    print("Session Secret Key Generator")
    print("=" * 70)
    
    # Generate the secret key
    secret_key = generate_secret_key()
    print(f"\n🔑 Generated new secret key: {secret_key[:16]}...{secret_key[-8:]}")
    
    # Update settings.json
    print("\n📝 Updating settings.json...")
    success = update_settings_json(secret_key)
    
    if success:
        print("\n" + "=" * 70)
        print("✨ All done! Your settings.json has been updated.")
        print("=" * 70)
        print("\n💡 Next steps:")
        print("   1. Make sure you've set webPassword in settings.json")
        print("   2. Make sure you've set palworldServerAdminPassword in settings.json")
        print("   3. Start your application: python src/main.py")
    else:
        print("\n" + "=" * 70)
        print("❌ Failed to update settings.json")
        print("=" * 70)
        print("\n📋 Manual setup:")
        print(f'   Add this to your settings.json:')
        print(f'   "sessionSecretKey": "{secret_key}"')
    
    print("=" * 70)

if __name__ == "__main__":
    main()

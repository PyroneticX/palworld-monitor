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
Helper script to verify that settings.json has all the required fields
for the new authentication system.
"""

import json
import os
import sys

def verify_settings():
    settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
    
    if not os.path.exists(settings_path):
        print(f"❌ Error: settings.json not found at {settings_path}")
        return False
        
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            
        required_fields = [
            'palworldServerAdminPassword',
            'webUsername',
            'webPassword',
            'sessionSecretKey'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in settings:
                missing_fields.append(field)
            elif settings[field] in [None, ""]:
                print(f"⚠️  Warning: '{field}' is present but empty")
                
        if missing_fields:
            print("❌ Missing required settings:")
            for field in missing_fields:
                print(f"   - {field}")
            print("\nPlease add these to your settings.json!")
            return False
            
        # Check for deprecated field
        if 'palworldAdminPassword' in settings:
            print("⚠️  Warning: Found deprecated setting 'palworldAdminPassword'")
            print("   You should remove this after verifying 'palworldServerAdminPassword' is correct.")
            
        print("✅ Settings verification passed!")
        print("   All required authentication fields are present.")
        return True
        
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON in settings.json")
        return False
    except Exception as e:
        print(f"❌ Error reading settings.json: {e}")
        return False

if __name__ == "__main__":
    verify_settings()

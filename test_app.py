#!/usr/bin/env python3
"""Test script for PreDentify Flask application"""

import requests
import json
import time
import sys

def test_endpoints():
    """Test all Flask application endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing PreDentify Application")
    print("=" * 40)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test main page
        print("\n📄 Testing main page...")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Main page loads successfully")
        else:
            print(f"❌ Main page failed: {response.status_code}")
            return False
        
        # Test procedures API
        print("\n🔍 Testing procedures API...")
        response = requests.get(f"{base_url}/api/procedures")
        if response.status_code == 200:
            procedures = response.json()
            print(f"✅ Procedures API works: {len(procedures)} procedures loaded")
            print(f"   Sample procedures: {procedures[:3]}")
        else:
            print(f"❌ Procedures API failed: {response.status_code}")
            return False
        
        # Test providers API
        print("\n👥 Testing providers API...")
        response = requests.get(f"{base_url}/api/providers")
        if response.status_code == 200:
            providers = response.json()
            print(f"✅ Providers API works: {len(providers)} providers loaded")
            print(f"   Providers: {providers}")
        else:
            print(f"❌ Providers API failed: {response.status_code}")
            return False
        
        # Test mitigating factors API
        print("\n⚠️  Testing mitigating factors API...")
        response = requests.get(f"{base_url}/api/mitigating_factors")
        if response.status_code == 200:
            factors = response.json()
            print(f"✅ Mitigating factors API works: {len(factors)} factors loaded")
            print(f"   Sample factors: {[f['name'] for f in factors[:3]]}")
        else:
            print(f"❌ Mitigating factors API failed: {response.status_code}")
            return False
        
        # Test estimation endpoint
        print("\n🧮 Testing estimation endpoint...")
        test_data = {
            "procedure": "Filling",
            "provider": "Kayla",
            "mitigating_factors": ["Special Needs"]
        }
        
        response = requests.post(
            f"{base_url}/estimate",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Estimation endpoint works")
            print(f"   Procedure: {result['procedure']}")
            print(f"   Provider: {result['provider']}")
            print(f"   Total time: {result['final_times']['total_time']} min")
            print(f"   Assistant time: {result['final_times']['assistant_time']} min")
            print(f"   Doctor time: {result['final_times']['doctor_time']} min")
        else:
            print(f"❌ Estimation endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        print("\n🎉 All tests passed! Application is working correctly.")
        print("\n🌐 Access the application at: http://localhost:5000")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Flask app is running.")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_endpoints()
    sys.exit(0 if success else 1) 
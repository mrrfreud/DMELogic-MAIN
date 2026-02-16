"""Test RingCentral phone numbers."""
from dmelogic.settings import load_settings
from dmelogic.services.ringcentral_service import get_ringcentral_service
import requests

settings = load_settings()
service = get_ringcentral_service(settings)

if service and service.is_connected:
    print('Connected to RingCentral')
    
    # Try different API endpoints to find phone numbers
    
    # 1. Try extension info
    print("\n--- Trying /restapi/v1.0/account/~/extension/~ ---")
    url = f'{service.config.server_url}/restapi/v1.0/account/~/extension/~'
    response = requests.get(url, headers=service._get_auth_header(), timeout=15)
    print('Status:', response.status_code)
    if response.status_code == 200:
        data = response.json()
        print(f"Extension ID: {data.get('id')}")
        print(f"Extension Number: {data.get('extensionNumber')}")
        if 'contact' in data:
            contact = data['contact']
            print(f"Name: {contact.get('firstName')} {contact.get('lastName')}")
            print(f"Email: {contact.get('email')}")
    else:
        print('Error:', response.text[:500])
    
    # 2. Try forwarding numbers (sometimes more permissive)
    print("\n--- Trying forwarding-number endpoint ---")
    url = f'{service.config.server_url}/restapi/v1.0/account/~/extension/~/forwarding-number'
    response = requests.get(url, headers=service._get_auth_header(), timeout=15)
    print('Status:', response.status_code)
    if response.status_code == 200:
        data = response.json()
        for rec in data.get('records', []):
            print(f"  Forwarding Number: {rec.get('phoneNumber')}")
    else:
        print('Error:', response.text[:300])
    
    # 3. Try caller ID
    print("\n--- Trying caller-id endpoint ---")
    url = f'{service.config.server_url}/restapi/v1.0/account/~/extension/~/caller-id'
    response = requests.get(url, headers=service._get_auth_header(), timeout=15)
    print('Status:', response.status_code)
    if response.status_code == 200:
        data = response.json()
        print(f"By Device: {data.get('byDevice', [])}")
        print(f"By Feature: {data.get('byFeature', [])}")
    else:
        print('Error:', response.text[:300])

    # 4. Try sending an SMS to see what default from number would be used
    print("\n--- Checking current user info via presence ---")
    url = f'{service.config.server_url}/restapi/v1.0/account/~/extension/~/presence'
    response = requests.get(url, headers=service._get_auth_header(), timeout=15)
    print('Status:', response.status_code)
    if response.status_code == 200:
        data = response.json()
        print(f"User status: {data.get('userStatus')}")
        print(f"Extension: {data.get('extension', {}).get('extensionNumber')}")
    else:
        print('Error:', response.text[:300])
        
else:
    print('Not connected to RingCentral')


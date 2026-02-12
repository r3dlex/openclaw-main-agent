import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes: Read/Write Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate(account_name):
    creds = None
    token_file = f"token_{account_name}.json"
    
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None

        if not creds:
            if not os.path.exists('client_secret.json'):
                print("Error: client_secret.json not found! Please download it from Google Cloud Console.")
                return

            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
            print(f"Token saved to {token_file}")

if __name__ == '__main__':
    account = "andre" # Default to andre
    if len(sys.argv) > 1:
        account = sys.argv[1]
    
    print(f"Authenticating for: {account}")
    authenticate(account)

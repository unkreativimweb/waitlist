import requests
import webbrowser
import http.server
import socketserver
import urllib.parse
import json
import os
from urllib.parse import urlencode

# Genius API credentials
GENIUS_CLIENT_ID = "UOHhyivLsNloYATFsVWTkROncho--frzu--c7B_F8__2zf9IRp36WnVkXtUBppe4"
GENIUS_CLIENT_SECRET = "M_aYL4_SHtmwwxGEKJVYq3LoMAD9nR_rQxnZX68swkz_5lVRalWsu7VWqWhXvgDPctSwMUluPLrHgwgUOlTGkw"
GENIUS_REDIRECT_URI = "http://localhost:8080"
GENIUS_AUTH_URL = "https://api.genius.com/oauth/authorize"
GENIUS_TOKEN_URL = "https://api.genius.com/oauth/token"

# Store the authorization code we'll receive
authorization_code = None

# HTTP request handler for the redirect URI
class AuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global authorization_code
        
        # Parse the query parameters
        query = urllib.parse.urlparse(self.path).query
        if query:
            query_components = urllib.parse.parse_qs(query)
            if 'code' in query_components:
                authorization_code = query_components['code'][0]
                
                # Send a success response to the browser
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authorization Successful!</h1>")
                self.wfile.write(b"<p>You can now close this window and return to your application.</p>")
                self.wfile.write(b"</body></html>")
            else:
                # Handle error
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authorization Failed</h1>")
                self.wfile.write(b"<p>No authorization code was received.</p>")
                self.wfile.write(b"</body></html>")
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Invalid Request</h1></body></html>")

def get_authorization_code():
    global authorization_code
    
    # Construct the authorization URL
    auth_params = {
        'client_id': GENIUS_CLIENT_ID,
        'redirect_uri': GENIUS_REDIRECT_URI,
        'scope': 'me',  # Request access to user info
        'response_type': 'code',
        'state': 'your_state_parameter'  # Use a random string for security
    }
    
    auth_url = f"{GENIUS_AUTH_URL}?{urlencode(auth_params)}"
    
    print(f"Opening browser to authorize application...")
    webbrowser.open(auth_url)
    
    # Start a local web server to handle the redirect
    PORT = 8080
    
    with socketserver.TCPServer(("", PORT), AuthHandler) as httpd:
        print("Server started. Waiting for authorization...")
        
        # Keep the server running until we receive the authorization code
        while authorization_code is None:
            httpd.handle_request()
    
    print("Authorization code received!")
    return authorization_code

def exchange_code_for_token(code):
    # Exchange the authorization code for an access token
    token_data = {
        'code': code,
        'client_id': GENIUS_CLIENT_ID,
        'client_secret': GENIUS_CLIENT_SECRET,
        'redirect_uri': GENIUS_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(GENIUS_TOKEN_URL, data=token_data)
    
    if response.status_code == 200:
        token_info = response.json()
        return token_info
    else:
        print(f"Error exchanging code for token: {response.status_code}")
        print(response.text)
        return None

def save_token_to_file(token_info):
    """Save the token information to cache.json file"""
    try:
        # Load existing cache data
        cache_data = {}
        try:
            with open('data/prod/cache.json', 'r') as f:
                cache_data = json.load(f)
        except FileNotFoundError:
            pass

        # Update with new token info
        cache_data['genius_token'] = token_info

        # Write back to cache
        with open('data/prod/cache.json', 'w') as f:
            json.dump(cache_data, f)
        print("✅ Token saved to cache.json")
        return True
    except Exception as e:
        print(f"❌ Error saving token: {e}")
        return False

def load_token_from_file():
    """Load token information from cache.json file"""
    try:
        with open('data/prod/cache.json', 'r') as f:
            cache_data = json.load(f)
            return cache_data.get('genius_token')
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"❌ Error loading token: {e}")
        return None

def main():
    # Check if we already have a saved token
    token_info = load_token_from_file()
    
    if token_info is None:
        # No saved token, start the authorization flow
        code = get_authorization_code()
        token_info = exchange_code_for_token(code)
        
        if token_info:
            save_token_to_file(token_info)
        else:
            print("Failed to obtain access token.")
            return
    
    # Use the access token
    access_token = token_info['access_token']
    print(f"Access token: {access_token}")

    test_api_call(access_token)

    return token_info
    
def test_api_call(access_token):
    # Test the API with a basic call to get the current user's account info
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get('https://api.genius.com/account', headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        # print("\nAPI call successful!")
        print(f"Logged in as: {user_data['response']['user']['name']}")
        return user_data
    else:
        print(f"API call failed: {response.status_code}")
        print(response.text)
        return None
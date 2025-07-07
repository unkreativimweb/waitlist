import dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import google.generativeai as genai
import genius_auth as genius_auth


def load_env_variables():
    """Load environment variables from .env file"""
    dotenv.load_dotenv(dotenv_path="data/prod/.env")  # Adjust the path to your .env file
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI") 
    GOOGLE_API_KEY = os.getenv('gemini_api_key')
    GENIUS_CLIENT_ID = os.getenv('GENIUS_CLIENT_ID')
    GENIUS_CLIENT_SECRET = os.getenv('GENIUS_CLIENT_SECRET')
    GENIUS_REDIRECT_URI = os.getenv('GENIUS_REDIRECT_URI')
    return SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, GOOGLE_API_KEY, GENIUS_CLIENT_ID, GENIUS_CLIENT_SECRET, GENIUS_REDIRECT_URI

def initialize_spotify_client():
    """Initialize the Spotify client with credentials"""
    SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, *_ = load_env_variables()

    # Initialize the Spotify client
    auth_manager = SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
    
    # Initialize Spotify client with OAuth for user authentication
    global sp
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="playlist-read-private playlist-read-collaborative user-library-read playlist-modify-public playlist-modify-private user-modify-playback-state",  # Added user-modify-playback-state
        cache_path="data/prod/.spotify_cache"
    ))
    return sp

def initialize_gemini_client():
    # Configure Gemini API
    # TODO: WARNING: THE REDIRECT URI IS USED BY TWO DIFFERENT CLIENTS (SPOTIFY AND GENIUS)
    SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, GOOGLE_API_KEY, *_ = load_env_variables() # TODO: dont load all variables
    genai.configure(api_key=GOOGLE_API_KEY) # use configure instead of client
    global model
    model = genai.GenerativeModel('gemini-2.0-flash-lite') #specify the model
    return model

def initialize_genius_client():
    try: 
        # Get vars from env
        SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, GOOGLE_API_KEY, GENIUS_CLIENT_ID, GENIUS_CLIENT_SECRET, GENIUS_REDIRECT_URI = load_env_variables()
        print(f"Genius client id: {GENIUS_CLIENT_ID}; Genius client secret: {GENIUS_CLIENT_SECRET}") 
        # TODO: WARNING: THE REDIRECT URI IS USED BY TWO DIFFERENT CLIENTS (SPOTIFY AND GENIUS)
        AUTH_URL = "https://api.genius.com/oauth/authorize"
        TOKEN_URL = "https://api.genius.com/oauth/token"

        # Get the authorization info & code from the callback server
        genius_token_info = genius_auth.main()
        print(f"Genius token info: {genius_token_info}") # Print the token info for debugging
        return
        # authorization_code = genius_token_info['code']

    except Exception as e:
        print(f"❌ Error initializing Genius client: {e}")
        return None

import dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import inquirer
from datetime import datetime
import google.generativeai as genai
import requests
import json

# load environment variables from .env file
dotenv.load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI") 

# Initialize the Spotify client
client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)   

# Initialize Spotify client with OAuth for user authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="playlist-read-private playlist-read-collaborative user-library-read playlist-modify-public playlist-modify-private",  # Added user-library-read scope
    cache_path=".spotify_cache"  # Store token locally to avoid re-authentication
))

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('gemini_api_key')
genai.configure(api_key=GOOGLE_API_KEY) # use configure instead of client
global model
model = genai.GenerativeModel('gemini-1.5-flash-latest') #specify the model

def from_where():
    # Get all user playlists and create a list of choices
    all_playlists = sp.current_user_playlists()
    playlist_choices = [item['name'] for item in all_playlists['items']]
    playlist_choices.append('None - Search all songs')  # Add option to search without playlist context

    # Create interactive prompts for user input
    type_question = [
        inquirer.List('search_type',
            message="Do you want to search for a playlist or a song?",
            choices=[ # TODO: make other options functional
                # 'playlist', # (is possible to search for a playlist)
                'song', 
                # 'liked songs', 
                # 'album',
                # 'artist',
                # 'None - Search all songs'
            ]),
    ]
    playlist_question = [
        inquirer.List('playlist',
            message="Select a playlist:",
            choices=playlist_choices)
    ]

    # Get user's search preference (playlist or song)
    global origin_type
    origin_type = inquirer.prompt(type_question)

    if origin_type['search_type'] == 'playlist':
        # Handle playlist selection
        chosen_playlist = inquirer.prompt(playlist_question)
        print(f"Selected playlist: {chosen_playlist['playlist']}")
        # Find and return the playlist ID
        for item in all_playlists['items']:
            if item['name'] == chosen_playlist['playlist']:
                print(f"Found playlist: {item['name']} with ID: {item['id']}")
                global playlist_id
                playlist_id = item['id']
                return item['id']

    elif origin_type['search_type'] == 'song':
        # Handle song search
        track_name = input("Enter the name of the song you want to search for: ")
        track_results = sp.search(q='track:' + track_name, type='track', limit=50)  # Search up to 50 tracks

        # Check if any tracks were found
        if not track_results['tracks']['items']:
            print(f"No song found for: {track_name}")
            return None
        
        # Create a list of tracks with artist names for better identification
        multiple_tracks = []
        track_info = {}  # Dictionary to store track IDs mapped to display names
        
        # Process each track result
        for item in track_results['tracks']['items']:
            track_with_artist = f"{item['name']} - {item['artists'][0]['name']}"
            multiple_tracks.append(track_with_artist)
            track_info[track_with_artist] = item['id']
        
        # Create interactive track selection prompt
        track_question = [
            inquirer.List('track',
                message="Select a track:",
                choices=multiple_tracks)
        ]
        
        # Get user's track selection and return the corresponding track ID
        answer = inquirer.prompt(track_question)
        print("==========this is for debugging purposes==========\n")
        selected_track = answer['track']
        global track_id
        track_id = track_info[selected_track]
        global is_track
        is_track = True  # Set flag to indicate a track was selected
        
        print(f"Selected song: {selected_track} (ID: {track_id})")
        return track_id
    
    elif origin_type['search_type'] == 'liked songs':
        # Get user's liked songs (saved tracks)
        results = sp.current_user_saved_tracks()
        liked_tracks = []
        track_info = {}

        # Process saved tracks
        for item in results['items']:
            track = item['track']
            track_with_artist = f"{track['name']} - {track['artists'][0]['name']}"
            liked_tracks.append(track_with_artist)
            track_info[track_with_artist] = track['id']

        # Create selection prompt for liked songs
        liked_question = [
            inquirer.List('track',
                message="Select from your liked songs:",
                choices=liked_tracks)
        ]

        answer = inquirer.prompt(liked_question)
        selected_track = answer['track']
        track_id = track_info[selected_track]
        
        print(f"Selected liked song: {selected_track} (ID: {track_id})")
        return track_id

    elif origin_type['search_type'] == 'album':
        # Get album name from user
        album_name = input("Enter the name of the album you want to search for: ")
        album_results = sp.search(q='album:' + album_name, type='album', limit=20)

        if not album_results['albums']['items']:
            print(f"No album found for: {album_name}")
            return None

        # Create album list with artists
        albums = []
        album_info = {}
        
        for item in album_results['albums']['items']:
            album_with_artist = f"{item['name']} - {item['artists'][0]['name']}"
            albums.append(album_with_artist)
            album_info[album_with_artist] = item['id']

        # Create album selection prompt
        album_question = [
            inquirer.List('album',
                message="Select an album:",
                choices=albums)
        ]

        answer = inquirer.prompt(album_question)
        selected_album = answer['album']
        global album_id
        album_id = album_info[selected_album]
        
        print(f"Selected album: {selected_album} (ID: {album_id})")
        return album_id
    
    elif origin_type['search_type'] == 'artist':
        # Get artist name from user
        artist_name = input("Enter the name of the artist you want to search for: ")
        artist_results = sp.search(q='artist:' + artist_name, type='artist', limit=20)

        if not artist_results['artists']['items']:
            print(f"No artist found for: {artist_name}")
            return None

        # Create artist list
        artists = []
        artist_info = {}
        
        for item in artist_results['artists']['items']:
            artists.append(item['name'])
            artist_info[item['name']] = item['id']

        # Create artist selection prompt
        artist_question = [
            inquirer.List('artist',
                message="Select an artist:",
                choices=artists)
        ]

        answer = inquirer.prompt(artist_question)
        selected_artist = answer['artist']
        global artist_id
        artist_id = artist_info[selected_artist]
        
        print(f"Selected artist: {selected_artist} (ID: {artist_id})")
        return artist_id

    return None  # Return None if no selection was made

def get_discovery_type():
    what_type = [
        inquirer.List('what_type',
            message="What do you want to do?",
            choices=[
                'i want to hear the same music as a playlist/song etc.',
                'mood',
                'genre',
                'discover new releases',
                'top charts',
                'recommendations based on time of day',
                'decade specific music',
            ]),
    ]

    discovery = inquirer.prompt(what_type)

    if discovery['what_type'] == 'i want to hear the same music as a playlist/song etc.':
        print("You chose to hear the same music as a playlist/song.")
        return '"the same music as"'
    elif discovery['what_type'] == 'mood':
        print("You chose mood-based music.")
        return '"the same mood as"'
    elif discovery['what_type'] == 'genre':
        print("You chose genre-based music.")
        return '"the same genre as"'
    elif discovery['what_type'] == 'discover new releases':
        print("You chose to discover new releases.")
        return '"new releases"'
    elif discovery['what_type'] == 'top charts':
        print("You chose top charts.")
        return '"top charts"'
    elif discovery['what_type'] == 'recommendations based on time of day':
        print("You chose recommendations based on time of day.")
        current_time = datetime.now().strftime("%H:%M")
        return f'recommendations based on the time of day ({current_time})'
    elif discovery['what_type'] == 'decade specific music':
        print("You chose decade-specific music.")
        return '"music in the same decade as"'
    
def ask_ai(discovery_type, origin, limit, track_attributes):
    '''
    This function sends a request to the AI model for music recommendations based on the provided parameters.
    It includes error handling for various scenarios and formats the response accordingly.
    It has the possibility to check if the Gemini API is working properly. (if needed)
    '''

    # if not check_gemini_status():
    #     print("❌ Gemini API is not working properly")
    #     return "ERROR: Gemini API unavailable"

    print('Origin: ', origin) # Print the origin (playlist/song/liked songs/album/artist)
    print('Limit: ', limit) # Print the limit (number of recommendations)
    track_attributes = json.dumps(track_attributes) # Convert track attributes to JSON string for AI input
    response = model.generate_content(
        """You are a music recommendation engine. Your task is to recommend music based on the following criteria:

        Input Parameters:
        - Discovery Type: {discovery_type} (defines what kind of music to recommend)
        - Origin: {origin} (the reference point for recommendations)
        - Track Attributes: {track_attributes} (musical characteristics to consider)
        
        Response Rules:
        1. Output Format: ONLY return a comma-separated list of 'song-artist' pairs
        2. Maximum Recommendations: {limit}
        3. Format Example: "Bohemian Rhapsody-Queen, Yesterday-The Beatles"
        
        Error Handling:
        - If logical error: return "ERROR: Invalid input combination"
        - If missing data: return "ERROR: Cannot access required data"
        - For any other error: return "ERROR: [specific error message]"
        
        DO NOT include any additional text, explanations, or formatting.""".format(
            discovery_type=discovery_type,
            origin=origin,
            track_attributes=json.dumps(track_attributes),
            limit=limit
        )
    )
    print("AI Response: ", response.text) # Print the AI's response
    print("==================================================\n")
    return response.text

def id_to_element_name(track_id):
    # Get track details using the track ID
    element = sp.track(track_id)
    # Extract the track name and artist name
    element_name = element['name']
    if element['type'] == 'track':
        artist_name = element['artists'][0]['name']
        return f"{element_name} ({element['type']}) - {artist_name}"
    elif element['type'] == 'album':
        return f"{element_name} - Album"
    elif element['type'] == 'artist':
        return f"{element_name} - Artist"
    elif element['type'] == 'playlist':
        return f"{element_name} - Playlist"
    else:
        return f"{element_name} - Unknown Type"

def check_gemini_status():
    """Check if Gemini API is properly configured and working"""
    try:
        # Test the model with a simple prompt
        test_response = model.generate_content("Reply with 'OK' if you can read this.")
        if test_response and test_response.text.strip() == "OK":
            return True
        else:
            print("⚠️ Gemini API response is not as expected")
            return False
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return False

def get_audio_db_info(artist_name, track_name):
    """
    Get track information from TheAudioDB API
    Returns: dict with track information or None if not found
    """
    # TheAudioDB API endpoint
    url = f"https://www.theaudiodb.com/api/v1/json/2/searchtrack.php?s={artist_name.strip().replace(" ", "%20")}&t={track_name.strip().replace(" ", "%20")}"
    # print(f"audiodb API URL: {url}")  # Print the API URL for debugging
    try:
        response = requests.get(url)
        # print(f"audiodb API Response: {response}")  # Print the API response status code
        data = response.json()
        # print(f"audiodb API Data: {data}")  # Print the API response data for debugging
        
        if not data['track'] or len(data['track']) == 0:
            print(f"No data found for {track_name} by {artist_name}")
            return None
            
        track = data['track'][0]
        # print(f"Track data: {track["strMood"]}")  # Print the track data for debugging
        return {
            'idLyric': track.get('idLyric', None),
            'intDuration': track.get('intDuration', None),
            'strGenre': track.get('strGenre', None),
            'strMood': track.get('strMood', None),
            'strStyle': track.get('strStyle', None),
            'strTheme': track.get('strTheme', None),
            'intTotalPlays': track.get('intTotalPlays', None)
        }
        
    except Exception as e:
        print(f"Error getting track info: {e}")
        return None

def string_to_list(string):
    """
    Convert a comma-separated string to a list of song-artist pairs
    Returns: List of strings, each formatted as 'song-artist'
    """
    # Split by comma and clean each entry
    items = [item.strip() for item in string.split(',')]
    
    # Remove any empty strings and clean newlines
    cleaned_items = [item.replace('\n', '') for item in items if item]
    
    # print("Converted list: ", cleaned_items)
    return cleaned_items

def process_track_recommendation(origin_name, discovery_type, limit):
    """
    Process a track and get AI recommendations based on its attributes
    Args:
        origin_name (str): Track name in format "Song Name (type) - Artist"
        discovery_type (str): Type of discovery/recommendation wanted
        limit (int): Number of recommendations to return
    Returns:
        list: List of recommended tracks
    """
    # Extract track name and artist from the formatted string
    track_name = origin_name.split(' - ')[0].split('(')[0].strip()
    artist_name = origin_name.split(' - ')[1].strip()
    
    # print(f"Processing track: '{track_name}' by '{artist_name}'")
    
    # Get additional track information from TheAudioDB
    track_attributes = get_audio_db_info(track_name, artist_name)
    
    # Get AI recommendations
    ai_response = ask_ai(discovery_type, origin_name, limit, track_attributes)
    
    # Convert AI response to list of recommendations
    recommendations = string_to_list(str(ai_response))
    
    # Verify recommendation count
    if len(recommendations) != limit:
        print(f"⚠️ PSA: Got {len(recommendations)} recommendations instead of requested {limit}")
    
    return recommendations

class PlaylistManager:
    def __init__(self, sp):
        self.sp = sp
        self.playlist = None

    def create_playlist(self, username):
        playlist_description = PlaylistManager.get_playlist_description(discovery_type, origin_name, origin_type)
        playlist_name = PlaylistManager.get_playlist_name(origin_name, origin_type, discovery_type)
        self.playlist = self.sp.user_playlist_create(
            user=username,
            name=playlist_name,
            public=False,
            collaborative=False,
            description=playlist_description
        )

    def get_playlist_cover_image(playlist_id):
        # TODO: get_playlist_cover_image
        pass

    def get_playlist_name(origin_name, origin_type, discovery_type):
        """
        Generate a playlist name based on the origin name and discovery type
        Args:
            origin_name (str): Name of the original track/playlist/album/artist
            origin_type (str): Type of origin wanted
            discovery_type (str): Type of discovery/recommendation wanted
        Returns:
            str: Generated playlist name
        """
        return f"{discovery_type} - {origin_name} ({origin_type})"

    def get_playlist_description(discovery_type, origin_name, origin_type):
        """
        Generate a playlist description based on the discovery type and origin name
        Args:
            discovery_type (str): Type of discovery/recommendation wanted
            origin_name (str): Name of the original track/playlist/album/artist
        Returns:
            str: Generated playlist description
        """
        return f"Discover {discovery_type} music based on the {origin_type}: {origin_name}"

    def process_playlist_recommendation(origin_name, recommendations):
        pass

    def fill_playlist(self, recommendations):
        # get recommended track uris
        recommended_track_ids = []
        max_retries = 3  # Number of retries for each track
        for rec in recommendations:
            name, artist = rec.split('-')
            for attempt in range(max_retries):
                try:
                    result = self.sp.search(
                        q=f'track:{name} artist:{artist}',
                        type='track',
                        limit=1,
                    )
                    if result['tracks']['items']:
                        track_uri = result['tracks']['items'][0]['uri']
                        recommended_track_ids.append(track_uri)
                        print(f"✅ Found track: {name} by {artist}")
                        break  # Success, exit retry loop
                    else:
                        print(f"❌ Could not find track: {name} by {artist}")
                        break  # No results, no need to retry
                        
                except requests.exceptions.Timeout:
                    if attempt == max_retries - 1:
                        print(f"⚠️ Timeout error after {max_retries} attempts: {name} by {artist}")
                    else:
                        print(f"⚠️ Attempt {attempt + 1} timed out, retrying...")
                        continue
                        
                except Exception as e:
                    print(f"❌ Error processing track: {e}")
                    break
        if recommended_track_ids:
            self.sp.playlist_add_items(self.playlist['id'], recommended_track_ids)
            print(f"✅ Added {len(recommended_track_ids)} tracks to the playlist: {self.playlist['name']}")

discovery_type = get_discovery_type() # auf was soll sich suche beziehen (mood/genre ehatever) -> returns string
origin_id = from_where() # von wo soll gesucht werden (playlist/song/liked songs/album/artist) -> returns id
origin_name = id_to_element_name(origin_id) # convert id to name (for AI input) -> returns string
limit = 10 # TODO: make this a user input

if is_track:
    recommendations = process_track_recommendation(origin_name, discovery_type, limit)
    print(f"🎵 Found {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    print("")  # print a new line for better readability
    
    # Create playlist manager instance
    playlist_manager = PlaylistManager(sp)
    # Create the playlist
    playlist_manager.create_playlist(sp.me()['id'])
    # Fill the playlist
    playlist_manager.fill_playlist(recommendations)

'''
TODO:
- add a function to create a playlist with the recommendations x
- add a function to add the recommendations to the playlist x
- add posibility to add to queue
- database is not really uptodate (maybe use a different one?)
- add a function to get the playlist cover image (if available)
'''

# playlist_replace_items(playlist_id, items)
# playlist_upload_cover_image(playlist_id, image_b64)

# SEARCHING: https://developer.spotify.com/documentation/web-api/reference/search
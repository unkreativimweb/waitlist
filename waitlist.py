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

def id_to_element_name(element_id):
    """
    Convert a Spotify ID to a readable name, handling different types (track, playlist, album, artist)
    Args:
        element_id (str): Spotify ID of the element
    Returns:
        str: Formatted name of the element
    """
    try:
        # First try as playlist
        try:
            element = sp.playlist(element_id)
            return f"{element['name']} (playlist)"
        except:
            pass
        
        # Then try as track
        try:
            element = sp.track(element_id)
            return f"{element['name']} (track) - {element['artists'][0]['name']}"
        except:
            pass
        
        # Then try as album
        try:
            element = sp.album(element_id)
            return f"{element['name']} (album) - {element['artists'][0]['name']}"
        except:
            pass
        
        # Finally try as artist
        try:
            element = sp.artist(element_id)
            return f"{element['name']} (artist)"
        except:
            pass
            
        raise Exception("Could not identify element type")
        
    except Exception as e:
        print(f"Error getting element name: {e}")
        return f"Unknown Element ({element_id})"

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
    print(f"Processing track: {origin_name}")
    print(f"Discovery type: {discovery_type}")
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

    def create_playlist(self, username, playlist_name=None):
        # playlist_description = PlaylistManager.get_playlist_description(discovery_type, origin_name, origin_type)
        if playlist_name is None:
            playlist_name = PlaylistManager.get_playlist_name()

        self.playlist = self.sp.user_playlist_create(
            user=username,
            name=playlist_name,
            public=False,
            collaborative=False,
            # description=playlist_description
        )

    def get_playlist_cover_image(playlist_id):
        # TODO: get_playlist_cover_image
        pass

    def get_playlist_name():
        """
        Generate a playlist name based on the origin name and discovery type
        Args:
            origin_name (str): Name of the original track/playlist/album/artist
            origin_type (str): Type of origin wanted
            discovery_type (str): Type of discovery/recommendation wanted
        Returns:
            str: Generated playlist name
        """
        return input (f"Enter a name for the playlist: ") 

    def get_playlist_description():
        """
        Generate a playlist description based on the discovery type and origin name
        Args:
            discovery_type (str): Type of discovery/recommendation wanted
            origin_name (str): Name of the original track/playlist/album/artist
        Returns:
            str: Generated playlist description
        """
        return input (f"Enter a description for the playlist: ")

    def process_playlist_recommendation(origin_name, recommendations):
        pass

    def change_playlist_name(self, old_name, new_name, is_default_playlist=False): # no need for is_default_playlist here, but maybe later
        global default_playlist_name
        # Get all user playlists and find the one to rename
        if old_name == default_playlist_name:
            default_playlist_name = new_name
            # Update the cache with the new default playlist name
            update_cache_data('default_playlist_name', new_name)
            print(f"Warning Default playlist name changed from '{old_name}' to '{new_name}'")

        all_playlists = sp.current_user_playlists()
        for item in all_playlists['items']:
            if item['name'] == old_name:
                # Rename the playlist
                sp.user_playlist_change_details(
                    user=sp.me()['id'],
                    playlist_id=item['id'],
                    name=new_name,
                    public=False,
                    collaborative=False,
                    description=item['description']
                )
                if is_default_playlist:
                    print(f"Default playlist name changed from '{old_name}' to '{new_name}'")
                else:
                    print(f"Renamed playlist '{old_name}' to '{new_name}'")
                return

        print(f"Playlist '{old_name}' not found. No changes made.")

    def find_user_playlist_id(self, playlist_name):
        """Find a specific playlist ID owned by the current user"""
        try:
            # Get all user playlists
            playlists = self.sp.current_user_playlists()
            
            # Search through user's playlists
            for playlist in playlists['items']:
                if playlist['name'] == playlist_name and playlist['owner']['id'] == self.sp.me()['id']:
                    return playlist['id']
            
            print(f"❌ Playlist '{playlist_name}' not found in your library")
            return None
        except Exception as e:
            print(f"❌ Error finding playlist: {e}")
            return None

    def fill_playlist(self, recommendations, playlist_id=None):
        # get recommended track uris
        recommended_track_ids = []
        max_retries = 3  # Number of retries for each track
        for rec in recommendations:
            if rec.count('-') == 1:
                # Split the recommendation into track name and artist
                name, artist = rec.split('-')
            else:
                print(f"❌ Invalid recommendation format: {rec}, this error will be fixed in the future")
                return
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
            # get the playlist id if given
            if playlist_id:
                self.sp.playlist_add_items(playlist_id, recommended_track_ids)
            else:
                # Add the recommended tracks to the playlist
                self.sp.playlist_add_items(self.playlist['id'], recommended_track_ids)

def what_to_do():
    # Create interactive prompts for user input
    what_to_do_choices = [
        inquirer.List('what_to_do_choices',
            message="What do you want to do?",
            choices=[
                'new recommendations',
                'add to liked songs', # TODO: implement if needed
                'settings',
                'nothing'
            ]),
    ]
    to_do_answer = inquirer.prompt(what_to_do_choices)
    if to_do_answer['what_to_do_choices'] == 'new recommendations':
        new_recs_question = [
            inquirer.List('new_recs',
                message="Where?",
                choices=[
                    'default playlist',
                    'create a new playlist',
                    'override another old playlist', # TODO: implement this
                    'add to existing playlist', # TODO
                    'add to queue', # TODO
                ]),
        ]
        new_recs_answer = inquirer.prompt(new_recs_question)
        if new_recs_answer['new_recs'] == 'default playlist':
            if default_playlist_name == "":
                print("No default playlist set. Please set a default playlist in the settings first.")
                return
            else: 
                global default_playlist_id
                if default_playlist_id is None and default_playlist_name is None: # if the default playlist id is not set, get it from the name
                    print("No default Playlist found. Please set one in the settings, or check Cache.")
                    return
                default_playlist_id = playlist_manager.find_user_playlist_id(default_playlist_name)
                old_tracks = [] # create a list to store the old tracks (to delete them later)
                results = playlist_manager.sp.playlist_tracks(default_playlist_id) # get the tracks from the default playlist & put them in a list
                for item in results['items']:
                    if item['track']:
                        old_tracks.append(item['track']['uri'])
                while results['next']:
                    results = playlist_manager.sp.next(results)
                    for item in results['items']:
                        if item['track']:
                            old_tracks.append(item['track']['uri'])
                playlist_manager.sp.playlist_replace_items(default_playlist_id, old_tracks) # remove the old tracks from the playlist
                print(f"Removed {len(old_tracks)} old tracks from the default playlist: {default_playlist_name}")
                basic_process(default_playlist_id) # fill the playlist with the new recommendationsq
        if new_recs_answer['new_recs'] == 'create a new playlist':
            basic_process()
        return True # continue the loop
    elif to_do_answer['what_to_do_choices'] == 'add to liked songs':
        print("NOT IMPLEMENTED YET")
        return True # continue the loop
    elif to_do_answer['what_to_do_choices'] == 'settings':
        while settings():
            pass
        return True # continue the loop
    elif to_do_answer['what_to_do_choices'] == 'nothing':
        print("Nothing to do. Exiting...")
        return False # exit the loop
    
def settings():
    global default_playlist_name
    # Create interactive prompts for user input
    basic_settings = [
        inquirer.List('settings',
            message="Settings",
            choices=[
                'set/change default playlist',
                'change playlist name',
                'change default playlist description',
                'change default limit for recommendations',
                # 'toggle playlist public/private',
                # 'toggle playlist collaborative',
                # 'change default playlist cover', 
                'advanced settings',
                'back'
            ]),
    ]
    advanced_settings = [
        inquirer.List('advanced_settings',
            message="Advanced Settings",
            choices=[
                'change Gemini API key',
                'clear authentication (resetting Spotify token)',
                'clear cache (not Spotify token)',
                # 'toggle debug mode', TODO: implement debug mod
                'back'
            ]),
    ]

    basic_settings_answer = inquirer.prompt(basic_settings)

    if basic_settings_answer['settings'] == 'advanced settings':
        advanced_settings_answer = inquirer.prompt(advanced_settings)
        if advanced_settings_answer['advanced_settings'] == 'clear authentication (resetting Spotify token)':
            open('.spotify_cache', 'w').close() # Clear the cache file to force re-authentication (by overwriting it)
            print("Spotify account changed. Please re-authenticate.")
        elif advanced_settings_answer['advanced_settings'] == 'change Gemini API key':
            os.putenv("gemini_api_key", input("Enter new Gemini API key: "))
        elif advanced_settings_answer['advanced_settings'] == 'clear cache (not Spotify token)':
            confirm = inquirer.prompt([
            inquirer.List('confirm',
                    message="⚠️  Warning: This will clear all cached settings (playlist names, limits, etc). Are you sure?",
                    choices=[
                        'Yes, clear cache',
                        'No, keep cache'
                    ]),
            ])
            
            if confirm['confirm'] == 'Yes, clear cache':
                update_cache_data('default_playlist_name', None) # reset the default playlist name to None
                update_cache_data('default_limit', 10) # reset the default limit to 10
                print("✅ Cache cleared successfully")
                # FIXME: this is not working as expected, it should clear the whole cache file (cant do it with overwriting tho
            else:
                print("Cache clearing cancelled")
        elif advanced_settings_answer['advanced_settings'] == 'back':
            settings()
    elif basic_settings_answer['settings'] == 'set/change default playlist':
        new_name = input("Enter the new default playlist name: ")
        if default_playlist_name is not None:
            print("old name assigned to None")
            old_name = default_playlist_name
        default_playlist_name = new_name

        # rewrite the default playlist name in the cache so it can be used later
        if update_cache_data('default_playlist_name', new_name):
            print(f"✅ Default playlist name saved to cache: {new_name}")
        else:
            print("⚠️ Failed to save playlist name to cache")
        
        print(f"Default playlist name set to: {default_playlist_name}")
        
        override_or_create_new_default = inquirer.prompt([
            inquirer.List('override/create default',
                message=f"Do you want to overwrite the old default playlist name from {old_name if 'old_name' in locals() else 'None'} to {new_name} or create a new?",
                choices=[
                    'overwrite old default playlist name',
                    'create new default playlist'
                ]),
        ])
        if override_or_create_new_default['override/create default'] == 'overwrite old default playlist name':
            if old_name is not None:
                playlist_manager.change_playlist_name(old_name, new_name, True) # change playlist name
                update_cache_data('default_playlist_name', new_name) # update the cache with the new default playlist name
            else:
                print("There is no old playlist to overwrite.")
                return
        elif override_or_create_new_default['override/create default'] == 'create new default playlist':
            playlist_manager.create_playlist(sp.me()['id'], default_playlist_name) # create a new playlist with the new name
            update_cache_data('default_playlist_name', new_name) # update the cache with the new default playlist name
            print(f"New default playlist created: {new_name}")
        
    elif basic_settings_answer['settings'] == 'change default playlist description':
        new_description = input("Enter the new playlist description: ")
        global default_playlist_id
        default_playlist_id = playlist_manager.find_user_playlist_id(default_playlist_name) # get the playlist id from the name
        if default_playlist_id is None:
            print("Cannot update description: Playlist not found")
            return

        playlist_manager.sp.user_playlist_change_details(
            user=sp.me()['id'],
            playlist_id=default_playlist_id,
            name=playlist_manager.sp.playlist(default_playlist_id, fields=['name']), # get the name of the playlist
            public=False,
            collaborative=False,
            description=new_description #set the new description
        )

        print(f"Default Playlist description changed to: {new_description}")

        
    elif basic_settings_answer['settings'] == 'change playlist name':
        old_name = input("Enter the old playlist name: ")
        new_name = input("Enter the new playlist name: ")
        playlist_manager.change_playlist_name(old_name, new_name) # TODO: implement this function      
    
    elif basic_settings_answer['settings'] == 'change default limit for recommendations':
        new_limit = input("Enter the new default limit for recommendations: ")
        default_limit = new_limit
        update_cache_data('default_limit', default_limit) # update the cache with the new limit
        print(f"Default limit for recommendations changed to: {default_limit}")
    
    elif basic_settings_answer['settings'] == 'back':
        return False # go back to the main menu
    
    else:
        print("Invalid choice or Error. Please try again.")
        settings()

def basic_process(playlist_id=None): 
    global discovery_type
    discovery_type = get_discovery_type() # auf was soll sich suche beziehen (mood/genre ehatever) -> returns string
    origin_id = from_where() # von wo soll gesucht werden (playlist/song/liked songs/album/artist) -> returns id
    origin_name = id_to_element_name(origin_id) # convert id to name (for AI input) -> returns string
    if playlist_id is None:
        # destination_playlist_name = input("Enter a name for the new playlist: ") # ask for a name for the new playlist
        pass
    elif playlist_id is not None: # lol idk why (when id is given)
        print(f"discovered playlist id input ({playlist_id})")
        

    if is_track: # if a track was selected
        recommendations = process_track_recommendation(origin_name, discovery_type, limit=default_limit) # get recommendations based on the track, discovery type and limit -> returns list of strings (song-artist pairs)
        print(f"🎵 Found {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        print("")  # print a new line for better readability

        # Create the playlist if not already created
        if playlist_id is None:
            playlist_manager.create_playlist(sp.me()['id'])
            # FIXME: der filled doch garnicht??? -> muss glaube noch fill_playlist aufgerufen werden
        else:
            playlist_manager.fill_playlist(recommendations, playlist_id) # fill the playlist with the recommendations

def update_cache_data(key, value):
    """Update a specific key in the cache file while preserving other data"""
    try:
        # Read existing cache data
        cache_data = {}
        try:
            with open('.cache', 'r') as cache:
                cache_data = json.load(cache)
        except (FileNotFoundError, json.JSONDecodeError):
            # File doesn't exist or is empty/invalid
            pass

        # Update the specific key
        cache_data[key] = value

        # Write back all data
        with open('.cache', 'w') as cache:
            json.dump(cache_data, cache)
            
        return True
    except Exception as e:
        print(f"❌ Error updating cache: {e}")
        return False


# ======================================================================
# Main program starts here

global default_limit
if os.path.exists('.cache'):
    with open('.cache', 'r') as cache:
        cache_data = json.load(cache)
        default_limit = cache_data.get('default_limit', None)
else: default_limit = None # read the default playlist name from the cache (if it exists)

global playlist_manager
playlist_manager = PlaylistManager(sp)

global default_playlist_name
global default_playlist_id

if os.path.exists('.cache'):
    with open('.cache', 'r') as cache:
        cache_data = json.load(cache)
        default_playlist_name = cache_data.get('default_playlist_name', None)
        default_playlist_id = cache_data.get('default_playlist_id', None)
        if default_playlist_name is not None:
            if default_playlist_id is not playlist_manager.find_user_playlist_id(default_playlist_name):
                print(f"Default playlist name '{default_playlist_name}' does not match the ID '{default_playlist_id}'. Please check your cache.")
                print("default playlist id: ", default_playlist_id)
                print("default playlist name: ", default_playlist_name)
                print("playlist id from name: ", playlist_manager.find_user_playlist_id(default_playlist_name))
else: 
    default_playlist_name = None # read the default playlist name from the cache (if it exists)
    print("No cache file found. Please set one ('.cache') to save the default playlist name.")


while what_to_do():
    pass


'''
TODO:
- save default playlist name in cache (or in a different file) so it can be used later x
- when creating new default playlist/overriding automatically set default_playlist_name and default_playlist_id x
- add a function to create a playlist with the recommendations x
- add a function to add the recommendations to the playlist x
- refine recommendations (more specific)
- add posibility to add to queue
- database is not really uptodate (maybe use a different one?)
- add a function to get the playlist cover image (if available)
- maybe dont ask gemini for recommendations, but look in database with same tag (could be a bit unspecific tho)
'''

# SEARCHING: https://developer.spotify.com/documentation/web-api/reference/search
import dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import inquirer

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
    scope="playlist-read-private playlist-read-collaborative user-library-read",  # Added user-library-read scope
    cache_path=".spotify_cache"  # Store token locally to avoid re-authentication
))

def get_user_data(
        
):
    # Get all user playlists and create a list of choices
    all_playlists = sp.current_user_playlists()
    playlist_choices = [item['name'] for item in all_playlists['items']]
    playlist_choices.append('None - Search all songs')  # Add option to search without playlist context

    # Create interactive prompts for user input
    type_question = [
        inquirer.List('search_type',
            message="Do you want to search for a playlist or a song?",
            choices=['playlist', 'song', 'liked songs', 'album', 'artist', 'None - Search all songs']),
    ]
    playlist_question = [
        inquirer.List('playlist',
            message="Select a playlist:",
            choices=playlist_choices)
    ]

    # Get user's search preference (playlist or song)
    wanted_type = inquirer.prompt(type_question)

    if wanted_type['search_type'] == 'playlist':
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

    elif wanted_type['search_type'] == 'song':
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
        selected_track = answer['track']
        global track_id
        track_id = track_info[selected_track]
        
        print(f"Selected song: {selected_track} (ID: {track_id})")
        return track_id
    
    elif wanted_type['search_type'] == 'liked songs':
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

    elif wanted_type['search_type'] == 'album':
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
    
    elif wanted_type['search_type'] == 'artist':
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

get_user_data()
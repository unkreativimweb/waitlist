from src.env import initialize_spotify_client
import requests
import inquirer
import datetime
# from audio_db import get_audio_db_info

global is_track
is_track = False
global sp
sp = initialize_spotify_client()
default_limit = 10

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
            origin (dict): Information about the original track/playlist/album/artist
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
            origin (dict): Information about the original track/playlist/album/artist
        Returns:
            str: Generated playlist description
        """
        return input (f"Enter a description for the playlist: ")

    def process_playlist_recommendation(origin, recommendations):
        pass

    def change_playlist_name(self, old_name, new_name, is_default_playlist=False): # no need for is_default_playlist here, but maybe later
        from cache_manager import update_cache_data, load_cache_data

        # need to update cache, if default_playlist_name is changed
        if is_default_playlist:
            print("Changing the default playlist name...")    
            global default_playlist_name
            default_playlist_name, *_ = load_cache_data()
            if old_name == default_playlist_name:
                default_playlist_name = new_name
                # Update the cache with the new default playlist name
                update_cache_data('default_playlist_name', new_name)
                print(f"! Warning ! Default playlist name changed from '{old_name}' to '{new_name}'")

        # Get all user playlists and find the one to rename
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
            # Split the string into name and artist
            # TODO: not very redundant, but works for now
            name, artist = [part.strip() for part in rec.rsplit('-', 1)]
            # Get track info from TheAudioDB
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


def add_to_queue():
    from utils import id_to_element_name, element_name_to_id
    from main import process_track_recommendation
    print("Adding to queue... \n")
    global discovery_type
    discovery_type = get_discovery_type() # auf was soll sich suche beziehen (mood/genre ehatever) -> returns string

    origin_id, is_track = from_where() # von wo soll gesucht werden (playlist/song/liked songs/album/artist) -> returns id
    origin = id_to_element_name(element_id=origin_id, type="track") # convert id to name (for AI input) -> returns string

    recommendations = process_track_recommendation(origin, discovery_type, limit=default_limit) # get recommendations based on the track, discovery type and limit -> returns list of strings (song-artist pairs)
    
    print(f"🎵 Found {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
        track, artist = [part.strip() for part in rec.rsplit('-', 1)]
        track_id = element_name_to_id(track.strip(), "track") # get the track id from the name
        try:
            # print(f"Adding {track} by {artist} to queue... (id: {track_id})")
            sp.add_to_queue(track_id, None) # add the track to the queue device_id=None (None = current device) see docs
        except Exception as e:
            print(f"Error adding to queue: {e}")
            continue
        

def get_discovery_type():
    what_type = [
        inquirer.List('what_type',
            message="What do you want to do?",
            choices=[
                'i want to hear the same music as a playlist/song etc.',
                'mood',
                'genre',
                # 'discover new releases', # TODO: implement this see basic_process
                # 'top charts', # TODO: implement this see basic_process
                # 'recommendations based on time of day', # TODO: implement this see basic_process
                # 'decade specific music', # TODO: implement this see basic_process
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

def from_where():
    is_track = False
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
                return item['id'], is_track

    elif origin_type['search_type'] == 'song':
        # Handle song search
        track_name = input("Enter the name of the song you want to search for: ")
        track_results = sp.search(q='track:' + track_name, type='track', limit=50)  # Search up to 50 tracks

        # Check if any tracks were found
        if not track_results['tracks']['items']:
            print(f"No song found for: {track_name}")
            return None, is_track
        
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
        is_track = True  # Set flag to indicate a track was selected
        
        print(f"Selected song: {selected_track} (ID: {track_id})")
        return track_id, is_track
    
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
        return track_id, is_track

    elif origin_type['search_type'] == 'album':
        # Get album name from user
        album_name = input("Enter the name of the album you want to search for: ")
        album_results = sp.search(q='album:' + album_name, type='album', limit=20)

        if not album_results['albums']['items']:
            print(f"No album found for: {album_name}")
            return None, is_track

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
        return album_id, is_track
    
    elif origin_type['search_type'] == 'artist':
        # Get artist name from user
        artist_name = input("Enter the name of the artist you want to search for: ")
        artist_results = sp.search(q='artist:' + artist_name, type='artist', limit=20)

        if not artist_results['artists']['items']:
            print(f"No artist found for: {artist_name}")
            return None, is_track

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
        return artist_id, is_track

    return None, is_track  # Return None if no selection was made


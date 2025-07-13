from src.env import initialize_spotify_client
from track_attributes import data, db
from src.genius import get_lyrics_genius
from src.utils import element_name_to_id, id_to_element_name
import traceback # for viewing full error tracebacks


def start_import():
    global sp
    sp = initialize_spotify_client()  # initialize the Spotify client

    playlist_id = input("give playlist id or link: ")
    # playlist_id = "https://open.spotify.com/playlist/4qUAY4SFePhy63TeKz3OJo?si=46fa95f46015447c&pt=edbfbcf9956a09a617ce5be212a7dda5" # for testing purposes
    if playlist_id[0:4] == "http":  # if the input is a link
        playlist_id = playlist_id.split("/")[-1]  # extract the playlist ID from the link
        if "?" in playlist_id:
            playlist_id = playlist_id.split("?")[0]
    
    # Get tracks from the playlist
    tracks = sp.playlist_tracks(playlist_id)
    db_instance = db() 
    
    for item in tracks['items']:
        try:
            track = item['track']
            track_id = track['id']
            track_name = track['name']
            main_artist_name = track['artists'][0]['name']

            lyrics = get_lyrics_genius(main_artist_name, track_name)
            track_data = data(main_artist_name, track_name, track_id, lyrics)
            track_data_dict = track_data.track_data_to_dict()
            audio_features_dict = track_data.audio_features_to_dict()
            

            # Efficiently check and insert
            if not db_instance.track_exists(track_id):
                if track_data_dict:
                    db_instance.add_track(track_data_dict)
                else:
                    print(f"Skipping track {track_name} by {main_artist_name} due to missing data.")
            else:
                print(f"Track {track_name} by {main_artist_name} already exists in the tracks table.")

            if not db_instance.audio_features_exists(track_id):
                if audio_features_dict:
                    db_instance.add_audio_features(audio_features_dict)
                else:
                    print(f"Skipping audio features for track {track_name} by {main_artist_name} due to missing data.")
            else:
                print(f"Audio features for track {track_name} by {main_artist_name} already exist in the audio_features table.")

            if not db_instance.artist_exists(track_data_dict["main_artist_id"]):
                # Add artist to the database if it doesn't exist
                artist_dict = db_instance.artist_to_dict()

                db_instance.cursor.execute('''
                    INSERT INTO artists (id, name, monthly_listeners, age, birth_date, number_of_tracks, number_of_albums, album_names)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (track_data_dict["main_artist_id"], track_data_dict["main_artist"],
                    track_data_dict["main_artist_monthly_listeners"], track_data_dict["main_artist_age"],
                    track_data_dict["main_artist_birth_date"], track_data_dict["main_artist_number_of_tracks"],
                    track_data_dict["main_artist_number_of_albums"], track_data_dict["main_artist_album_names"]))
                db_instance.conn.commit()



        except Exception as e:
            print(f"Error processing track {item.get('track', {}).get('name', 'unknown')}: {e}")
            traceback.print_exc()
            

def import_artist(artist_id=None, artist_name=None):
    global sp
    sp = initialize_spotify_client()  # initialize the Spotify client

    if artist_id is None and artist_name is None:
        print("give either artist_id or artist_name")
        return

    if artist_id is None:
        artist_id = element_name_to_id(artist_name=artist_name, element_type="artist")
    
    if artist_name is None:
        artist_name = id_to_element_name(element_id=artist_id, type="artist").split("(")[0]
    
    track_data = data(artist=artist_name)
    db_instance = db()

    artist_dict =  track_data.artist_to_dict()
    db_instance.add_artist(artist_dict)



if __name__ == "__main__":
    import sys

    action = sys.argv[1] if len(sys.argv) > 1 else None
    if action == "start_import":
        start_import()
    elif action == "import_artist":
        artist_id = sys.argv[2] if len(sys.argv) > 2 else None
        artist_name = sys.argv[3] if len(sys.argv) > 3 else None
        import_artist(artist_id, artist_name)
    else:
        print("Usage: python db.py start_import OR python db.py import_artist <artist_id> <artist_name>")

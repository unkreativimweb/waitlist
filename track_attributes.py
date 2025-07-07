# get the songs die eingeordnet werden sollen
# kategorien der einordnung entscheiden und unterscheiden (genre, erscheinungsdatum, artists, bpm, Language, songlänge, 
# lyrics: Sprachniveau, Thema[liebe, politik, ...], )

# also 3 funktionen: A) genre, erschienungsdatum, artists, Language, songlänge B) bpm, C) lyrics: Sprachniveau, Thema, ...
from waitlist import initialize_spotify_client, get_lyrics_genius, initialize_gemini_client, element_name_to_id, id_to_element_name
import requests
import os
from dotenv import load_dotenv
from langdetect import detect
import sqlite3
import importlib # for debugging in terminal
import time
import traceback # for viewing full error tracebacks


class data:
    """
    Class to hold song data and retrieve metadata, genre, and lyrics analysis.
    Inputs:
        artist (str): Name of the artist
        title (str): Title of the song
        lyrics (str, optional): Lyrics of the song
    Outputs:
        metadata (dict): Metadata information about the song
            release_date (str),
            main_artist (str),
            featured_artists (list),
            language (str),
            song_length (float)
        genre (str): Genre of the song
            top_genre + other_genres (str)
        bpm (float): BPM (Beats Per Minute) of the song
            nothing yet, FIXME: get bpm for the song
        lyric_data (dict): Lyrics analysis data
            language_level (str)
            topic (str)
    """
    def __init__(self, artist, title, track_id, lyrics=None):
        self.artist = artist
        self.title = title
        self.track_id = track_id
        self.lyrics = lyrics
        self.metadata = self.get_song_metadata(title, lyrics)  # get metadata for the song
        self.genre = self.get_song_genre(title, artist)  # get genre for the song
        # self.bpm = self.get_song_bpm(title, artist)  # FIXME: get bpm for the song
        self.lyric_data = self.get_song_lyrics(title, artist, lyrics)  # get lyrics data for the song

    def get_getgenre_access_token(self):
        """
        Get an access token from the GetGenre API using password grant type
        Returns:
            str: Access token if successful
            None: If authentication fails
        """
        try:
            load_dotenv()
            username = os.getenv('GET_GENRE_API_USERNAME')
            password = os.getenv('GET_GENRE_API_PASSWORD')
            
            if not all([username, password]):
                raise ValueError("GetGenre credentials not found in environment variables")
                
            # Fixed URL - removed /oauth/ part
            url = "https://api.getgenre.com/token"
            data = {
                "grant_type": "password",
                "username": username,
                "password": password,
                "remember_me": True
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            response = requests.post(url, data=data, headers=headers)
            
            # print(f"Token request status: {response.status_code}")
            # print(f"Token response: {response.text}")
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                print(f"Authentication failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting access token: {e}")
            return None

    def get_song_metadata(self, title, lyrics=None):
        '''
        retrieves song metadata (release date, artists, language, song length) with the help of the Spotify API.
        '''
        try:
            search = sp.search(q=f"track:{title} artist:{self.artist}", type='track', limit=1)
            release_date = search['tracks']['items'][0]['album']['release_date']  # get the release date
            main_artist = self.artist
            featured_artists = [artist['name'] for artist in search['tracks']['items'][0]['artists'][1:]]  # get the featured artists
            if lyrics:
                language = detect(str(lyrics))  # use langedetect to detect the language of the track name
            song_length = search['tracks']['items'][0]['duration_ms'] / 1000  # get the song length in seconds
            # Return all metadata as a dictionary
            return {
                "track_id": sp.search(q='track:' + title + ' artist:' + self.artist, type='track', limit=1)['tracks']['items'][0]['id'],  # get the track ID
                "album_name": search['tracks']['items'][0]['album']['name'],
                "album_id": search['tracks']['items'][0]['album']['id'],
                "release_date": release_date,
                "main_artist": main_artist,
                "featured_artists": featured_artists,
                "language": language,
                "song_length": song_length
            }
        except Exception as e:
            print(f"Error retrieving metadata for {title} by {self.artist}: {e}")
            return None
        
    def get_song_bpm(self, title, artist=None):
        """
        Get the BPM (Beats Per Minute) of a song using the Spotify API.
        """
        try:
            query = f"track:{title}"
            if artist:
                query += f" artist:{artist}"
            
            # Search for the track
            search = sp.search(q=query, type='track', limit=1)
            if not search['tracks']['items']:
                print(f"No track found for: {query}")
                return None

            # Get the track ID and make sure it's a list
            track_id = search['tracks']['items'][0]['id']
            print(f"Found track ID: {track_id}")

            # Get audio features - note we pass a list of track IDs
            audio_features = sp.audio_features([track_id])
            
            if not audio_features or not audio_features[0]:
                print("No audio features found")
                return None

            tempo = audio_features[0].get('tempo')
            print(f"Found BPM: {tempo}")
            return tempo

        except Exception as e:
            print(f"Error getting BPM: {str(e)}")
            return None

    def get_song_genre(self, title, artist=None):
        """
        Get genre information for a track using the GetGenre API
        
        Args:
            title (str): Name of the track
            artist (str, optional): Name of the artist
        
        Returns:
            list: List of genres associated with the track
            None: If no genres found or error occurs
        """
        try:
            # Get access token
            access_token = self.get_getgenre_access_token()
            if not access_token:
                raise ValueError("Could not obtain GetGenre API access token")
                
            # Make API request - GetGenre API requires specific parameter names
            url = "https://api.getgenre.com/search"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }

            # 'FIXME: THE TIMEOUT FUCKS ME WOHOOOOOOO'
            # Construct the URL with parameters
            if artist:
                url += "?artist_name=" + artist.replace(" ", "%20") 
            url += f"&track_name={title.replace(' ', '%20')}"  # Use track_name instead of artist
            url += f"&timeout=10"  # Add timeout parameter (has to be between 10 and 60)

            print(f"Request URL for GetGenre: {url}")  # Debugging line to see the full request URL

            for attempt in range(5):  # Retry up to 5 times
                print(f"Attempt {attempt + 1} to get genre information for {title}")
                response = requests.get(url, headers=headers)
                print(response.status_code, response.text)  # Debugging line

                try:
                    data = response.json()
                except Exception:
                    data = {}

                # Only break if top_genres is present and non-empty
                if data.get("top_genres"):
                    break
                time.sleep(5)  # Wait before retrying

            # Now handle the result after the loop
            if data.get("top_genres"):
                top_genre = data.get('top_genres', [])
                other_genres = data.get('genres', [])
                if response.status_code == 202:
                    data = response.json()
                    top_genre = data.get('top_genres', [])
                    other_genres = data.get('genres', [])
                    # FIXME: can be done without ifelse later (extra var)
                    return { # if not finished processing add genre_status
                        "top_genre": top_genre,
                        "other_genres": other_genres,
                        "genre_finished": False
                    }
                else: # when processing finished no status
                    return {
                        "top_genre": top_genre,
                        "other_genres": other_genres,
                        "genre_finished": True
                    }
            else:
                print(f"Error: GetGenre API request failed with status code {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting genre information: {e}")
            return None

    def get_song_lyrics(self, title, artist, lyrics): # Sprachniveau, Thema
        '''
        Retrieves the lyrics of a song and analyzes them for language level and topic.
        
        notes:
            Sprachniveau: vulgär, jugendslang, umgangssprache, standard, gehoben, fachlich, poetisch
            Thema: Liebe, Politik, Gesellschaft, Natur, etc.
        '''
        # waitlist.initialize_gemini_client() # initialize the client for lyrics retrieval => FALSCHER CLIENT?????
        
        model = initialize_gemini_client()  # initialize the client for text generation
        response = model.generate_content(
            f"""
            Analyse the following lyrics according to two criteria:
            1. language level: choose exactly one! - vulgar, youth slang, colloquial, standard, sophisticated, technical, poetic.
            2. topic: e.g. love, politics, society, nature, etc.

            Lyrics:\n{lyrics}

            Output as follows: "<level> / <topic1>, <topic2>, ..."
            """
            # max_tokens=500,  # Adjust max tokens as needed
        )
        language_level, topic = response.text.split(" / ")
        return {
            "language_level": language_level,
            "topic": topic
        }

    def audio_features_to_dict(self):
        # Only merge if all are dicts
        if all(isinstance(x, dict) for x in [self.lyric_data, self.metadata, self.genre]):
            audio_features = {
                "track_id": self.track_id,
                "release_date": self.metadata.get("release_date", ""),
                "main_artist": self.artist,
                "featured_artists": ', '.join(self.metadata.get("featured_artists", [])),
                "language": self.metadata.get("language", ""),
                "song_length": self.metadata.get("song_length", 0),
                "top_genre": self.genre.get("top_genre", ""),
                "other_genres": ', '.join(self.genre["other_genres"]) if isinstance(self.genre["other_genres"], list) else self.genre["other_genres"],
                "genre_finished": self.genre.get("genre_finished", False),
                "bpm": None, # FIXME: bpm
                "lyrics": self.lyrics,
                "language_level": self.lyric_data.get("language_level", ""),
                "topic": self.lyric_data.get("topic", ""),
            }
            return audio_features
        else:
            print("lyric_data, metadata, and genre must be dictionaries. Skipping track.")
            return None

    def track_data_to_dict(self):
        """
        Convert the track data to a dictionary format for database insertion.
        Returns:
            dict: Dictionary containing track data
        """
        return {
            "track_id": self.track_id,
            "title": self.title,
            "main_artist": self.artist,
            "main_artist_id": element_name_to_id(self.artist, "artist"),
            "featured_artists": self.metadata.get("featured_artists", []),
            "album_name": self.metadata.get("album_name", ""),
            "album_id": self.metadata.get("album_id", ""),
        }

    def artist_to_dict(self):
        artist_id = self.artist
        artist_name = id_to_element_name(artist_id)
        monthly_listeners = None
        """
            id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                monthly_listeners INTEGER,
                age INTEGER,
                birth_date DATE,
                number_of_tracks INTEGER,
                number_of_albums INTEGER,
                album_names TEXT#
        """

    def __str__(self):
        out = {
            "artist": self.artist,
            "title": self.title,
            "lyrics": self.lyrics,
            "bpm": None,  # FIXME: get bpm for the song
        }
        out = {**out, **self.metadata, **self.lyric_data, **self.genre}
        return str(out)  # <-- Convert dict to string for printing

class db:
    def __init__(self, db_name='songs.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
    
    def track_exists(self, track_id):
        self.cursor.execute("SELECT 1 FROM tracks WHERE track_id = ?", (track_id,))
        return self.cursor.fetchone() is not None

    def audio_features_exists(self, track_id):
        self.cursor.execute("SELECT 1 FROM audio_features WHERE track_id = ?", (track_id,))
        return self.cursor.fetchone() is not None
    
    def artist_exists(self, artist_id):
        self.cursor.execute("SELECT 1 FROM artists WHERE id = ?", (artist_id,))
        return self.cursor.fetchone() is not None

    # TODO: track_data von audio features trennen
    def add_track(self, track_data):
        """
        Add a track to the database
        track_id, name, main_artist_name, main_artist_id, featured_artists, album_name
        """
        try: 
            # print(track_data)
            self.cursor.execute('''
                INSERT INTO tracks (track_id, name, main_artist_name, main_artist_id, featured_artists, album_name, album_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                track_data["track_id"],
                track_data["title"],
                track_data["main_artist"],
                track_data["main_artist_id"],
                ''.join(track_data["featured_artists"]),
                track_data["album_name"],
                track_data["album_id"]
            ))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error adding track: {e}")
    
    def add_audio_features(self, audio_features):
        """
        Add audio features to the database
        track_id, release_date, main_artist, featured_artists, language, song_length, top_genre, other_genres, language_level, topic
        """
        if not audio_features:
            print("audio_features dict is None in adding process, skipping...")
            return
        try:
            self.cursor.execute('''
                INSERT INTO audio_features (track_id, release_date, main_artist, featured_artists, language, song_length, top_genre, other_genres, genre_finished, language_level, topic)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                audio_features["track_id"],
                audio_features["release_date"],
                audio_features["main_artist"],
                ''.join(audio_features["featured_artists"]),
                audio_features["language"],
                audio_features["song_length"],
                ''.join(audio_features["top_genre"]),
                ''.join(audio_features["other_genres"]),
                audio_features["genre_finished"],
                audio_features["language_level"],
                audio_features["topic"]
            ))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error adding audio features: {e}")

class db_factory:
    """Factory class for database management"""
    
    @staticmethod
    def create_db(db_path, overwrite=False):
        """Create tables and indexes"""
        if input("are you sure you want to overwrite the database? (y/n): ").lower() == 'y':
            print("Overwriting existing database...")
            try:
                # Close any open connections before deleting
                try:
                    conn.close()
                except Exception:
                    pass  # conn may not exist yet
                os.remove(db_path)
            except PermissionError as e:
                print(f"Could not delete {db_path}: {e}")
                print("Make sure no other process (including this script) is using the file.")
                return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Artists table
        cursor.execute('''
            CREATE TABLE artists (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                monthly_listeners INTEGER,
                age INTEGER,
                birth_date DATE,
                number_of_tracks INTEGER,
                number_of_albums INTEGER,
                album_names TEXT
            )
        ''')
        
        # Tracks table
        cursor.execute('''
            CREATE TABLE tracks (
                track_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                main_artist_name TEXT,
                main_artist_id TEXT,
                featured_artists TEXT,
                album_name TEXT,
                album_id TEXT,
                FOREIGN KEY (main_artist_id) REFERENCES artists (id)
            )
        ''')


        # Audio features table
        cursor.execute('''
            CREATE TABLE audio_features (
                track_id TEXT PRIMARY KEY,
                release_date DATE,
                main_artist TEXT,
                featured_artists TEXT,
                language TEXT,
                song_length REAL,
                top_genre TEXT,
                other_genres TEXT,
                genre_finished TEXT,
                language_level TEXT,
                topic TEXT,
                FOREIGN KEY (track_id) REFERENCES tracks (track_id)
            )
        ''')
        
        # Basic indexes
        cursor.execute('CREATE INDEX idx_artist_name ON artists(name)')
        cursor.execute('CREATE INDEX idx_genre ON audio_features(top_genre)')
        
        conn.commit()
        conn.close()
        print("Database setup complete!")
    
    @staticmethod
    def create_indexes(db_path):
        """Create database indexes"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_artist_name ON artists(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_genre ON audio_features(top_genre)')

        conn.commit()
        conn.close()

if __name__ == "__main__":
    global sp
    sp = initialize_spotify_client()  # initialize the Spotify client

    # playlist_id = input("give playlist id or link: ")
    playlist_id = "https://open.spotify.com/playlist/4qUAY4SFePhy63TeKz3OJo?si=46fa95f46015447c&pt=edbfbcf9956a09a617ce5be212a7dda5" # for testing purposes
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
            print(main_artist_name, track_name, track_id)  # Debugging line

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
                            
                """
                id TEXT PRIMARY KEY,
                                name TEXT NOT NULL,
                                monthly_listeners INTEGER,
                                age INTEGER,
                                birth_date DATE,
                                number_of_tracks INTEGER,
                                number_of_albums INTEGER,
                                album_names TEXT

                """



        except Exception as e:
            print(f"Error processing track {item.get('track', {}).get('name', 'unknown')}: {e}")
            traceback.print_exc()
            
       
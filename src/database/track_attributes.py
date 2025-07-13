from src.utils import initialize_spotify_client, element_name_to_id
from src.env import initialize_gemini_client
from src.genius import get_lyrics_genius
import requests
import os
from dotenv import load_dotenv
from langdetect import detect
import sqlite3
import importlib # for debugging in terminal
import time
from datetime import date
from bs4 import BeautifulSoup as bs

global sp
sp = initialize_spotify_client()  # initialize the Spotify client


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
    def __init__(self, artist=None, title=None, track_id=None, lyrics=None):
        # FIXME: keep init as minimal as possible, so i can call the artist to dict with just artist
        self.artist = artist
        self.title = title
        self.track_id = track_id
        self.lyrics = lyrics
        # self.metadata = self.get_song_metadata(title, lyrics)  # get metadata for the song
        # self.genre = self.get_song_genre(title, artist)  # get genre for the song
        # self.bpm = self.get_song_bpm(title, artist)  # FIXME: get bpm for the song
        # self.lyric_data = self.get_song_lyrics(title, artist, lyrics)  # get lyrics data for the song

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
        
    def get_song_bpm(self, title, artist=None): # TODO
        """
        Get the BPM (Beats Per Minute) of a song using the Spotify API.
        """
        pass

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
                "top_genre": self.get_song_genre(self.title, self.artist).get("top_genre", ""),
                "other_genres": ', '.join(self.get_song_genre(self.title, self.artist)["other_genres"]) if isinstance(self.genre["other_genres"], list) else self.genre["other_genres"],
                "genre_finished": self.get_song_genre(self.title, self.artist).get("genre_finished", False),
                "bpm": None, # FIXME: bpm
                "lyrics": self.lyrics,
                "language_level": self.get_song_lyrics(self.title, self.artist, self.lyrics).get("language_level", ""),
                "topic": self.get_song_lyrics(self.title, self.artist, self.lyrics).get("topic", ""),
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
            "featured_artists": self.get_song_metadata(self.title, self.lyrics).get("featured_artists", []),
            "album_name": self.get_song_metadata(self.title, self.lyrics).get("album_name", ""),
            "album_id": self.get_song_metadata(self.title, self.lyrics).get("album_id", ""),
        }

    def artist_to_dict(self):
        artist_id = element_name_to_id(element_name=self.artist, element_type="artist")
        artist_name = self.artist
        today= date.today()
        number_of_tracks = 0
        album_names = []
        album_ids = []
        # TODO: artist follower can be aquired with sp.search
        #  same with genres
    
        # Get monthly listeners from Spotify, by scraping the artist's page
        try: 
            headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
            }
            spotify_artist_url = f"https://open.spotify.com/intl-de/artist/{artist_id}"
            response = requests.get(spotify_artist_url, headers=headers)
            print(spotify_artist_url)
            soup = bs(response.text, 'html.parser')
            meta_tag = soup.find("meta", property="og:description")
            if meta_tag:
                content = meta_tag.get("content")
                monthly_listeners = content.split(' ')[2]
                monthly_listeners = monthly_listeners.replace('M', '00.000').replace('K', '000').replace('.', '')
                monthly_listeners = int(monthly_listeners)
        except Exception as e:
            print(f"Error fetching artist data from Spotify: {e}")
            return None

        # Get birth date from Wikidata using SPARQL query
        try:
            url = "https://query.wikidata.org/sparql"
            query = f"""
            SELECT ?birthDate WHERE {{
            ?person rdfs:label "{artist_name}"@en;
                    wdt:P569 ?birthDate.
            LIMIT 1}}
            """
            headers = {
                "Accept": "application/sparql-results+json"
            }
            response = requests.get(url, params={'query': query}, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data['results']['bindings']:
                    birth_date = data['results']['bindings'][0]['birthDate']['value'].split("T")[0]
                else:
                    birth_date = None
            else:
                print(f"Error: {response.status_code}")
                birth_date = None
        except Exception as e:
            print(f"Error fetching birth date for {artist_name}: {e}")
            birth_date = None

        # Calculate age if birth_date is available
        try:
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except:
            age = None

        # Get number of albums and their respective names from Spotify
        try:
            artist_albums = sp.artist_albums(artist_id=artist_id, include_groups="album")
            number_of_albums = artist_albums["total"]
            for item in artist_albums["items"]:
                album_names.append(item["name"]) 
                album_ids.append(item["id"])
        except Exception as e:
            print(f"Error fetching album names and ids for {artist_name}: {e}")
            number_of_tracks = None
            number_of_albums = None
            album_names = None

        # Count all tracks by an artist by iterating through their spotify discography
        try:
            artist_discography = sp.artist_albums(artist_id=artist_id)["items"]  # Access the 'items' list
            for item in artist_discography:
                track_ids_of_album = sp.album_tracks(item["id"])["items"]  # Access the 'items' list
                for track in track_ids_of_album:
                    number_of_tracks += 1
        except Exception as e:
            print(f"Error fetching number of tracks for {artist_name}: {e}")

        return {
            "id": artist_id,
            "name": artist_name,
            "monthly_listeners": monthly_listeners,
            "birth_date": birth_date,
            "age": age,
            "album_names": album_names,
            "number_of_albums": number_of_albums,
            "number_of_tracks": number_of_tracks
        }

    def __str__(self):
        # out = {
        #     "artist": self.artist,
        #     "title": self.title,
        #     "lyrics": self.lyrics,
        #     "bpm": None,  # FIXME: get bpm for the song
        # }
        # out = {**out, **self.metadata, **self.lyric_data, **self.genre}
        # return str(out)  # <-- Convert dict to string for printing
        pass

class db:
    def __init__(self, db_name='data/prod/songs.db'):
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

    # TODO: track_data von audio features trennen (ist glaube fertig lol)
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

    def add_artist(self, artist_data=None):
        if artist_data is None:
            print("artist_dict is None in adding process, skipping...")
            return
        
        try:
            self.cursor.execute('''
                    INSERT INTO artists (id, name, monthly_listeners, age, birth_date, number_of_tracks, number_of_albums, album_names)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    artist_data["id"],
                    artist_data["name"],
                    artist_data["monthly_listeners"],
                    artist_data["age"],
                    artist_data["birth_date"],
                    artist_data["number_of_tracks"],
                    artist_data["number_of_albums"],
                    ', '.join(artist_data["album_names"])
                ))
            self.conn.commit()
        
        except sqlite3.IntegrityError as e:
            print(f"Error adding audio features: {e}")
        


if __name__ == "__main__":
    pass
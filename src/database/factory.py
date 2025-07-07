import os
import sqlite3

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

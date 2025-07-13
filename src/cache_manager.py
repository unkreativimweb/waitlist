import json
import os
from src.utils import element_name_to_id

def update_cache_data(key, value):
    """Update a specific key in the cache file while preserving other data"""
    try:
        # Read existing cache data
        cache_data = {}
        try:
            with open('data/prod/cache.json', 'r') as cache:
                cache_data = json.load(cache)
        except (FileNotFoundError, json.JSONDecodeError):
            # File doesn't exist or is empty/invalid
            raise FileNotFoundError("Cache file not found or is empty. Creating a new one.")

        # Update the specific key
        cache_data[key] = value

        # Write back all data
        with open('data/prod/cache.json', 'w') as cache:
            json.dump(cache_data, cache)
        
        return True
    
    except Exception as e:
        print(f"❌ Error updating cache: {e}")
        return False

def load_cache_data():
    """Load cache data from the cache file"""
    global default_limit, default_playlist_name, default_playlist_id

    if os.path.exists('data/prod/cache.json'):
        with open('data/prod/cache.json', 'r') as cache:
            cache_data = json.load(cache)
            default_limit = cache_data.get('default_limit')
    else: default_limit = 10 # read the default playlist name from the cache (if it exists)

    if os.path.exists('data/prod/cache.json'):
        with open('data/prod/cache.json', 'r') as cache:
            cache_data = json.load(cache)
            default_playlist_name = cache_data.get('default_playlist_name', None)
            default_playlist_id = cache_data.get('default_playlist_id', None)
        if default_playlist_name is not None:
            if default_playlist_id != element_name_to_id(default_playlist_name, "playlist"):
                print(f"Default playlist name '{default_playlist_name}' does not match the ID '{default_playlist_id}'. Please check your cache.")
                print("default playlist id: ", default_playlist_id)
                print("default playlist name: ", default_playlist_name)
                print("playlist id from name: is something else (but cant show lol)")
            else: 
                print("cache matches")
        return default_playlist_name, default_playlist_id, default_limit
    else: 
        default_playlist_name = None # read the default playlist name from the cache (if it exists)
        print("No cache file found. Please set one ('data/prod/cache.json') to save the default playlist name.")

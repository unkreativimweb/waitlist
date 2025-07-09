from env import initialize_spotify_client

global sp
sp = initialize_spotify_client()  # Assuming this function initializes the Spotify client

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

def id_to_element_name(element_id):
    """
    Convert a Spotify ID to a readable name, handling different types (track, playlist, album, artist)

    !! TODO: BE AWARE: the ouput for songs was changed to a dict and the rest will follow (this func needs overhaul anyway lol)

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
            return {
                "track_name": element['name'],
                "artist": {element['artists'][0]['name']} if element['artists'] else None
            }
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

def element_name_to_id(element_name, element_type):
    """
    Convert a readable name to a Spotify ID, handling different types (track, playlist, album, artist)
    Args:
        element_name (str): Readable name of the element
        element_type (str): Type of the element (track, playlist, album, artist)
    Returns:
        str: Spotify ID of the element
    """
    try: 
        item = sp.search(q=element_name, limit=10, offset=0, type=element_type, market=None)
        return item['tracks']['items'][0]['id'] if element_type == 'track' else None
    except Exception as e:
        print(f"Error searching for element: {e}")
        return None
    
    '''
        try:
            if element_type == 'playlist':
                playlists = sp.current_user_playlists()
                for item in playlists['items']:
                    if item['name'] == element_name:
                        return item['id']
            
            elif element_type == 'track':
                results = sp.search(q='track:' + element_name, type='track', limit=1)
                if results['tracks']['items']:
                    return results['tracks']['items'][0]['id']
            
            elif element_type == 'album':
                results = sp.search(q='album:' + element_name, type='album', limit=1)
                if results['albums']['items']:
                    return results['albums']['items'][0]['id']
            
            elif element_type == 'artist':
                results = sp.search(q='artist:' + element_name, type='artist', limit=1)
                if results['artists']['items']:
                    return results['artists']['items'][0]['id']
            
            

            raise Exception("Could not identify element type")
            
        except Exception as e:
            print(f"Error converting name to ID: {e}")
            return None

    '''
        
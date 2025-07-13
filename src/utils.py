from src.env import initialize_spotify_client

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

def id_to_element_name(element_id, type=None, type_given=True):
    """
    Convert a Spotify ID to a readable name, handling different types (track, playlist, album, artist)

    Args:
        element_id (str): Spotify ID of the element
        type (str): type of element searched for, can be None if not sure
        type_given (bool): so program knows to go the long way round
    Returns:
        str: Formatted name of the element
        dict: if type == track with artist and track name
    """

    if type_given:
        if type == "track":
            return {
                    "track_name": element['name'],
                    "artist": {element['artists'][0]['name']} if element['artists'] else None
            }
        else:     
            try:
                element = getattr(sp, type)(element_id)
                return element["name"]
            except Exception as e:
                print("Error finding element_name from id in utils.py")
    
    # vvv Technically old, unused vvv
    else:
        try:
            # First try as playlist
            try:
                element = sp.playlist(element_id)
                return {element['name']}
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
                return {element['name']}
            except:
                pass
            
            # Finally try as artist
            try:
                element = sp.artist(element_id)
                return {element['name']}
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
        item = sp.search(q=element_name, type=element_type)
        return item['artists']['items'][0]['id']
    except Exception as e:
        print(f"Error searching for element: {e}")
        return None
    
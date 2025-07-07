import requests

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

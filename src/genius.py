import json
import requests
from bs4 import BeautifulSoup
import src.genius_auth as genius_auth

def get_lyrics_genius(artist_name, track_name):
    """
    Get lyrics from Genius API
    Returns: Lyrics as a string or None if not found
    FIXME: ALSO: WHY THE FUCK IS IT SEARCHING FOR THE WRONG TRACKS (SEE CELO ABDI 20 ZOLL MAE)
    """
    # Load token from cache
    with open('data/prod/cache.json', 'r') as f:
        cache_data = json.load(f)
        access_token = cache_data.get('genius_token', {}).get('access_token')
    
    if not access_token:
        print("❌ No Genius access token found in cache")
        return None

    # Configure headers with Bearer token
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    track_id = get_genius_track_id(artist_name, track_name) # get the song id from genius
    track_url = f"https://api.genius.com/songs/{track_id}" # get the song url from genius
    data = requests.get(track_url, headers=headers).json() # get the song data from genius
    # print(track_id)
    # print(track_url)
    # print(data) # print the song data

    lyrics_url = data['response']['song']['url'] # get the lyrics url from genius
    
    # Get the actual lyrics by scraping the page
    page = requests.get(lyrics_url)
    # print(f"Scraping lyrics from: {lyrics_url}")
    soup = BeautifulSoup(page.content, 'html.parser')
    
    # Find lyrics container and extract text
    lyrics_div = soup.find('div', class_='bjajog')
    if lyrics_div:
        # Remove script tags and clean up the text
        [s.extract() for s in lyrics_div(['script', 'style'])]
        lyrics = lyrics_div.get_text()
        lyrics = lyrics.split('[')[1:] # remove irrelevant stuff from beautifulsoup scraping
        # print("Lyrics found:")
        # print(lyrics)
        return lyrics
    else:
        print("❌ Could not extract lyrics from page, the class on genius' website probably changed")

def get_genius_track_id(artist_name, track_name):
    try:
        # Load token from cache
        with open('data/prod/cache.json', 'r') as f:
            cache_data = json.load(f)
            access_token = cache_data.get('genius_token', {}).get('access_token')
        
        if not access_token:
            print("❌ No Genius access token found in cache")
            return None

        # Configure headers with Bearer token
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        # URL encode the search parameters
        search_query = f"{artist_name} {track_name}".replace(" ", "%20")
        url = f'https://api.genius.com/search?q={search_query}'
        # for debugging
        # print(f"search url for genius lyrics api: {url + search_query}")
        # Make authenticated request
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ API request failed with status code: {response.status_code}")
            return None

        data = response.json()
        hits = data.get('response', {}).get('hits', [])
        # FIXME: if hits is empty, dont begin the entire thing at all, just return None
        try:     
            if hits:
                print("✅ API request successful!")
                print(hits[0].get('result', {}).get('id'))
                return hits[0].get('result', {}).get('id')
            else:
                print("❌ No results found")
                return None
        except KeyError as e:
            print(f"❌ KeyError: {e} - Response structure may have changed")
            return None
    except Exception as e:
        print(f"❌ Error accessing Genius API: {e}")
        return None

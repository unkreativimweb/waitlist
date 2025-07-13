import inquirer
import os
import json
import datetime
from src.env import initialize_spotify_client, initialize_gemini_client, initialize_genius_client
from src.utils import string_to_list, id_to_element_name
from src.cache_manager import load_cache_data, update_cache_data
from src.spotify import add_to_queue, get_discovery_type, from_where, PlaylistManager
from src.ai import get_lyric_attributes_ai, ask_ai
from src.genius import get_lyrics_genius
from src.audio_db import get_audio_db_info


def what_to_do():
    # Create interactive prompts for user input
    what_to_do_choices = [
        inquirer.List('what_to_do_choices',
            message="What do you want to do?",
            choices=[
                'new recommendations',
                # 'add to liked songs', # TODO: implement if needed
                'settings',
                'nothing'
            ]),
    ]
    to_do_answer = inquirer.prompt(what_to_do_choices)
    if to_do_answer['what_to_do_choices'] == 'new recommendations':
        new_recs_question = [
            inquirer.List('new_recs',
                message="Where?",
                choices=[
                    'default playlist',
                    'create a new playlist',
                    # 'override another old playlist', # TODO: implement this
                    # 'add to existing playlist', # TODO
                    'add to queue',
                ]),
        ]
        new_recs_answer = inquirer.prompt(new_recs_question)
        if new_recs_answer['new_recs'] == 'default playlist':
            if default_playlist_name == "":
                print("No default playlist set. Please set a default playlist in the settings first.")
                return
            else: 
                global default_playlist_id
                if default_playlist_id is None and default_playlist_name is None:
                    print("No default Playlist found. Please set one in the settings, or check Cache.")
                    return
                # remove old tracks from the default playlist
                playlist_manager.sp.playlist_replace_items(default_playlist_id, [])
                print(f"Removed old tracks from the default playlist: {default_playlist_name}")
                # start the basic process with the default playlist id
                basic_process(default_playlist_id) # fill the playlist with the new recommendationsq
        elif new_recs_answer['new_recs'] == 'create a new playlist':
            basic_process()
        elif new_recs_answer['new_recs'] == 'add to queue':
            add_to_queue()
        
        return True # continue the loop
    
    elif to_do_answer['what_to_do_choices'] == 'add to liked songs':
        print("NOT IMPLEMENTED YET")
        return True # continue the loop
    elif to_do_answer['what_to_do_choices'] == 'settings':
        while settings():
            pass
        return True # continue the loop
    elif to_do_answer['what_to_do_choices'] == 'nothing':
        print("Nothing to do. Exiting...")
        return False # exit the loop
    
def settings():
    # Create interactive prompts for user input
    basic_settings = [
        inquirer.List('settings',
            message="Settings",
            choices=[
                'set/change default playlist',
                'change playlist name',
                'change default playlist description',
                'change default limit for recommendations',
                # 'toggle playlist public/private',
                # 'toggle playlist collaborative',
                # 'change default playlist cover', 
                'advanced settings',
                'back'
            ]),
    ]
    advanced_settings = [
        inquirer.List('advanced_settings',
            message="Advanced Settings",
            choices=[
                'change Gemini API key',
                'clear authentication (resetting Spotify token)',
                'clear cache (not Spotify token)',
                # 'toggle debug mode', TODO: implement debug mode
                'output cache data',
                'back'
            ]),
    ]

    basic_settings_answer = inquirer.prompt(basic_settings)

    if basic_settings_answer['settings'] == 'advanced settings':
        advanced_settings_answer = inquirer.prompt(advanced_settings)
        if advanced_settings_answer['advanced_settings'] == 'clear authentication (resetting Spotify token)':
            open('data/prod/.spotify_cache', 'w').close() # Clear the cache file to force re-authentication (by overwriting it)
            print("Spotify account changed. Please re-authenticate.")
        elif advanced_settings_answer['advanced_settings'] == 'change Gemini API key':
            os.putenv("gemini_api_key", input("Enter new Gemini API key: "))
        elif advanced_settings_answer['advanced_settings'] == 'clear cache (not Spotify token)':
            confirm = inquirer.prompt([
            inquirer.List('confirm',
                    message="⚠️  Warning: This will clear all cached settings (playlist names, limits, etc). Are you sure?",
                    choices=[
                        'Yes, clear cache',
                        'No, keep cache'
                    ]),
            ])
            
            if confirm['confirm'] == 'Yes, clear cache':
                update_cache_data('default_playlist_name', None) # reset the default playlist name to None
                update_cache_data('default_limit', 10) # reset the default limit to 10
                update_cache_data('default_playlist_id', None) # reset the default playlist id to None
                print("✅ Cache cleared successfully")
                # TODO: make it automatically reset all data not reset every single key singularly 
            else:
                print("Cache clearing cancelled")
        elif advanced_settings_answer['advanced_settings'] == 'output cache data':
            try:
                with open('data/prod/cache.json', 'r') as cache:
                    cache_data = json.load(cache)
                    print("Cache data: ", cache_data)
            except FileNotFoundError:
                print("Cache file not found.")
        elif advanced_settings_answer['advanced_settings'] == 'back':
            settings()
    elif basic_settings_answer['settings'] == 'set/change default playlist':
        global default_playlist_name
        new_name = input("Enter the new default playlist name: ")
        if default_playlist_name is not None: # lol
            print("old name assigned to None")
            old_name = default_playlist_name
        else: print(f"old name is: {default_playlist_name}, new name: {new_name}")
        
        default_playlist_name = new_name

        # rewrite the default playlist name in the cache so it can be used later
        if update_cache_data('default_playlist_name', new_name):
            print(f"✅ Default playlist name saved to cache: {new_name}")
        else:
            print("⚠️ Failed to save playlist name to cache")
        
        print(f"Default playlist name set to: {default_playlist_name}")
        
        override_or_create_new_default = inquirer.prompt([
            inquirer.List('override/create default',
                message=f"Do you want to overwrite the old default playlist name from {old_name if 'old_name' in locals() else 'None'} to {new_name} or create a new?",
                choices=[
                    'overwrite old default playlist name',
                    'create new default playlist'
                ]),
        ])
        
        if override_or_create_new_default['override/create default'] == 'overwrite old default playlist name':
            if old_name is not None:
                playlist_manager.change_playlist_name(old_name, new_name, True) # change playlist name
                update_cache_data('default_playlist_name', new_name) # update the cache with the new default playlist name
            else:
                print("There is no old playlist to overwrite.")
                return
        elif override_or_create_new_default['override/create default'] == 'create new default playlist':
            playlist_manager.create_playlist(sp.me()['id'], default_playlist_name) # create a new playlist with the new name
            update_cache_data('default_playlist_name', new_name) # update the cache with the new default playlist name
            print(f"New default playlist created: {new_name}")

            # find new id and save it to cache for later use
            global default_playlist_id
            default_playlist_id = playlist_manager.find_user_playlist_id(default_playlist_name) # get the playlist id from the name
            update_cache_data('default_playlist_id', default_playlist_id) # update the cache with the new default playlist id
        
    elif basic_settings_answer['settings'] == 'change default playlist description':
        new_description = input("Enter the new playlist description: ")
        default_playlist_id = playlist_manager.find_user_playlist_id(default_playlist_name) # get the playlist id from the name
        update_cache_data('default_playlist_id', default_playlist_id) # update the cache with the new default playlist id
        if default_playlist_id is None:
            print("Cannot update description: Playlist not found")
            return

        playlist_manager.sp.user_playlist_change_details(
            user=sp.me()['id'],
            playlist_id=default_playlist_id,
            name=playlist_manager.sp.playlist(default_playlist_id, fields=['name']), # get the name of the playlist
            public=False,
            collaborative=False,
            description=new_description #set the new description
        )

        print(f"Default Playlist description changed to: {new_description}")
   
    elif basic_settings_answer['settings'] == 'change playlist name':
        old_name = input("Enter the old playlist name: ")
        new_name = input("Enter the new playlist name: ")
        if old_name == new_name:
            print("Old and new playlist names are the same. No changes made.")
            return
        if old_name == default_playlist_name:
            playlist_manager.change_playlist_name(old_name, new_name, True)
        else:
            playlist_manager.change_playlist_name(old_name, new_name, False)



    elif basic_settings_answer['settings'] == 'change default limit for recommendations':
        new_limit = input("Enter the new default limit for recommendations: ")
        default_limit = new_limit
        update_cache_data('default_limit', default_limit) # update the cache with the new limit
        print(f"Default limit for recommendations changed to: {default_limit}")
    
    elif basic_settings_answer['settings'] == 'back':
        return False # go back to the main menu
    
    else:
        print("Invalid choice or Error. Please try again.")
        settings()

def basic_process(playlist_id=None): 
    global discovery_type
    discovery_type = get_discovery_type() # auf was soll sich suche beziehen (mood/genre ehatever) -> returns string
    if "recommendations based on the time of day" in discovery_type or "decade specific music" in discovery_type or "new releases" in discovery_type or "top charts" in discovery_type:
        # print("Discovery type: ", discovery_type) # print the discovery type for debugging
        print("this mode is not yet fully functional")
        return
    origin_id, is_track = from_where() # von wo soll gesucht werden (playlist/song/liked songs/album/artist) -> returns id
    origin = id_to_element_name(element_id=origin_id, type="track") # convert id to name (for AI input) -> returns string
    if playlist_id is None:
        print("playlist id is None")
        pass
    elif playlist_id is not None: # lol idk why (when id is given)
        print(f"discovered playlist id input ({playlist_id})")

    if is_track: # if a track was selected
        recommendations = process_track_recommendation(origin, discovery_type, limit=default_limit) # get recommendations based on the track, discovery type and limit -> returns list of strings (song-artist pairs)
        print(f"🎵 Found {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

        # Create the playlist if not already created
        if playlist_id is None:
            playlist_manager.create_playlist(sp.me()['id'])
            playlist_manager.fill_playlist(recommendations) # fill the playlist with the recommendations
        else:
            playlist_manager.fill_playlist(recommendations, playlist_id) # fill the playlist with the recommendations

def process_track_recommendation(origin, discovery_type, limit):
    """
    Process a track and get AI recommendations based on its attributes
    Args:
        origin (dict): Track information containing name and artist
        discovery_type (str): Type of discovery/recommendation wanted
        limit (int): Number of recommendations to return
    Returns:
        list: List of recommended tracks
    """
    print(f"Processing track: {origin}")
    print(f"Discovery type: {discovery_type}")
    # Extract track name and artist from the formatted string
    track_name = str(origin["track_name"])
    artist_name = str(origin["artist"])

    # print(f"Processing track: '{track_name}' by '{artist_name}'")
    
    # Get additional track information from TheAudioDB
    track_attributes = get_audio_db_info(track_name, artist_name)
    
    # Get lyric-attributes
    lyrics = get_lyrics_genius(artist_name, track_name)
    lyric_attributes = get_lyric_attributes_ai(lyrics) 
    # print(lyric_attributes)

    # TODO: filter lyrics attributes out of json, so theres not as much irrelevant info passed onto gemini
    # ^ may be redundant, if database is used, instead of ai

    # Get AI recommendations
    ai_response = ask_ai(discovery_type, origin, limit, track_attributes, lyric_attributes)
    
    # Convert AI response to list of recommendations
    recommendations = string_to_list(str(ai_response))
    
    # Verify recommendation count
    if len(recommendations) != limit:
        print(f"⚠️ PSA: Got {len(recommendations)} recommendations instead of requested {limit}")
    
    return recommendations


if __name__ == "__main__":
    global default_limit
    global default_playlist_name
    global default_playlist_id
    global playlist_manager
    global sp

    sp = initialize_spotify_client()
    model = initialize_gemini_client()
    initialize_genius_client()

    default_playlist_name, default_playlist_id, default_limit = load_cache_data() # load the cache data to get the default playlist name and id
    playlist_manager = PlaylistManager(sp)

    while what_to_do():
        pass
from env import initialize_gemini_client
import json

model = initialize_gemini_client()  # Initialize the Gemini model

@staticmethod
def check_gemini_status():
    """Check if Gemini API is properly configured and working"""
    try:
        # Test the model with a simple prompt
        test_response = model.generate_content("Reply with 'OK' if you can read this.")
        if test_response and test_response.text.strip() == "OK":
            return True
        else:
            print("⚠️ Gemini API response is not as expected")
            return False
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return False
    
def ask_ai(discovery_type, origin, limit, track_attributes, lyric_attributes):
    '''
    This function sends a request to the AI model for music recommendations based on the provided parameters.
    It includes error handling for various scenarios and formats the response accordingly.
    It has the possibility to check if the Gemini API is working properly. (if needed)
    '''

    # if not check_gemini_status():
    #     print("❌ Gemini API is not working properly")
    #     return "ERROR: Gemini API unavailable"

    print('Origin: ', origin) # Print the origin (playlist/song/liked songs/album/artist)
    print('Limit: ', limit) # Print the limit (number of recommendations)
    track_attributes = json.dumps(track_attributes) # Convert track attributes to JSON string for AI input
    text = """You are a music recommendation engine. Your task is to recommend music based on the following criteria:

        Input Parameters:
        - Discovery Type: {discovery_type} (defines what kind of music to recommend) => MAKE SURE TO FOLLOW THIS INSTRUCTION 100%
        - Origin: {origin} (the reference point for recommendations)
        - Track Attributes: {track_attributes} (musical characteristics to consider)
        - Lyric Attributes: {lyric_attributes} (focus mainly on this)
        
        Response Rules:
        1. Output Format: ONLY return a comma-separated list of 'song-artist' pairs
        2. Maximum Recommendations: {limit}
        3. Format Example: "Bohemian Rhapsody-Queen, Yesterday-The Beatles"
        
        Error Handling:
        - If logical error: return "ERROR: Invalid input combination"
        - If missing data: return "ERROR: Cannot access required data"
        - For any other error: return "ERROR: [specific error message]"
        
        DO NOT include any additional text, explanations, or formatting.""".format(
            discovery_type=discovery_type,
            origin=origin,
            track_attributes=json.dumps(track_attributes),
            limit=limit,
            lyric_attributes=lyric_attributes
        )
    response = model.generate_content(text)
    # print("AI Input: ", text)
    print("AI Response: ", response.text) # Print the AI's response
    print("==================================================\n")
    return response.text

def get_lyric_attributes_ai(lyrics):
    """
    Get lyric attributes from the lyrics text with ai
    Returns: dict with lyric attributes or None if not found
    """
    print("Getting lyric attributes from AI...")
    
    try:
        with open('data/prod/lyric_attributes.json', 'r') as l:
            lyric_attributes = json.load(l)


        text = f"""You are a music analysis engine. Your task is to analyze the following lyrics and extract their attributes:

                Input Parameters:
                - Lyrics: {lyrics} (the text of the song's lyrics)
                
                Response Format:
                - Return a JSON object with attributes from this schema: {lyric_attributes}
                - Ensure the response is valid JSON format, use " instead of '
                - DO NOT include markdown code block markers
                
                Error Handling:
                - If logical error: return "ERROR: Invalid input combination"
                - If missing data: return "ERROR: Cannot access required data"
                - For any other error: return "ERROR: [specific error message]"
                
                DO NOT include any additional text, explanations, or formatting."""

        # Send the lyrics to the AI model for analysis
        response = model.generate_content(text)
        
        # Print raw response for debugging
        # print("\nRaw AI Response:")
        # print(response.text.strip())
        # print("\n-------------------")

        # Clean the response by removing markdown code block markers
        cleaned_response = response.text.strip()
        cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
        
        # print("Cleaned Response:")
        # print(cleaned_response)
        # print("\n-------------------")
        
        if "ERROR:" in cleaned_response:
            print("AI Error: ", cleaned_response)
            return None
            
        try:
            # was for debugging
            # with open ("test.json", "w") as test:
            #     test.write(cleaned_response)
                
            # Try to parse the cleaned response as JSON
            parsed_response = json.loads(cleaned_response)
            return parsed_response
        except json.JSONDecodeError as je:
            import sys
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(f"JSON parsing error at line {exc_traceback.tb_lineno}: {je}")
            print("Response was not valid JSON format")
            return None
            
    except Exception as e:
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(f"Error in lyric analysis at line {exc_traceback.tb_lineno}: {e}")
        return None

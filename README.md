# 🎵 MOOD - Your Spotify Music Explorer
A command-line interface tool to explore and manage your Spotify music in style. Features coming soon...
> ⚠️ **Project Status: In Development**  
## ⚠️ Disclaimer
This project is not hosted - you'll need to create your own Spotify Developer application and use your own API credentials to run this code.

## ✨ Features
coming soon...

## 🚀 Getting Started
### Prerequisites

- Python 3.8 or higher
- Gemini Account
- [Gemini API Key](https://aistudio.google.com/app/u/1/apikey)
- Spotify Account
- [Spotify Developer Account](https://developer.spotify.com/dashboard)
---

1. **Clone the repository:**
```bash
git clone https://github.com/unkreativimweb/blackjack.git
cd waitlist
```

2. **Install dependencies:**
```bash
pip install spotipy inquirer python-dotenv
```

3. **Set up your environment:**
   - Create a `.env` file in the project root
   - Create a `.cache` file in the project root
   - Add your Spotify API credentials:
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
REDIRECT_URI="https://127.0.0.1"
```
4. **Authorization Process:**
   1. When you first run the application, it will open your default browser
   2. You'll be prompted to log in to your Spotify account
   3. Spotify will ask if you want to grant access to MOOD
   4. After accepting, Spotify will redirect you to a URL
   5. Copy this URL from your browser's address bar
   6. Paste it into the terminal when prompted
   7. The application will save your authorization token locally in `.spotify_cache`
   8. Future runs won't require re-authorization unless the token expires

> **Note:** The authorization is required because MOOD needs permission to:
> - Read your private playlists
> - Access your liked songs
> - Search Spotify's catalog
> - View your saved albums and artists

**Troubleshooting:**
- If authorization fails, delete the `.spotify_cache` file and try again
- Make sure your `REDIRECT_URI` in `.env` matches exactly what's in your Spotify App settings
- Check that you've granted all required permissions when authorizing

## 🔑 Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Get your Client ID and Client Secret
4. Add `https://127.0.0.1` to your Redirect URIs

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

## 🙏 Acknowledgments

- [Spotipy](https://spotipy.readthedocs.io/) - Handles all Spotify API interactions including playlist management, track searching, and user authentication. Used for accessing and manipulating Spotify data throughout the application.
- [Inquirer](https://python-inquirer.readthedocs.io/) - Creates the interactive CLI menu system for selecting music discovery types, choosing playlists, and navigating search results. Makes the user interface clean and intuitive.
- [Python-dotenv](https://github.com/theskumar/python-dotenv) - Manages API credentials securely by loading them from a local `.env` file, keeping sensitive Spotify and Gemini API keys separate from the code.
- [TheAudioDB](https://www.theaudiodb.com/free_music_api) - Enriches track recommendations by providing additional metadata like genres, moods, and themes that aren't available through Spotify's API. Helps create more accurate music suggestions.
- [Gemini](https://aistudio.google.com/) - Powers the intelligent recommendation system by analyzing track characteristics and user preferences to generate personalized music suggestions based on various criteria like mood, genre, or similar artists.
- soon: [Genius](https://docs.genius.com) - Will add lyrical analysis capabilities to enhance music recommendations by considering song themes and meanings.
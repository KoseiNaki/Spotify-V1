import Foundation

struct Config {
    // MARK: - API Configuration
    static let apiBaseURL = "http://localhost:8000" // Change to your backend URL
    
    // MARK: - Spotify Configuration
    static let spotifyClientId = "YOUR_SPOTIFY_CLIENT_ID"
    static let spotifyRedirectURI = "moodlens://callback"
    static let spotifyScopes = [
        "user-read-recently-played",
        "user-top-read",
        "user-library-read",
        "playlist-read-private"
    ]
    
    // MARK: - Spotify Auth URLs
    static let spotifyAuthURL = "https://accounts.spotify.com/authorize"
    
    // MARK: - Keychain Keys
    static let keychainService = "com.moodlens.app"
    static let keychainAccessTokenKey = "access_token"
}

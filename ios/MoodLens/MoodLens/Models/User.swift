import Foundation

// MARK: - User Models
struct User: Codable, Identifiable {
    let id: Int
    let spotifyUserId: String
    let displayName: String?
    let email: String?
    let connected: Bool
    let createdAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case spotifyUserId = "spotify_user_id"
        case displayName = "display_name"
        case email
        case connected
        case createdAt = "created_at"
    }
}

// MARK: - Auth Models
struct SpotifyExchangeRequest: Codable {
    let code: String
    let codeVerifier: String
    let redirectUri: String
    
    enum CodingKeys: String, CodingKey {
        case code
        case codeVerifier = "code_verifier"
        case redirectUri = "redirect_uri"
    }
}

struct SpotifyExchangeResponse: Codable {
    let accessToken: String
    let user: User
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case user
    }
}

struct DisconnectRequest: Codable {
    let deleteData: Bool
    
    enum CodingKeys: String, CodingKey {
        case deleteData = "delete_data"
    }
}

struct MessageResponse: Codable {
    let message: String
}

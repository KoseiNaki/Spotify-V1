import Foundation

enum APIError: Error {
    case invalidURL
    case networkError(Error)
    case invalidResponse
    case unauthorized
    case serverError(Int)
    case decodingError(Error)
}

class APIClient {
    static let shared = APIClient()
    
    private let baseURL = Config.apiBaseURL
    private let decoder: JSONDecoder
    
    private init() {
        decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
    }
    
    // MARK: - Generic Request
    func request<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Encodable? = nil,
        requiresAuth: Bool = true
    ) async throws -> T {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Add auth token if required
        if requiresAuth, let token = KeychainHelper.load(key: Config.keychainAccessTokenKey) {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        // Add body if present
        if let body = body {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            request.httpBody = try encoder.encode(body)
        }
        
        // Make request
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            switch httpResponse.statusCode {
            case 200...299:
                return try decoder.decode(T.self, from: data)
            case 401:
                throw APIError.unauthorized
            default:
                throw APIError.serverError(httpResponse.statusCode)
            }
        } catch let error as APIError {
            throw error
        } catch let error as DecodingError {
            throw APIError.decodingError(error)
        } catch {
            throw APIError.networkError(error)
        }
    }
    
    // MARK: - Auth Endpoints
    func exchangeSpotifyCode(code: String, codeVerifier: String) async throws -> SpotifyExchangeResponse {
        let request = SpotifyExchangeRequest(
            code: code,
            codeVerifier: codeVerifier,
            redirectUri: Config.spotifyRedirectURI
        )
        
        return try await self.request(
            endpoint: "/auth/spotify/exchange",
            method: "POST",
            body: request,
            requiresAuth: false
        )
    }
    
    func getCurrentUser() async throws -> User {
        return try await request(endpoint: "/me")
    }
    
    func disconnect(deleteData: Bool) async throws -> MessageResponse {
        let req = DisconnectRequest(deleteData: deleteData)
        return try await request(endpoint: "/disconnect", method: "POST", body: req)
    }
    
    func deleteUserData() async throws -> MessageResponse {
        return try await request(endpoint: "/me", method: "DELETE")
    }
    
    // MARK: - Analytics Endpoints
    func getAnalyticsSummary(range: String = "7d") async throws -> AnalyticsSummary {
        return try await request(endpoint: "/analytics/summary?range=\(range)")
    }
    
    func getTimeline(granularity: String = "day", range: String = "7d") async throws -> TimelineResponse {
        return try await request(endpoint: "/analytics/timeline?granularity=\(granularity)&range=\(range)")
    }
    
    func getInsights(range: String = "30d") async throws -> InsightsResponse {
        return try await request(endpoint: "/analytics/insights?range=\(range)")
    }
    
    func exportData() async throws -> Data {
        guard let url = URL(string: baseURL + "/analytics/export") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        if let token = KeychainHelper.load(key: Config.keychainAccessTokenKey) {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return data
    }
}

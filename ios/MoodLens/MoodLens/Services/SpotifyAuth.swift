import Foundation
import AuthenticationServices
import CryptoKit

@MainActor
class AuthManager: NSObject, ObservableObject {
    static let shared = AuthManager()
    
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var errorMessage: String?
    
    private var authSession: ASWebAuthenticationSession?
    private var codeVerifier: String?
    
    private override init() {
        super.init()
    }
    
    // MARK: - Load Auth State
    func loadAuth() {
        if let token = KeychainHelper.load(key: Config.keychainAccessTokenKey) {
            isAuthenticated = !token.isEmpty
            
            // Fetch user profile
            Task {
                do {
                    currentUser = try await APIClient.shared.getCurrentUser()
                } catch {
                    // Token might be invalid, clear it
                    logout()
                }
            }
        }
    }
    
    // MARK: - Connect Spotify (PKCE Flow)
    func connectSpotify() {
        // Generate PKCE code verifier and challenge
        let verifier = generateCodeVerifier()
        let challenge = generateCodeChallenge(from: verifier)
        self.codeVerifier = verifier
        
        // Build authorization URL
        var components = URLComponents(string: Config.spotifyAuthURL)!
        components.queryItems = [
            URLQueryItem(name: "client_id", value: Config.spotifyClientId),
            URLQueryItem(name: "response_type", value: "code"),
            URLQueryItem(name: "redirect_uri", value: Config.spotifyRedirectURI),
            URLQueryItem(name: "code_challenge_method", value: "S256"),
            URLQueryItem(name: "code_challenge", value: challenge),
            URLQueryItem(name: "scope", value: Config.spotifyScopes.joined(separator: " "))
        ]
        
        guard let authURL = components.url else {
            errorMessage = "Failed to create authorization URL"
            return
        }
        
        // Start web authentication session
        authSession = ASWebAuthenticationSession(
            url: authURL,
            callbackURLScheme: "moodlens"
        ) { [weak self] callbackURL, error in
            guard let self = self else { return }
            
            Task { @MainActor in
                if let error = error {
                    self.errorMessage = "Authentication failed: \(error.localizedDescription)"
                    return
                }
                
                guard let callbackURL = callbackURL,
                      let code = URLComponents(url: callbackURL, resolvingAgainstBaseURL: false)?
                    .queryItems?.first(where: { $0.name == "code" })?.value else {
                    self.errorMessage = "Failed to get authorization code"
                    return
                }
                
                // Exchange code for tokens
                await self.exchangeCode(code)
            }
        }
        
        authSession?.presentationContextProvider = self
        authSession?.prefersEphemeralWebBrowserSession = true
        authSession?.start()
    }
    
    // MARK: - Exchange Code
    private func exchangeCode(_ code: String) async {
        guard let verifier = codeVerifier else {
            errorMessage = "Missing code verifier"
            return
        }
        
        do {
            let response = try await APIClient.shared.exchangeSpotifyCode(
                code: code,
                codeVerifier: verifier
            )
            
            // Save token
            KeychainHelper.save(key: Config.keychainAccessTokenKey, value: response.accessToken)
            
            // Update state
            isAuthenticated = true
            currentUser = response.user
            errorMessage = nil
            
        } catch {
            errorMessage = "Failed to connect: \(error.localizedDescription)"
        }
    }
    
    // MARK: - Logout
    func logout() {
        KeychainHelper.delete(key: Config.keychainAccessTokenKey)
        isAuthenticated = false
        currentUser = nil
    }
    
    // MARK: - Disconnect
    func disconnect(deleteData: Bool) async {
        do {
            _ = try await APIClient.shared.disconnect(deleteData: deleteData)
            logout()
        } catch {
            errorMessage = "Failed to disconnect: \(error.localizedDescription)"
        }
    }
    
    // MARK: - PKCE Helpers
    private func generateCodeVerifier() -> String {
        var buffer = [UInt8](repeating: 0, count: 32)
        _ = SecRandomCopyBytes(kSecRandomDefault, buffer.count, &buffer)
        return Data(buffer).base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
            .trimmingCharacters(in: .whitespaces)
    }
    
    private func generateCodeChallenge(from verifier: String) -> String {
        let data = Data(verifier.utf8)
        let hash = SHA256.hash(data: data)
        return Data(hash).base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
            .trimmingCharacters(in: .whitespaces)
    }
}

// MARK: - ASWebAuthenticationPresentationContextProviding
extension AuthManager: ASWebAuthenticationPresentationContextProviding {
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        return ASPresentationAnchor()
    }
}

// MARK: - Keychain Helper
class KeychainHelper {
    static func save(key: String, value: String) {
        let data = value.data(using: .utf8)!
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: Config.keychainService,
            kSecAttrAccount as String: key,
            kSecValueData as String: data
        ]
        
        SecItemDelete(query as CFDictionary) // Delete existing
        SecItemAdd(query as CFDictionary, nil)
    }
    
    static func load(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: Config.keychainService,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess,
              let data = result as? Data,
              let value = String(data: data, encoding: .utf8) else {
            return nil
        }
        
        return value
    }
    
    static func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: Config.keychainService,
            kSecAttrAccount as String: key
        ]
        
        SecItemDelete(query as CFDictionary)
    }
}

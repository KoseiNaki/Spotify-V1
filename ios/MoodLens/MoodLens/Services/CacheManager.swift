import Foundation

class CacheManager {
    static let shared = CacheManager()
    
    private let defaults = UserDefaults.standard
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    
    private init() {
        encoder.dateEncodingStrategy = .iso8601
        decoder.dateDecodingStrategy = .iso8601
    }
    
    // MARK: - Cache Keys
    private enum CacheKey: String {
        case analyticsSummary = "cache_analytics_summary"
        case timeline = "cache_timeline"
        case insights = "cache_insights"
        case lastFetch = "cache_last_fetch"
    }
    
    // MARK: - Save/Load
    func save<T: Encodable>(_ value: T, for key: CacheKey) {
        if let data = try? encoder.encode(value) {
            defaults.set(data, forKey: key.rawValue)
            defaults.set(Date(), forKey: "\(key.rawValue)_timestamp")
        }
    }
    
    func load<T: Decodable>(for key: CacheKey, maxAge: TimeInterval = 300) -> T? {
        guard let data = defaults.data(forKey: key.rawValue),
              let timestamp = defaults.object(forKey: "\(key.rawValue)_timestamp") as? Date else {
            return nil
        }
        
        // Check if cache is too old
        if Date().timeIntervalSince(timestamp) > maxAge {
            return nil
        }
        
        return try? decoder.decode(T.self, from: data)
    }
    
    func clear() {
        CacheKey.allCases.forEach { key in
            defaults.removeObject(forKey: key.rawValue)
            defaults.removeObject(forKey: "\(key.rawValue)_timestamp")
        }
    }
}

extension CacheManager.CacheKey: CaseIterable {}

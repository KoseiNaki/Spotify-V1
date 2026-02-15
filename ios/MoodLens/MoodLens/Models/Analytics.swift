import Foundation

// MARK: - Analytics Summary
struct AnalyticsSummary: Codable {
    let rangeDays: Int
    let minutesListened: Int
    let sessionsCount: Int
    let uniqueTracks: Int
    let uniqueArtists: Int
    let repeatRate: Double
    let explorationRate: Double
    let comfortIndex: Double
    let avgMood: MoodAxes
    let topTracks: [TrackInfo]
    let topArtists: [ArtistInfo]
    
    enum CodingKeys: String, CodingKey {
        case rangeDays = "range_days"
        case minutesListened = "minutes_listened"
        case sessionsCount = "sessions_count"
        case uniqueTracks = "unique_tracks"
        case uniqueArtists = "unique_artists"
        case repeatRate = "repeat_rate"
        case explorationRate = "exploration_rate"
        case comfortIndex = "comfort_index"
        case avgMood = "avg_mood"
        case topTracks = "top_tracks"
        case topArtists = "top_artists"
    }
}

struct TrackInfo: Codable, Identifiable {
    var id: String { trackId }
    let trackId: String
    let name: String
    let artistName: String
    let albumName: String?
    let playCount: Int
    let durationMs: Int
    
    enum CodingKeys: String, CodingKey {
        case trackId = "track_id"
        case name
        case artistName = "artist_name"
        case albumName = "album_name"
        case playCount = "play_count"
        case durationMs = "duration_ms"
    }
}

struct ArtistInfo: Codable, Identifiable {
    var id: String { artistId }
    let artistId: String
    let name: String
    let playCount: Int
    let genres: [String]?
    
    enum CodingKeys: String, CodingKey {
        case artistId = "artist_id"
        case name
        case playCount = "play_count"
        case genres
    }
}

// MARK: - Insights
struct InsightsResponse: Codable {
    let rangeDays: Int
    let moodAnchors: [MoodAnchor]
    let comfortLoops: [ComfortLoop]
    let discoveryBursts: [DiscoveryBurst]
    
    enum CodingKeys: String, CodingKey {
        case rangeDays = "range_days"
        case moodAnchors = "mood_anchors"
        case comfortLoops = "comfort_loops"
        case discoveryBursts = "discovery_bursts"
    }
}

struct MoodAnchor: Codable, Identifiable {
    var id: String { trackId + moodAxis }
    let trackId: String
    let trackName: String
    let artistName: String
    let moodAxis: String
    let axisValue: Double
    let playCount: Int
    
    enum CodingKeys: String, CodingKey {
        case trackId = "track_id"
        case trackName = "track_name"
        case artistName = "artist_name"
        case moodAxis = "mood_axis"
        case axisValue = "axis_value"
        case playCount = "play_count"
    }
}

struct ComfortLoop: Codable, Identifiable {
    var id: String { trackId }
    let trackId: String
    let trackName: String
    let artistName: String
    let repeatCount: Int
    let timeSpanHours: Double
    
    enum CodingKeys: String, CodingKey {
        case trackId = "track_id"
        case trackName = "track_name"
        case artistName = "artist_name"
        case repeatCount = "repeat_count"
        case timeSpanHours = "time_span_hours"
    }
}

struct DiscoveryBurst: Codable, Identifiable {
    var id: String { date.ISO8601Format() }
    let date: Date
    let newArtists: Int
    let newTracks: Int
    
    enum CodingKeys: String, CodingKey {
        case date
        case newArtists = "new_artists"
        case newTracks = "new_tracks"
    }
}

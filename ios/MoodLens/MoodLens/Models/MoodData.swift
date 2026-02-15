import Foundation

// MARK: - Mood Axes
struct MoodAxes: Codable, Equatable {
    let positivity: Double
    let arousal: Double
    let warmth: Double
    let focus: Double
    
    static let zero = MoodAxes(positivity: 0, arousal: 0, warmth: 0, focus: 0)
    
    var auraColor: (red: Double, green: Double, blue: Double) {
        // Map mood to color
        let red = positivity * 0.5 + arousal * 0.3 + 0.2
        let green = warmth * 0.5 + positivity * 0.3 + 0.2
        let blue = focus * 0.4 + (1 - arousal) * 0.4 + 0.2
        return (red, green, blue)
    }
    
    var dominantMood: String {
        let moods = [
            ("Positive", positivity),
            ("Energetic", arousal),
            ("Warm", warmth),
            ("Focused", focus)
        ]
        return moods.max(by: { $0.1 < $1.1 })?.0 ?? "Neutral"
    }
}

// MARK: - Timeline Models
struct TimelinePoint: Codable, Identifiable {
    var id: String { timestamp.ISO8601Format() }
    let timestamp: Date
    let mood: MoodAxes
    let volatility: MoodAxes?
    let minutes: Int
    let playCount: Int
    
    enum CodingKeys: String, CodingKey {
        case timestamp, mood, volatility, minutes
        case playCount = "play_count"
    }
}

struct TimelineResponse: Codable {
    let granularity: String
    let rangeDays: Int
    let data: [TimelinePoint]
    
    enum CodingKeys: String, CodingKey {
        case granularity
        case rangeDays = "range_days"
        case data
    }
}

// MARK: - Session Model
struct Session: Codable, Identifiable {
    var id: String { startAt.ISO8601Format() }
    let startAt: Date
    let endAt: Date
    let mood: MoodAxes
    let playCount: Int
    
    enum CodingKeys: String, CodingKey {
        case startAt = "start_at"
        case endAt = "end_at"
        case mood = "avg_axes"
        case playCount = "play_count"
    }
}

import SwiftUI

struct DashboardView: View {
    @State private var summary: AnalyticsSummary?
    @State private var isLoading = true
    @State private var errorMessage: String?
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    if isLoading {
                        ProgressView("Loading your vibe...")
                            .padding()
                    } else if let summary = summary {
                        // Moment Check Card
                        MomentCheckCard(mood: summary.avgMood, minutes: summary.minutesListened)
                        
                        // Stats Grid
                        StatsGrid(summary: summary)
                        
                        // Top Tracks
                        if !summary.topTracks.isEmpty {
                            TopItemsSection(
                                title: "Your Top Tracks",
                                items: summary.topTracks.prefix(5).map { track in
                                    TopItem(
                                        name: track.name,
                                        subtitle: track.artistName,
                                        count: track.playCount
                                    )
                                }
                            )
                        }
                        
                        // Top Artists
                        if !summary.topArtists.isEmpty {
                            TopItemsSection(
                                title: "Your Top Artists",
                                items: summary.topArtists.prefix(5).map { artist in
                                    TopItem(
                                        name: artist.name,
                                        subtitle: artist.genres?.first ?? "",
                                        count: artist.playCount
                                    )
                                }
                            )
                        }
                    } else if let error = errorMessage {
                        Text("Error: \(error)")
                            .foregroundColor(.red)
                    }
                }
                .padding()
            }
            .navigationTitle("Dashboard")
            .refreshable {
                await loadData()
            }
        }
        .task {
            await loadData()
        }
    }
    
    private func loadData() async {
        isLoading = true
        errorMessage = nil
        
        do {
            summary = try await APIClient.shared.getAnalyticsSummary(range: "7d")
            CacheManager.shared.save(summary!, for: .analyticsSummary)
        } catch {
            errorMessage = error.localizedDescription
            // Try to load from cache
            summary = CacheManager.shared.load(for: .analyticsSummary, maxAge: 3600)
        }
        
        isLoading = false
    }
}

struct MomentCheckCard: View {
    let mood: MoodAxes
    let minutes: Int
    
    var body: some View {
        VStack(spacing: 16) {
            Text("Your Current Vibe")
                .font(.headline)
                .foregroundColor(.secondary)
            
            // Aura visualization
            let colors = mood.auraColor
            Circle()
                .fill(
                    RadialGradient(
                        colors: [
                            Color(red: colors.red, green: colors.green, blue: colors.blue),
                            Color(red: colors.red * 0.7, green: colors.green * 0.7, blue: colors.blue * 0.7)
                        ],
                        center: .center,
                        startRadius: 20,
                        endRadius: 80
                    )
                )
                .frame(width: 120, height: 120)
                .shadow(color: Color(red: colors.red, green: colors.green, blue: colors.blue).opacity(0.5), radius: 20)
            
            Text(mood.dominantMood)
                .font(.title2)
                .fontWeight(.bold)
            
            HStack(spacing: 20) {
                StatPill(label: "Positivity", value: mood.positivity)
                StatPill(label: "Energy", value: mood.arousal)
                StatPill(label: "Warmth", value: mood.warmth)
                StatPill(label: "Focus", value: mood.focus)
            }
            
            Text("\(minutes) minutes today")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 10)
    }
}

struct StatPill: View {
    let label: String
    let value: Double
    
    var body: some View {
        VStack(spacing: 4) {
            Text(String(format: "%.0f%%", value * 100))
                .font(.caption)
                .fontWeight(.bold)
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color.purple.opacity(0.1))
        .cornerRadius(8)
    }
}

struct StatsGrid: View {
    let summary: AnalyticsSummary
    
    var body: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
            StatCard(
                title: "Sessions",
                value: "\(summary.sessionsCount)",
                icon: "headphones"
            )
            
            StatCard(
                title: "Unique Tracks",
                value: "\(summary.uniqueTracks)",
                icon: "music.note.list"
            )
            
            StatCard(
                title: "Repeat Rate",
                value: String(format: "%.0f%%", summary.repeatRate * 100),
                icon: "repeat"
            )
            
            StatCard(
                title: "Exploration",
                value: String(format: "%.0f%%", summary.explorationRate * 100),
                icon: "sparkles"
            )
        }
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(.purple)
                Spacer()
            }
            
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.05), radius: 5)
    }
}

struct TopItem {
    let name: String
    let subtitle: String
    let count: Int
}

struct TopItemsSection: View {
    let title: String
    let items: [TopItem]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
                .padding(.horizontal)
            
            VStack(spacing: 8) {
                ForEach(items.indices, id: \.self) { index in
                    HStack {
                        Text("\(index + 1)")
                            .font(.caption)
                            .fontWeight(.bold)
                            .foregroundColor(.purple)
                            .frame(width: 20)
                        
                        VStack(alignment: .leading) {
                            Text(items[index].name)
                                .font(.subheadline)
                                .fontWeight(.medium)
                            if !items[index].subtitle.isEmpty {
                                Text(items[index].subtitle)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        
                        Spacer()
                        
                        Text("\(items[index].count) plays")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 8)
                }
            }
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(color: .black.opacity(0.05), radius: 5)
        }
    }
}

import SwiftUI

struct InsightsView: View {
    @State private var insights: InsightsResponse?
    @State private var isLoading = true
    @State private var selectedRange: String = "30d"
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Range selector
                    Picker("Range", selection: $selectedRange) {
                        Text("Week").tag("7d")
                        Text("Month").tag("30d")
                        Text("3 Months").tag("90d")
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal)
                    
                    if isLoading {
                        ProgressView("Loading insights...")
                            .padding()
                    } else if let insights = insights {
                        // Mood Anchors
                        if !insights.moodAnchors.isEmpty {
                            MoodAnchorsSection(anchors: insights.moodAnchors)
                        }
                        
                        // Comfort Loops
                        if !insights.comfortLoops.isEmpty {
                            ComfortLoopsSection(loops: insights.comfortLoops)
                        }
                        
                        // Discovery Bursts
                        if !insights.discoveryBursts.isEmpty {
                            DiscoveryBurstsSection(bursts: insights.discoveryBursts)
                        }
                    }
                }
                .padding(.vertical)
            }
            .navigationTitle("Insights")
            .refreshable {
                await loadData()
            }
        }
        .task {
            await loadData()
        }
        .onChange(of: selectedRange) { _, _ in
            Task { await loadData() }
        }
    }
    
    private func loadData() async {
        isLoading = true
        
        do {
            insights = try await APIClient.shared.getInsights(range: selectedRange)
            CacheManager.shared.save(insights!, for: .insights)
        } catch {
            insights = CacheManager.shared.load(for: .insights, maxAge: 3600)
        }
        
        isLoading = false
    }
}

struct MoodAnchorsSection: View {
    let anchors: [MoodAnchor]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "anchor.fill")
                    .foregroundColor(.purple)
                Text("Mood Anchors")
                    .font(.headline)
            }
            .padding(.horizontal)
            
            Text("Tracks that define your moods")
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.horizontal)
            
            VStack(spacing: 8) {
                ForEach(Array(anchors.prefix(12)), id: \.id) { anchor in
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(anchor.trackName)
                                .font(.subheadline)
                                .fontWeight(.medium)
                            Text(anchor.artistName)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        VStack(alignment: .trailing, spacing: 2) {
                            Text(anchor.moodAxis.capitalized)
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundColor(moodColor(for: anchor.moodAxis))
                            Text(String(format: "%.0f%%", anchor.axisValue * 100))
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding()
                    .background(Color(.secondarySystemBackground))
                    .cornerRadius(10)
                }
            }
            .padding(.horizontal)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 10)
        .padding(.horizontal)
    }
    
    private func moodColor(for axis: String) -> Color {
        switch axis {
        case "positivity": return .green
        case "arousal": return .orange
        case "warmth": return .pink
        case "focus": return .blue
        default: return .purple
        }
    }
}

struct ComfortLoopsSection: View {
    let loops: [ComfortLoop]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "repeat.circle.fill")
                    .foregroundColor(.purple)
                Text("Comfort Loops")
                    .font(.headline)
            }
            .padding(.horizontal)
            
            Text("Tracks you return to for comfort")
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.horizontal)
            
            VStack(spacing: 8) {
                ForEach(loops) { loop in
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(loop.trackName)
                                .font(.subheadline)
                                .fontWeight(.medium)
                            Text(loop.artistName)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        VStack(alignment: .trailing, spacing: 2) {
                            Text("\(loop.repeatCount)x")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundColor(.purple)
                            Text(String(format: "%.1fh span", loop.timeSpanHours))
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding()
                    .background(Color(.secondarySystemBackground))
                    .cornerRadius(10)
                }
            }
            .padding(.horizontal)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 10)
        .padding(.horizontal)
    }
}

struct DiscoveryBurstsSection: View {
    let bursts: [DiscoveryBurst]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "sparkle")
                    .foregroundColor(.purple)
                Text("Discovery Bursts")
                    .font(.headline)
            }
            .padding(.horizontal)
            
            Text("Days when you explored new music")
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.horizontal)
            
            VStack(spacing: 8) {
                ForEach(bursts) { burst in
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(burst.date, format: .dateTime.month().day().year())
                                .font(.subheadline)
                                .fontWeight(.medium)
                            
                            HStack(spacing: 12) {
                                Label("\(burst.newTracks) tracks", systemImage: "music.note")
                                Label("\(burst.newArtists) artists", systemImage: "person.2")
                            }
                            .font(.caption)
                            .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        Image(systemName: "sparkles")
                            .foregroundColor(.yellow)
                    }
                    .padding()
                    .background(Color(.secondarySystemBackground))
                    .cornerRadius(10)
                }
            }
            .padding(.horizontal)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 10)
        .padding(.horizontal)
    }
}

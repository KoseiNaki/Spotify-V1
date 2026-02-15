import SwiftUI
import Charts

struct TimelineView: View {
    @State private var timeline: TimelineResponse?
    @State private var isLoading = true
    @State private var selectedGranularity: Granularity = .day
    @State private var selectedRange: Range = .week
    
    enum Granularity: String, CaseIterable {
        case hour = "hour"
        case day = "day"
    }
    
    enum Range: String, CaseIterable {
        case week = "7d"
        case month = "30d"
        case quarter = "90d"
        
        var displayName: String {
            switch self {
            case .week: return "Week"
            case .month: return "Month"
            case .quarter: return "3 Months"
            }
        }
    }
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Controls
                    HStack {
                        Picker("Granularity", selection: $selectedGranularity) {
                            ForEach(Granularity.allCases, id: \.self) { gran in
                                Text(gran.rawValue.capitalized).tag(gran)
                            }
                        }
                        .pickerStyle(.segmented)
                        
                        Picker("Range", selection: $selectedRange) {
                            ForEach(Range.allCases, id: \.self) { range in
                                Text(range.displayName).tag(range)
                            }
                        }
                        .pickerStyle(.menu)
                    }
                    .padding(.horizontal)
                    
                    if isLoading {
                        ProgressView("Loading timeline...")
                            .padding()
                    } else if let timeline = timeline {
                        // Mood charts
                        if !timeline.data.isEmpty {
                            MoodChartsView(data: timeline.data)
                            
                            // Heatmap (if daily)
                            if selectedGranularity == .day {
                                MoodHeatmap(data: timeline.data)
                            }
                        } else {
                            Text("No data available for this period")
                                .foregroundColor(.secondary)
                                .padding()
                        }
                    }
                }
                .padding(.vertical)
            }
            .navigationTitle("Timeline")
            .refreshable {
                await loadData()
            }
        }
        .task {
            await loadData()
        }
        .onChange(of: selectedGranularity) { _, _ in
            Task { await loadData() }
        }
        .onChange(of: selectedRange) { _, _ in
            Task { await loadData() }
        }
    }
    
    private func loadData() async {
        isLoading = true
        
        do {
            timeline = try await APIClient.shared.getTimeline(
                granularity: selectedGranularity.rawValue,
                range: selectedRange.rawValue
            )
            CacheManager.shared.save(timeline!, for: .timeline)
        } catch {
            // Try cache
            timeline = CacheManager.shared.load(for: .timeline, maxAge: 3600)
        }
        
        isLoading = false
    }
}

struct MoodChartsView: View {
    let data: [TimelinePoint]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Mood Over Time")
                .font(.headline)
                .padding(.horizontal)
            
            // Positivity chart
            MoodLineChart(data: data, axis: \.mood.positivity, title: "Positivity", color: .green)
            
            // Arousal chart
            MoodLineChart(data: data, axis: \.mood.arousal, title: "Energy", color: .orange)
            
            // Warmth chart
            MoodLineChart(data: data, axis: \.mood.warmth, title: "Warmth", color: .pink)
            
            // Focus chart
            MoodLineChart(data: data, axis: \.mood.focus, title: "Focus", color: .blue)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 10)
        .padding(.horizontal)
    }
}

struct MoodLineChart: View {
    let data: [TimelinePoint]
    let axis: KeyPath<TimelinePoint, Double>
    let title: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            Chart {
                ForEach(data) { point in
                    LineMark(
                        x: .value("Time", point.timestamp),
                        y: .value(title, point[keyPath: axis])
                    )
                    .foregroundStyle(color)
                    
                    AreaMark(
                        x: .value("Time", point.timestamp),
                        y: .value(title, point[keyPath: axis])
                    )
                    .foregroundStyle(color.opacity(0.2))
                }
            }
            .frame(height: 100)
            .chartYScale(domain: 0...1)
        }
    }
}

struct MoodHeatmap: View {
    let data: [TimelinePoint]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Weekly Pattern")
                .font(.headline)
                .padding(.horizontal)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(data) { point in
                        VStack(spacing: 4) {
                            let colors = point.mood.auraColor
                            RoundedRectangle(cornerRadius: 8)
                                .fill(Color(red: colors.red, green: colors.green, blue: colors.blue))
                                .frame(width: 40, height: 60)
                            
                            Text(point.timestamp, format: .dateTime.day())
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                .padding(.horizontal)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 10)
        .padding(.horizontal)
    }
}

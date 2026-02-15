import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager
    
    var body: some View {
        Group {
            if authManager.isAuthenticated {
                TabView {
                    DashboardView()
                        .tabItem {
                            Label("Dashboard", systemImage: "chart.line.uptrend.xyaxis")
                        }
                    
                    TimelineView()
                        .tabItem {
                            Label("Timeline", systemImage: "calendar")
                        }
                    
                    InsightsView()
                        .tabItem {
                            Label("Insights", systemImage: "sparkles")
                        }
                    
                    SettingsView()
                        .tabItem {
                            Label("Settings", systemImage: "gearshape.fill")
                        }
                }
                .accentColor(Color.purple)
            } else {
                OnboardingView()
            }
        }
        .onAppear {
            authManager.loadAuth()
        }
    }
}

struct OnboardingView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var isConnecting = false
    
    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color.purple.opacity(0.8), Color.blue.opacity(0.6)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            VStack(spacing: 30) {
                Spacer()
                
                Image(systemName: "music.note.list")
                    .font(.system(size: 80))
                    .foregroundColor(.white)
                
                Text("MoodLens")
                    .font(.system(size: 48, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                
                Text("Your listening, through an emotional lens")
                    .font(.title3)
                    .foregroundColor(.white.opacity(0.9))
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
                
                Spacer()
                
                Button(action: {
                    isConnecting = true
                    authManager.connectSpotify()
                }) {
                    HStack {
                        Image(systemName: "music.note")
                        Text("Connect Spotify")
                    }
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.green)
                    .cornerRadius(12)
                }
                .disabled(isConnecting)
                .padding(.horizontal, 40)
                .padding(.bottom, 50)
            }
        }
    }
}

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var showingDisconnectAlert = false
    @State private var showingDeleteAlert = false
    @State private var isExporting = false
    
    var body: some View {
        NavigationView {
            List {
                // Profile Section
                Section {
                    if let user = authManager.currentUser {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(user.displayName ?? "Spotify User")
                                .font(.headline)
                            if let email = user.email {
                                Text(email)
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                            Text("Connected since \(user.createdAt, format: .dateTime.month().day().year())")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(.vertical, 4)
                    }
                } header: {
                    Text("Account")
                }
                
                // Data Section
                Section {
                    Button(action: {
                        Task {
                            await exportData()
                        }
                    }) {
                        HStack {
                            Label("Export My Data", systemImage: "square.and.arrow.up")
                            if isExporting {
                                Spacer()
                                ProgressView()
                            }
                        }
                    }
                    .disabled(isExporting)
                } header: {
                    Text("Data")
                } footer: {
                    Text("Download a JSON file containing all your listening data and mood analytics")
                }
                
                // Privacy Section
                Section {
                    NavigationLink(destination: PrivacyView()) {
                        Label("Privacy Policy", systemImage: "hand.raised.fill")
                    }
                } header: {
                    Text("Privacy")
                }
                
                // Danger Zone
                Section {
                    Button(role: .destructive, action: {
                        showingDisconnectAlert = true
                    }) {
                        Label("Disconnect Spotify", systemImage: "link.badge.minus")
                    }
                    
                    Button(role: .destructive, action: {
                        showingDeleteAlert = true
                    }) {
                        Label("Delete All Data", systemImage: "trash")
                    }
                } header: {
                    Text("Danger Zone")
                } footer: {
                    Text("Disconnecting removes your Spotify connection but preserves your data. Deleting removes everything permanently.")
                }
                
                // App Info
                Section {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                } header: {
                    Text("About")
                }
            }
            .navigationTitle("Settings")
            .alert("Disconnect Spotify?", isPresented: $showingDisconnectAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Keep Data & Disconnect", role: .destructive) {
                    Task {
                        await authManager.disconnect(deleteData: false)
                    }
                }
                Button("Delete Everything", role: .destructive) {
                    Task {
                        await authManager.disconnect(deleteData: true)
                    }
                }
            } message: {
                Text("Choose whether to keep or delete your listening data")
            }
            .alert("Delete All Data?", isPresented: $showingDeleteAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Delete", role: .destructive) {
                    Task {
                        await authManager.disconnect(deleteData: true)
                    }
                }
            } message: {
                Text("This will permanently delete all your data. This action cannot be undone.")
            }
        }
    }
    
    private func exportData() async {
        isExporting = true
        
        do {
            let data = try await APIClient.shared.exportData()
            
            // Save to files
            let tempURL = FileManager.default.temporaryDirectory
                .appendingPathComponent("moodlens_export_\(Date().timeIntervalSince1970).json")
            try data.write(to: tempURL)
            
            // Share
            await MainActor.run {
                let activityVC = UIActivityViewController(
                    activityItems: [tempURL],
                    applicationActivities: nil
                )
                
                if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                   let window = windowScene.windows.first,
                   let rootVC = window.rootViewController {
                    rootVC.present(activityVC, animated: true)
                }
            }
        } catch {
            print("Export failed: \(error)")
        }
        
        isExporting = false
    }
}

struct PrivacyView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Privacy Policy")
                    .font(.title)
                    .fontWeight(.bold)
                
                Text("Last Updated: February 2026")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Divider()
                
                privacySection(
                    title: "What We Collect",
                    content: """
                    MoodLens collects your Spotify listening history, including:
                    • Recently played tracks
                    • Track metadata (song names, artists, albums)
                    • Audio features (energy, valence, tempo, etc.)
                    • Your Spotify user ID and display name
                    
                    We only collect data from the moment you connect your account forward. We do not have access to your complete listening history.
                    """
                )
                
                privacySection(
                    title: "How We Use Your Data",
                    content: """
                    Your data is used exclusively to:
                    • Compute mood analytics and listening patterns
                    • Generate personalized insights
                    • Display your listening trends over time
                    
                    We do NOT:
                    • Sell your data to third parties
                    • Use your data for advertising
                    • Share your data with anyone except as required by law
                    """
                )
                
                privacySection(
                    title: "Data Storage",
                    content: """
                    Your data is stored securely on our servers with encryption. Your Spotify refresh token is encrypted at rest using industry-standard encryption (Fernet).
                    """
                )
                
                privacySection(
                    title: "Your Rights",
                    content: """
                    You have the right to:
                    • Export all your data at any time
                    • Disconnect your Spotify account
                    • Delete all your data permanently
                    
                    Use the settings menu to exercise these rights.
                    """
                )
                
                privacySection(
                    title: "Data Retention",
                    content: """
                    We retain your data as long as you have an active account. When you delete your account, all associated data is permanently removed from our systems within 30 days.
                    """
                )
                
                privacySection(
                    title: "Not Medical Advice",
                    content: """
                    MoodLens provides entertainment and self-discovery features only. Our mood analytics are based on audio features and listening patterns, not clinical assessment. This is not a medical or mental health tool.
                    """
                )
                
                privacySection(
                    title: "Contact",
                    content: """
                    Questions about privacy? Contact us at privacy@moodlens.app
                    """
                )
            }
            .padding()
        }
        .navigationTitle("Privacy")
        .navigationBarTitleDisplayMode(.inline)
    }
    
    private func privacySection(title: String, content: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)
                .foregroundColor(.purple)
            
            Text(content)
                .font(.body)
                .foregroundColor(.primary)
        }
        .padding(.vertical, 8)
    }
}

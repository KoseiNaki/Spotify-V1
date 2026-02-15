# MoodLens - Complete Setup Guide

## 📋 Table of Contents
1. [Spotify Developer Setup](#spotify-developer-setup)
2. [Backend Setup](#backend-setup)
3. [iOS App Setup](#ios-app-setup)
4. [Testing the Integration](#testing-the-integration)
5. [Troubleshooting](#troubleshooting)

---

## 🎵 Spotify Developer Setup

### Step 1: Create Spotify App

1. Go to [Spotify for Developers](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create app"**
4. Fill in the details:
   - **App name**: `MoodLens`
   - **App description**: `Personal listening analytics dashboard`
   - **Website**: `http://localhost:8000` (or your domain)
   - **Redirect URI**: `moodlens://callback`
   - **Which API/SDKs are you planning to use?**: Select "Web API"

5. Agree to terms and click **"Save"**

### Step 2: Configure App Settings

1. In your app dashboard, click **"Settings"**
2. Under **"Redirect URIs"**, add both:
   ```
   moodlens://callback
   http://localhost:8000/callback
   ```
3. Click **"Add"** then **"Save"**

### Step 3: Get Credentials

1. Copy **Client ID** (you'll need this for both backend and iOS)
2. Click **"View client secret"** and copy it (backend only!)
3. Save these securely - never commit them to git!

---

## 🖥️ Backend Setup

### Prerequisites
- Python 3.10 or higher
- PostgreSQL 14 or higher (or Docker)
- Git

### Step 1: Clone Repository
```bash
git clone https://github.com/KoseiNaki/Spotify-V1.git
cd Spotify-V1/backend
```

### Step 2: Create Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Start PostgreSQL

**Option A: Docker (Recommended)**
```bash
docker-compose up -d postgres
```

**Option B: Local PostgreSQL**
```bash
# macOS (Homebrew)
brew install postgresql@14
brew services start postgresql@14
createdb moodlens

# Ubuntu/Debian
sudo apt-get install postgresql
sudo -u postgres createdb moodlens
```

### Step 5: Configure Environment
```bash
cp .env.example .env
```

**Generate encryption key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Edit `.env` file:**
```env
# Database
DATABASE_URL=postgresql://moodlens:moodlens_dev@localhost:5432/moodlens

# Encryption (paste generated key from above)
ENCRYPTION_KEY=YOUR_GENERATED_FERNET_KEY_HERE

# JWT (generate a random string)
JWT_SECRET_KEY=your-very-secret-jwt-key-change-this

# Spotify (from Spotify Developer Dashboard)
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_REDIRECT_URI=moodlens://callback

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

### Step 6: Run Database Migrations
```bash
alembic upgrade head
```

You should see output like:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial, Initial schema
```

### Step 7: Start Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify it's running:**
- Open browser: http://localhost:8000
- Should see: `{"name": "MoodLens API", "version": "1.0.0", "status": "running"}`
- API docs: http://localhost:8000/docs

---

## 📱 iOS App Setup

### Prerequisites
- macOS with Xcode 15+
- iOS 17+ device or simulator

### Step 1: Open Project
```bash
cd ../ios/MoodLens
open MoodLens.xcodeproj
```

Or open Xcode → File → Open → Navigate to `ios/MoodLens/MoodLens.xcodeproj`

### Step 2: Configure Project Settings

1. **Select MoodLens target** (top left, next to play button)
2. **Signing & Capabilities** tab:
   - Team: Select your Apple Developer account
   - Bundle Identifier: Use `com.yourname.moodlens` (must be unique)

### Step 3: Add URL Scheme

1. Still in MoodLens target settings
2. **Info** tab
3. Scroll to **URL Types**
4. Click **+** to add new URL type
5. Set:
   - **Identifier**: `com.moodlens.auth`
   - **URL Schemes**: `moodlens`
   - **Role**: Editor

### Step 4: Configure API and Spotify

Edit `MoodLens/Config.swift`:

```swift
struct Config {
    // Backend URL (use your computer's IP if testing on device)
    static let apiBaseURL = "http://localhost:8000"  // Simulator
    // static let apiBaseURL = "http://192.168.1.XXX:8000"  // Physical device
    
    // Spotify (from Spotify Developer Dashboard)
    static let spotifyClientId = "YOUR_SPOTIFY_CLIENT_ID"
    static let spotifyRedirectURI = "moodlens://callback"
    // ... rest stays the same
}
```

**For physical device testing:**
1. Find your Mac's local IP: System Settings → Network → Wi-Fi → Details
2. Use that IP instead of `localhost` (e.g., `http://192.168.1.5:8000`)

### Step 5: Add Spotify to Info.plist

1. Right-click `Info.plist` → Open As → Source Code
2. Add before the last `</dict>`:

```xml
<key>LSApplicationQueriesSchemes</key>
<array>
    <string>spotify</string>
</array>
```

### Step 6: Build and Run

1. Select target device (iPhone simulator or your device)
2. Press **Cmd + R** to build and run
3. App should launch and show onboarding screen

---

## 🧪 Testing the Integration

### Test 1: Backend Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "scheduler": "running"
}
```

### Test 2: iOS Connection Flow

1. Launch iOS app
2. Tap **"Connect Spotify"**
3. Should open Spotify login in web view
4. Log in with your Spotify account
5. Click **"Agree"** to authorize
6. Should return to app and show dashboard
7. Initially empty (no data yet)

### Test 3: Verify Token Storage

**Backend (PostgreSQL):**
```bash
docker exec -it spotify-v1-postgres-1 psql -U moodlens -d moodlens

# In psql:
SELECT id, spotify_user_id, display_name FROM users;
SELECT user_id, access_expires_at FROM spotify_tokens;
```

**iOS (Console logs in Xcode):**
- Should see "Refreshed access token for user X" in backend logs after 15 minutes

### Test 4: Wait for Data Ingestion

1. Listen to some music on Spotify (any device)
2. Wait 15-20 minutes (ingestion job runs every 15 min)
3. Pull to refresh in iOS app
4. Should start seeing data populate

### Test 5: Check Background Job

```bash
# View backend logs
# Should see every 15 minutes:
# "Starting ingestion for X users"
# "Ingested Y new plays for user Z"
```

---

## 🔧 Troubleshooting

### Backend Issues

**Problem: "ModuleNotFoundError" or "ImportError"**
```bash
# Solution: Ensure venv is activated and dependencies installed
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Problem: "Connection refused" to PostgreSQL**
```bash
# Solution 1: Check Docker is running
docker-compose ps

# Solution 2: Restart PostgreSQL
docker-compose restart postgres

# Solution 3: Check DATABASE_URL in .env matches your setup
```

**Problem: Alembic migration fails**
```bash
# Solution: Drop and recreate database
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

**Problem: "Invalid encryption key"**
```bash
# Solution: Regenerate key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Update ENCRYPTION_KEY in .env
```

### iOS Issues

**Problem: "Cannot connect to localhost"**
```
Solution 1: If using device (not simulator), use Mac's IP address:
- System Settings → Network → Wi-Fi → Details
- Use that IP in Config.swift (e.g., http://192.168.1.5:8000)

Solution 2: If using simulator, ensure backend is running:
- curl http://localhost:8000/health
```

**Problem: Spotify login opens but doesn't redirect back**
```
Solution: Check URL scheme is configured
1. Xcode → MoodLens target → Info tab → URL Types
2. Verify "moodlens" is listed
3. Clean build folder (Cmd+Shift+K) and rebuild
```

**Problem: "The operation couldn't be completed"**
```
Solution: Check Spotify Dashboard redirect URIs
1. Go to https://developer.spotify.com/dashboard
2. Your app → Settings → Redirect URIs
3. Ensure "moodlens://callback" is listed
4. Click Save
```

**Problem: App crashes on launch**
```
Solution 1: Check Config.swift has valid values
Solution 2: Clean DerivedData:
- Xcode → Product → Clean Build Folder (Cmd+Shift+K)
- Quit Xcode
- rm -rf ~/Library/Developer/Xcode/DerivedData
- Reopen and rebuild
```

### Data Not Appearing

**Problem: Connected but no data in dashboard**
```
Solution: This is normal initially!
1. Listen to music on Spotify
2. Wait 15-20 minutes for first ingestion
3. Pull to refresh in app
4. Check backend logs for "Ingested X new plays"
```

**Problem: Background job not running**
```
Solution: Check backend logs
# Should see every 15 minutes:
INFO - Starting ingestion for 1 users

If not:
1. Restart backend
2. Check /health endpoint shows "scheduler": "running"
```

---

## 📊 Monitoring

### Backend Logs
```bash
# Watch logs in real-time
tail -f backend.log  # if you set up logging to file

# Or just watch terminal where uvicorn is running
```

### Database Queries
```bash
docker exec -it spotify-v1-postgres-1 psql -U moodlens -d moodlens

# Check user count
SELECT COUNT(*) FROM users;

# Check play events
SELECT COUNT(*) FROM play_events;

# Check recent plays
SELECT p.played_at, t.name, t.primary_artist_name 
FROM play_events p 
JOIN tracks t ON p.track_id = t.track_id 
ORDER BY p.played_at DESC 
LIMIT 10;
```

---

## 🚀 Next Steps

1. **Listen to music** on Spotify (any device)
2. **Wait 15-20 minutes** for first data sync
3. **Explore the app:**
   - Dashboard: See your current mood
   - Timeline: View mood trends over time
   - Insights: Discover patterns and favorites
   - Settings: Export data or disconnect

4. **Customize:**
   - Adjust ingestion interval in `.env` (INGESTION_INTERVAL_MINUTES)
   - Modify mood formulas in `backend/app/mood_engine.py`
   - Change colors in iOS app (Views use Color.purple)

---

## 📝 Notes

- **First sync takes time**: Initial ingestion populates tracks, artists, and audio features
- **Rate limits**: Spotify allows ~180 requests/minute - background job handles this
- **Token refresh**: Happens automatically every ~50 minutes
- **Offline mode**: iOS app uses cached data when network unavailable

---

## ✅ Success Checklist

- [ ] Backend running at http://localhost:8000
- [ ] PostgreSQL database created and migrated
- [ ] Spotify app created with correct redirect URI
- [ ] iOS app builds without errors
- [ ] Can tap "Connect Spotify" and complete auth flow
- [ ] Backend logs show "Starting ingestion" every 15 minutes
- [ ] After 15+ minutes, data appears in app

---

**Need help?** Open an issue on GitHub with:
- Error message (full text)
- Steps to reproduce
- Backend logs (relevant section)
- iOS console output (if applicable)

Happy analyzing! 🎵✨

# MoodLens 🎵✨

**Your Spotify listening, through an emotional lens**

MoodLens is a quantified-self analytics dashboard that transforms your Spotify listening history into emotional insights. Track your moods, discover patterns, and understand how music shapes your daily experience.

---

## 🌟 Features

- **Mood Analytics**: 4-axis mood system (Positivity, Arousal, Warmth, Focus) derived from Spotify audio features
- **Continuous Tracking**: Background ingestion collects listening data every 15 minutes
- **Beautiful Visualizations**: Aura-based mood colors, timeline charts, and heatmaps
- **Deep Insights**: Mood anchors, comfort loops, discovery bursts, and repeat patterns
- **Privacy First**: Encrypted token storage, data export, and complete deletion control
- **iOS Native**: SwiftUI app optimized for iOS 17+

---

## 📁 Repository Structure

```
Spotify-V1/
├── backend/              # FastAPI Python backend
│   ├── app/
│   │   ├── main.py      # FastAPI application
│   │   ├── models.py    # SQLAlchemy database models
│   │   ├── spotify_client.py
│   │   ├── mood_engine.py
│   │   ├── jobs.py      # Background ingestion (APScheduler)
│   │   └── routers/     # API endpoints
│   ├── alembic/         # Database migrations
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── .env.example
│
└── ios/                 # SwiftUI iOS app
    └── MoodLens/
        ├── Models/      # Data models
        ├── Services/    # API client, Auth, Cache
        └── Views/       # Dashboard, Timeline, Insights, Settings
```

---

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.10+, PostgreSQL 14+, Docker (optional)
- **iOS**: Xcode 15+, iOS 17+
- **Spotify**: Developer account with registered app

---

## 🔧 Backend Setup

### 1. Clone and Navigate

```bash
git clone https://github.com/KoseiNaki/Spotify-V1.git
cd Spotify-V1/backend
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start Database (Docker)

```bash
docker-compose up -d postgres
```

Or install PostgreSQL locally and create a database:
```sql
CREATE DATABASE moodlens;
CREATE USER moodlens WITH PASSWORD 'moodlens_dev';
GRANT ALL PRIVILEGES ON DATABASE moodlens TO moodlens;
```

### 4. Configure Environment

```bash
cp .env.example .env
```

**Edit `.env`** and fill in:

```env
# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Use generated key in .env
ENCRYPTION_KEY=your-generated-key-here

# Spotify API (from step 5)
SPOTIFY_CLIENT_ID=your-client-id
SPOTIFY_CLIENT_SECRET=your-client-secret
SPOTIFY_REDIRECT_URI=moodlens://callback

# JWT Secret (generate random string)
JWT_SECRET_KEY=your-jwt-secret-change-in-production
```

### 5. Spotify Developer Dashboard Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app:
   - **App Name**: MoodLens
   - **App Description**: Personal Spotify analytics
   - **Redirect URI**: `moodlens://callback`
3. Copy **Client ID** and **Client Secret** to `.env`
4. Under "Edit Settings" → "Redirect URIs", add:
   - `moodlens://callback`
   - `http://localhost:8000/callback` (for testing)

### 6. Run Database Migrations

```bash
alembic upgrade head
```

### 7. Start Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

---

## 📱 iOS Setup

### 1. Open Xcode Project

```bash
cd ../ios/MoodLens
open MoodLens.xcodeproj
```

### 2. Configure App

Edit `MoodLens/Config.swift`:

```swift
static let apiBaseURL = "http://localhost:8000"  // Or your server URL
static let spotifyClientId = "YOUR_SPOTIFY_CLIENT_ID"
static let spotifyRedirectURI = "moodlens://callback"
```

### 3. Add URL Scheme

In Xcode:
1. Select **MoodLens** target
2. Go to **Info** tab
3. Expand **URL Types**
4. Add URL Scheme: `moodlens`

### 4. Update Info.plist

Add this to `Info.plist`:

```xml
<key>LSApplicationQueriesSchemes</key>
<array>
    <string>spotify</string>
</array>
```

### 5. Build and Run

- Select a simulator or device
- Press **Cmd+R** to build and run

---

## 🎯 How It Works

### Authentication Flow

1. User taps "Connect Spotify" in iOS app
2. iOS initiates **PKCE** flow via `ASWebAuthenticationSession`
3. User authorizes on Spotify
4. iOS receives authorization code
5. iOS sends code + code_verifier to backend `/auth/spotify/exchange`
6. Backend exchanges for tokens, stores refresh token (encrypted)
7. Backend returns JWT to iOS
8. iOS stores JWT in Keychain

### Data Ingestion

1. Background job runs every **15 minutes** (APScheduler)
2. For each user:
   - Refresh access token if needed
   - Fetch `/me/player/recently-played` (limit=50)
   - Store new play events (dedupe by user_id, track_id, played_at)
   - Cache track/artist metadata
   - Fetch audio features for new tracks
   - Compute sessions (plays grouped by <30min gap)
   - Compute daily mood aggregates

### Mood Engine

**4 Mood Axes** (0-1 scale):

```
Positivity = valence
Arousal    = 0.7*energy + 0.3*(tempo/200 capped at 1)
Warmth     = 0.6*acousticness + 0.4*(1 - normalized_loudness)
Focus      = 0.7*instrumentalness + 0.3*(1 - speechiness)
```

**Aggregations**:
- **Session mood**: Weighted average (by track duration)
- **Daily mood**: Average + volatility (std dev) + drift (morning→night slope)
- **Metrics**: Repeat rate, exploration rate, comfort index

---

## 📊 API Endpoints

### Auth
- `POST /auth/spotify/exchange` - Exchange code for JWT
- `GET /me` - Get current user
- `POST /disconnect` - Disconnect Spotify
- `DELETE /me` - Delete all user data

### Analytics
- `GET /analytics/summary?range=7d|30d|90d` - Summary stats
- `GET /analytics/timeline?granularity=hour|day&range=...` - Mood timeline
- `GET /analytics/insights?range=...` - Mood anchors, comfort loops, discovery
- `GET /analytics/export` - Export data as JSON

---

## 🔐 Security

- **Token Encryption**: Refresh tokens encrypted with Fernet (symmetric)
- **JWT Sessions**: 30-day expiration, stored in iOS Keychain
- **No Client Secrets**: iOS never sees refresh tokens or client secret
- **HTTPS Only**: Production must use HTTPS

---

## 🧪 Testing

### Backend

```bash
# Health check
curl http://localhost:8000/health

# Test auth (replace with real token)
curl -H "Authorization: Bearer YOUR_JWT" http://localhost:8000/me
```

### iOS

1. Set breakpoint in `SpotifyAuth.swift` → `exchangeCode`
2. Connect Spotify
3. Verify JWT is saved to Keychain
4. Check API calls in Network debug console

---

## 📦 Production Deployment

### Backend

**Option 1: Heroku**
```bash
heroku create moodlens-api
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set ENCRYPTION_KEY=...
heroku config:set SPOTIFY_CLIENT_ID=...
git push heroku main
```

**Option 2: DigitalOcean / Railway / Fly.io**
- Deploy Docker container
- Set environment variables
- Run migrations: `alembic upgrade head`

**Important**: Update `SPOTIFY_REDIRECT_URI` in Spotify Dashboard to your production URL

### iOS

1. Update `Config.swift` with production API URL
2. Archive app in Xcode
3. Upload to App Store Connect
4. Submit for review

---

## 🛠 Troubleshooting

### Backend won't start
- Check PostgreSQL is running: `docker-compose ps`
- Verify `.env` has all required variables
- Check database connection: `psql -h localhost -U moodlens -d moodlens`

### iOS can't connect
- Ensure backend is running and accessible
- Check `Config.swift` has correct `apiBaseURL`
- Verify Spotify Client ID matches dashboard
- Check URL scheme is registered in Xcode

### No data appearing
- Check background job is running: `GET /health` should show `scheduler: running`
- Verify tokens are saved: Query `spotify_tokens` table
- Check logs for ingestion errors
- Wait 15 minutes for first ingestion

### Token refresh fails
- Spotify refresh tokens can expire if not used for 3 months
- User must re-authenticate

---

## 📝 Spotify API Limitations

- **No lifetime play counts**: Only data from connect date forward
- **Recently played limit**: 50 tracks per request (covers ~2-3 hours)
- **No skip/seek data**: Not reliably available from API
- **Rate limits**: 429 errors handled with backoff

---

## 🤝 Contributing

This is a personal MVP project, but suggestions are welcome!

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- **Spotify Web API** for audio features and listening data
- **FastAPI** for the elegant Python backend
- **SwiftUI** for iOS native UI
- **SQLAlchemy** for database ORM

---

## 📧 Contact

Questions? Open an issue or reach out!

Built with ❤️ for music lovers who want to understand their listening through an emotional lens.

---

**Note**: MoodLens is for entertainment and self-discovery only. It is not a medical or mental health tool.
We shall see

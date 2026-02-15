import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models
from .database import SessionLocal
from .spotify_client import SpotifyClient
from .mood_engine import MoodEngine
import logging

logger = logging.getLogger(__name__)


class IngestionJob:
    """Background job to ingest Spotify data for all users"""
    
    @staticmethod
    async def ingest_recently_played():
        """
        Main ingestion job:
        1. For each user with tokens
        2. Refresh access token if needed
        3. Fetch recently played (limit=50)
        4. Store new play events (dedupe by user_id, track_id, played_at)
        5. Cache track/artist metadata
        6. Fetch audio features for new tracks
        7. Compute sessions and daily aggregates
        """
        db = SessionLocal()
        try:
            # Get all users with valid tokens
            users = (
                db.query(models.User)
                .join(models.SpotifyToken)
                .all()
            )
            
            logger.info(f"Starting ingestion for {len(users)} users")
            
            for user in users:
                try:
                    await IngestionJob._ingest_user(db, user)
                except Exception as e:
                    logger.error(f"Failed to ingest for user {user.id}: {e}")
                    continue
            
            logger.info("Ingestion job completed")
        
        finally:
            db.close()
    
    @staticmethod
    async def _ingest_user(db: Session, user: models.User):
        """Ingest data for a single user"""
        spotify = SpotifyClient(db)
        
        # Get valid access token
        access_token = await spotify.get_valid_access_token(user)
        if not access_token:
            logger.warning(f"No valid access token for user {user.id}")
            return
        
        # Get recently played
        try:
            recent_data = await spotify.get_recently_played(access_token, limit=50)
        except Exception as e:
            logger.error(f"Failed to fetch recently played for user {user.id}: {e}")
            return
        
        items = recent_data.get("items", [])
        if not items:
            logger.info(f"No new plays for user {user.id}")
            return
        
        new_plays = 0
        new_tracks_ids = set()
        
        for item in items:
            track_data = item.get("track")
            played_at_str = item.get("played_at")
            context_uri = item.get("context", {}).get("uri") if item.get("context") else None
            
            if not track_data or not played_at_str:
                continue
            
            track_id = track_data["id"]
            played_at = datetime.fromisoformat(played_at_str.replace("Z", "+00:00"))
            
            # Check if this play event already exists
            existing = (
                db.query(models.PlayEvent)
                .filter(
                    and_(
                        models.PlayEvent.user_id == user.id,
                        models.PlayEvent.track_id == track_id,
                        models.PlayEvent.played_at == played_at
                    )
                )
                .first()
            )
            
            if existing:
                continue
            
            # Cache track metadata if not exists
            track = db.query(models.Track).filter(models.Track.track_id == track_id).first()
            if not track:
                track = IngestionJob._create_track_from_data(track_data)
                db.add(track)
                new_tracks_ids.add(track_id)
                
                # Cache artist
                if track_data.get("artists"):
                    artist_data = track_data["artists"][0]
                    artist = db.query(models.Artist).filter(
                        models.Artist.artist_id == artist_data["id"]
                    ).first()
                    if not artist:
                        artist = models.Artist(
                            artist_id=artist_data["id"],
                            name=artist_data["name"],
                            raw_json=artist_data
                        )
                        db.add(artist)
            
            # Create play event
            play_event = models.PlayEvent(
                user_id=user.id,
                track_id=track_id,
                played_at=played_at,
                context_uri=context_uri
            )
            db.add(play_event)
            new_plays += 1
        
        db.commit()
        
        # Fetch audio features for new tracks
        if new_tracks_ids:
            await IngestionJob._fetch_audio_features(db, spotify, access_token, list(new_tracks_ids))
        
        # Compute sessions and daily aggregates for the last 2 days
        await IngestionJob._compute_aggregates(db, user)
        
        logger.info(f"Ingested {new_plays} new plays for user {user.id}")
    
    @staticmethod
    def _create_track_from_data(track_data: dict) -> models.Track:
        """Create Track model from Spotify API data"""
        album = track_data.get("album", {})
        artists = track_data.get("artists", [])
        primary_artist = artists[0] if artists else {}
        
        return models.Track(
            track_id=track_data["id"],
            name=track_data["name"],
            duration_ms=track_data["duration_ms"],
            explicit=track_data.get("explicit", False),
            album_id=album.get("id"),
            album_name=album.get("name"),
            primary_artist_id=primary_artist.get("id"),
            primary_artist_name=primary_artist.get("name"),
            popularity=track_data.get("popularity"),
            raw_json=track_data
        )
    
    @staticmethod
    async def _fetch_audio_features(
        db: Session,
        spotify: SpotifyClient,
        access_token: str,
        track_ids: list
    ):
        """Fetch and store audio features for tracks"""
        try:
            features_list = await spotify.get_audio_features(access_token, track_ids)
            
            for features_data in features_list:
                if not features_data:
                    continue
                
                track_id = features_data["id"]
                
                # Check if already exists
                existing = db.query(models.AudioFeatures).filter(
                    models.AudioFeatures.track_id == track_id
                ).first()
                
                if not existing:
                    audio_features = models.AudioFeatures(
                        track_id=track_id,
                        danceability=features_data.get("danceability"),
                        energy=features_data.get("energy"),
                        valence=features_data.get("valence"),
                        tempo=features_data.get("tempo"),
                        loudness=features_data.get("loudness"),
                        speechiness=features_data.get("speechiness"),
                        acousticness=features_data.get("acousticness"),
                        instrumentalness=features_data.get("instrumentalness"),
                        liveness=features_data.get("liveness"),
                        key=features_data.get("key"),
                        mode=features_data.get("mode"),
                        time_signature=features_data.get("time_signature")
                    )
                    db.add(audio_features)
            
            db.commit()
        
        except Exception as e:
            logger.error(f"Failed to fetch audio features: {e}")
    
    @staticmethod
    async def _compute_aggregates(db: Session, user: models.User):
        """Compute sessions and daily mood for recent days"""
        mood_engine = MoodEngine(db)
        
        # Compute for last 2 days
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        for date in [yesterday, today]:
            # Compute sessions
            sessions = mood_engine.group_plays_into_sessions(
                user,
                date,
                date + timedelta(days=1)
            )
            
            # Delete old sessions for this day and add new ones
            db.query(models.Session).filter(
                and_(
                    models.Session.user_id == user.id,
                    models.Session.start_at >= date,
                    models.Session.start_at < date + timedelta(days=1)
                )
            ).delete()
            
            for session in sessions:
                db.add(session)
            
            # Compute daily mood
            daily_mood = mood_engine.compute_daily_mood(user, date)
            if daily_mood:
                # Upsert (delete old, insert new)
                db.query(models.DailyMood).filter(
                    and_(
                        models.DailyMood.user_id == user.id,
                        models.DailyMood.date == date
                    )
                ).delete()
                db.add(daily_mood)
        
        db.commit()

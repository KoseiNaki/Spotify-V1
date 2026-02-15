from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    spotify_user_id = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255))
    email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    tokens = relationship("SpotifyToken", back_populates="user", uselist=False)
    play_events = relationship("PlayEvent", back_populates="user")
    sessions = relationship("Session", back_populates="user")
    daily_moods = relationship("DailyMood", back_populates="user")


class SpotifyToken(Base):
    __tablename__ = "spotify_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    refresh_token_encrypted = Column(Text, nullable=False)
    access_token = Column(Text, nullable=False)
    access_expires_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="tokens")


class Track(Base):
    __tablename__ = "tracks"
    
    track_id = Column(String(255), primary_key=True)
    name = Column(String(500), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    explicit = Column(Boolean, default=False)
    album_id = Column(String(255))
    album_name = Column(String(500))
    primary_artist_id = Column(String(255), ForeignKey("artists.artist_id"))
    primary_artist_name = Column(String(500))
    popularity = Column(Integer)
    raw_json = Column(JSONB)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    audio_features = relationship("AudioFeatures", back_populates="track", uselist=False)
    play_events = relationship("PlayEvent", back_populates="track")


class Artist(Base):
    __tablename__ = "artists"
    
    artist_id = Column(String(255), primary_key=True)
    name = Column(String(500), nullable=False)
    genres = Column(JSONB)
    popularity = Column(Integer)
    followers = Column(Integer)
    raw_json = Column(JSONB)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AudioFeatures(Base):
    __tablename__ = "audio_features"
    
    track_id = Column(String(255), ForeignKey("tracks.track_id", ondelete="CASCADE"), primary_key=True)
    danceability = Column(Float)
    energy = Column(Float)
    valence = Column(Float)
    tempo = Column(Float)
    loudness = Column(Float)
    speechiness = Column(Float)
    acousticness = Column(Float)
    instrumentalness = Column(Float)
    liveness = Column(Float)
    key = Column(Integer)
    mode = Column(Integer)
    time_signature = Column(Integer)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    track = relationship("Track", back_populates="audio_features")


class PlayEvent(Base):
    __tablename__ = "play_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    track_id = Column(String(255), ForeignKey("tracks.track_id"), nullable=False)
    played_at = Column(DateTime, nullable=False, index=True)
    context_uri = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="play_events")
    track = relationship("Track", back_populates="play_events")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'track_id', 'played_at', name='uq_user_track_played_at'),
        Index('ix_play_events_user_played_at', 'user_id', 'played_at'),
    )


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    play_count = Column(Integer, nullable=False)
    avg_axes = Column(JSONB)  # {"positivity": 0.7, "arousal": 0.6, "warmth": 0.5, "focus": 0.4}
    volatility = Column(JSONB)  # std dev for each axis
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index('ix_sessions_user_start', 'user_id', 'start_at'),
    )


class DailyMood(Base):
    __tablename__ = "daily_mood"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)  # date only (time is 00:00:00)
    avg_axes = Column(JSONB)  # {"positivity": 0.7, "arousal": 0.6, "warmth": 0.5, "focus": 0.4}
    volatility = Column(JSONB)  # std dev for each axis
    drift = Column(JSONB)  # slope from morning to night for each axis
    minutes_listened = Column(Integer, nullable=False, default=0)
    sessions_count = Column(Integer, nullable=False, default=0)
    repeat_rate = Column(Float)  # % of plays that are repeats
    exploration_rate = Column(Float)  # % of new artists/tracks
    comfort_index = Column(Float)  # composite: repeats + low diversity
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="daily_moods")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_user_date'),
        Index('ix_daily_mood_user_date', 'user_id', 'date'),
    )

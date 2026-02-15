from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, List


# Auth schemas
class SpotifyExchangeRequest(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: str


class SpotifyExchangeResponse(BaseModel):
    access_token: str
    user: "UserProfile"


class UserProfile(BaseModel):
    id: int
    spotify_user_id: str
    display_name: Optional[str]
    email: Optional[str]
    connected: bool
    created_at: datetime


# Analytics schemas
class MoodAxes(BaseModel):
    positivity: float = Field(ge=0, le=1)
    arousal: float = Field(ge=0, le=1)
    warmth: float = Field(ge=0, le=1)
    focus: float = Field(ge=0, le=1)


class AnalyticsSummary(BaseModel):
    range_days: int
    minutes_listened: int
    sessions_count: int
    unique_tracks: int
    unique_artists: int
    repeat_rate: float
    exploration_rate: float
    comfort_index: float
    avg_mood: MoodAxes
    top_tracks: List["TrackInfo"]
    top_artists: List["ArtistInfo"]


class TimelinePoint(BaseModel):
    timestamp: datetime
    mood: MoodAxes
    volatility: Optional[MoodAxes]
    minutes: int
    play_count: int


class TimelineResponse(BaseModel):
    granularity: str
    range_days: int
    data: List[TimelinePoint]


class MoodAnchor(BaseModel):
    track_id: str
    track_name: str
    artist_name: str
    mood_axis: str
    axis_value: float
    play_count: int


class ComfortLoop(BaseModel):
    track_id: str
    track_name: str
    artist_name: str
    repeat_count: int
    time_span_hours: float


class DiscoveryBurst(BaseModel):
    date: datetime
    new_artists: int
    new_tracks: int


class InsightsResponse(BaseModel):
    range_days: int
    mood_anchors: List[MoodAnchor]
    comfort_loops: List[ComfortLoop]
    discovery_bursts: List[DiscoveryBurst]


class TrackInfo(BaseModel):
    track_id: str
    name: str
    artist_name: str
    album_name: Optional[str]
    play_count: int
    duration_ms: int


class ArtistInfo(BaseModel):
    artist_id: str
    name: str
    play_count: int
    genres: Optional[List[str]]


class ExportData(BaseModel):
    user: UserProfile
    play_events: List[Dict]
    daily_moods: List[Dict]
    sessions: List[Dict]
    export_date: datetime


# Request models
class DisconnectRequest(BaseModel):
    delete_data: bool = False


# Response wrappers
class MessageResponse(BaseModel):
    message: str

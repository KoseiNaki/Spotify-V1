from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from datetime import datetime, timedelta
from typing import Optional
from .. import models, schemas, auth
from ..database import get_db
from ..mood_engine import MoodEngine
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def parse_range(range_str: str) -> int:
    """Parse range string like '7d', '30d', '90d' to number of days"""
    if range_str.endswith('d'):
        return int(range_str[:-1])
    return 7  # default


@router.get("/summary", response_model=schemas.AnalyticsSummary)
def get_analytics_summary(
    range: str = Query("7d", regex="^[0-9]+d$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(lambda creds, db=Depends(get_db): auth.get_current_user(creds, db))
):
    """
    Get analytics summary for a time range
    """
    days = parse_range(range)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get play events in range
    plays = (
        db.query(models.PlayEvent)
        .filter(
            and_(
                models.PlayEvent.user_id == current_user.id,
                models.PlayEvent.played_at >= start_date
            )
        )
        .all()
    )
    
    if not plays:
        # Return empty summary
        return schemas.AnalyticsSummary(
            range_days=days,
            minutes_listened=0,
            sessions_count=0,
            unique_tracks=0,
            unique_artists=0,
            repeat_rate=0,
            exploration_rate=0,
            comfort_index=0,
            avg_mood=schemas.MoodAxes(positivity=0, arousal=0, warmth=0, focus=0),
            top_tracks=[],
            top_artists=[]
        )
    
    # Calculate metrics
    minutes_listened = sum(p.track.duration_ms for p in plays if p.track) / 1000 / 60
    unique_tracks = len(set(p.track_id for p in plays))
    unique_artists = len(set(p.track.primary_artist_id for p in plays if p.track and p.track.primary_artist_id))
    
    # Count sessions
    sessions_count = (
        db.query(models.Session)
        .filter(
            and_(
                models.Session.user_id == current_user.id,
                models.Session.start_at >= start_date
            )
        )
        .count()
    )
    
    # Repeat rate
    track_counts = {}
    for play in plays:
        track_counts[play.track_id] = track_counts.get(play.track_id, 0) + 1
    repeats = sum(1 for count in track_counts.values() if count > 1)
    repeat_rate = repeats / len(plays)
    
    # Exploration rate
    exploration_rate = unique_tracks / len(plays)
    
    # Comfort index
    comfort_index = (repeat_rate * 0.7) + ((1 - exploration_rate) * 0.3)
    
    # Average mood
    mood_engine = MoodEngine(db)
    avg_axes, _ = mood_engine.compute_session_mood(plays)
    
    # Top tracks
    top_tracks_data = (
        db.query(
            models.PlayEvent.track_id,
            func.count(models.PlayEvent.id).label('play_count')
        )
        .filter(
            and_(
                models.PlayEvent.user_id == current_user.id,
                models.PlayEvent.played_at >= start_date
            )
        )
        .group_by(models.PlayEvent.track_id)
        .order_by(desc('play_count'))
        .limit(10)
        .all()
    )
    
    top_tracks = []
    for track_id, play_count in top_tracks_data:
        track = db.query(models.Track).filter(models.Track.track_id == track_id).first()
        if track:
            top_tracks.append(schemas.TrackInfo(
                track_id=track.track_id,
                name=track.name,
                artist_name=track.primary_artist_name or "Unknown",
                album_name=track.album_name,
                play_count=play_count,
                duration_ms=track.duration_ms
            ))
    
    # Top artists
    top_artists_data = (
        db.query(
            models.Track.primary_artist_id,
            models.Track.primary_artist_name,
            func.count(models.PlayEvent.id).label('play_count')
        )
        .join(models.Track, models.PlayEvent.track_id == models.Track.track_id)
        .filter(
            and_(
                models.PlayEvent.user_id == current_user.id,
                models.PlayEvent.played_at >= start_date,
                models.Track.primary_artist_id.isnot(None)
            )
        )
        .group_by(models.Track.primary_artist_id, models.Track.primary_artist_name)
        .order_by(desc('play_count'))
        .limit(10)
        .all()
    )
    
    top_artists = []
    for artist_id, artist_name, play_count in top_artists_data:
        artist = db.query(models.Artist).filter(models.Artist.artist_id == artist_id).first()
        top_artists.append(schemas.ArtistInfo(
            artist_id=artist_id,
            name=artist_name,
            play_count=play_count,
            genres=artist.genres if artist else None
        ))
    
    return schemas.AnalyticsSummary(
        range_days=days,
        minutes_listened=int(minutes_listened),
        sessions_count=sessions_count,
        unique_tracks=unique_tracks,
        unique_artists=unique_artists,
        repeat_rate=round(repeat_rate, 3),
        exploration_rate=round(exploration_rate, 3),
        comfort_index=round(comfort_index, 3),
        avg_mood=schemas.MoodAxes(**avg_axes) if avg_axes else schemas.MoodAxes(positivity=0, arousal=0, warmth=0, focus=0),
        top_tracks=top_tracks,
        top_artists=top_artists
    )


@router.get("/timeline", response_model=schemas.TimelineResponse)
def get_analytics_timeline(
    granularity: str = Query("day", regex="^(hour|day)$"),
    range: str = Query("7d", regex="^[0-9]+d$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(lambda creds, db=Depends(get_db): auth.get_current_user(creds, db))
):
    """
    Get mood timeline data
    """
    days = parse_range(range)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    if granularity == "day":
        # Get daily mood records
        daily_moods = (
            db.query(models.DailyMood)
            .filter(
                and_(
                    models.DailyMood.user_id == current_user.id,
                    models.DailyMood.date >= start_date
                )
            )
            .order_by(models.DailyMood.date)
            .all()
        )
        
        timeline_data = []
        for dm in daily_moods:
            if dm.avg_axes:
                timeline_data.append(schemas.TimelinePoint(
                    timestamp=dm.date,
                    mood=schemas.MoodAxes(**dm.avg_axes),
                    volatility=schemas.MoodAxes(**dm.volatility) if dm.volatility else None,
                    minutes=dm.minutes_listened,
                    play_count=0  # Can add if needed
                ))
        
        return schemas.TimelineResponse(
            granularity=granularity,
            range_days=days,
            data=timeline_data
        )
    
    else:  # hour
        # Group plays by hour
        plays = (
            db.query(models.PlayEvent)
            .filter(
                and_(
                    models.PlayEvent.user_id == current_user.id,
                    models.PlayEvent.played_at >= start_date
                )
            )
            .order_by(models.PlayEvent.played_at)
            .all()
        )
        
        # Group by hour
        hourly_plays = {}
        for play in plays:
            hour_key = play.played_at.replace(minute=0, second=0, microsecond=0)
            if hour_key not in hourly_plays:
                hourly_plays[hour_key] = []
            hourly_plays[hour_key].append(play)
        
        mood_engine = MoodEngine(db)
        timeline_data = []
        
        for hour_key in sorted(hourly_plays.keys()):
            plays_in_hour = hourly_plays[hour_key]
            avg_axes, volatility = mood_engine.compute_session_mood(plays_in_hour)
            minutes = sum(p.track.duration_ms for p in plays_in_hour if p.track) / 1000 / 60
            
            if avg_axes:
                timeline_data.append(schemas.TimelinePoint(
                    timestamp=hour_key,
                    mood=schemas.MoodAxes(**avg_axes),
                    volatility=schemas.MoodAxes(**volatility) if volatility else None,
                    minutes=int(minutes),
                    play_count=len(plays_in_hour)
                ))
        
        return schemas.TimelineResponse(
            granularity=granularity,
            range_days=days,
            data=timeline_data
        )


@router.get("/insights", response_model=schemas.InsightsResponse)
def get_analytics_insights(
    range: str = Query("30d", regex="^[0-9]+d$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(lambda creds, db=Depends(get_db): auth.get_current_user(creds, db))
):
    """
    Get insights: mood anchors, comfort loops, discovery bursts
    """
    days = parse_range(range)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get plays
    plays = (
        db.query(models.PlayEvent)
        .filter(
            and_(
                models.PlayEvent.user_id == current_user.id,
                models.PlayEvent.played_at >= start_date
            )
        )
        .all()
    )
    
    # Mood anchors: tracks with extreme mood values
    mood_engine = MoodEngine(db)
    anchors = []
    
    track_moods = {}
    for play in plays:
        if play.track and play.track.audio_features:
            track_id = play.track_id
            if track_id not in track_moods:
                mood = mood_engine.compute_mood_axes(play.track.audio_features)
                track_moods[track_id] = {
                    'mood': mood,
                    'track': play.track,
                    'count': 0
                }
            track_moods[track_id]['count'] += 1
    
    # Find top anchors for each axis
    for axis in ['positivity', 'arousal', 'warmth', 'focus']:
        sorted_tracks = sorted(
            track_moods.items(),
            key=lambda x: (x[1]['mood'][axis], x[1]['count']),
            reverse=True
        )[:3]
        
        for track_id, data in sorted_tracks:
            anchors.append(schemas.MoodAnchor(
                track_id=track_id,
                track_name=data['track'].name,
                artist_name=data['track'].primary_artist_name or "Unknown",
                mood_axis=axis,
                axis_value=data['mood'][axis],
                play_count=data['count']
            ))
    
    # Comfort loops: tracks repeated in short time spans
    comfort_loops = []
    track_play_times = {}
    
    for play in plays:
        if play.track_id not in track_play_times:
            track_play_times[play.track_id] = []
        track_play_times[play.track_id].append(play.played_at)
    
    for track_id, play_times in track_play_times.items():
        if len(play_times) >= 3:
            # Check if plays are within 24 hours
            play_times.sort()
            time_span = (play_times[-1] - play_times[0]).total_seconds() / 3600
            if time_span <= 24:
                track = db.query(models.Track).filter(models.Track.track_id == track_id).first()
                if track:
                    comfort_loops.append(schemas.ComfortLoop(
                        track_id=track_id,
                        track_name=track.name,
                        artist_name=track.primary_artist_name or "Unknown",
                        repeat_count=len(play_times),
                        time_span_hours=round(time_span, 1)
                    ))
    
    comfort_loops.sort(key=lambda x: x.repeat_count, reverse=True)
    comfort_loops = comfort_loops[:10]
    
    # Discovery bursts: days with many new artists/tracks
    daily_discoveries = {}
    seen_tracks = set()
    seen_artists = set()
    
    for play in sorted(plays, key=lambda p: p.played_at):
        date = play.played_at.date()
        if date not in daily_discoveries:
            daily_discoveries[date] = {'new_tracks': 0, 'new_artists': 0}
        
        if play.track_id not in seen_tracks:
            daily_discoveries[date]['new_tracks'] += 1
            seen_tracks.add(play.track_id)
        
        if play.track and play.track.primary_artist_id:
            if play.track.primary_artist_id not in seen_artists:
                daily_discoveries[date]['new_artists'] += 1
                seen_artists.add(play.track.primary_artist_id)
    
    discovery_bursts = [
        schemas.DiscoveryBurst(
            date=datetime.combine(date, datetime.min.time()),
            new_artists=data['new_artists'],
            new_tracks=data['new_tracks']
        )
        for date, data in sorted(
            daily_discoveries.items(),
            key=lambda x: x[1]['new_tracks'] + x[1]['new_artists'],
            reverse=True
        )[:10]
    ]
    
    return schemas.InsightsResponse(
        range_days=days,
        mood_anchors=anchors,
        comfort_loops=comfort_loops,
        discovery_bursts=discovery_bursts
    )


@router.get("/export")
def export_user_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(lambda creds, db=Depends(get_db): auth.get_current_user(creds, db))
):
    """
    Export all user data as JSON
    """
    # Get all play events
    plays = db.query(models.PlayEvent).filter(
        models.PlayEvent.user_id == current_user.id
    ).all()
    
    play_events = [
        {
            'track_id': p.track_id,
            'track_name': p.track.name if p.track else None,
            'artist_name': p.track.primary_artist_name if p.track else None,
            'played_at': p.played_at.isoformat(),
            'context_uri': p.context_uri
        }
        for p in plays
    ]
    
    # Get daily moods
    daily_moods = db.query(models.DailyMood).filter(
        models.DailyMood.user_id == current_user.id
    ).all()
    
    daily_mood_data = [
        {
            'date': dm.date.isoformat(),
            'avg_mood': dm.avg_axes,
            'volatility': dm.volatility,
            'drift': dm.drift,
            'minutes_listened': dm.minutes_listened,
            'sessions_count': dm.sessions_count,
            'repeat_rate': dm.repeat_rate,
            'exploration_rate': dm.exploration_rate,
            'comfort_index': dm.comfort_index
        }
        for dm in daily_moods
    ]
    
    # Get sessions
    sessions = db.query(models.Session).filter(
        models.Session.user_id == current_user.id
    ).all()
    
    session_data = [
        {
            'start_at': s.start_at.isoformat(),
            'end_at': s.end_at.isoformat(),
            'play_count': s.play_count,
            'avg_mood': s.avg_axes,
            'volatility': s.volatility
        }
        for s in sessions
    ]
    
    export = {
        'user': {
            'spotify_user_id': current_user.spotify_user_id,
            'display_name': current_user.display_name,
            'email': current_user.email,
            'created_at': current_user.created_at.isoformat()
        },
        'play_events': play_events,
        'daily_moods': daily_mood_data,
        'sessions': session_data,
        'export_date': datetime.utcnow().isoformat()
    }
    
    return JSONResponse(content=export)

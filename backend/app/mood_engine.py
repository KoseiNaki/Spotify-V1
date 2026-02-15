import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from . import models
import logging

logger = logging.getLogger(__name__)


class MoodEngine:
    """Compute mood axes and analytics from listening data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def compute_mood_axes(audio_features: models.AudioFeatures) -> Dict[str, float]:
        """
        Compute 4 mood axes from Spotify audio features:
        1. Positivity = valence
        2. Arousal = 0.7*energy + 0.3*(tempo/200 capped at 1)
        3. Warmth = 0.6*acousticness + 0.4*(1 - normalized_loudness)
        4. Focus = 0.7*instrumentalness + 0.3*(1 - speechiness)
        
        All axes normalized to [0, 1]
        """
        # Normalize loudness (typical range -60 to 0 dB)
        normalized_loudness = (audio_features.loudness + 60) / 60
        normalized_loudness = max(0, min(1, normalized_loudness))
        
        # Normalize tempo (typical range 0-200 BPM)
        normalized_tempo = min(audio_features.tempo / 200, 1.0)
        
        return {
            "positivity": round(audio_features.valence, 3),
            "arousal": round(0.7 * audio_features.energy + 0.3 * normalized_tempo, 3),
            "warmth": round(0.6 * audio_features.acousticness + 0.4 * (1 - normalized_loudness), 3),
            "focus": round(0.7 * audio_features.instrumentalness + 0.3 * (1 - audio_features.speechiness), 3)
        }
    
    def compute_session_mood(
        self,
        play_events: List[models.PlayEvent]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Compute average mood and volatility for a session
        Returns: (avg_axes, volatility)
        """
        if not play_events:
            return {}, {}
        
        axes_data = {"positivity": [], "arousal": [], "warmth": [], "focus": []}
        weights = []
        
        for event in play_events:
            if event.track and event.track.audio_features:
                mood = self.compute_mood_axes(event.track.audio_features)
                weight = event.track.duration_ms / 1000  # weight by seconds
                
                for axis in axes_data:
                    axes_data[axis].append(mood[axis])
                weights.append(weight)
        
        if not weights:
            return {}, {}
        
        # Compute weighted average
        avg_axes = {}
        volatility = {}
        for axis, values in axes_data.items():
            if values:
                avg_axes[axis] = round(np.average(values, weights=weights), 3)
                volatility[axis] = round(np.std(values), 3)
        
        return avg_axes, volatility
    
    def group_plays_into_sessions(
        self,
        user: models.User,
        start_date: datetime,
        end_date: datetime,
        gap_minutes: int = 30
    ) -> List[models.Session]:
        """
        Group play events into sessions (gap < gap_minutes)
        Returns list of Session objects (not yet committed)
        """
        # Get plays ordered by time
        plays = (
            self.db.query(models.PlayEvent)
            .filter(
                and_(
                    models.PlayEvent.user_id == user.id,
                    models.PlayEvent.played_at >= start_date,
                    models.PlayEvent.played_at <= end_date
                )
            )
            .order_by(models.PlayEvent.played_at)
            .all()
        )
        
        if not plays:
            return []
        
        sessions = []
        current_session_plays = [plays[0]]
        
        for i in range(1, len(plays)):
            time_gap = (plays[i].played_at - plays[i-1].played_at).total_seconds() / 60
            
            if time_gap <= gap_minutes:
                current_session_plays.append(plays[i])
            else:
                # End current session, start new one
                sessions.append(self._create_session(user, current_session_plays))
                current_session_plays = [plays[i]]
        
        # Don't forget the last session
        if current_session_plays:
            sessions.append(self._create_session(user, current_session_plays))
        
        return sessions
    
    def _create_session(
        self,
        user: models.User,
        plays: List[models.PlayEvent]
    ) -> models.Session:
        """Create a Session object from play events"""
        avg_axes, volatility = self.compute_session_mood(plays)
        
        return models.Session(
            user_id=user.id,
            start_at=plays[0].played_at,
            end_at=plays[-1].played_at,
            play_count=len(plays),
            avg_axes=avg_axes,
            volatility=volatility
        )
    
    def compute_daily_mood(
        self,
        user: models.User,
        date: datetime
    ) -> Optional[models.DailyMood]:
        """
        Compute daily mood aggregate for a specific date
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Get all plays for the day
        plays = (
            self.db.query(models.PlayEvent)
            .filter(
                and_(
                    models.PlayEvent.user_id == user.id,
                    models.PlayEvent.played_at >= start_of_day,
                    models.PlayEvent.played_at < end_of_day
                )
            )
            .all()
        )
        
        if not plays:
            return None
        
        # Compute mood
        avg_axes, volatility = self.compute_session_mood(plays)
        
        # Compute drift (morning to night slope)
        drift = self._compute_drift(plays)
        
        # Compute minutes listened
        unique_tracks = {p.track_id for p in plays}
        minutes_listened = sum(p.track.duration_ms for p in plays if p.track) / 1000 / 60
        
        # Get sessions for this day
        sessions = (
            self.db.query(models.Session)
            .filter(
                and_(
                    models.Session.user_id == user.id,
                    models.Session.start_at >= start_of_day,
                    models.Session.start_at < end_of_day
                )
            )
            .count()
        )
        
        # Compute repeat rate
        track_play_counts = {}
        for play in plays:
            track_play_counts[play.track_id] = track_play_counts.get(play.track_id, 0) + 1
        
        repeats = sum(1 for count in track_play_counts.values() if count > 1)
        repeat_rate = repeats / len(plays) if plays else 0
        
        # Compute exploration rate (simplified)
        exploration_rate = len(unique_tracks) / len(plays) if plays else 0
        
        # Comfort index (high repeats + low diversity)
        comfort_index = (repeat_rate * 0.7) + ((1 - exploration_rate) * 0.3)
        
        return models.DailyMood(
            user_id=user.id,
            date=start_of_day,
            avg_axes=avg_axes,
            volatility=volatility,
            drift=drift,
            minutes_listened=int(minutes_listened),
            sessions_count=sessions,
            repeat_rate=round(repeat_rate, 3),
            exploration_rate=round(exploration_rate, 3),
            comfort_index=round(comfort_index, 3)
        )
    
    def _compute_drift(self, plays: List[models.PlayEvent]) -> Dict[str, float]:
        """
        Compute mood drift from morning to night (simple linear regression)
        Returns slope for each axis
        """
        if len(plays) < 2:
            return {"positivity": 0, "arousal": 0, "warmth": 0, "focus": 0}
        
        # Convert times to hours since midnight
        times = []
        moods = []
        
        for play in plays:
            if play.track and play.track.audio_features:
                hour = play.played_at.hour + play.played_at.minute / 60
                times.append(hour)
                moods.append(self.compute_mood_axes(play.track.audio_features))
        
        if len(times) < 2:
            return {"positivity": 0, "arousal": 0, "warmth": 0, "focus": 0}
        
        drift = {}
        for axis in ["positivity", "arousal", "warmth", "focus"]:
            axis_values = [m[axis] for m in moods]
            # Simple linear regression slope
            slope = np.polyfit(times, axis_values, 1)[0]
            drift[axis] = round(float(slope), 4)
        
        return drift

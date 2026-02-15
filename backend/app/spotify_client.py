import httpx
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from .config import settings
from . import models, crypto
import logging

logger = logging.getLogger(__name__)

SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


class SpotifyClient:
    """Client for interacting with Spotify API"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def exchange_code_for_tokens(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str
    ) -> Dict:
        """Exchange authorization code for access and refresh tokens"""
        async with httpx.AsyncClient() as client:
            auth_header = base64.b64encode(
                f"{settings.spotify_client_id}:{settings.spotify_client_secret}".encode()
            ).decode()
            
            response = await client.post(
                SPOTIFY_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "code_verifier": code_verifier,
                    "client_id": settings.spotify_client_id
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh an access token using refresh token"""
        async with httpx.AsyncClient() as client:
            auth_header = base64.b64encode(
                f"{settings.spotify_client_id}:{settings.spotify_client_secret}".encode()
            ).decode()
            
            response = await client.post(
                SPOTIFY_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_profile(self, access_token: str) -> Dict:
        """Get Spotify user profile"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SPOTIFY_API_BASE}/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_recently_played(
        self,
        access_token: str,
        limit: int = 50,
        after: Optional[int] = None
    ) -> Dict:
        """Get recently played tracks"""
        params = {"limit": limit}
        if after:
            params["after"] = after
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SPOTIFY_API_BASE}/me/player/recently-played",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_audio_features(self, access_token: str, track_ids: List[str]) -> List[Dict]:
        """Get audio features for multiple tracks (max 100)"""
        if not track_ids:
            return []
        
        # Spotify allows max 100 ids
        track_ids = track_ids[:100]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SPOTIFY_API_BASE}/audio-features",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"ids": ",".join(track_ids)}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("audio_features", [])
    
    async def get_valid_access_token(self, user: models.User) -> Optional[str]:
        """Get a valid access token for user, refreshing if needed"""
        token_record = user.tokens
        if not token_record:
            return None
        
        # Check if token is expired
        now = datetime.utcnow()
        if now >= token_record.access_expires_at - timedelta(minutes=5):
            # Token expired or expiring soon, refresh it
            try:
                decrypted_refresh = crypto.decrypt_token(token_record.refresh_token_encrypted)
                token_data = await self.refresh_access_token(decrypted_refresh)
                
                # Update token in database
                token_record.access_token = token_data["access_token"]
                token_record.access_expires_at = now + timedelta(seconds=token_data["expires_in"])
                token_record.updated_at = now
                
                # Refresh token might be rotated
                if "refresh_token" in token_data:
                    token_record.refresh_token_encrypted = crypto.encrypt_token(token_data["refresh_token"])
                
                self.db.commit()
                logger.info(f"Refreshed access token for user {user.id}")
                
                return token_data["access_token"]
            except Exception as e:
                logger.error(f"Failed to refresh token for user {user.id}: {e}")
                return None
        
        return token_record.access_token
    
    def save_tokens(
        self,
        user: models.User,
        access_token: str,
        refresh_token: str,
        expires_in: int
    ):
        """Save or update Spotify tokens for user"""
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=expires_in)
        
        token_record = user.tokens
        if token_record:
            token_record.access_token = access_token
            token_record.refresh_token_encrypted = crypto.encrypt_token(refresh_token)
            token_record.access_expires_at = expires_at
            token_record.updated_at = now
        else:
            token_record = models.SpotifyToken(
                user_id=user.id,
                access_token=access_token,
                refresh_token_encrypted=crypto.encrypt_token(refresh_token),
                access_expires_at=expires_at,
                updated_at=now
            )
            self.db.add(token_record)
        
        self.db.commit()

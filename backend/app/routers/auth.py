from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from ..spotify_client import SpotifyClient
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/spotify/exchange", response_model=schemas.SpotifyExchangeResponse)
async def exchange_spotify_code(
    request: schemas.SpotifyExchangeRequest,
    db: Session = Depends(get_db)
):
    """
    Exchange Spotify authorization code for access tokens
    Creates or updates user account
    Returns JWT session token
    """
    spotify = SpotifyClient(db)
    
    try:
        # Exchange code for tokens
        token_data = await spotify.exchange_code_for_tokens(
            request.code,
            request.code_verifier,
            request.redirect_uri
        )
        
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data["expires_in"]
        
        # Get user profile from Spotify
        profile = await spotify.get_user_profile(access_token)
        
        spotify_user_id = profile["id"]
        display_name = profile.get("display_name")
        email = profile.get("email")
        
        # Find or create user
        user = db.query(models.User).filter(
            models.User.spotify_user_id == spotify_user_id
        ).first()
        
        if not user:
            user = models.User(
                spotify_user_id=spotify_user_id,
                display_name=display_name,
                email=email
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {user.id}")
        else:
            # Update profile if changed
            user.display_name = display_name
            user.email = email
            db.commit()
        
        # Save tokens
        spotify.save_tokens(user, access_token, refresh_token, expires_in)
        
        # Create JWT session token
        jwt_token = auth.create_jwt_token(user.id)
        
        return schemas.SpotifyExchangeResponse(
            access_token=jwt_token,
            user=schemas.UserProfile(
                id=user.id,
                spotify_user_id=user.spotify_user_id,
                display_name=user.display_name,
                email=user.email,
                connected=True,
                created_at=user.created_at
            )
        )
    
    except Exception as e:
        logger.error(f"Failed to exchange Spotify code: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to connect Spotify: {str(e)}")

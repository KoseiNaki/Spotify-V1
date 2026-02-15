from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["user"])


@router.get("/me", response_model=schemas.UserProfile)
def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(lambda db=Depends(get_db): lambda creds: auth.get_current_user(creds, db))
):
    """Get current user profile and connection status"""
    # Fix the dependency issue by creating a proper wrapper
    pass


def get_user_with_db(credentials, db: Session):
    """Helper to properly inject db into auth dependency"""
    return auth.get_current_user(credentials, db)


@router.get("/me", response_model=schemas.UserProfile)
def get_me(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(lambda creds, db=Depends(get_db): auth.get_current_user(creds, db))
):
    """Get current user profile"""
    connected = current_user.tokens is not None
    
    return schemas.UserProfile(
        id=current_user.id,
        spotify_user_id=current_user.spotify_user_id,
        display_name=current_user.display_name,
        email=current_user.email,
        connected=connected,
        created_at=current_user.created_at
    )


@router.post("/disconnect", response_model=schemas.MessageResponse)
def disconnect_spotify(
    request: schemas.DisconnectRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(lambda creds, db=Depends(get_db): auth.get_current_user(creds, db))
):
    """
    Disconnect Spotify account
    Optionally delete all user data
    """
    if request.delete_data:
        # Delete all user data
        db.query(models.PlayEvent).filter(models.PlayEvent.user_id == current_user.id).delete()
        db.query(models.Session).filter(models.Session.user_id == current_user.id).delete()
        db.query(models.DailyMood).filter(models.DailyMood.user_id == current_user.id).delete()
        db.query(models.SpotifyToken).filter(models.SpotifyToken.user_id == current_user.id).delete()
        db.query(models.User).filter(models.User.id == current_user.id).delete()
        db.commit()
        
        return schemas.MessageResponse(message="Account disconnected and all data deleted")
    else:
        # Just delete tokens
        db.query(models.SpotifyToken).filter(models.SpotifyToken.user_id == current_user.id).delete()
        db.commit()
        
        return schemas.MessageResponse(message="Spotify disconnected. Data preserved.")


@router.delete("/me", response_model=schemas.MessageResponse)
def delete_user_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(lambda creds, db=Depends(get_db): auth.get_current_user(creds, db))
):
    """Delete all user data"""
    db.query(models.PlayEvent).filter(models.PlayEvent.user_id == current_user.id).delete()
    db.query(models.Session).filter(models.Session.user_id == current_user.id).delete()
    db.query(models.DailyMood).filter(models.DailyMood.user_id == current_user.id).delete()
    db.query(models.SpotifyToken).filter(models.SpotifyToken.user_id == current_user.id).delete()
    db.query(models.User).filter(models.User.id == current_user.id).delete()
    db.commit()
    
    return schemas.MessageResponse(message="All user data deleted")

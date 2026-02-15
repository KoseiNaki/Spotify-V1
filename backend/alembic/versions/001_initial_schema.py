"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-02-15 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('spotify_user_id', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_spotify_user_id'), 'users', ['spotify_user_id'], unique=True)
    
    # Create spotify_tokens table
    op.create_table(
        'spotify_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('access_expires_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_spotify_tokens_id'), 'spotify_tokens', ['id'], unique=False)
    
    # Create artists table
    op.create_table(
        'artists',
        sa.Column('artist_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('genres', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('popularity', sa.Integer(), nullable=True),
        sa.Column('followers', sa.Integer(), nullable=True),
        sa.Column('raw_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('artist_id')
    )
    
    # Create tracks table
    op.create_table(
        'tracks',
        sa.Column('track_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('explicit', sa.Boolean(), nullable=True),
        sa.Column('album_id', sa.String(length=255), nullable=True),
        sa.Column('album_name', sa.String(length=500), nullable=True),
        sa.Column('primary_artist_id', sa.String(length=255), nullable=True),
        sa.Column('primary_artist_name', sa.String(length=500), nullable=True),
        sa.Column('popularity', sa.Integer(), nullable=True),
        sa.Column('raw_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['primary_artist_id'], ['artists.artist_id'], ),
        sa.PrimaryKeyConstraint('track_id')
    )
    
    # Create audio_features table
    op.create_table(
        'audio_features',
        sa.Column('track_id', sa.String(length=255), nullable=False),
        sa.Column('danceability', sa.Float(), nullable=True),
        sa.Column('energy', sa.Float(), nullable=True),
        sa.Column('valence', sa.Float(), nullable=True),
        sa.Column('tempo', sa.Float(), nullable=True),
        sa.Column('loudness', sa.Float(), nullable=True),
        sa.Column('speechiness', sa.Float(), nullable=True),
        sa.Column('acousticness', sa.Float(), nullable=True),
        sa.Column('instrumentalness', sa.Float(), nullable=True),
        sa.Column('liveness', sa.Float(), nullable=True),
        sa.Column('key', sa.Integer(), nullable=True),
        sa.Column('mode', sa.Integer(), nullable=True),
        sa.Column('time_signature', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['track_id'], ['tracks.track_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('track_id')
    )
    
    # Create play_events table
    op.create_table(
        'play_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('track_id', sa.String(length=255), nullable=False),
        sa.Column('played_at', sa.DateTime(), nullable=False),
        sa.Column('context_uri', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['track_id'], ['tracks.track_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'track_id', 'played_at', name='uq_user_track_played_at')
    )
    op.create_index(op.f('ix_play_events_id'), 'play_events', ['id'], unique=False)
    op.create_index(op.f('ix_play_events_played_at'), 'play_events', ['played_at'], unique=False)
    op.create_index(op.f('ix_play_events_user_id'), 'play_events', ['user_id'], unique=False)
    op.create_index('ix_play_events_user_played_at', 'play_events', ['user_id', 'played_at'], unique=False)
    
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('start_at', sa.DateTime(), nullable=False),
        sa.Column('end_at', sa.DateTime(), nullable=False),
        sa.Column('play_count', sa.Integer(), nullable=False),
        sa.Column('avg_axes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('volatility', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'], unique=False)
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    op.create_index('ix_sessions_user_start', 'sessions', ['user_id', 'start_at'], unique=False)
    
    # Create daily_mood table
    op.create_table(
        'daily_mood',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('avg_axes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('volatility', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('drift', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('minutes_listened', sa.Integer(), nullable=False),
        sa.Column('sessions_count', sa.Integer(), nullable=False),
        sa.Column('repeat_rate', sa.Float(), nullable=True),
        sa.Column('exploration_rate', sa.Float(), nullable=True),
        sa.Column('comfort_index', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uq_user_date')
    )
    op.create_index(op.f('ix_daily_mood_id'), 'daily_mood', ['id'], unique=False)
    op.create_index('ix_daily_mood_user_date', 'daily_mood', ['user_id', 'date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_daily_mood_user_date', table_name='daily_mood')
    op.drop_index(op.f('ix_daily_mood_id'), table_name='daily_mood')
    op.drop_table('daily_mood')
    
    op.drop_index('ix_sessions_user_start', table_name='sessions')
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_id'), table_name='sessions')
    op.drop_table('sessions')
    
    op.drop_index('ix_play_events_user_played_at', table_name='play_events')
    op.drop_index(op.f('ix_play_events_user_id'), table_name='play_events')
    op.drop_index(op.f('ix_play_events_played_at'), table_name='play_events')
    op.drop_index(op.f('ix_play_events_id'), table_name='play_events')
    op.drop_table('play_events')
    
    op.drop_table('audio_features')
    op.drop_table('tracks')
    op.drop_table('artists')
    
    op.drop_index(op.f('ix_spotify_tokens_id'), table_name='spotify_tokens')
    op.drop_table('spotify_tokens')
    
    op.drop_index(op.f('ix_users_spotify_user_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

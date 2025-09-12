"""
Video model definition
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Video(Base):
    """Video model"""
    
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    title = Column(String(500), nullable=False, index=True)
    artist = Column(String(255), nullable=False, index=True)
    featuring = Column(String(500))
    
    # File info
    file_path = Column(String(1000))
    file_size = Column(Integer)  # in bytes
    duration = Column(Integer)  # in seconds
    format = Column(String(50))
    resolution = Column(String(20))
    
    # Metadata
    year = Column(Integer, index=True)
    genre = Column(String(100))
    director = Column(String(255))
    producer = Column(String(255))
    label = Column(String(255))
    
    # External IDs
    imvdb_id = Column(String(100), unique=True, index=True)
    youtube_id = Column(String(100), index=True)
    source_url = Column(String(1000))
    
    # Thumbnails
    thumbnail_url = Column(String(1000))
    thumbnail_path = Column(String(1000))
    
    # Source verification
    is_official = Column(Integer, default=0)  # 0: unknown, 1: unofficial, 2: official
    source_verified_at = Column(DateTime(timezone=True))
    source_confidence = Column(Float, default=0.0)
    source_data = Column(JSON)  # Store additional source metadata
    
    # Additional metadata
    description = Column(Text)
    tags = Column(JSON)  # Store as JSON array
    custom_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_played_at = Column(DateTime(timezone=True))
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="videos")
    
    # Queue items relationship
    queue_items = relationship("QueueItem", back_populates="video", cascade="all, delete-orphan")
"""
Queue and QueueItem models definition
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class QueueStatus(str, enum.Enum):
    """Queue item status enum"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueItem(Base):
    """Queue item model"""
    
    __tablename__ = "queue_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Queue info
    url = Column(String(1000), nullable=False)
    title = Column(String(500))
    artist = Column(String(255))
    status = Column(Enum(QueueStatus), default=QueueStatus.PENDING, index=True)
    priority = Column(Integer, default=0, index=True)
    
    # Progress tracking
    progress = Column(Integer, default=0)  # 0-100
    file_size = Column(Integer)  # in bytes
    downloaded_size = Column(Integer, default=0)  # in bytes
    
    # Error handling
    error_message = Column(String(1000))
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Metadata
    metadata = Column(JSON)  # Store additional metadata from source
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="queue_items")
    
    video_id = Column(Integer, ForeignKey("videos.id"))
    video = relationship("Video", back_populates="queue_items")
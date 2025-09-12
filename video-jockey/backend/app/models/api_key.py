"""
API Key model definition
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class APIKey(Base):
    """API Key model for external service integration"""
    
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Key info
    service = Column(String(100), nullable=False, index=True)  # e.g., "imvdb", "youtube"
    key_value = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    
    # Rate limiting
    rate_limit = Column(Integer)  # requests per day
    rate_limit_remaining = Column(Integer)
    rate_limit_reset_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="api_keys")
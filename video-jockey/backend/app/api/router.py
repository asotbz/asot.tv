"""
Main API router that combines all endpoint routers
"""

from fastapi import APIRouter

# Import endpoint routers (to be created)
# from app.api.endpoints import auth, users, videos, queue

# Create main API router
api_router = APIRouter()

# Include endpoint routers
# api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
# api_router.include_router(queue.router, prefix="/queue", tags=["queue"])


# Temporary test endpoint
@api_router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "API is working!"}
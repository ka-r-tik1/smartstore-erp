# SmartStore ERP — Health Check API
# Ye API check karti hai ki server chal raha hai ya nahi
# Browser mein /docs kholne pe ye dikhai dega

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    """Server health check — agar ye response aaye toh sab sahi hai"""
    return {
        "status": "healthy",
        "app": "SmartStore ERP",
        "version": "1.0.0",
        "message": "Backend chal raha hai! 🟢"
    }

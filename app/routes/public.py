from fastapi import APIRouter

router = APIRouter()

@router.get("/public/info")
def public_info():
    return {"message": "This is public"}

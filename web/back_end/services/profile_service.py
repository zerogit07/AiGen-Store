from source.config import ADMIN_ID

async def get_admin_profile():
    return {
        "user_id": ADMIN_ID,
        "username": "Admin",
        "role": "Super Admin"
    }

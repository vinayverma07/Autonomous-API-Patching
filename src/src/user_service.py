from fastapi import FastAPI, HTTPException
from typing import Dict, Any, Optional

app = FastAPI()

@app.post("/api/users/profile")
def create_user_profile(user_data: Dict[str, Any]):
    if not user_data:
        raise HTTPException(status_code=400, detail="Payload required")
    
    first_name = user_data.get("first_name")
    last_name = user_data.get("last_name")
    
    if first_name is None or last_name is None:
        raise HTTPException(status_code=400, detail="Both 'first_name' and 'last_name' are required")
    
    formatted_name = first_name.strip().title() + " " + last_name.strip().title()
    
    email = user_data.get("email", "").lower()
    
    return {
        "status": "created",
        "full_name": formatted_name,
        "email": email
    }
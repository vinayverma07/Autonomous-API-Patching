from fastapi import FastAPI, HTTPException
from typing import Dict, Any

app = FastAPI()

@app.post("/api/users/format-name")
def format_user_name(payload: Dict[str, Any]):
    # Safely retrieve first_name and last_name, defaulting to empty string if None or missing
    formatted_first = (payload.get("first_name") or "").strip().title()
    formatted_last = (payload.get("last_name") or "").strip().title()
    
    # Check if both names are empty after formatting
    if not formatted_first and not formatted_last:
        raise HTTPException(status_code=400, detail="Both first_name and last_name are required.")
    
    full_name = f"{formatted_first} {formatted_last}".strip()
    return {"status": "success", "full_name": full_name}
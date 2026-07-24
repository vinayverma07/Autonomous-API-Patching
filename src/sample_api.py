"""
Module: Bug Simulation Target API
File Path: src/sample_api.py
Description: An intentionally broken mock microservice endpoint module 
             used to test our agent's self-healing capabilities.
"""

from fastapi import FastAPI, HTTPException

app = FastAPI()

# Database mock data dictionary missing explicit user structural attributes
MOCK_DATABASE = {
    "user_101": {"name": "Alice Dev"},
    "user_102": {"name": "Bob Architect"}
}

@app.get("/api/user/{user_id}")
def get_user_profile(user_id: str):
    """
    Simulates a breaking code bug. If the user payload request doesn't match 
    the hardcoded scheme structure, it crashes with a key mapping exception.
    """
    # BUG: If a client asks for a user_id that isn't explicitly defined, 
    # it throws a raw KeyError instead of returning a clean HTTP 404 response.
    user_record = MOCK_DATABASE[user_id]
    
    return {
        "status": "success",
        "user_data": user_record
    }
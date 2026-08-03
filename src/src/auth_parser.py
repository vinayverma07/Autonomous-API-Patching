from fastapi import FastAPI, Header, HTTPException
from typing import Optional

app = FastAPI()

@app.get("/api/secure/data")
def parse_auth_header(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing header")
    
    # Split the authorization header and check its format
    auth_parts = authorization.split(" ")
    
    # Check if the authorization header is malformed
    if len(auth_parts) < 2 or auth_parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Malformed authorization header")
    
    token = auth_parts[1]
    
    return {"status": "authenticated", "token": token}
> **Purpose:** Guides the RAG agent on resolving key errors, payload parsing crashes, and endpoint exceptions in FastAPI apps.

```markdown
# FastAPI Exception Handling & Payload Parsing

## Handling KeyErrors and TypeErrors
When building endpoint handlers in FastAPI using raw dictionaries (`Dict[str, Any]`), unhandled missing keys raise `KeyError`.

### Recommended Patterns:

1. **Use Pydantic Models for Automatic Validation:**
```python
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserProfileRequest(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None


 
@app.post("/api/users/profile")
def create_profile(payload: dict):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid JSON body format.")
        
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=422, detail="Missing mandatory 'user_id' field.")

```


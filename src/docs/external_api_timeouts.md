> **Purpose:** Guides the RAG agent on resolving external HTTP client errors (`httpx`, `requests`) such as network timeouts and connection refusal.

```markdown
# Resilience & Timeout Handling for External API Calls

## Overview
When an API service makes HTTP requests to downstream microservices or third-party webhooks, unhandled network delays cause hanging requests or raw `httpx.ConnectTimeout` / `requests.exceptions.RequestException` crashes.

## Best Practices

### 1. Explicit Timeout Configurations
Always specify explicit request timeouts rather than relying on default indefinite blocks.

**Safe Pattern with `httpx`:**
```python
import httpx
from fastapi import HTTPException

async def fetch_third_party_data(target_url: str) -> dict:
    # Set explicit connect and read timeouts (in seconds)
    timeout = httpx.Timeout(5.0, connect=2.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(target_url)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, 
                detail="Upstream service request timed out."
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code, 
                detail=f"Upstream service error: {exc.response.text}"
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=502, 
                detail="Unable to reach upstream service."
            )

```
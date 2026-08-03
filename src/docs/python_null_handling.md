# Defensive Programming & Null Safety in Python APIs

## Overview
A common cause of API 500 internal server errors is assuming incoming JSON body parameters are non-null string types. When client requests contain `null` or missing keys, calling string methods directly raises `AttributeError: 'NoneType' object has no attribute 'method'`.

## Best Practices

### 1. Dictionary Fetching with Fallbacks
Never call string operations directly on dictionary values without validating existence and type first.

**Unsafe:**
```python
formatted_name = user_data["first_name"].strip().title()
```

**Safe:**
# Returns an empty string if key is missing or value is None
```python
first_name = user_data.get("first_name") or ""
formatted_name = first_name.strip().title()
```


### 2. If fields are strictly required, validate them explicitly before processing and return a structured 400 HTTP error:

```python
from fastapi import HTTPException

first_name = user_data.get("first_name")
last_name = user_data.get("last_name")

if not first_name or not last_name:
    raise HTTPException(
        status_code=400, 
        detail="Fields 'first_name' and 'last_name' must be valid non-empty strings."
    )
```

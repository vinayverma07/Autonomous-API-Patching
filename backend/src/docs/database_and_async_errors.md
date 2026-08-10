
> **Purpose:** Teaches the agent how to fix missing `await` statements, async connection failures, and MongoDB/SQL driver crashes.

```markdown
# Asynchronous Database Operations & Connection Management

## Overview
When converting synchronous API code to `async/await` syntax, two frequent failure modes occur:
1. Forgetting to `await` coroutines (returning an unawaited `coroutine` object instead of the actual data).
2. Leaving database connections uninitialized or unhandled during query execution.

## Best Practices

### 1. Handling Missing `await` Coroutines
Calling an async database or network function without `await` leads to unexpected runtime behavior or downstream attribute errors.

**Unsafe:**
```python
# Returns <coroutine object find_one at 0x...> instead of dict
user_record = db["users"].find_one({"_id": user_id})
email = user_record.get("email") # Raises AttributeError
```

**Safe:**
```python
user_record = await db["users"].find_one({"_id": user_id})

if not user_record:
    raise HTTPException(status_code=404, detail="User not found.")

email = user_record.get("email", "")
```
### Always guard database operations against uninitialized client connections:
```python
if db_client is None:
    raise RuntimeError("Database connection pool uninitialized. Call db.connect() first.")
```


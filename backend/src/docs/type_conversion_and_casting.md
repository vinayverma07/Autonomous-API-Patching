# Handling Type Casting and Conversion Errors in Python APIs

## Overview
APIs frequently receive string inputs from query parameters (`?age=25`), path variables, or unparsed JSON headers. Attempting to convert invalid or empty strings into numerical types directly causes unhandled `ValueError: invalid literal for int()` crashes.

## Best Practices

### 1. Safe Numerical Parsing
Never attempt direct casting without catching `ValueError` or verifying input types first.

**Unsafe:**
```python
user_age = int(request_data["age"])
```

**Safe:**
```python
raw_age = request_data.get("age")

try:
    user_age = int(raw_age) if raw_age is not None else 0
except (ValueError, TypeError):
    raise HTTPException(
        status_code=400, 
        detail="Invalid parameter: 'age' must be a valid integer."
    )
```

### When parsing financial data, ratings, or coordinates, validate range boundaries alongside type conversion:
```python
raw_rate = request_data.get("tax_rate")

try:
    tax_rate = float(raw_rate)
    if tax_rate < 0.0 or tax_rate > 100.0:
        raise ValueError("Tax rate out of bounds")
except (ValueError, TypeError):
    raise HTTPException(
        status_code=422, 
        detail="Tax rate must be a valid float between 0.0 and 100.0."
    )
```
import time
import uuid
from typing import List
from fastapi import FastAPI, Query, HTTPException, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI()

# --- Configuration ---
ALLOWED_ORIGIN = "https://dash-e2tqwr.example.com"
USER_EMAIL = "your-email@example.com"  # Replace with your actual logged-in email


@app.middleware("http")
async def custom_cors_and_headers_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    request_id = str(uuid.uuid4())
    
    origin = request.headers.get("Origin")
    is_options = request.method == "OPTIONS"

    # Handle Preflight/CORS routing explicitly
    if origin == ALLOWED_ORIGIN:
        if is_options:
            # Short-circuit and return a successful 200 OK preflight response
            response = Response(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
        else:
            # Process normal request
            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    else:
        if is_options:
            # Reject untrusted preflights with a 400 or 403 (and NO ACAO header)
            response = Response(status_code=400, content="CORS Not Allowed")
        else:
            # Normal requests from other origins proceed but do NOT get the ACAO header
            response = await call_next(request)

    # Inject required middleware tracking headers to EVERY response
    process_time = time.perf_counter() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    
    return response


@app.get("/stats")
async def get_stats(values: str = Query(..., description="Comma-separated integers")):
    try:
        # Parse comma-separated string into integers
        parsed_values = [int(x.strip()) for x in values.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integers provided in query string.")

    if not parsed_values:
        raise HTTPException(status_code=400, detail="Value list cannot be empty.")

    # Compute descriptive statistics
    count = len(parsed_values)
    total_sum = sum(parsed_values)
    minimum = min(parsed_values)
    maximum = max(parsed_values)
    mean = total_sum / count

    return {
        "email": USER_EMAIL,
        "count": count,
        "sum": total_sum,
        "min": minimum,
        "max": maximum,
        "mean": round(mean, 4)  # Comfortably within the ±0.01 threshold
    }

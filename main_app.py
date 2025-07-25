from fastapi import FastAPI, Request
import logging
import logstash
import time
import uvicorn

# Create FastAPI app
app = FastAPI()

# Set up logger
logger = logging.getLogger("fastapi-logger")
logger.setLevel(logging.INFO)

# Add logstash handler
logstash_handler = logstash.TCPLogstashHandler(
    host='localhost',
    port=5000,
    version=1  # Version 1 is for the Logstash event format
)

# Add handler to logger
logger.addHandler(logstash_handler)

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    # Log request details
    logger.info(
        f"Request processed: {request.method} {request.url.path}",
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
            "status_code": response.status_code,
            "process_time_ms": round(process_time, 2)
        }
    )
    
    return response

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run("main_app:app", host="0.0.0.0", port=8000)
import os
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Azure Application Insights
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace import config_integration

# Configure Azure Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')

# Configure logging for Application Insights
def setup_logging():
    logger = logging.getLogger(__name__)

    if APPLICATIONINSIGHTS_CONNECTION_STRING:
        # Add Azure Log Handler
        azure_handler = AzureLogHandler(
            connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING
        )
        azure_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        azure_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(azure_handler)
        logger.setLevel(logging.INFO)

        # Configure tracing
        config_integration.trace_integrations(['requests'])

    else:
        # Fallback to console logging for local development
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    return logger


# Initialize logger
logger = setup_logging()

# Configure tracer for Application Insights
tracer = None
if APPLICATIONINSIGHTS_CONNECTION_STRING:
    tracer = Tracer(
        exporter=AzureExporter(
            connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING
        ),
        sampler=ProbabilitySampler(1.0)
    )


# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class UserCreate(BaseModel):
    name: str
    email: str
    age: int


class User(BaseModel):
    id: int
    name: str
    email: str
    age: int
    created_at: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: str


# In-memory storage (use a real database in production)
users_db: List[User] = []
user_id_counter = 1


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("FastAPI application starting up")
    logger.info(f"Application Insights configured: {bool(APPLICATIONINSIGHTS_CONNECTION_STRING)}")
    yield
    # Shutdown
    logger.info("FastAPI application shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="Azure FastAPI Demo",
    description="A FastAPI application with Azure Application Insights integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom middleware for request logging and metrics
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url}")

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log response with timing
    logger.info(
        f"Response: {response.status_code} for {request.method} {request.url} "
        f"in {process_time:.4f}s",
        extra={
            'custom_dimensions': {
                'method': request.method,
                'url': str(request.url),
                'status_code': response.status_code,
                'process_time': process_time,
                'user_agent': request.headers.get('user-agent', ''),
                'client_ip': request.client.host if request.client else 'unknown'
            }
        }
    )

    # Add custom header with processing time
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for Azure App Service"""
    logger.info("Health check requested")

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")

    return {
        "message": "Welcome to FastAPI on Azure App Service!",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "health": "/health"
    }


# Users endpoints
@app.get("/users", response_model=List[User], tags=["Users"])
async def get_users():
    """Get all users"""
    logger.info(f"Retrieved {len(users_db)} users")

    # Log custom metric
    if APPLICATIONINSIGHTS_CONNECTION_STRING:
        logger.info("Users retrieved", extra={
            'custom_dimensions': {
                'operation': 'get_users',
                'user_count': len(users_db)
            }
        })

    return users_db


@app.get("/users/{user_id}", response_model=User, tags=["Users"])
async def get_user(user_id: int):
    """Get a specific user by ID"""
    logger.info(f"Retrieving user with ID: {user_id}")

    user = next((user for user in users_db if user.id == user_id), None)

    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"User found: {user.name}")
    return user


@app.post("/users", response_model=User, status_code=201, tags=["Users"])
async def create_user(user_data: UserCreate):
    """Create a new user"""
    global user_id_counter

    logger.info(f"Creating new user: {user_data.name}")

    # Create new user
    new_user = User(
        id=user_id_counter,
        name=user_data.name,
        email=user_data.email,
        age=user_data.age,
        created_at=datetime.utcnow().isoformat()
    )

    users_db.append(new_user)
    user_id_counter += 1

    logger.info(
        f"User created successfully: ID {new_user.id}",
        extra={
            'custom_dimensions': {
                'operation': 'create_user',
                'user_id': new_user.id,
                'user_name': new_user.name,
                'user_age': new_user.age
            }
        }
    )

    return new_user


@app.delete("/users/{user_id}", tags=["Users"])
async def delete_user(user_id: int):
    """Delete a user by ID"""
    logger.info(f"Attempting to delete user: {user_id}")

    global users_db
    user_index = next((i for i, user in enumerate(users_db) if user.id == user_id), None)

    if user_index is None:
        logger.warning(f"User not found for deletion: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    deleted_user = users_db.pop(user_index)
    logger.info(
        f"User deleted successfully: {deleted_user.name}",
        extra={
            'custom_dimensions': {
                'operation': 'delete_user',
                'user_id': user_id,
                'user_name': deleted_user.name
            }
        }
    )

    return {"message": f"User {user_id} deleted successfully"}


# Metrics endpoint
@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Get application metrics"""
    logger.info("Metrics requested")

    metrics = {
        "total_users": len(users_db),
        "timestamp": datetime.utcnow().isoformat(),
        "application_insights_configured": bool(APPLICATIONINSIGHTS_CONNECTION_STRING),
        "environment": os.environ.get("ENVIRONMENT", "development")
    }

    # Log metrics
    logger.info(
        "Application metrics collected",
        extra={
            'custom_dimensions': metrics
        }
    )

    return metrics


# Simulate error endpoint for testing
@app.get("/error", tags=["Testing"])
async def simulate_error():
    """Simulate an error for testing logging"""
    logger.error("Simulated error occurred")
    raise HTTPException(status_code=500, detail="This is a simulated error for testing")


# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            'custom_dimensions': {
                'status_code': exc.status_code,
                'detail': exc.detail,
                'path': request.url.path,
                'method': request.method
            }
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP Exception",
            message=exc.detail,
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            'custom_dimensions': {
                'exception_type': type(exc).__name__,
                'exception_message': str(exc),
                'path': request.url.path,
                'method': request.method
            }
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred",
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

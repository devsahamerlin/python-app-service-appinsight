# import os
# import logging
# import time
# from typing import Dict, List, Optional
# from datetime import datetime
#
# from fastapi import FastAPI, HTTPException, Request, Depends
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from contextlib import asynccontextmanager
# import asyncio
#
# # Database imports
# import aiomysql
# from aiomysql import Pool
#
# # Azure Application Insights
# from opencensus.ext.azure.log_exporter import AzureLogHandler
# from opencensus.ext.azure.trace_exporter import AzureExporter
# from opencensus.trace.samplers import ProbabilitySampler
# from opencensus.trace.tracer import Tracer
# from opencensus.trace import config_integration
#
# # Configure Azure Application Insights
# APPLICATIONINSIGHTS_CONNECTION_STRING = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')
#
# # Database configuration
# DATABASE_CONFIG = {
#     'host': os.environ.get('DB_HOST', 'localhost'),
#     'port': int(os.environ.get('DB_PORT', 3306)),
#     'user': os.environ.get('DB_USER', 'root'),
#     'password': os.environ.get('DB_PASSWORD', ''),
#     'db': os.environ.get('DB_NAME', 'fastapi_db'),
#     'charset': 'utf8mb4',
#     'autocommit': True
# }
#
# # Global database pool
# db_pool: Optional[Pool] = None
#
#
# # Configure logging for Application Insights
# def setup_logging():
#     logger = logging.getLogger(__name__)
#
#     if APPLICATIONINSIGHTS_CONNECTION_STRING:
#         # Add Azure Log Handler
#         azure_handler = AzureLogHandler(
#             connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING
#         )
#         azure_handler.setLevel(logging.INFO)
#
#         # Create formatter
#         formatter = logging.Formatter(
#             '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#         )
#         azure_handler.setFormatter(formatter)
#
#         # Add handler to logger
#         logger.addHandler(azure_handler)
#         logger.setLevel(logging.INFO)
#
#         # Configure tracing
#         config_integration.trace_integrations(['requests'])
#
#     else:
#         # Fallback to console logging for local development
#         logging.basicConfig(
#             level=logging.INFO,
#             format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#         )
#
#     return logger
#
#
# # Initialize logger
# logger = setup_logging()
#
# # Configure tracer for Application Insights
# tracer = None
# if APPLICATIONINSIGHTS_CONNECTION_STRING:
#     tracer = Tracer(
#         exporter=AzureExporter(
#             connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING
#         ),
#         sampler=ProbabilitySampler(1.0)
#     )
#
#
# # Pydantic models
# class HealthResponse(BaseModel):
#     status: str
#     timestamp: str
#     version: str
#
#
# class UserCreate(BaseModel):
#     name: str
#     email: str
#     age: int
#
#
# class User(BaseModel):
#     id: int
#     name: str
#     email: str
#     age: int
#     created_at: str
#
#
# class ErrorResponse(BaseModel):
#     error: str
#     message: str
#     timestamp: str
#
#
# # In-memory storage (use a real database in production) - REMOVED
# # users_db: List[User] = []
# # user_id_counter = 1
#
# # Database functions
# async def init_database():
#     """Initialize database connection pool and create tables"""
#     global db_pool
#
#     try:
#         # Create connection pool
#         db_pool = await aiomysql.create_pool(
#             minsize=1,
#             maxsize=10,
#             **DATABASE_CONFIG
#         )
#
#         logger.info("Database connection pool created successfully")
#
#         # Create tables if they don't exist
#         await create_tables()
#
#     except Exception as e:
#         logger.error(f"Failed to initialize database: {str(e)}")
#         raise
#
#
# async def create_tables():
#     """Create database tables if they don't exist"""
#     create_users_table = """
#     CREATE TABLE IF NOT EXISTS users (
#         id INT AUTO_INCREMENT PRIMARY KEY,
#         name VARCHAR(255) NOT NULL,
#         email VARCHAR(255) NOT NULL UNIQUE,
#         age INT NOT NULL,
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
#     )
#     """
#
#     async with db_pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(create_users_table)
#             logger.info("Users table created/verified successfully")
#
#
# async def get_db_connection():
#     """Get database connection from pool"""
#     if not db_pool:
#         raise HTTPException(status_code=503, detail="Database not available")
#     return db_pool.acquire()
#
#
# async def close_database():
#     """Close database connection pool"""
#     global db_pool
#     if db_pool:
#         db_pool.close()
#         await db_pool.wait_closed()
#         logger.info("Database connection pool closed")
#
#
# # Lifespan context manager
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     logger.info("FastAPI application starting up")
#     logger.info(f"Application Insights configured: {bool(APPLICATIONINSIGHTS_CONNECTION_STRING)}")
#
#     # Initialize database
#     try:
#         await init_database()
#         logger.info("Database initialized successfully")
#     except Exception as e:
#         logger.error(f"Database initialization failed: {str(e)}")
#         # Don't raise here to allow app to start even if DB is not available
#
#     yield
#
#     # Shutdown
#     logger.info("FastAPI application shutting down")
#     await close_database()
#
#
# # Initialize FastAPI app
# app = FastAPI(
#     title="Azure FastAPI Demo",
#     description="A FastAPI application with Azure Application Insights integration",
#     version="1.0.0",
#     lifespan=lifespan
# )
#
# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
#
# # Custom middleware for request logging and metrics
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     start_time = time.time()
#
#     # Log request
#     logger.info(f"Request: {request.method} {request.url}")
#
#     # Process request
#     response = await call_next(request)
#
#     # Calculate processing time
#     process_time = time.time() - start_time
#
#     # Log response with timing
#     logger.info(
#         f"Response: {response.status_code} for {request.method} {request.url} "
#         f"in {process_time:.4f}s",
#         extra={
#             'custom_dimensions': {
#                 'method': request.method,
#                 'url': str(request.url),
#                 'status_code': response.status_code,
#                 'process_time': process_time,
#                 'user_agent': request.headers.get('user-agent', ''),
#                 'client_ip': request.client.host if request.client else 'unknown'
#             }
#         }
#     )
#
#     # Add custom header with processing time
#     response.headers["X-Process-Time"] = str(process_time)
#
#     return response
#
#
# # Health check endpoint
# @app.get("/health", response_model=HealthResponse, tags=["Health"])
# async def health_check():
#     """Health check endpoint for Azure App Service"""
#     logger.info("Health check requested")
#
#     return HealthResponse(
#         status="healthy",
#         timestamp=datetime.utcnow().isoformat(),
#         version="1.0.0"
#     )
#
#
# # Root endpoint
# @app.get("/", tags=["Root"])
# async def read_root():
#     """Root endpoint"""
#     logger.info("Root endpoint accessed")
#
#     return {
#         "message": "Welcome to FastAPI on Azure App Service!",
#         "timestamp": datetime.utcnow().isoformat(),
#         "docs": "/docs",
#         "health": "/health"
#     }
#
#
# # Users endpoints
# @app.get("/users", response_model=List[User], tags=["Users"])
# async def get_users():
#     """Get all users from database"""
#     logger.info("Retrieving all users from database")
#
#     try:
#         async with await get_db_connection() as conn:
#             async with conn.cursor(aiomysql.DictCursor) as cursor:
#                 await cursor.execute(
#                     "SELECT id, name, email, age, created_at FROM users ORDER BY created_at DESC"
#                 )
#                 rows = await cursor.fetchall()
#
#                 users = []
#                 for row in rows:
#                     users.append(User(
#                         id=row['id'],
#                         name=row['name'],
#                         email=row['email'],
#                         age=row['age'],
#                         created_at=row['created_at'].isoformat()
#                     ))
#
#                 logger.info(f"Retrieved {len(users)} users from database")
#
#                 # Log custom metric
#                 if APPLICATIONINSIGHTS_CONNECTION_STRING:
#                     logger.info("Users retrieved from database", extra={
#                         'custom_dimensions': {
#                             'operation': 'get_users',
#                             'user_count': len(users)
#                         }
#                     })
#
#                 return users
#
#     except Exception as e:
#         logger.error(f"Error retrieving users: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error retrieving users from database")
#
#
# @app.get("/users/{user_id}", response_model=User, tags=["Users"])
# async def get_user(user_id: int):
#     """Get a specific user by ID from database"""
#     logger.info(f"Retrieving user with ID: {user_id}")
#
#     try:
#         async with await get_db_connection() as conn:
#             async with conn.cursor(aiomysql.DictCursor) as cursor:
#                 await cursor.execute(
#                     "SELECT id, name, email, age, created_at FROM users WHERE id = %s",
#                     (user_id,)
#                 )
#                 row = await cursor.fetchone()
#
#                 if not row:
#                     logger.warning(f"User not found in database: {user_id}")
#                     raise HTTPException(status_code=404, detail="User not found")
#
#                 user = User(
#                     id=row['id'],
#                     name=row['name'],
#                     email=row['email'],
#                     age=row['age'],
#                     created_at=row['created_at'].isoformat()
#                 )
#
#                 logger.info(f"User found in database: {user.name}")
#                 return user
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error retrieving user {user_id}: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error retrieving user from database")
#
#
# @app.post("/users", response_model=User, status_code=201, tags=["Users"])
# async def create_user(user_data: UserCreate):
#     """Create a new user in database"""
#     logger.info(f"Creating new user in database: {user_data.name}")
#
#     try:
#         async with await get_db_connection() as conn:
#             async with conn.cursor(aiomysql.DictCursor) as cursor:
#                 # Insert new user
#                 await cursor.execute(
#                     """
#                     INSERT INTO users (name, email, age)
#                     VALUES (%s, %s, %s)
#                     """,
#                     (user_data.name, user_data.email, user_data.age)
#                 )
#
#                 # Get the created user
#                 user_id = cursor.lastrowid
#                 await cursor.execute(
#                     "SELECT id, name, email, age, created_at FROM users WHERE id = %s",
#                     (user_id,)
#                 )
#                 row = await cursor.fetchone()
#
#                 new_user = User(
#                     id=row['id'],
#                     name=row['name'],
#                     email=row['email'],
#                     age=row['age'],
#                     created_at=row['created_at'].isoformat()
#                 )
#
#                 logger.info(
#                     f"User created successfully in database: ID {new_user.id}",
#                     extra={
#                         'custom_dimensions': {
#                             'operation': 'create_user',
#                             'user_id': new_user.id,
#                             'user_name': new_user.name,
#                             'user_age': new_user.age
#                         }
#                     }
#                 )
#
#                 return new_user
#
#     except aiomysql.IntegrityError as e:
#         if "Duplicate entry" in str(e):
#             logger.warning(f"Duplicate email attempted: {user_data.email}")
#             raise HTTPException(status_code=400, detail="Email already exists")
#         raise HTTPException(status_code=400, detail="Database constraint violation")
#     except Exception as e:
#         logger.error(f"Error creating user: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error creating user in database")
#
#
# @app.delete("/users/{user_id}", tags=["Users"])
# async def delete_user(user_id: int):
#     """Delete a user by ID from database"""
#     logger.info(f"Attempting to delete user from database: {user_id}")
#
#     try:
#         async with await get_db_connection() as conn:
#             async with conn.cursor(aiomysql.DictCursor) as cursor:
#                 # First, get user info for logging
#                 await cursor.execute(
#                     "SELECT name FROM users WHERE id = %s", (user_id,)
#                 )
#                 user_row = await cursor.fetchone()
#
#                 if not user_row:
#                     logger.warning(f"User not found for deletion: {user_id}")
#                     raise HTTPException(status_code=404, detail="User not found")
#
#                 # Delete the user
#                 await cursor.execute(
#                     "DELETE FROM users WHERE id = %s", (user_id,)
#                 )
#
#                 if cursor.rowcount == 0:
#                     raise HTTPException(status_code=404, detail="User not found")
#
#                 logger.info(
#                     f"User deleted successfully from database: {user_row['name']}",
#                     extra={
#                         'custom_dimensions': {
#                             'operation': 'delete_user',
#                             'user_id': user_id,
#                             'user_name': user_row['name']
#                         }
#                     }
#                 )
#
#                 return {"message": f"User {user_id} deleted successfully"}
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error deleting user {user_id}: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error deleting user from database")
#
#
# # Database health check endpoint
# @app.get("/db-health", tags=["Monitoring"])
# async def database_health_check():
#     """Check database health and performance"""
#     logger.info("Database health check requested")
#
#     try:
#         async with await get_db_connection() as conn:
#             async with conn.cursor(aiomysql.DictCursor) as cursor:
#                 # Check connection
#                 await cursor.execute("SELECT 1")
#
#                 # Get database stats
#                 await cursor.execute("""
#                     SELECT
#                         COUNT(*) as total_users,
#                         MAX(created_at) as last_user_created,
#                         MIN(created_at) as first_user_created
#                     FROM users
#                 """)
#                 stats = await cursor.fetchone()
#
#                 # Check table status
#                 await cursor.execute("SHOW TABLE STATUS LIKE 'users'")
#                 table_info = await cursor.fetchone()
#
#                 health_status = {
#                     "status": "healthy",
#                     "database": DATABASE_CONFIG['db'],
#                     "host": DATABASE_CONFIG['host'],
#                     "total_users": stats['total_users'] if stats else 0,
#                     "last_user_created": stats['last_user_created'].isoformat() if stats and stats[
#                         'last_user_created'] else None,
#                     "first_user_created": stats['first_user_created'].isoformat() if stats and stats[
#                         'first_user_created'] else None,
#                     "table_rows": table_info['Rows'] if table_info else 0,
#                     "table_size_mb": round(table_info['Data_length'] / 1024 / 1024, 2) if table_info and table_info[
#                         'Data_length'] else 0,
#                     "timestamp": datetime.utcnow().isoformat()
#                 }
#
#                 logger.info("Database health check completed successfully")
#                 return health_status
#
#     except Exception as e:
#         logger.error(f"Database health check failed: {str(e)}")
#         return {
#             "status": "unhealthy",
#             "error": str(e),
#             "timestamp": datetime.utcnow().isoformat()
#         }
#
#
# @app.get("/metrics", tags=["Monitoring"])
# async def get_metrics():
#     """Get application metrics"""
#     logger.info("Metrics requested")
#
#     try:
#         # Get user count from database
#         user_count = 0
#         if db_pool:
#             async with await get_db_connection() as conn:
#                 async with conn.cursor() as cursor:
#                     await cursor.execute("SELECT COUNT(*) as count FROM users")
#                     result = await cursor.fetchone()
#                     user_count = result[0] if result else 0
#
#         metrics = {
#             "total_users": user_count,
#             "timestamp": datetime.utcnow().isoformat(),
#             "application_insights_configured": bool(APPLICATIONINSIGHTS_CONNECTION_STRING),
#             "database_connected": bool(db_pool and not db_pool.closed),
#             "environment": os.environ.get("ENVIRONMENT", "development")
#         }
#
#         # Log metrics
#         logger.info(
#             "Application metrics collected",
#             extra={
#                 'custom_dimensions': metrics
#             }
#         )
#
#         return metrics
#
#     except Exception as e:
#         logger.error(f"Error collecting metrics: {str(e)}")
#         # Return basic metrics if database is unavailable
#         return {
#             "total_users": "unavailable",
#             "timestamp": datetime.utcnow().isoformat(),
#             "application_insights_configured": bool(APPLICATIONINSIGHTS_CONNECTION_STRING),
#             "database_connected": False,
#             "environment": os.environ.get("ENVIRONMENT", "development"),
#             "error": "Database unavailable"
#         }
#
#
# # Simulate error endpoint for testing
# @app.get("/error", tags=["Testing"])
# async def simulate_error():
#     """Simulate an error for testing logging"""
#     logger.error("Simulated error occurred")
#     raise HTTPException(status_code=500, detail="This is a simulated error for testing")
#
#
# # Custom exception handler
# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     logger.error(
#         f"HTTP Exception: {exc.status_code} - {exc.detail}",
#         extra={
#             'custom_dimensions': {
#                 'status_code': exc.status_code,
#                 'detail': exc.detail,
#                 'path': request.url.path,
#                 'method': request.method
#             }
#         }
#     )
#
#     return JSONResponse(
#         status_code=exc.status_code,
#         content=ErrorResponse(
#             error="HTTP Exception",
#             message=exc.detail,
#             timestamp=datetime.utcnow().isoformat()
#         ).dict()
#     )
#
#
# # Global exception handler
# @app.exception_handler(Exception)
# async def global_exception_handler(request: Request, exc: Exception):
#     logger.error(
#         f"Unhandled exception: {str(exc)}",
#         extra={
#             'custom_dimensions': {
#                 'exception_type': type(exc).__name__,
#                 'exception_message': str(exc),
#                 'path': request.url.path,
#                 'method': request.method
#             }
#         },
#         exc_info=True
#     )
#
#     return JSONResponse(
#         status_code=500,
#         content=ErrorResponse(
#             error="Internal Server Error",
#             message="An unexpected error occurred",
#             timestamp=datetime.utcnow().isoformat()
#         ).dict()
#     )
#
#
# if __name__ == "__main__":
#     import uvicorn
#
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=port,
#         reload=False,
#         log_level="info"
#     )
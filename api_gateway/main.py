"""
Main FastAPI application for API Gateway.
"""
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
import logging
import json
from datetime import datetime, timezone
from typing import Optional

try:
    from .database import get_db_session, init_db, PricingConfig, ModelMetadata, Customer
    from .auth import get_current_customer
    from .ollama_client import list_models, chat, generate, check_ollama_health
    from .usage import calculate_cost, log_usage, check_budget
    from .external_apis import (
        openai_chat_completions,
        calculate_openai_cost,
        claude_messages,
        calculate_claude_cost
    )
    from .models import (
        ChatRequest,
        GenerateRequest,
        OpenAICompletionsRequest,
        ModelsListResponse,
        ModelInfo
    )
except ImportError:
    from database import get_db_session, init_db, PricingConfig, ModelMetadata, Customer
    from auth import get_current_customer
    from ollama_client import list_models, chat, generate, check_ollama_health
    from usage import calculate_cost, log_usage, check_budget
    from external_apis import (
        openai_chat_completions,
        calculate_openai_cost,
        claude_messages,
        calculate_claude_cost
    )
    from models import (
        ChatRequest,
        GenerateRequest,
        OpenAICompletionsRequest,
        ModelsListResponse,
        ModelInfo
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Ollama API Gateway",
    description="API Gateway for Ollama with authentication and billing",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    logger.info("Database initialized")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with customer context."""
    start_time = datetime.utcnow()
    
    # Process request
    response = await call_next(request)
    
    # Log request
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint with current timestamp."""
    return {
        "status": "healthy",
        "service": "api_gateway",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timestamp_local": datetime.now().isoformat()
    }


@app.get("/health/dashboard", response_class=HTMLResponse)
async def health_dashboard():
    """Health check dashboard with auto-updating time."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Gateway Health Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 15px;
                padding: 40px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                max-width: 600px;
                width: 100%;
            }
            h1 {
                color: #333;
                margin-top: 0;
                text-align: center;
            }
            .status {
                text-align: center;
                padding: 20px;
                margin: 20px 0;
                border-radius: 10px;
                background: #e8f5e9;
                border: 2px solid #4caf50;
            }
            .status.healthy {
                background: #e8f5e9;
                border-color: #4caf50;
                color: #2e7d32;
            }
            .time {
                font-size: 2.5em;
                font-weight: bold;
                text-align: center;
                color: #667eea;
                margin: 20px 0;
                font-family: 'Courier New', monospace;
            }
            .time-label {
                font-size: 0.4em;
                color: #666;
                font-weight: normal;
                display: block;
                margin-top: 10px;
            }
            .info {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }
            .info-item {
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #f0f0f0;
            }
            .info-label {
                font-weight: bold;
                color: #666;
            }
            .info-value {
                color: #333;
            }
            .refresh-indicator {
                text-align: center;
                color: #999;
                font-size: 0.9em;
                margin-top: 20px;
            }
        </style>
        <script>
            // Wait for DOM to be ready
            document.addEventListener('DOMContentLoaded', function() {
                function updateTime() {
                    const now = new Date();
                    const utcTime = now.toISOString();
                    const localTime = now.toLocaleString('en-US', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: false
                    });
                    
                    const utcElement = document.getElementById('utc-time');
                    const localElement = document.getElementById('local-time');
                    const timestampElement = document.getElementById('timestamp');
                    
                    if (utcElement) utcElement.textContent = utcTime;
                    if (localElement) localElement.textContent = localTime;
                    if (timestampElement) timestampElement.textContent = now.getTime();
                }
                
                // Update time immediately and then every 100ms for smooth updates
                updateTime();
                setInterval(updateTime, 100);
                
                // Fetch health status every 5 seconds
                async function fetchHealthStatus() {
                    try {
                        const response = await fetch('/health');
                        const data = await response.json();
                        const lastCheckElement = document.getElementById('last-check');
                        if (lastCheckElement) {
                            lastCheckElement.textContent = new Date(data.timestamp).toLocaleTimeString();
                        }
                        
                        // Update status if needed
                        const statusElement = document.querySelector('.status');
                        if (statusElement && data.status === 'healthy') {
                            statusElement.className = 'status healthy';
                            statusElement.innerHTML = '<strong>Status:</strong> Healthy ✓';
                        }
                    } catch (error) {
                        console.error('Health check failed:', error);
                        const statusElement = document.querySelector('.status');
                        if (statusElement) {
                            statusElement.className = 'status';
                            statusElement.style.background = '#ffebee';
                            statusElement.style.borderColor = '#f44336';
                            statusElement.style.color = '#c62828';
                            statusElement.innerHTML = '<strong>Status:</strong> Error ✗';
                        }
                    }
                }
                
                fetchHealthStatus();
                setInterval(fetchHealthStatus, 5000);
            });
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🚀 API Gateway Health Dashboard</h1>
            
            <div class="status healthy">
                <strong>Status:</strong> Healthy ✓
            </div>
            
            <div class="time">
                <span id="utc-time"></span>
                <span class="time-label">UTC Time</span>
                <span id="local-time" style="display: block; margin-top: 15px; font-size: 0.6em;"></span>
                <span class="time-label">Local Time</span>
            </div>
            
            <div class="info">
                <div class="info-item">
                    <span class="info-label">Service:</span>
                    <span class="info-value">API Gateway</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Status:</span>
                    <span class="info-value">Healthy</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Last Health Check:</span>
                    <span class="info-value" id="last-check">Checking...</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Timestamp (Unix):</span>
                    <span class="info-value" id="timestamp"></span>
                </div>
            </div>
            
            <div class="refresh-indicator">
                Time updates every 100ms • Health status updates every 5 seconds
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health/ollama")
async def ollama_health_check():
    """Check Ollama connectivity."""
    is_healthy = await check_ollama_health()
    if is_healthy:
        return {
            "status": "healthy",
            "service": "ollama",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "timestamp_local": datetime.now().isoformat()
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama service unavailable"
        )


# Model discovery endpoints
@app.get("/api/models", response_model=ModelsListResponse)
async def get_models(
    customer: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db_session)
):
    """List available models (Ollama format)."""
    from database import PricingConfig, ModelMetadata
    
    models = await list_models()
    
    # Get pricing configs
    pricing_configs = db.query(PricingConfig).filter(
        PricingConfig.active == True
    ).all()
    pricing_map = {p.model_name: True for p in pricing_configs}
    
    # Get model metadata
    metadata_records = db.query(ModelMetadata).all()
    metadata_map = {m.model_name: m for m in metadata_records}
    
    model_list = []
    for model in models:
        model_name = model.get("name", "")
        metadata = metadata_map.get(model_name)
        
        model_list.append(ModelInfo(
            id=model_name,
            name=model_name,
            pricing_configured=model_name in pricing_map
        ))
    
    return ModelsListResponse(models=model_list)


@app.get("/v1/models", response_model=dict)
async def get_models_openai_format(
    customer: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db_session)
):
    """List available models (OpenAI-compatible format)."""
    from database import PricingConfig, ModelMetadata
    
    models = await list_models()
    
    # Get pricing configs
    pricing_configs = db.query(PricingConfig).filter(
        PricingConfig.active == True
    ).all()
    pricing_map = {p.model_name: True for p in pricing_configs}
    
    # Get model metadata
    metadata_records = db.query(ModelMetadata).all()
    metadata_map = {m.model_name: m for m in metadata_records}
    
    model_list = []
    for model in models:
        model_name = model.get("name", "")
        metadata = metadata_map.get(model_name)
        
        model_data = {
            "id": model_name,
            "object": "model",
            "created": int(datetime.utcnow().timestamp()),
            "owned_by": "ollama",
            "pricing_configured": model_name in pricing_map
        }
        
        # Add metadata if available
        if metadata:
            if metadata.description:
                model_data["description"] = metadata.description
            if metadata.context_window:
                model_data["context_window"] = metadata.context_window
        
        model_list.append(model_data)
    
    return {
        "object": "list",
        "data": model_list
    }


# Ollama API endpoints
@app.post("/api/chat")
async def ollama_chat(
    request: ChatRequest,
    customer_data: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db_session)
):
    """Ollama chat endpoint."""
    customer, api_key = customer_data
    
    # Check budget
    within_budget, spending, budget_limit = check_budget(customer.id, db)
    if not within_budget:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Budget exceeded. Current spending: ${spending:.2f}, Budget: ${budget_limit:.2f}"
        )
    
    try:
        # Call Ollama
        response = await chat(
            model=request.model,
            messages=request.messages,
            stream=request.stream,
            options=request.options
        )
        
        # Calculate and log cost
        cost = calculate_cost(request.model, "/api/chat", db)
        log_usage(
            customer_id=customer.id,
            api_key_id=api_key.id,
            endpoint="/api/chat",
            model=request.model,
            cost=cost,
            db=db,
            metadata=json.dumps({"stream": request.stream})
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/generate")
async def ollama_generate(
    request: GenerateRequest,
    customer_data: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db_session)
):
    """Ollama generate endpoint."""
    customer, api_key = customer_data
    
    # Check budget
    within_budget, spending, budget_limit = check_budget(customer.id, db)
    if not within_budget:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Budget exceeded. Current spending: ${spending:.2f}, Budget: ${budget_limit:.2f}"
        )
    
    try:
        # Call Ollama
        response = await generate(
            model=request.model,
            prompt=request.prompt,
            stream=request.stream,
            options=request.options
        )
        
        # Calculate and log cost
        cost = calculate_cost(request.model, "/api/generate", db)
        log_usage(
            customer_id=customer.id,
            api_key_id=api_key.id,
            endpoint="/api/generate",
            model=request.model,
            cost=cost,
            db=db,
            metadata=json.dumps({"stream": request.stream})
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# OpenAI-compatible endpoints
@app.post("/v1/chat/completions")
async def openai_chat_completions(
    request: OpenAICompletionsRequest,
    customer_data: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db_session)
):
    """OpenAI-compatible chat completions endpoint."""
    customer, api_key = customer_data
    
    # Check budget
    within_budget, spending, budget_limit = check_budget(customer.id, db)
    if not within_budget:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Budget exceeded. Current spending: ${spending:.2f}, Budget: ${budget_limit:.2f}"
        )
    
    try:
        # Call OpenAI API
        response = await openai_chat_completions(
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p
        )
        
        # Calculate cost from usage
        usage = response.get("usage", {})
        cost = calculate_openai_cost(request.model, usage)
        
        # Log usage
        log_usage(
            customer_id=customer.id,
            api_key_id=api_key.id,
            endpoint="/v1/chat/completions",
            model=request.model,
            cost=cost,
            db=db,
            metadata=json.dumps({"usage": usage})
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in OpenAI chat completions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Claude-compatible endpoints
@app.post("/v1/messages")
async def claude_messages_endpoint(
    request: dict,
    customer_data: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db_session)
):
    """Claude-compatible messages endpoint."""
    customer, api_key = customer_data
    
    # Check budget
    within_budget, spending, budget_limit = check_budget(customer.id, db)
    if not within_budget:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Budget exceeded. Current spending: ${spending:.2f}, Budget: ${budget_limit:.2f}"
        )
    
    try:
        model = request.get("model")
        messages = request.get("messages", [])
        max_tokens = request.get("max_tokens")
        temperature = request.get("temperature")
        
        # Call Claude API
        response = await claude_messages(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Calculate cost from usage
        usage = response.get("usage", {})
        cost = calculate_claude_cost(model, usage)
        
        # Log usage
        log_usage(
            customer_id=customer.id,
            api_key_id=api_key.id,
            endpoint="/v1/messages",
            model=model,
            cost=cost,
            db=db,
            metadata=json.dumps({"usage": usage})
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in Claude messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"message": exc.detail, "type": "api_error"}}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"message": "Internal server error", "type": "internal_error"}}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


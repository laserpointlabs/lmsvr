"""
Main FastAPI application for API Gateway.
"""
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
import json
from datetime import datetime
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
    """Health check endpoint."""
    return {"status": "healthy", "service": "api_gateway"}


@app.get("/health/ollama")
async def ollama_health_check():
    """Check Ollama connectivity."""
    is_healthy = await check_ollama_health()
    if is_healthy:
        return {"status": "healthy", "service": "ollama"}
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


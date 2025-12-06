"""
Main FastAPI application for API Gateway.
"""
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging
import json
import os
import httpx
import secrets
from datetime import datetime, timezone
from typing import Optional

try:
    from .database import get_db_session, init_db, PricingConfig, ModelMetadata, Customer, DeviceRegistration, APIKey
    from .auth import get_current_customer, hash_api_key
    from .ollama_client import list_models, chat, chat_stream, generate, check_ollama_health
    from .usage import calculate_cost, log_usage, check_budget
    from .mcp_manager import mcp_manager
    from .external_apis import (
        openai_chat_completions,
        calculate_openai_cost,
        claude_messages,
        calculate_claude_cost
    )
    from .openai_handler import handle_openai_chat
    from .models import (
        ChatRequest,
        GenerateRequest,
        OpenAICompletionsRequest,
        ModelsListResponse,
        ModelInfo
    )
except ImportError:
    from database import get_db_session, init_db, PricingConfig, ModelMetadata, Customer, DeviceRegistration, APIKey
    from auth import get_current_customer, hash_api_key
    from ollama_client import list_models, chat, chat_stream, generate, check_ollama_health
    from usage import calculate_cost, log_usage, check_budget
    from mcp_manager import mcp_manager
    from external_apis import (
        openai_chat_completions,
        calculate_openai_cost,
        claude_messages,
        calculate_claude_cost
    )
    from openai_handler import handle_openai_chat
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

# Background task for monitoring
import asyncio

async def monitor_lines_loop():
    """
    Background task to monitor line movements periodically.
    Runs every 15 minutes (900 seconds).
    """
    logger.info("Starting background monitoring task...")

    # Sports to monitor
    sports_to_monitor = [
        "americanfootball_nfl",
        "americanfootball_ncaaf",
        "basketball_nba",
        "basketball_ncaab",
        "baseball_mlb"
    ]

    # Ensure tools are loaded
    try:
        logger.info("Refreshing tool list for monitoring task...")
        await mcp_manager.get_tools_ollama_format()
    except Exception as e:
        logger.error(f"Failed to refresh tools: {e}")

    try:
        while True:
            try:
                logger.info("Running scheduled line movement check...")

                for sport in sports_to_monitor:
                    logger.info(f"Checking {sport}...")

                    # 1. Check if we have opening lines (baseline) for this sport
                    from pathlib import Path
                    import json
                    opening_file = Path("/mcp_servers/betting_monitor/data/opening_lines.json")

                    has_opening = False
                    if opening_file.exists():
                        try:
                            data = json.load(open(opening_file))
                            if sport in data:
                                has_opening = True
                        except:
                            pass

                    if not has_opening:
                        logger.info(f"No opening lines found for {sport}. Taking initial snapshot...")
                        result = await mcp_manager.execute_tool("get_opening_lines", {
                            "sport": sport,
                            "hours_ago": 48
                        })
                        logger.info(f"Snapshot result ({sport}): {result}")

                    # 2. Check for line movements (compare to opening)
                    result = await mcp_manager.execute_tool("compare_to_opening", {"sport": sport})
                    logger.info(f"Line movement check ({sport}): {result}")

                    # 3. Check for steam moves (last 30 min)
                    result = await mcp_manager.execute_tool("detect_steam_moves", {"sport": sport})
                    logger.info(f"Steam check ({sport}): {result}")

                logger.info("Scheduled check complete.")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            # Wait for next interval (5 minutes)
            await asyncio.sleep(300)

    except asyncio.CancelledError:
        logger.info("Monitoring task cancelled")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and MCP servers on startup."""
    init_db()
    await mcp_manager.start_servers()
    logger.info("Database initialized and MCP servers started")

    # Start monitoring task
    asyncio.create_task(monitor_lines_loop())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    await mcp_manager.cleanup()
    logger.info("MCP servers stopped")

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


# ============================================================================
# Device Registration Endpoints (for frontend authentication)
# ============================================================================

class RegisterDeviceRequest(BaseModel):
    api_key: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None

class VerifyDeviceRequest(BaseModel):
    device_token: str


@app.post("/api/register-device")
async def register_device(
    request: RegisterDeviceRequest,
    db: Session = Depends(get_db_session)
):
    """
    Register a device with an API key.
    Returns a device token that can be used for future authentication.
    """
    try:
        # Validate the API key
        key_hash = hash_api_key(request.api_key)
        api_key_record = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.active == True
        ).first()

        if not api_key_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        # Check if customer is active
        customer = api_key_record.customer
        if not customer.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Customer account is inactive"
            )

        # Generate a unique device token
        device_token = f"dt_{secrets.token_urlsafe(32)}"

        # Create device registration
        device_reg = DeviceRegistration(
            device_token=device_token,
            api_key_id=api_key_record.id,
            device_name=request.device_name,
            device_type=request.device_type
        )
        db.add(device_reg)
        db.commit()

        logger.info(f"Device registered for customer {customer.name} (API key ID: {api_key_record.id})")

        return {
            "success": True,
            "device_token": device_token,
            "customer_name": customer.name,
            "message": "Device registered successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering device: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device"
        )


@app.post("/api/verify-device")
async def verify_device(
    request: VerifyDeviceRequest,
    db: Session = Depends(get_db_session)
):
    """
    Verify a device token and return the associated API key info.
    Used by frontend to check if a device is already registered.
    """
    try:
        # Find device registration
        device_reg = db.query(DeviceRegistration).filter(
            DeviceRegistration.device_token == request.device_token,
            DeviceRegistration.active == True
        ).first()

        if not device_reg:
            return {
                "valid": False,
                "message": "Device not registered"
            }

        # Check if API key is still active
        api_key = device_reg.api_key
        if not api_key.active:
            return {
                "valid": False,
                "message": "API key has been revoked"
            }

        # Check if customer is active
        customer = api_key.customer
        if not customer.active:
            return {
                "valid": False,
                "message": "Customer account is inactive"
            }

        # Update last used timestamp
        device_reg.last_used = datetime.utcnow()
        db.commit()

        return {
            "valid": True,
            "customer_name": customer.name,
            "device_name": device_reg.device_name,
            "api_key_id": api_key.id,
            "message": "Device verified"
        }

    except Exception as e:
        logger.error(f"Error verifying device: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify device"
        )


@app.delete("/api/device/{device_token}")
async def revoke_device(
    device_token: str,
    db: Session = Depends(get_db_session)
):
    """
    Revoke a device registration.
    """
    try:
        device_reg = db.query(DeviceRegistration).filter(
            DeviceRegistration.device_token == device_token
        ).first()

        if not device_reg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )

        device_reg.active = False
        db.commit()

        return {
            "success": True,
            "message": "Device revoked successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking device: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke device"
        )


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

    # Add OpenAI models if key is configured
    if os.getenv("OPENAI_API_KEY"):
        model_list.append(ModelInfo(
            id="gpt-4o",
            name="gpt-4o",
            pricing_configured=True
        ))

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

    # Add OpenAI models if key is configured
    if os.getenv("OPENAI_API_KEY"):
        model_list.append({
            "id": "gpt-4o",
            "object": "model",
            "created": int(datetime.utcnow().timestamp()),
            "owned_by": "openai",
            "pricing_configured": True
        })

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
    """Ollama chat endpoint with streaming support."""
    customer, api_key = customer_data

    # Check budget
    within_budget, spending, budget_limit = check_budget(customer.id, db)
    if not within_budget:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Budget exceeded. Current spending: ${spending:.2f}, Budget: ${budget_limit:.2f}"
        )


    # Get available tools
    tools = await mcp_manager.get_tools_ollama_format()

    # Inject system message if tools are available and not already present
    messages_with_system = request.messages.copy()

    # Get current time for context
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    if tools and (not messages_with_system or messages_with_system[0].get("role") != "system"):
        system_message = {
            "role": "system",
            "content": f"""You are an ELITE PROFESSIONAL sports betting analyst. Your goal is to help users make INFORMED, DATA-DRIVEN betting decisions.

CURRENT DATE/TIME: {current_time}

═══════════════════════════════════════════════════════════════
YOUR MISSION: SYNTHESIZE ALL DATA INTO ACTIONABLE RECOMMENDATIONS
═══════════════════════════════════════════════════════════════

When a user asks about betting on a game, you should:
1. Get LIVE ODDS (get_odds)
2. Get TEAM STATS & INJURIES (get_nfl_team_stats, get_nfl_injuries)
3. Apply STRATEGY KNOWLEDGE (search_guides)
4. Provide a COMPREHENSIVE ANALYSIS with specific bet recommendations

═══════════════════════════════════════════════════════════════
AVAILABLE TOOLS
═══════════════════════════════════════════════════════════════

**get_odds(sport, team)** - LIVE betting lines from major sportsbooks
  • Use for: Getting current spreads, moneylines, totals for a specific team
  • Sports: "americanfootball_nfl", "americanfootball_ncaaf", "basketball_nba", "basketball_ncaab", "baseball_mlb"
  • Example: get_odds(sport="basketball_nba", team="Lakers")

**get_team_stats(sport, team_name)** - Team record, standing, next game
  • Use for: Understanding team context, home/away, record
  • Sports: "nfl", "ncaaf", "nba", "ncaam", "mlb"
  • Example: get_team_stats(sport="nba", team_name="Lakers")

**get_injuries(sport, team_name)** - Current injury/roster news
  • Use for: Identifying key players out/questionable/transfers
  • Example: get_injuries(sport="nba", team_name="LeBron James") (Team name works best)

**get_weekend_slate(sport)** - ALL games with full odds
  • Use for: "What's good this weekend?", "Best bets?", "Any opportunities?"
  • Returns all upcoming games with spreads, moneylines, totals
  • Example: get_weekend_slate(sport="americanfootball_nfl")

**find_teaser_candidates(sport)** - Auto-find Wong teaser qualifiers
  • Use for: Finding games that qualify for Wong teasers
  • Example: find_teaser_candidates(sport="americanfootball_nfl")

**get_value_finder(sport)** - Scan all games for value
  • Use for: Finding key number positions, teaser candidates, big underdogs
  • Example: get_value_finder(sport="americanfootball_nfl")

**detect_line_movements(sport)** - Line movement alerts
  • Use for: Checking for significant spread/total movements
  • Example: detect_line_movements(sport="americanfootball_nfl")

**get_sharp_action_indicators(sport)** - Sharp money signals
  • Use for: Detecting steam moves, RLM patterns, key number traps
  • Example: get_sharp_action_indicators(sport="americanfootball_nfl")

**get_game_weather(home_team, game_time_iso)** - Stadium weather forecast
  • Use for: Checking wind/rain impact on Totals (Over/Under)
  • Example: get_game_weather(home_team="Bills")

**snapshot_lines(sport)** - Save current lines for tracking
  • Use for: Establishing baseline for line movement detection
  • Example: snapshot_lines(sport="americanfootball_nfl")

**search_guides(query)** - Strategy knowledge base
  • Use for: Key numbers, situational spots, bankroll advice, prop strategies
  • Example: search_guides("Wong teaser strategy")

**read_guide(filename)** - Full strategy guide
  • Files available:
    - nfl_betting_strategy.md (key numbers, QB value, situational betting, weather)
    - player_props_strategy.md (QB/RB/WR props, PrizePicks strategy, correlations)
    - parlay_portfolio_strategy.md (Wong teasers, SGP strategy, bankroll allocation)
    - line_shopping_value.md (CLV, EV calculation, odds comparison)
    - bankroll_management.md (unit sizing, Kelly criterion, drawdown rules)
    - ncaa_betting_strategy.md (college-specific angles)
    - betting_glossary.md (terms and definitions)

═══════════════════════════════════════════════════════════════
RESPONSE FORMAT FOR GAME ANALYSIS
═══════════════════════════════════════════════════════════════

When analyzing a specific game, structure your response as:

## 📊 [MATCHUP] Team A vs Team B
**Game Time**: [date/time]

### Current Lines
| Book | Spread | ML | Total |
|------|--------|----|----|
| [Book 1] | X | X | X |
| [Book 2] | X | X | X |

### Key Factors
- **Team A**: [record, injuries, situational spot]
- **Team B**: [record, injuries, situational spot]
- **Edge Identified**: [key number, RLM, weather, etc.]

### 🎯 RECOMMENDED BETS
1. **[PRIMARY BET]**: [Spread/ML/Total] @ [odds] - [confidence: 1-3u]
   - Rationale: [why this is the play]

2. **[SECONDARY BET]** (if applicable): [description]

3. **[PLAYER PROP]** (if applicable): [player] O/U [line]

### ⚠️ Risk Factors
- [What could go wrong]

### 💰 Bankroll Note
- [Unit sizing recommendation based on confidence]

═══════════════════════════════════════════════════════════════
KEY ANALYSIS RULES
═══════════════════════════════════════════════════════════════

1. **KEY NUMBERS**: In NFL, 3 and 7 are crucial. Getting +3.5 vs +2.5 is a 15% swing.

2. **CALCULATE IMPLIED PROBABILITY**:
   - Negative odds: |odds| / (|odds| + 100) = implied %
   - Positive odds: 100 / (odds + 100) = implied %
   - Example: -150 → 150/250 = 60% implied

3. **IDENTIFY VALUE**: If your estimated probability > implied probability = +EV bet

4. **SITUATIONAL SPOTS**: Look for:
   - Lookahead spots (weak opponent before big game)
   - Revenge games
   - Short rest (TNF road teams)
   - West Coast teams at 1pm ET

5. **WEATHER IMPACT**: Wind 15+ mph = strong Under lean

6. **NEVER**:
   - Fabricate odds or game data
   - Recommend parlays without explaining the math
   - Suggest bets without live data backing
   - Ignore injury impact on the line

═══════════════════════════════════════════════════════════════
TOOL USAGE RULES
═══════════════════════════════════════════════════════════════

FOR "WHAT'S GOOD THIS WEEKEND?" / "BEST BETS?":
1. Call get_weekend_slate() for ALL games
2. Call find_teaser_candidates() for Wong teaser options
3. Call get_value_finder() for key number opportunities
4. Call detect_line_movements() for recent line changes
5. Synthesize into TOP 3-5 recommended plays with rationale

FOR "ANALYZE THIS LINE MOVEMENT" / "WHY DID LINE MOVE?":
1. Call get_odds(sport, team) for current status
2. Call detect_line_movements() to confirm the move magnitude
3. Call get_injuries(sport, team) for BOTH teams (often the cause)
4. Call get_team_stats(sport, team) to check record/standings
5. Call get_game_weather(home_team) for outdoor games
6. Call search_guides("line movement analysis") for general theory if needed
7. EXPLAIN the move in the final response (Injury? Sharp money? Weather?)

FOR SPECIFIC GAME QUESTIONS ("What should I bet on Chiefs?"):
1. Call get_odds() for live lines
2. Call get_team_stats() for both teams
3. Call get_injuries() for both teams
4. Call get_game_weather(home_team) for outdoor games
5. Call search_guides() if situational factor applies
6. Synthesize into recommendation

FOR "ANY LINE MOVEMENT?" / "SHARP ACTION?" QUESTIONS:
1. Call detect_line_movements() for recent changes
2. Call get_sharp_action_indicators() for steam/RLM
3. Call get_alerts_history() for recent alerts

FOR STRATEGY QUESTIONS ("How do teasers work?"):
→ Use search_guides() or read_guide() ONLY
→ DO NOT call get_odds()

FOR PROPS/PRIZEPICKS QUESTIONS:
→ Use search_guides("player props") or read_guide("player_props_strategy.md")
→ Explain correlation, matchup adjustments, game script impact"""
        }
        messages_with_system.insert(0, system_message)

    # Route to OpenAI if model is GPT
    if request.model.startswith("gpt-"):
        try:
            result = await handle_openai_chat(
                request=request,
                messages_with_system=messages_with_system,
                tools=tools,
                mcp_manager=mcp_manager,
                openai_chat_completions=openai_chat_completions
            )

            # Wrap in streaming response if requested
            if request.stream:
                async def fake_stream():
                    yield json.dumps(result).encode() + b"\n"

                return StreamingResponse(fake_stream(), media_type="application/x-ndjson")
            else:
                return result

        except Exception as e:
            logger.error(f"OpenAI error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"OpenAI Error: {str(e)}")

    try:
        # Calculate and log cost upfront (for streaming we can't wait)
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

        # FORCE NON-STREAMING loop first to handle tools
        # If we stream immediately, we can't intercept tool calls easily.
        # This is a compromise: we wait for the full response (potentially including tool calls)
        # before sending anything back.

        # Force low temperature for tool calling to improve consistency
        tool_call_options = request.options.copy() if request.options else {}
        if "temperature" not in tool_call_options:
            tool_call_options["temperature"] = 0.1  # Low temp for deterministic tool calling

        response = await chat(
            model=request.model,
            messages=messages_with_system,
            stream=False,
            options=tool_call_options,
            tools=tools if tools else None
        )

        # Handle tool calls with loop (support recursive calling)
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        messages = messages_with_system.copy()

        while response.get("message", {}).get("tool_calls") and iteration < max_iterations:
            iteration += 1
            tool_calls = response["message"]["tool_calls"]

            logger.info(f"Tool calls detected (iteration {iteration}): {[tc.get('function', {}).get('name') for tc in tool_calls]}")

            # Append assistant's tool call message to history
            messages.append(response["message"])

            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                name = function.get("name")
                args = function.get("arguments", {})

                # Execute tool
                logger.info(f"Executing tool: {name} with args: {args}")
                result = await mcp_manager.execute_tool(name, args)
                logger.info(f"Tool result length: {len(str(result))} chars")

                # Add result message
                messages.append({
                    "role": "tool",
                    "content": str(result)
                })

            # Call chat again with accumulated tool results
            # Add a stronger instruction to use the tool data correctly
            messages.append({
                "role": "system",
                "content": """You have received REAL-TIME DATA from your tools. NOW SYNTHESIZE this into a PRO-LEVEL BETTING ANALYSIS.

═══════════════════════════════════════════════════════════════
⚠️ ANALYSIS CHECKLIST (MANDATORY)
═══════════════════════════════════════════════════════════════

1. **DATA VALIDATION**:
   - Did you get odds? If not, why? (Check team name spellings if needed).
   - Did you get stats? If not, explicitly state "Stats unavailable" but try to infer from odds.
   - **INJURIES**: If a line moved > 2 pts and you found "No injuries", DOUBLE CHECK. Is there a QB change? Suspension? If tool says "No info", state "No reported injuries found via API, but line move suggests hidden factor."

2. **LINE MOVEMENT DEEP DIVE**:
   - **WHY did it move?** Don't just say "It moved."
   - HYPOTHESIZE:
     - Crossing 0 (Fav flip)? -> Major sentiment shift.
     - Crossing 3 or 7? -> Key number protection.
     - Steam (rapid move)? -> Syndicate/Sharp action.
   - **Correlation**: Does the Total move match the Spread move? (e.g., Fav spreads -2 -> -4 AND Total drops -> Defense/Weather upgrade).

3. **IMPLIED PROBABILITY & EV**:
   - Calculate implied % for EVERY recommended bet.
   - Compare to your estimated win probability.
   - Example: "Line -110 (52.4%) vs Estimated Win 60% = +EV"

4. **CONTEXTUAL FACTORS**:
   - **Venue**: Dome? Outdoors? (Impacts totals).
   - **Rest**: Bye week? Short week (TNF)?
   - **Motivation**: Playoff spot? Tanking?

═══════════════════════════════════════════════════════════════
FORMAT YOUR RESPONSE
═══════════════════════════════════════════════════════════════

## 📊 [MATCHUP] Analysis
**Time**: [Date/Time] | **Venue**: [Stadium/Type]

### 1. The Setup (Facts)
- **Current Line**: [Spread] | [Total]
- **Movement**: [Describe move]
- **Key Injuries**: [List or "None reported"]

### 2. The "WHY" (Analysis)
- [Explain the market logic. Why is the line here? Why did it move?]
- [Mention Sharp vs Public splits if evident]

### 3. 🎯 EDGE & RECOMMENDATION
- **Primary Bet**: [Selection] @ [Odds] ([Units]u)
- **Confidence**: [Low/Med/High] because [Rationale]
- **Value**: Implied [X]% vs Estimated [Y]%

### 4. Risks
- [What kills this bet?]

═══════════════════════════════════════════════════════════════
DO NOT:
- Output raw JSON
- Suggest "check later" - give the best advice NOW based on current data
- Ignore the "Why"
- Recommend parlays unless highly correlated (+EV)"""
            })

            logger.info(f"Making follow-up chat call with {len([m for m in messages if m.get('role') == 'tool'])} tool result(s)...")
            response = await chat(
                model=request.model,
                messages=messages,
                stream=False,
                options=request.options,
                tools=None  # Disable tools to force an actual answer
            )

        # At this point, we have the final response (no more tool calls)
        if iteration > 0:
            logger.info(f"Tool calling completed after {iteration} iteration(s)")

        # Return based on stream preference
        if request.stream:
            # Fake stream the already-complete response
            async def fake_stream():
                yield json.dumps(response).encode() + b"\n"

            return StreamingResponse(fake_stream(), media_type="application/x-ndjson")
        else:
            return response

        # No tool calls in the first response
        if request.stream:
            # We already have the full response in 'response', so we can't "stream" it from Ollama again
            # without making a new request (wasteful).
            # Hack: Fake stream it back.
            async def fake_stream():
                 yield json.dumps(response).encode() + b"\n"

            return StreamingResponse(fake_stream(), media_type="application/x-ndjson")
        else:
            return response

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/show")
async def ollama_show(
    request: dict,
    customer_data: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db_session)
):
    """Ollama show model info endpoint - proxies to Ollama."""
    try:
        model_name = request.get("name", request.get("model", ""))
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')}/api/show",
                json={"name": model_name}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama returned {response.status_code}"
                )
    except httpx.HTTPError as e:
        logger.error(f"Error in show endpoint: {e}")
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
async def openai_chat_completions_endpoint(
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


# OpenAI-compatible endpoint for Ollama models
@app.post("/v1/ollama/chat/completions")
async def ollama_openai_chat_completions(
    request: OpenAICompletionsRequest,
    customer_data: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db_session)
):
    """OpenAI-compatible chat completions endpoint that uses Ollama models."""
    customer, api_key = customer_data

    # Check budget
    within_budget, spending, budget_limit = check_budget(customer.id, db)
    if not within_budget:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Budget exceeded. Current spending: ${spending:.2f}, Budget: ${budget_limit:.2f}"
        )

    # Calculate and log cost upfront
    cost = calculate_cost(request.model, "/v1/ollama/chat/completions", db)
    log_usage(
        customer_id=customer.id,
        api_key_id=api_key.id,
        endpoint="/v1/ollama/chat/completions",
        model=request.model,
        cost=cost,
        db=db,
        metadata=json.dumps({"stream": request.stream})
    )

    try:
        # Convert OpenAI format to Ollama format
        options = {}
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens
        if request.top_p is not None:
            options["top_p"] = request.top_p

        if request.stream:
            # Return streaming response in OpenAI SSE format
            async def generate_sse():
                chat_id = f"chatcmpl-{api_key.id}-{customer.id}-{int(datetime.now(timezone.utc).timestamp())}"
                async for chunk in chat_stream(
                    model=request.model,
                    messages=request.messages,
                    options=options if options else None
                ):
                    try:
                        # Parse Ollama NDJSON chunk
                        ollama_chunk = json.loads(chunk.decode().strip())
                        content = ollama_chunk.get("message", {}).get("content", "")
                        done = ollama_chunk.get("done", False)

                        # Convert to OpenAI SSE format
                        openai_chunk = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": int(datetime.now(timezone.utc).timestamp()),
                            "model": request.model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": content} if content else {},
                                    "finish_reason": "stop" if done else None
                                }
                            ]
                        }
                        yield f"data: {json.dumps(openai_chunk)}\n\n"

                        if done:
                            yield "data: [DONE]\n\n"
                    except json.JSONDecodeError:
                        continue

            return StreamingResponse(
                generate_sse(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # Non-streaming response
            ollama_response = await chat(
                model=request.model,
                messages=request.messages,
                stream=False,
                options=options if options else None
            )

            # Convert non-streaming response
            openai_response = {
                "id": f"chatcmpl-{api_key.id}-{customer.id}",
                "object": "chat.completion",
                "created": int(datetime.now(timezone.utc).timestamp()),
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": ollama_response.get("message", {}).get("role", "assistant"),
                            "content": ollama_response.get("message", {}).get("content", "")
                        },
                        "finish_reason": ollama_response.get("done", True) and "stop" or "length"
                    }
                ],
                "usage": {
                    "prompt_tokens": ollama_response.get("prompt_eval_count", 0),
                    "completion_tokens": ollama_response.get("eval_count", 0),
                    "total_tokens": (ollama_response.get("prompt_eval_count", 0) +
                                   ollama_response.get("eval_count", 0))
                }
            }

            return openai_response

    except Exception as e:
        logger.error(f"Error in Ollama OpenAI chat completions: {e}", exc_info=True)
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


# ============================================================================
# Betting Alerts Endpoint
# ============================================================================

@app.get("/api/alerts")
async def get_betting_alerts(
    limit: int = 20,
    customer_data: tuple = Depends(get_current_customer)
):
    """
    Get recent betting alerts (line movements, steam moves, etc.)
    Reads from the betting_monitor MCP server's alert storage.
    """
    try:
        from pathlib import Path
        alerts_file = Path("/mcp_servers/betting_monitor/data/alerts.json")

        if not alerts_file.exists():
            return {"alerts": [], "message": "No alerts yet. Run line monitoring tools first."}

        with open(alerts_file, 'r') as f:
            data = json.load(f)

        alerts = data.get('alerts', [])[:limit]
        last_updated = data.get('last_updated', None)

        return {
            "alerts": alerts,
            "count": len(alerts),
            "last_updated": last_updated
        }
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return {"alerts": [], "error": str(e)}


@app.post("/api/alerts/check")
async def trigger_alert_check(
    customer_data: tuple = Depends(get_current_customer)
):
    """
    Trigger a manual check for line movements and steam moves.
    This calls the betting_monitor MCP tools.
    """
    try:
        results = {}

        # Check for line movements (compare to opening)
        movement_result = await mcp_manager.execute_tool("compare_to_opening", {"sport": "americanfootball_nfl"})
        results["line_movements"] = movement_result

        # Check for steam moves (last 30 min)
        steam_result = await mcp_manager.execute_tool("detect_steam_moves", {"sport": "americanfootball_nfl"})
        results["steam_moves"] = steam_result

        return {
            "status": "checked",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/snapshot")
async def take_opening_snapshot(
    hours_ago: int = 48,
    customer_data: tuple = Depends(get_current_customer)
):
    """
    Take a snapshot of opening lines for comparison.
    Default: 48 hours ago (typical NFL line opening time).
    """
    try:
        result = await mcp_manager.execute_tool("get_opening_lines", {
            "sport": "americanfootball_nfl",
            "hours_ago": hours_ago
        })

        return {
            "status": "snapshot_taken",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": result
        }
    except Exception as e:
        logger.error(f"Error taking snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

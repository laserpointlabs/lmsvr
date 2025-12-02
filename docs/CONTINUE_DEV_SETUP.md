# Continue.dev Integration Guide

This guide shows how to configure Continue.dev (VS Code extension) to use Ollama models running in your API Gateway, optimized for **Agent Mode**.

**Reference:** [Continue.dev Agent Model Setup](https://docs.continue.dev/ide-extensions/agent/model-setup)

## Recommended Models for Continue.dev Agent Mode

Based on official Continue.dev Agent Mode documentation, here are the best open-source models for different roles:

### Agent Plan & Chat/Edit Models (Best Open Models)

These are the top-performing open-source models for Agent Mode planning and chat/edit tasks:

1. **Qwen3 Coder 30B** ⭐ **RECOMMENDED**
   - Model: `qwen3-coder:30b`
   - Size: ~18-20 GB VRAM
   - Best for: Agent Plan, Chat, Edit
   - **Note:** You already have this model loaded!

2. **Devstral 27B**
   - Model: `devstral`
   - Size: ~16-18 GB VRAM
   - Best for: Agent Plan, Chat, Edit
   - Alternative to Qwen3 Coder

3. **gpt-oss 20B**
   - Model: `gpt-oss:20b`
   - Size: ~12-14 GB VRAM
   - Best for: Agent Plan, Chat, Edit
   - Good balance of performance and size

### Autocomplete Models

4. **Qwen2.5-Coder 1.5B** ⭐ **RECOMMENDED**
   - Model: `qwen2.5-coder:1.5b-base`
   - Size: ~1.5 GB VRAM
   - Best for: Fast code autocompletion

5. **Qwen2.5-Coder 7B** (Alternative)
   - Model: `qwen2.5-coder:7b-base`
   - Size: ~4-5 GB VRAM
   - Best for: Higher quality autocomplete (slightly slower)

### Embeddings Model

6. **Nomic Embed Text** ⭐ **RECOMMENDED**
   - Model: `nomic-embed-text`
   - Size: ~274 MB VRAM
   - Best for: Code search and similarity detection

7. **Qwen3 Embedding** (Alternative)
   - Model: `qwen3-embedding`
   - Size: ~500 MB VRAM
   - Alternative embeddings model

### Apply Model (Optional)

8. **FastApply 15B**
   - Model: `fast-apply:15b-v10`
   - Size: ~9-10 GB VRAM
   - Best for: Fast code application/editing
   - **Note:** May require custom setup

## Optimal Configuration for 64GB VRAM (4x16GB GPUs)

With your hardware, you can run multiple large models simultaneously. Here's the recommended setup:

### Recommended Multi-Model Setup

```bash
# Agent Plan & Chat/Edit (pick one or two)
OLLAMA_PRELOAD_MODELS="qwen3-coder:30b,devstral,qwen2.5-coder:1.5b-base,nomic-embed-text"
```

**VRAM Distribution:**
- Qwen3 Coder 30B: ~18-20 GB (can use 1-2 GPUs)
- Devstral 27B: ~16-18 GB (can use 1-2 GPUs)
- Qwen2.5-Coder 1.5B: ~1.5 GB
- Nomic Embed Text: ~274 MB
- **Total: ~36-40 GB** (leaves room for other processes)

### Maximum Performance Setup (All Models)

If you want maximum performance and can dedicate most VRAM:

```bash
# Load all recommended models simultaneously
OLLAMA_PRELOAD_MODELS="qwen3-coder:30b,devstral,gpt-oss:20b,qwen2.5-coder:7b-base,nomic-embed-text"
```

**VRAM Distribution:**
- Qwen3 Coder 30B: ~18-20 GB
- Devstral 27B: ~16-18 GB
- gpt-oss 20B: ~12-14 GB
- Qwen2.5-Coder 7B: ~4-5 GB
- Nomic Embed Text: ~274 MB
- **Total: ~50-57 GB** (fits comfortably in 64GB)

## Setup Instructions

### 1. Pull Recommended Models

Pull the Agent Mode recommended models:

```bash
# Agent Plan & Chat/Edit models
docker exec ollama ollama pull qwen3-coder:30b
docker exec ollama ollama pull devstral
docker exec ollama ollama pull gpt-oss:20b

# Autocomplete models
docker exec ollama ollama pull qwen2.5-coder:1.5b-base
docker exec ollama ollama pull qwen2.5-coder:7b-base

# Embeddings
docker exec ollama ollama pull nomic-embed-text
docker exec ollama ollama pull qwen3-embedding
```

### 2. Configure Auto-Loading

Add to your `.env` file:

```bash
# Recommended Agent Mode setup (fits in 64GB VRAM)
OLLAMA_PRELOAD_MODELS="qwen3-coder:30b,devstral,qwen2.5-coder:1.5b-base,nomic-embed-text"
```

Or for maximum performance:

```bash
# Maximum performance setup
OLLAMA_PRELOAD_MODELS="qwen3-coder:30b,devstral,gpt-oss:20b,qwen2.5-coder:7b-base,nomic-embed-text"
```

### 3. Increase Max Loaded Models

With 64GB VRAM, you can increase the maximum number of loaded models:

```bash
# In your .env file
OLLAMA_MAX_LOADED_MODELS=6
```

### 4. Configure Continue.dev for Agent Mode

Edit your Continue.dev config file (usually `~/.continue/config.json` or `.continue/config.json`):

```json
{
  "models": [
    {
      "title": "Qwen3 Coder 30B",
      "provider": "ollama",
      "model": "qwen3-coder:30b",
      "roles": ["chat", "edit"]
    },
    {
      "title": "Devstral 27B",
      "provider": "ollama",
      "model": "devstral",
      "roles": ["chat", "edit"]
    },
    {
      "title": "Qwen2.5-Coder 1.5B",
      "provider": "ollama",
      "model": "qwen2.5-coder:1.5b-base",
      "roles": ["autocomplete"]
    },
    {
      "title": "Nomic Embed Text",
      "provider": "ollama",
      "model": "nomic-embed-text",
      "roles": ["embed"]
    }
  ],
  "allowAnonymousTelemetry": false
}
```

### 5. Restart Ollama

After updating your `.env` file:

```bash
docker compose restart ollama
```

## Model Roles Explained

- **chat**: Used for conversational interactions and code explanations
- **edit**: Used for code editing and modifications
- **autocomplete**: Used for inline code completion as you type
- **embed**: Used for semantic search and code similarity detection
- **Agent Plan**: Automatically uses chat models with tool calling support

## System Message Tools

Continue.dev uses an innovative "system message tools" approach that:
- Works with **any model** capable of following instructions (not just native tool-calling models)
- Provides consistent behavior across all providers
- Allows seamless switching between models
- **No additional configuration needed** - Continue automatically detects model capabilities

## Resource Requirements

### Your Setup (64GB VRAM - 4x16GB GPUs)

**Recommended Configuration:**
- **VRAM Usage**: ~36-40 GB
- **Models**: Qwen3 Coder 30B + Devstral + Qwen2.5-Coder 1.5B + Nomic Embed Text
- **Headroom**: ~24 GB for other processes

**Maximum Performance Configuration:**
- **VRAM Usage**: ~50-57 GB
- **Models**: All recommended models loaded simultaneously
- **Headroom**: ~7-14 GB for other processes

### GPU Distribution

Ollama will automatically distribute models across your 4 GPUs. You can verify GPU usage:

```bash
docker exec ollama nvidia-smi
```

## Verification

After setup, verify models are loaded:

```bash
docker exec ollama ollama ps
```

You should see all your models with "Forever" in the UNTIL column.

Check GPU utilization:

```bash
docker exec ollama nvidia-smi
```

## Troubleshooting

### Models Not Loading
- Check `OLLAMA_PRELOAD_MODELS` in `.env` file
- Verify models are pulled: `docker exec ollama ollama list`
- Check container logs: `docker compose logs ollama`
- Ensure `OLLAMA_MAX_LOADED_MODELS` is set high enough (try 6-8)

### Out of Memory Errors
- Reduce number of models in `OLLAMA_PRELOAD_MODELS`
- Use smaller models (e.g., Qwen2.5-Coder 1.5B instead of 7B)
- Check GPU memory: `docker exec ollama nvidia-smi`

### Continue.dev Can't Connect
- Verify Ollama is accessible: `curl http://localhost:11434/api/tags`
- Check firewall settings if connecting remotely
- Ensure port 11434 is exposed in docker-compose.yml

### Agent Mode Not Working
- Ensure you're using models that support tool calling (Qwen3 Coder, Devstral, etc.)
- Check Continue.dev logs for errors
- Verify model roles are correctly configured in Continue.dev config

## Model Comparison

| Model | Size | Best For | VRAM | Speed |
|-------|------|----------|------|-------|
| Qwen3 Coder 30B | 18-20 GB | Agent Plan, Chat, Edit | High | Fast |
| Devstral 27B | 16-18 GB | Agent Plan, Chat, Edit | High | Fast |
| gpt-oss 20B | 12-14 GB | Agent Plan, Chat, Edit | Medium | Medium |
| Qwen2.5-Coder 7B | 4-5 GB | Autocomplete | Medium | Very Fast |
| Qwen2.5-Coder 1.5B | 1.5 GB | Autocomplete | Low | Very Fast |
| Nomic Embed Text | 274 MB | Embeddings | Low | Very Fast |

## References

- [Continue.dev Agent Model Setup](https://docs.continue.dev/ide-extensions/agent/model-setup)
- [Continue.dev Ollama Documentation](https://docs.continue.dev/customize/model-providers/ollama/)
- [Ollama Model Library](https://ollama.com/library)
- [Continue.dev Model Capabilities](https://docs.continue.dev/reference/model-capabilities)

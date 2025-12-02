# Continue.dev Setup Guide

Use LaserPoint Labs AI models with [Continue.dev](https://continue.dev/) - the open-source AI code assistant for VS Code and JetBrains IDEs.

## Quick Setup

### Step 1: Save Your API Key

#### Linux / macOS

Open a terminal and run:

```bash
mkdir -p ~/.continue && echo "LMAPI_KEY=YOUR_API_KEY" > ~/.continue/.env
```

#### Windows (PowerShell)

Open PowerShell and run:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.continue"
Set-Content -Path "$env:USERPROFILE\.continue\.env" -Value "LMAPI_KEY=YOUR_API_KEY"
```

#### Windows (Command Prompt)

Open Command Prompt and run:

```cmd
mkdir %USERPROFILE%\.continue
echo LMAPI_KEY=YOUR_API_KEY > %USERPROFILE%\.continue\.env
```

**Replace `YOUR_API_KEY` with the key you were given.**

#### Alternative: Set as System Environment Variable

You can also set `LMAPI_KEY` as a system environment variable instead of using the `.env` file.

**Linux / macOS** - Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):
```bash
echo 'export LMAPI_KEY=YOUR_API_KEY' >> ~/.bashrc
source ~/.bashrc
```

**Windows (GUI):**
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Go to **Advanced** tab → **Environment Variables**
3. Under **User variables**, click **New**
4. Variable name: `LMAPI_KEY`
5. Variable value: `YOUR_API_KEY`
6. Click OK, then restart VS Code

**Windows (PowerShell - permanent):**
```powershell
[Environment]::SetEnvironmentVariable("LMAPI_KEY", "YOUR_API_KEY", "User")
```

Then restart VS Code to pick up the new environment variable.

### Step 2: Add Config to Your Project

Create the config directory in your project:

**Linux / macOS:**
```bash
mkdir -p .continue/agents
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path ".continue\agents"
```

**Windows (Command Prompt):**
```cmd
mkdir .continue\agents
```

Then save the following as `.continue/agents/config.yaml`:

```yaml
name: LaserPoint Labs API Gateway
version: 1.0.0
schema: v1

models:
  - name: Qwen3 Coder 30B
    provider: openai
    model: qwen3-coder:30b
    apiBase: https://lmapi.laserpointlabs.com/v1/ollama
    apiKey: ${{ secrets.LMAPI_KEY }}
    roles:
      - chat
      - edit
      - apply
    defaultCompletionOptions:
      temperature: 0.7
      maxTokens: 4096
    requestOptions:
      timeout: 300

  - name: Devstral 27B
    provider: openai
    model: devstral
    apiBase: https://lmapi.laserpointlabs.com/v1/ollama
    apiKey: ${{ secrets.LMAPI_KEY }}
    roles:
      - chat
      - edit
      - apply
    defaultCompletionOptions:
      temperature: 0.7
      maxTokens: 4096
    requestOptions:
      timeout: 300

  - name: GPT-OSS 20B
    provider: openai
    model: gpt-oss:20b
    apiBase: https://lmapi.laserpointlabs.com/v1/ollama
    apiKey: ${{ secrets.LMAPI_KEY }}
    roles:
      - chat
      - edit
      - apply
    defaultCompletionOptions:
      temperature: 0.7
      maxTokens: 4096
    requestOptions:
      timeout: 300

context:
  - provider: file
  - provider: code
  - provider: diff
  - provider: terminal

rules:
  - Be concise and helpful in responses
  - Focus on code quality and best practices
  - When editing code, maintain existing patterns and style
```

### Step 3: Restart VS Code

Reload your VS Code window (`Ctrl+Shift+P` → "Developer: Reload Window") or restart VS Code completely.

## You're Done!

Open Continue.dev (click the Continue icon in the sidebar) and you should see the models available:

- **Qwen3 Coder 30B** - Best for code generation and complex tasks
- **Devstral 27B** - Great alternative for coding tasks  
- **GPT-OSS 20B** - Good balance of speed and quality

## Available Models

| Model | Size | Best For |
|-------|------|----------|
| Qwen3 Coder 30B | 30B | Code generation, refactoring, complex edits |
| Devstral 27B | 27B | Code generation, debugging, explanations |
| GPT-OSS 20B | 20B | General coding assistance, faster responses |

## Troubleshooting

### "401 Invalid API Key"

1. Check that the `.env` file exists:

   **Linux / macOS:**
   ```bash
   cat ~/.continue/.env
   ```
   
   **Windows (PowerShell):**
   ```powershell
   Get-Content "$env:USERPROFILE\.continue\.env"
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   type %USERPROFILE%\.continue\.env
   ```
   
   It should show: `LMAPI_KEY=sk_...`

2. Make sure there are no extra spaces or quotes in the file

3. Restart VS Code completely (not just reload)

### No Response / Spinning Forever

1. Verify your config file is at `.continue/agents/config.yaml` (not `.continue/config.yaml`)

2. Make sure `provider: openai` is set (not `provider: ollama`)

3. Check your internet connection to `lmapi.laserpointlabs.com`

### Config Not Loading

1. The config must be inside your project folder at `.continue/agents/config.yaml`

2. Reload VS Code window after any config changes

## Test Your Connection

Run this in terminal to verify your API key works:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3-coder:30b","messages":[{"role":"user","content":"Say hello"}],"stream":false}' \
  https://lmapi.laserpointlabs.com/v1/ollama/chat/completions
```

You should see a JSON response with "Hello" in it.

## Need Help?

Contact your administrator for API key issues or access problems.


# Email Setup for API Key Delivery

## Gmail Configuration

To send API keys via email, you need to set up Gmail App Password authentication.

### Step 1: Enable 2-Step Verification

1. Go to your Google Account: https://myaccount.google.com
2. Click "Security" in the left sidebar
3. Under "Signing in to Google", enable "2-Step Verification"

### Step 2: Generate App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" as the app
3. Select "Other (Custom name)" as the device
4. Enter a name like "Bet Assistant CLI"
5. Click "Generate"
6. Copy the 16-character password (no spaces)

### Step 3: Configure Environment Variables

Add to your `.env` file:

```bash
GMAIL_USER=your-email@gmail.com
GMAIL_PASSWORD=your-16-char-app-password
```

Or export in your shell:

```bash
export GMAIL_USER=your-email@gmail.com
export GMAIL_PASSWORD=your-16-char-app-password
```

## Usage

### Generate and Email API Key

```bash
# Using environment variables
python cli/cli.py generate-key 1 --send-email

# Or specify credentials directly (less secure)
python cli/cli.py generate-key 1 --send-email \
    --gmail-user your-email@gmail.com \
    --gmail-password your-app-password
```

### Generate Without Email (default)

```bash
python cli/cli.py generate-key 1
```

## Security Notes

- **Never commit** `.env` file with Gmail credentials
- Use App Passwords, not your regular Gmail password
- App Passwords are more secure and can be revoked individually
- The API key is sent in plain text email (consider this for security)

## Troubleshooting

### "Error sending email"
- Verify 2-Step Verification is enabled
- Check App Password is correct (16 characters, no spaces)
- Ensure Gmail account allows "Less secure app access" is NOT needed (App Passwords replace this)

### "Gmail credentials not provided"
- Set environment variables or use `--gmail-user` and `--gmail-password` flags



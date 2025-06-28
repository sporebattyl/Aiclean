# 🔒 Secrets Management Setup

## Overview

This project uses a secure secrets management system to keep sensitive API keys and tokens out of version control while maintaining easy development workflow.

## 📁 File Structure

```
├── .env.mcp                    # Main MCP configuration (safe to commit)
├── .env.secrets.template       # Template for secrets (safe to commit)
├── .env.secrets               # Actual secrets (NEVER commit - in .gitignore)
└── SECRETS_SETUP.md           # This documentation
```

## 🚀 Quick Setup

### 1. Copy the Template
```bash
cp .env.secrets.template .env.secrets
```

### 2. Edit Your Secrets
Open `.env.secrets` and replace the placeholder values with your actual API keys:

```bash
# Example - replace with your actual tokens
export GITHUB_PERSONAL_ACCESS_TOKEN="github_pat_your_actual_token_here"
export BRAVE_API_KEY="BSA_your_actual_key_here"
export NOTION_TOKEN="ntn_your_actual_token_here"
```

### 3. Load the Configuration
```bash
source .env.mcp
```

The `.env.mcp` file will automatically load your secrets from `.env.secrets` if it exists.

## 🔑 Required API Keys

### GitHub Personal Access Token
- **Get from:** https://github.com/settings/tokens
- **Scopes needed:** `repo`, `user`, `gist`
- **Used for:** GitHub API integration, repository management

### Brave Search API Key
- **Get from:** https://brave.com/search/api/
- **Free tier:** 2,000 queries/month
- **Used for:** Web search functionality in MCP servers

### Notion Integration Token
- **Get from:** https://www.notion.so/my-integrations
- **Used for:** Notion workspace integration and database management
- **Page ID:** Already configured (non-sensitive)

## 🛡️ Security Features

### ✅ What's Protected
- All sensitive API keys and tokens are in `.env.secrets`
- `.env.secrets` is in `.gitignore` and will never be committed
- Template file provides clear guidance without exposing secrets
- Automatic fallback to placeholders if secrets file is missing

### ✅ What's Safe to Commit
- `.env.mcp` - Main configuration with placeholders
- `.env.secrets.template` - Template with placeholder values
- `SECRETS_SETUP.md` - This documentation
- Notion Page ID (non-sensitive identifier)

### ❌ What's Never Committed
- `.env.secrets` - Your actual API keys and tokens
- Any file containing real API keys or passwords

## 🔧 How It Works

1. **`.env.mcp`** sources **`.env.secrets`** if it exists
2. If **`.env.secrets`** is missing, it falls back to placeholder values
3. Clear warning messages guide users to set up their secrets
4. All sensitive information stays local to your development environment

## 📋 Usage Examples

### Loading Configuration
```bash
# Load all MCP configuration including secrets
source .env.mcp

# Verify tokens are loaded
echo "GitHub token: ${GITHUB_PERSONAL_ACCESS_TOKEN:0:10}..."
echo "Notion token: ${NOTION_TOKEN:0:10}..."
```

### Adding New Secrets
1. Add to `.env.secrets.template` with placeholder value
2. Add to your local `.env.secrets` with actual value
3. Update documentation if needed

## 🚨 Important Notes

- **Never commit `.env.secrets`** - It's in `.gitignore` for a reason
- **Always use the template** when setting up on new machines
- **Keep secrets file permissions restricted:** `chmod 600 .env.secrets`
- **Rotate tokens regularly** for security best practices

## 🆘 Troubleshooting

### "Warning: .env.secrets not found"
```bash
# Copy the template and edit it
cp .env.secrets.template .env.secrets
# Edit .env.secrets with your actual API keys
```

### "Permission denied" errors
```bash
# Fix file permissions
chmod 600 .env.secrets
```

### Tokens not loading
```bash
# Verify the file exists and has content
ls -la .env.secrets
cat .env.secrets

# Re-source the configuration
source .env.mcp
```

## 🎯 Benefits

- ✅ **Secure:** Sensitive data never enters version control
- ✅ **Simple:** Easy setup with clear instructions
- ✅ **Flexible:** Easy to add new secrets as needed
- ✅ **Robust:** Graceful fallback if secrets are missing
- ✅ **Team-friendly:** Template makes onboarding easy

**Your secrets are now properly managed and secure!** 🔒🎉

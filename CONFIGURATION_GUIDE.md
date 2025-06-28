# 🔧 MCP Services Configuration Guide

## Quick Setup for GitHub, Puppeteer, and Brave Search

### 🚀 One-Command Setup
```bash
./configure-mcp-services.sh
```

This interactive script will guide you through configuring all three services.

## 📋 Manual Configuration Steps

### 1. 🐙 GitHub MCP Server

**Get Your GitHub Token:**
1. Go to [GitHub Settings → Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (for repository access)
   - `user` (for user information)
   - `gist` (for gist operations)
4. Copy the generated token

**Set Environment Variable:**
```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
```

**Test:**
```bash
./start-mcp-server.sh github
```

### 2. 🤖 Puppeteer MCP Server

**Requirements:**
- ✅ Chromium browser (already installed)
- ✅ Node.js and npm (already installed)

**Configuration:**
```bash
export PUPPETEER_EXECUTABLE_PATH="/usr/bin/chromium-browser"
```

**Test:**
```bash
./start-mcp-server.sh puppeteer
```

### 3. 🔍 Brave Search MCP Server

**Get Your API Key:**
1. Go to [Brave Search API](https://brave.com/search/api/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier: 2,000 queries/month

**Set Environment Variable:**
```bash
export BRAVE_API_KEY="your_api_key_here"
```

**Test:**
```bash
./start-mcp-server.sh brave-search
```

## 🧪 Testing

### Test All Services
```bash
node test-individual-services.js
```

### Test Individual Services
```bash
# Test GitHub
GITHUB_PERSONAL_ACCESS_TOKEN=your_token ./start-mcp-server.sh github

# Test Puppeteer  
./start-mcp-server.sh puppeteer

# Test Brave Search
BRAVE_API_KEY=your_key ./start-mcp-server.sh brave-search
```

## 💾 Persistent Configuration

The configuration script creates `.env.mcp.configured` with your settings.

**Load configuration:**
```bash
source .env.mcp.configured
```

**Add to your shell profile for persistence:**
```bash
echo "source /root/addons/Aiclean/.env.mcp.configured" >> ~/.bashrc
```

## 🔧 Troubleshooting

### GitHub Issues
- **Token invalid**: Regenerate token with correct scopes
- **Rate limiting**: Use token to increase API limits

### Puppeteer Issues
- **Browser not found**: Check Chromium installation
- **Permissions**: Ensure Chromium can run in container

### Brave Search Issues
- **API key invalid**: Check key in Brave dashboard
- **Quota exceeded**: Monitor usage in dashboard

## 🎯 Next Steps

1. **Configure services**: Run `./configure-mcp-services.sh`
2. **Test functionality**: Run `node test-individual-services.js`
3. **Start using**: Use `./start-mcp-server.sh [service-name]`
4. **Integrate with MCP clients**: Connect to your preferred MCP client

## 📚 Service Capabilities

### GitHub MCP Server
- Repository management
- Issue and PR operations
- Code search and analysis
- User and organization data

### Puppeteer MCP Server
- Web scraping and automation
- Screenshot capture
- PDF generation
- Form interaction and testing

### Brave Search MCP Server
- Web search queries
- Real-time search results
- Privacy-focused search
- API-based search integration

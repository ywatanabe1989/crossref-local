# Remote MCP Deployment Guide

Run CrossRef Local as a persistent MCP server accessible over the network.

## Why HTTP Transport?

| SSH Transport | HTTP Transport |
|--------------|----------------|
| Claude Code hangs on connection failure | Graceful timeout/retry |
| Spawns new process per session | Persistent server |
| Shell management overhead | Clean HTTP protocol |
| Requires SSH key setup | Firewall-friendly |

**Note:** SSE transport is deprecated as of MCP spec 2025-03-26. Use HTTP (Streamable HTTP) instead.

## Quick Start

```bash
# Start MCP server with HTTP transport
CROSSREF_LOCAL_DB=/path/to/crossref.db \
crossref-local run-server-mcp -t http --host 0.0.0.0 --port 8082
```

Client configuration:
```json
{
  "mcpServers": {
    "crossref-remote": {
      "url": "http://your-server:8082/mcp"
    }
  }
}
```

## Systemd Service (Recommended)

For production deployment, use systemd to manage the service.

### 1. Edit the service file

```bash
# Copy and customize the service file
sudo cp examples/crossref-mcp.service /etc/systemd/system/

# Edit to match your setup
sudo nano /etc/systemd/system/crossref-mcp.service
```

Key settings to customize:
- `User` and `Group` - your user account
- `CROSSREF_LOCAL_DB` - path to your database
- `--port` - change if 8082 is in use

### 2. Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable crossref-mcp
sudo systemctl start crossref-mcp
```

### 3. Verify

```bash
# Check service status
sudo systemctl status crossref-mcp

# View logs
journalctl -u crossref-mcp -f

# Test endpoint
curl http://localhost:8082/mcp
```

## Docker Deployment

### Using Docker Compose

```yaml
# docker-compose.yml
services:
  crossref-mcp:
    image: python:3.11-slim
    command: >
      sh -c "pip install crossref-local[mcp] &&
             crossref-local run-server-mcp -t http --host 0.0.0.0 --port 8082"
    ports:
      - "8082:8082"
    volumes:
      - /path/to/crossref.db:/data/crossref.db:ro
    environment:
      - CROSSREF_LOCAL_DB=/data/crossref.db
    restart: unless-stopped
```

### Using Dockerfile

```dockerfile
FROM python:3.11-slim

RUN pip install crossref-local[mcp]

ENV CROSSREF_LOCAL_DB=/data/crossref.db

EXPOSE 8082

CMD ["crossref-local", "run-server-mcp", "-t", "http", "--host", "0.0.0.0", "--port", "8082"]
```

Build and run:
```bash
docker build -t crossref-mcp .
docker run -d \
  -p 8082:8082 \
  -v /path/to/crossref.db:/data/crossref.db:ro \
  --name crossref-mcp \
  crossref-mcp
```

## Client Configuration

### Claude Desktop / Claude Code

Add to your MCP configuration file:

```json
{
  "mcpServers": {
    "crossref-remote": {
      "url": "http://your-server:8082/mcp"
    }
  }
}
```

Configuration file locations:
- **Claude Desktop (macOS):** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Claude Desktop (Windows):** `%APPDATA%\Claude\claude_desktop_config.json`
- **Claude Code:** `.claude/settings.json` or `~/.claude/settings.json`

### Multiple Servers

You can configure both local and remote servers:

```json
{
  "mcpServers": {
    "crossref-local": {
      "command": "crossref-local",
      "args": ["run-server-mcp"],
      "env": {
        "CROSSREF_LOCAL_DB": "/local/path/crossref.db"
      }
    },
    "crossref-remote": {
      "url": "http://nas:8082/mcp"
    }
  }
}
```

## Security Considerations

### Firewall

Restrict access to trusted networks:

```bash
# UFW example
sudo ufw allow from 192.168.1.0/24 to any port 8082

# iptables example
iptables -A INPUT -p tcp --dport 8082 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8082 -j DROP
```

### Reverse Proxy with TLS

For production, use a reverse proxy with TLS:

```nginx
# /etc/nginx/sites-available/crossref-mcp
server {
    listen 443 ssl http2;
    server_name crossref.example.com;

    ssl_certificate /etc/letsencrypt/live/crossref.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/crossref.example.com/privkey.pem;

    location /mcp {
        proxy_pass http://127.0.0.1:8082;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

## Troubleshooting

### Service won't start

```bash
# Check logs
journalctl -u crossref-mcp -n 50

# Common issues:
# - Database path doesn't exist
# - Port already in use
# - Permission denied
```

### Connection refused

```bash
# Verify service is running
systemctl status crossref-mcp

# Check port is listening
ss -tlnp | grep 8082

# Test locally first
curl http://localhost:8082/mcp
```

### Claude Code hangs

If using SSH transport and experiencing hangs, switch to HTTP:

```json
// Before (SSH - can hang)
{
  "crossref-remote": {
    "command": "ssh",
    "args": ["nas", "crossref-local", "run-server-mcp"]
  }
}

// After (HTTP - recommended)
{
  "crossref-remote": {
    "url": "http://nas:8082/mcp"
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CROSSREF_LOCAL_DB` | Path to SQLite database | Auto-detect |
| `CROSSREF_LOCAL_MCP_HOST` | Host to bind | `localhost` |
| `CROSSREF_LOCAL_MCP_PORT` | Port to listen on | `8082` |

## References

- [MCP Transports Specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

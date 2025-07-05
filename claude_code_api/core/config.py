"""Configuration management for Claude Code API Gateway."""

import os
import shutil
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


def find_claude_binary() -> str:
    """Find Claude binary path automatically."""
    # First check environment variable
    if 'CLAUDE_BINARY_PATH' in os.environ:
        claude_path = os.environ['CLAUDE_BINARY_PATH']
        if os.path.exists(claude_path):
            return claude_path
    
    # Try to find claude in PATH - this should work for npm global installs
    claude_path = shutil.which("claude")
    if claude_path:
        return claude_path
    
    # Import npm environment if needed
    try:
        import subprocess
        # Try to get npm global bin path
        result = subprocess.run(['npm', 'bin', '-g'], capture_output=True, text=True)
        if result.returncode == 0:
            npm_bin_path = result.stdout.strip()
            claude_npm_path = os.path.join(npm_bin_path, 'claude')
            if os.path.exists(claude_npm_path):
                return claude_npm_path
    except Exception:
        pass
    
    # Check for Windows/WSL paths
    if os.path.exists("/root/.nvm/versions/node/v22.16.0/bin/claude"):
        return "/root/.nvm/versions/node/v22.16.0/bin/claude"
    
    # Fallback to common npm/nvm locations
    import glob
    common_patterns = [
        "/usr/local/bin/claude",
        "/usr/local/share/nvm/versions/node/*/bin/claude",
        "~/.nvm/versions/node/*/bin/claude",
        "/root/.nvm/versions/node/*/bin/claude",
    ]
    
    for pattern in common_patterns:
        expanded_pattern = os.path.expanduser(pattern)
        matches = glob.glob(expanded_pattern)
        if matches:
            # Return the most recent version
            return sorted(matches)[-1]
    
    return "claude"  # Final fallback


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_title: str = "Claude Code API Gateway"
    api_version: str = "1.0.0"
    api_description: str = "OpenAI-compatible API for Claude Code"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Authentication
    api_keys: List[str] = Field(default_factory=list)
    require_auth: bool = False
    
    @field_validator('api_keys', mode='before')
    def parse_api_keys(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(',') if x.strip()]
        return v or []
    
    # Claude Configuration  
    claude_binary_path: str = find_claude_binary()
    claude_api_key: str = ""
    default_model: str = "claude-3-5-sonnet-20241022"
    max_concurrent_sessions: int = 10
    session_timeout_minutes: int = 30
    
    # Project Configuration
    project_root: str = "/tmp/claude_projects"
    max_project_size_mb: int = 1000
    cleanup_interval_minutes: int = 60
    
    # Database Configuration
    database_url: str = "sqlite:///./claude_api.db"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    
    # CORS Configuration
    allowed_origins: List[str] = Field(default=["*"])
    allowed_methods: List[str] = Field(default=["*"])
    allowed_headers: List[str] = Field(default=["*"])
    
    @field_validator('allowed_origins', 'allowed_methods', 'allowed_headers', mode='before')
    def parse_cors_lists(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(',') if x.strip()]
        return v or ["*"]
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst: int = 10
    
    # Streaming Configuration
    streaming_chunk_size: int = 1024
    streaming_timeout_seconds: int = 300
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create global settings instance
settings = Settings()

# Ensure project root exists
os.makedirs(settings.project_root, exist_ok=True)

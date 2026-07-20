import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def authenticate(credentials: HTTPBasicCredentials = Security(security)):
    """Standard basic authentication for MCP web bridges."""
    correct_username = secrets.compare_digest(credentials.username, os.getenv("MCP_USER", "sandra"))
    correct_password = secrets.compare_digest(credentials.password, os.getenv("MCP_PASS", "sandra123"))

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

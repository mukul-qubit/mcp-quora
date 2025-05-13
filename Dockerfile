FROM python:3.12.3

WORKDIR /app
 
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

COPY . .

# For Azure, App Service provides PORT env; expose default 8080
EXPOSE 80

# Use MCP CLI with SSE transport instead of uvicorn
CMD ["python", "-m", "quora_api_tools"]

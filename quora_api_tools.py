from fastmcp import FastMCP
from typing import List, Dict, Optional, Any, Union
import http.client
import json
import os
import urllib.parse
import logging
import traceback
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('quora_api_tools')

# Create MCP server
mcp = FastMCP("QuoraProfiler")

# Get Quora API credentials from environment variables
QUORA_API_KEY = os.environ.get("QUORA_API_KEY", "xxxx")
QUORA_API_HOST = os.environ.get("QUORA_API_HOST", "quora-scraper.p.rapidapi.com")

# Helper function for making API requests with error handling
def make_api_request(method: str, endpoint: str, params: Dict = None, headers: Dict = None) -> Dict[str, Any]:
    """
    Makes an API request with error handling.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint
        params: Query parameters (for GET)
        headers: Request headers
        
    Returns:
        API response as a dictionary
    """
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    # Ensure headers are set
    if headers is None:
        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": QUORA_API_HOST,
            "x-rapidapi-key": QUORA_API_KEY
        }
    
    # Build query string for GET requests
    query_string = ""
    if params and method == "GET":
        query_string = "?" + urllib.parse.urlencode(params)
    
    # Log the request details (without sensitive info)
    sanitized_headers = {k: v for k, v in headers.items() if k.lower() not in ['x-rapidapi-key', 'authorization']}
    logger.info(f"API Request: {method} {endpoint}{query_string}")
    logger.debug(f"Headers: {sanitized_headers}")
    if params and method == "GET":
        logger.debug(f"Params: {params}")
    
    for attempt in range(MAX_RETRIES):
        try:
            # Create connection
            conn = http.client.HTTPSConnection(QUORA_API_HOST)
            
            # Set timeout to prevent hanging requests
            conn.timeout = 30
            
            # Make request
            conn.request(method, endpoint + query_string, None, headers)
            
            # Get response
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            
            # Log response status
            logger.info(f"API Response: {method} {endpoint}{query_string} - Status: {res.status}")
            
            # Parse response
            if data:
                try:
                    response_data = json.loads(data)
                    
                    # Log partial response for debugging
                    if isinstance(response_data, dict):
                        log_keys = list(response_data.keys())
                        logger.debug(f"Response keys: {log_keys}")
                    
                    # Check for API errors in response
                    if res.status >= 400:
                        error_msg = response_data.get('message', 'Unknown API error')
                        logger.error(f"API Error: {method} {endpoint}{query_string} - Status: {res.status} - Error: {error_msg}")
                        
                        # Return error response
                        return {
                            "success": False,
                            "status": res.status,
                            "message": error_msg,
                            "details": response_data
                        }
                    
                    # Return successful response
                    return {
                        "success": True,
                        "status": res.status,
                        "data": response_data
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"JSON Decode Error: {method} {endpoint}{query_string} - {str(e)}")
                    logger.error(f"Raw response: {data[:200]}..." if len(data) > 200 else f"Raw response: {data}")
                    
                    # Return error response
                    return {
                        "success": False,
                        "status": res.status,
                        "message": "Failed to decode JSON response",
                        "details": {"error": str(e), "raw_data": data[:1000] if len(data) > 1000 else data}
                    }
            else:
                logger.warning(f"Empty response: {method} {endpoint}{query_string}")
                return {
                    "success": False,
                    "status": res.status,
                    "message": "Empty response from API"
                }
                
        except Exception as e:
            logger.error(f"Request Error: {method} {endpoint}{query_string} - {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Check if we should retry
            if attempt < MAX_RETRIES - 1:
                retry_wait = RETRY_DELAY * (attempt + 1)
                logger.info(f"Retrying in {retry_wait} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(retry_wait)
            else:
                # Return error response after all retries failed
                return {
                    "success": False,
                    "status": 500,
                    "message": f"Request failed after {MAX_RETRIES} attempts",
                    "details": {"error": str(e)}
                }
        finally:
            # Close connection
            if 'conn' in locals():
                conn.close()
    
    # This should never be reached due to the return in the last retry attempt
    return {
        "success": False,
        "status": 500,
        "message": "Unexpected error in API request"
    }

# Quora API headers
QUORA_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": QUORA_API_HOST,
    "x-rapidapi-key": QUORA_API_KEY
}

# Quora API Tools based on quora_apis.jsonl

# Tool: Search Questions
@mcp.tool()
def search_questions(query: str, language: str, cursor: str = None, time: str = None) -> Dict:
    """Search for Questions Across Quora
    
    Get Request Parameters:
    - query: Search query (paramType: STRING, required) (e.g., "cars")
    - language: Language filter (paramType: ENUM, required)
    - cursor: Pagination cursor (paramType: STRING, optional)
    - time: Time filter (paramType: ENUM, optional)
    """
    try:
        params = {
            "query": query,
            "language": language
        }
        
        if cursor:
            params["cursor"] = cursor
            
        if time:
            params["time"] = time
            
        return make_api_request("GET", "/search_questions", params, QUORA_HEADERS)
    except Exception as e:
        logger.error(f"Error in search_questions tool: {str(e)}")
        return {"error": str(e), "exception_type": type(e).__name__}

# Tool: Search Answers
@mcp.tool()
def search_answers(query: str, language: str, cursor: str = None, time: str = None) -> Dict:
    """Search for Answers Across Quora
    
    Get Request Parameters:
    - query: Search query (paramType: STRING, required) (e.g., "cars")
    - language: Language filter (paramType: ENUM, required)
    - cursor: Pagination cursor (paramType: STRING, optional)
    - time: Time filter (paramType: ENUM, optional)
    """
    try:
        params = {
            "query": query,
            "language": language
        }
        
        if cursor:
            params["cursor"] = cursor
            
        if time:
            params["time"] = time
            
        return make_api_request("GET", "/search_answers", params, QUORA_HEADERS)
    except Exception as e:
        logger.error(f"Error in search_answers tool: {str(e)}")
        return {"error": str(e), "exception_type": type(e).__name__}

# Tool: Search Profiles
@mcp.tool()
def search_profiles(query: str, language: str, cursor: str = None) -> Dict:
    """Search for User Profiles Across Quora
    
    Get Request Parameters:
    - query: Search query (paramType: STRING, required) (e.g., "cars")
    - language: Language filter (paramType: ENUM, required)
    - cursor: Pagination cursor (paramType: STRING, optional)
    """
    try:
        params = {
            "query": query,
            "language": language
        }
        
        if cursor:
            params["cursor"] = cursor
            
        return make_api_request("GET", "/search_profiles", params, QUORA_HEADERS)
    except Exception as e:
        logger.error(f"Error in search_profiles tool: {str(e)}")
        return {"error": str(e), "exception_type": type(e).__name__}

# Tool: Get Answers From Question
@mcp.tool()
def question_answers(url: str, cursor: str = None, sort: str = None) -> Dict:
    """Get Answers for a Specific Question
    
    Get Request Parameters:
    - url: Quora question URL (paramType: STRING, required) (e.g., "https://www.quora.com/Does-China-have-cars")
    - cursor: Pagination cursor (paramType: STRING, optional)
    - sort: Sort order (paramType: ENUM, optional)
    """
    try:
        params = {
            "url": url
        }
        
        if cursor:
            params["cursor"] = cursor
            
        if sort:
            params["sort"] = sort
            
        return make_api_request("GET", "/question_answers", params, QUORA_HEADERS)
    except Exception as e:
        logger.error(f"Error in question_answers tool: {str(e)}")
        return {"error": str(e), "exception_type": type(e).__name__}

# Tool: Get Comments From Question
@mcp.tool()
def question_comments(url: str, cursor: str = None) -> Dict:
    """Get Comments for a Specific Question
    
    Get Request Parameters:
    - url: Quora question URL (paramType: STRING, required) (e.g., "https://www.quora.com/Does-China-have-cars")
    - cursor: Pagination cursor (paramType: STRING, optional)
    """
    try:
        params = {
            "url": url
        }
        
        if cursor:
            params["cursor"] = cursor
            
        return make_api_request("GET", "/question_comments", params, QUORA_HEADERS)
    except Exception as e:
        logger.error(f"Error in question_comments tool: {str(e)}")
        return {"error": str(e), "exception_type": type(e).__name__}

# Start the MCP server if this file is run directly
if __name__ == "__main__":
    mcp.start()

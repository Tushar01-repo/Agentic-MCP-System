# mcp_server.py
from fastmcp import FastMCP
from mcp.server.fastmcp.server import FastMCP
import json
import os
import sys
import threading

# Path to the JSON file storing movie and showtime data
BASE_DIR = os.path.dirname(__file__)
print(BASE_DIR)
DATA_FILE = os.path.join(BASE_DIR, "movies_data", "data.json")
# DATA_FILE = os.path.join("movies_data", "data.json")

# Lock for thread-safe file read/write operations
_lock = threading.Lock()


# ---------------------------
# Utility functions
# ---------------------------

def load_data():
    
    """
    Load movie data from the JSON file.
    Thread-safe using a lock.

    Input: None
    Output: list[dict] -> A list of movie objects with their details and showtimes.
    """
    
    with _lock:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

def save_data(data):
    
    """
    Save movie data to the JSON file.
    Thread-safe using a lock.

    Input: data (list[dict]) -> Updated list of movies with their details and showtimes.
    Output: None
    """
    
    with _lock:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Initialize FastMCP server instance
mcp = FastMCP("Movie Booking MCP Server")


# ---------------------------
# MCP Tools (API endpoints)
# ---------------------------

@mcp.tool()
def list_movies(location: str):

    """
    List all movies available in a given location.

    Input:
        location (str) -> City name (case-insensitive), e.g., "Delhi"
    
    Output:
        dict:
        {
            "movies": [
                {
                    "movie_id": str,
                    "name": str,
                    "genre": str,
                    "location": str
                },
                ...
            ]
        }
    """

    movies = load_data()
    loc = location.lower()
    return {
        "movies": [
            {"movie_id": m["movie_id"], "name": m["name"], "genre": m["genre"], "location": m["location"]}
            for m in movies if m["location"].lower() == loc
        ]
    }



@mcp.tool()
def get_showtimes(movie_name: str, location: str):

    """
    Get all showtimes for a specific movie in a given location.

    Input:
        movie_name (str) -> Name of the movie (case-insensitive), e.g., "Inception"
        location (str)   -> City name (case-insensitive), e.g., "Delhi"
    
    Output:
        dict:
        {
            "movie_id": str,
            "name": str,
            "location": str,
            "showtimes": [
                {
                    "show_id": str,
                    "time": str,
                    "theatre_name": str,
                    "seats": {"available": int, "total": int}
                },
                ...
            ]
        }
        OR
        {"error": "No showtimes found"}
    """

    movies = load_data()
    mname, loc = movie_name.lower(), location.lower()
    for m in movies:
        if m["name"].lower() == mname and m["location"].lower() == loc:
            return {
                "movie_id": m["movie_id"],
                "name": m["name"],
                "location": m["location"],
                "showtimes": m.get("showtimes", [])
            }
    return {"error": "No showtimes found"}



@mcp.tool()
def book_ticket(show_id: str, seats: int, user_id: str = None):
    
    """
    Book a certain number of seats for a given show ID.

    Input:
        show_id (str) -> Unique identifier for the show (case-insensitive)
        seats (int)   -> Number of seats to book (must be > 0)
        user_id (str) -> Optional user identifier
    
    Output:
        Success:
        {
            "success": True,
            "message": "X seats booked for show <show_id>",
            "remaining": <remaining seats>
        }

        Failure:
        {"error": "Seats must be greater than 0"}
        {"error": "Only <available> seats available"}
        {"error": "Show not found"}
    """

    if seats <= 0:
        return {"error": "Seats must be greater than 0"}
    movies = load_data()
    sid = show_id.lower()
    for mi, m in enumerate(movies):
        for si, s in enumerate(m.get("showtimes", [])):
            if s.get("show_id", "").lower() == sid:
                available = s.get("seats", {}).get("available", 0)
                if available < seats:
                    return {"error": f"Only {available} seats available"}
                movies[mi]["showtimes"][si]["seats"]["available"] = available - seats
                save_data(movies)
                return {
                    "success": True,
                    "message": f"{seats} seats booked for show {show_id}",
                    "remaining": available - seats,
                }
    return {"error": "Show not found"}



@mcp.tool()
def ping():
    
    """
    Health check tool to verify MCP server is running.

    Input: None
    Output:
        {"status": "ok"}
    """
    
    return {"status": "ok"}

# Start the MCP server
if __name__ == "__main__":
    mcp.run()

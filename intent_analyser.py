# intent_analyser.py
import os, json, asyncio, re, requests, time
from dotenv import load_dotenv
from fastmcp import Client

load_dotenv()

# Configuration variables for DeepSeek API and MCP server
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
API_URL = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
MCP_HTTP_URL = "http://127.0.0.1:8000/mcp"


# Initialize MCP client for making tool calls
client = Client(MCP_HTTP_URL)


# Prompt that instructs the LLM to act as an intent and parameter extractor
INTENT_PROMPT = """
You are an intent & parameter extractor for a movie booking system.
Valid intents and mandatory parameters:
- list_movies: { "location": string }
- get_showtimes: { "movie_name": string, "location": string }
- book_ticket: { "show_id": string, "seats": number, "user_id"?: string }

Return STRICT JSON ONLY like:
{"intent": "list_movies", "parameters": {"location": "Delhi"}}
"""


def _strip_code_fences(text: str) -> str:
    
    """
    Remove Markdown-style code fences (```json ... ```) from LLM response if present.

    Input:
        text (str): Raw text response from LLM which might include code fences.

    Output:
        str: Cleaned text without code fences.
    """

    if text.strip().startswith("```"):
        text = re.sub(r"^```(\w+)?\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()



def analyze_intent_llm(user_text: str) -> dict:
    
    """
    Send the user input to the DeepSeek LLM to extract intent and parameters.

    Input:
        user_text (str): The user's message (e.g., "Show me movies in Delhi").

    Output:
        dict: Example:
            {
                "intent": "list_movies",
                "parameters": {"location": "Delhi"}
            }
    """
    
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": INTENT_PROMPT},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0
    }
    r = requests.post(f"{API_URL}/chat/completions", headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    cleaned = _strip_code_fences(content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print("⚠️ LLM non-JSON:\n", content)
        return {"intent": None, "parameters": {}}


REQUIRED = {
    "list_movies": ["location"],
    "get_showtimes": ["movie_name", "location"],
    "book_ticket": ["show_id", "seats"]
}



def find_missing(intent: str, params: dict):
    
    """
    Find which mandatory parameters are missing for the given intent.

    Input:
        intent (str): Intent name (e.g., "list_movies").
        params (dict): Extracted parameters.

    Output:
        list: List of missing parameter names.
    """
    must = REQUIRED.get(intent, [])
    return [k for k in must if params.get(k) in (None, "", [])]



async def call_mcp_tool(intent: str, params: dict):
    
    """
    Call MCP tool asynchronously for the given intent and parameters.

    Input:
        intent (str): Name of the MCP tool (matches intent).
        params (dict): Parameters for the tool call.

    Output:
        dict or object: Response from MCP tool (depends on the tool implementation).
    """
    
    async with client:
        return await client.call_tool(intent, params)



def safe_run(intent: str, params: dict, retries=3, delay=2):

    """
    Call MCP tool with retry logic in case of failures.

    Input:
        intent (str): Tool name.
        params (dict): Tool parameters.
        retries (int): Number of retry attempts.
        delay (int): Delay in seconds between retries.

    Output:
        dict: Result from the MCP tool or error message.
    """
    
    for attempt in range(retries):
        try:
            return asyncio.run(call_mcp_tool(intent, params))
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed: {e}")
            time.sleep(delay)
    return {"error": "Failed after retries"}



def pretty_print(result):
    
    """
    Print results in a user-friendly format.

    Input:
        result (dict): Result from MCP tool (movies or showtimes).

    Output:
        Prints formatted text (no return).
    """
    
    if isinstance(result, dict) and "movies" in result:
        movies = result["movies"]
        if not movies:
            print("🎬 No movies found.")
            return
        print("🎬 Movies:")
        for m in movies:
            print(f"- {m['name']} ({m['genre']}) [{m['movie_id']}] in {m['location']}")
        return

    if isinstance(result, dict) and "showtimes" in result:
        sts = result["showtimes"]
        if not sts:
            print("🎭 No showtimes found.")
            return
        print("🎭 Showtimes:")
        for s in sts:
            t = s.get("time")
            th = s.get("theatre_name")
            sid = s.get("show_id")
            avail = s.get("seats", {}).get("available", "?")
            total = s.get("seats", {}).get("total", "?")
            print(f"- [{sid}] {t} @ {th}  — seats {avail}/{total}")
        return

    print(result)



def interactive_fill(intent: str, params: dict) -> dict:
    
    """
    Ask user for missing mandatory parameters interactively.

    Input:
        intent (str): Detected intent.
        params (dict): Current parameters (may be incomplete).

    Output:
        dict: Complete parameters with missing fields filled by user.
    """
    
    missing = find_missing(intent, params)
    while missing:
        need = missing[0]
        prompt = {
            "location": "Please provide the city (e.g., Delhi/Mumbai/Bengaluru): ",
            "movie_name": "Which movie?: ",
            "show_id": "Enter show_id to book: ",
            "seats": "How many seats?: ",
        }.get(need, f"Provide {need}: ")
        val = input(prompt).strip()
        if need == "seats":
            try:
                val = int(val)
            except:
                print("Please enter a valid number.")
                continue
        params[need] = val
        missing = find_missing(intent, params)
    return params



def main():
    
    """
    Main interactive loop for the Movie Booking Assistant.

    Input:
        User types natural language commands (e.g., "List movies in Delhi").

    Output:
        Prints results of intent execution and optionally books tickets.
    """
        
    print("🎬 Movie Booking Assistant (DeepSeek + FastMCP) — type 'exit' to quit")

    while True:
        user = input("You: ").strip()
        if user.lower() in ("exit", "quit"):
            break

        intent_data = analyze_intent_llm(user)
        intent = intent_data.get("intent")
        params = intent_data.get("parameters", {}) or {}

        print(f"✅ Detected intent: {intent}")
        print(f"✅ Params: {params}")

        if not intent:
            print("❌ No intent recognized.")
            continue

        params = interactive_fill(intent, params)
        print(f"➡ Calling MCP tool: {intent} with {params}")
        result = safe_run(intent, params)
        print("🤖 Result:")
        pretty_print(result)

        # Unwrap CallToolResult
        if hasattr(result, "structured_content"):
            result = result.structured_content
            
        if intent == "get_showtimes" and isinstance(result, dict) and "showtimes" in result:
            follow_up = input("🎟️ Would you like to book tickets for one of these shows? (yes/no): ").strip().lower()
            if follow_up == "yes":
                booking_params = {"show_id": "", "seats": ""}
                booking_params = interactive_fill("book_ticket", booking_params)
                print(f"➡ Calling MCP tool: book_ticket with {booking_params}")
                booking_result = safe_run("book_ticket", booking_params)
                print("🤖 Booking Result:")
                pretty_print(booking_result)


if __name__ == "__main__":
    main()

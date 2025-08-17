# 🎬 Movie Booking Assistant — DeepSeek + FastMCP (V1)

An intelligent, agentic CLI assistant for movie discovery and ticket booking. Powered by DeepSeek LLM for intent extraction and FastMCP for modular tool orchestration.

---

## 🚀 Features

- 🧠 **LLM-driven intent extraction** from natural language
- 🔧 **FastMCP tool orchestration** for modular API calls
- 🧵 **Interactive slot filling** for missing parameters
- 🔁 **Multi-step flows** (e.g., showtimes → booking)
- 🛡️ **Thread-safe data access** and retry logic
- 🖨️ **User-friendly CLI output** with emoji cues

---

## 🗂️ Project Structure

├── server.py # FastMCP server with movie tools 
├── intent_analyser.py # CLI assistant with DeepSeek integration 
├── movies_data/ 
│ └── data.json # Movie + showtime data 
├── .env # API keys and config 
└── README.md 

## 📄 Install dependencies
- pip install -r requirements.txt

## 🧭 Start the server (running on HTTP)
- python server.py

## 🌐 Launch CLI assistant (Custom Elicitation)
- python intent_analyser.py

## 💬 Example Usage (with MCP server running on HTTP with the use of custom elicitation)
🎬 Movie Booking Assistant (DeepSeek + FastMCP) — type 'exit' to quit

You: Show me movies in Delhi
✅ Detected intent: list_movies
✅ Params: {'location': 'Delhi'}
➡ Calling MCP tool: list_movies with {'location': 'Delhi'}
🤖 Result:
🎬 Movies:
- Inception (Sci-Fi) [mov001] in Delhi
- Dune (Adventure) [mov002] in Delhi

You: Showtimes for Inception in Delhi
✅ Detected intent: get_showtimes
✅ Params: {'movie_name': 'Inception', 'location': 'Delhi'}
🎭 Showtimes:
- [show001] 7:00 PM @ PVR Saket — seats 42/50

🎟️ Would you like to book tickets for one of these shows? (yes/no): yes
Enter show_id to book: show001
How many seats?: 2
➡ Calling MCP tool: book_ticket with {'show_id': 'show001', 'seats': 2}
🤖 Booking Result:
✅ 2 seats booked for show show001 — remaining: 40

## 🧩 Working with MCP Server (Start MCP Server)

1. **Install Claude Desktop**  
   Download and install the [Claude Desktop app](https://claude.ai).

2. **Run the MCP Server**  
   Start your MCP server using: **python mcp_server.py**
   
4. **Install the MCP Server in Claud**
   Use uv to register your MCP server with Claude: **uv run mcp install mcp_server.py**

5. **Verify in Claude Settings & Test**
   - Open Claude Desktop
   - Go to Settings → MCP Servers and confirm your server is listed and running
   - Start a new chat and interact with your MCP server (e.g., ask about movies, showtimes, ticket booking)

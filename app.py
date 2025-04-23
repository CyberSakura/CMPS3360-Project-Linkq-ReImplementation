from flask import Flask, request, jsonify, send_from_directory

from flask_cors import CORS
from main_scripts.components.chat import handle_chat
from main_scripts.components.runQuery import run_sparql_query
from main_scripts.fuzzy_entity_search import get_potential_entities, ask_llm_to_select_entity
from datetime import datetime, timezone
import openai
import sqlite3
import os
from dotenv import load_dotenv
from config import DB_PATH, DEBUG, HOST, PORT

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OpenAI API key not found.")

app = Flask(__name__)

# Configure CORS properly
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Ensure database exists
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user TEXT,
            bot TEXT,
            entity_context TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def serve():
    print(app.url_map)
    return send_from_directory(app.static_folder, "index.html")

@app.route('/search_entity', methods=['GET'])
def search_entity_api():
    user_query = request.args.get('query')
    if not user_query:
        return jsonify({"error": "Please provide a query"}), 400

    entity_candidates = get_potential_entities(user_query)

    if not entity_candidates:
        print("No entities found.")
    else:
        selected_entity_id = ask_llm_to_select_entity(user_query, entity_candidates)
        print(f"\n[SELECTED ENTITY]: {selected_entity_id}")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    return handle_chat(user_message)

@app.route("/chat-history", methods=["GET"])
def chat_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Get all messages ordered by timestamp in descending order
        cursor.execute("SELECT timestamp, user, bot FROM chats ORDER BY timestamp DESC")
        chat_history = [{
            "timestamp": row[0],
            "user": row[1],
            "bot": row[2],
            "type": "system" if row[1] == "system" else "user"
        } for row in cursor.fetchall()]
        conn.close()

        return jsonify({"history": chat_history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

print("[DEBUG] Before defining /run_query route")
@app.route("/run_query", methods=["POST"])
def run_query():
    print("[DEBUG] After defining /run_query route")
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "SPARQL query is required"}), 400

        # Run the query
        result_json = run_sparql_query(query)

        # Store in DB as a new message with user="system"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        timestamp = datetime.now(timezone.utc).isoformat()
        result_str = str(result_json)

        cursor.execute(
            "INSERT INTO chats (timestamp, user, bot, entity_context) VALUES (?, ?, ?, ?)",
            (timestamp, "system", result_str, None)
        )
        conn.commit()

        # Retrieve the last 10 messages
        cursor.execute("SELECT user, bot FROM chats ORDER BY id DESC LIMIT 10")
        chat_history = [{"user": row[0], "bot": row[1]} for row in cursor.fetchall()]
        conn.close()

        # Include both the query and results in the response
        return jsonify({
            "result": result_json,
            "history": chat_history,
            "query": query  # Add the original query to the response
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate-query-name", methods=["POST"])
def generate_query_name():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400

        # Generate a descriptive name using GPT
        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates concise, descriptive names for SPARQL queries. The name should be brief (max 50 characters) but descriptive of what the query does."},
            {"role": "user", "content": f"Generate a concise name for this SPARQL query:\n\n{query}"}
        ]
        
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=50,
            temperature=0.7
        )
        
        query_name = response.choices[0].message.content.strip()
        
        return jsonify({"name": query_name})

    except Exception as e:
        print(f"Error generating query name: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/debug/routes")
def debug_routes():
    return str(app.url_map)

if __name__ == '__main__':
    print("AVAILABLE ROUTES:", app.url_map)
    app.run(debug=DEBUG, host=HOST, port=PORT)
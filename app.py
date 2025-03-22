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

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OpenAI API key not found.")


DB_PATH = "chat_history.db"

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Corrected "origins" to "origins"

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
        cursor.execute("SELECT user, bot FROM chats ORDER BY id DESC LIMIT 10")
        chat_history = [{"user": row[0], "bot": row[1]} for row in cursor.fetchall()]
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

        print("[DEBUG] result_str is: "+result_str)
        cursor.execute(
            "INSERT INTO chats (timestamp, user, bot, entity_context) VALUES (?, ?, ?, ?)",
            (timestamp, "system", result_str, None)
        )
        conn.commit()

        # Retrieve the last 10 messages
        cursor.execute("SELECT user, bot FROM chats ORDER BY id DESC LIMIT 10")
        chat_history = [{"user": row[0], "bot": row[1]} for row in cursor.fetchall()]
        conn.close()

        print("[DEBUG] json of result is:", {"result": result_json, "history": chat_history})
        # Return the results + updated chat history
        return jsonify({"result": result_json, "history": chat_history}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/debug/routes")
def debug_routes():
    return str(app.url_map)

if __name__ == '__main__':
    print("AVAILABLE ROUTES:", app.url_map)
    app.run(debug=True, use_reloader=False)
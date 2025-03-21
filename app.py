from flask import Flask, request, jsonify, send_from_directory

from flask_cors import CORS
from main_scripts.components.chat import handle_chat
from main_scripts.fuzzy_entity_search import get_potential_entities, ask_llm_to_select_entity
import openai
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OpenAI API key not found.")


DB_PATH = "chat_history.db"

app = Flask(__name__, static_folder="../frontend/linkq-frontend/build")
CORS(app)  # Enable CORS to allow front-end communication

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

if __name__ == '__main__':
    app.run(debug=True)

import sqlite3
import openai
import os
from flask import jsonify
from datetime import datetime, timezone
from main_scripts.fuzzy_entity_search import get_potential_entities, ask_llm_to_select_entity, find_sub_entities
from main_scripts.components.query_build import query_building_workflow
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key:
    raise ValueError("Missing OpenAI API Key! Please set it in the .env file.")

DB_PATH = "../chat_history.db"

# Define a fixed INITIAL_SYSTEM_MESSAGE
INITIAL_SYSTEM_MESSAGE = (
    "You are a SPARQL query construction assistant for Wikidata. Your primary role is to help users construct precise SPARQL queries.\n\n"
    "When users ask questions, you should:\n"
    "1. FIRST, evaluate if the question is specific enough for a precise SPARQL query\n"
    "2. If the question is too broad or vague, ask the user to be more specific\n"
    "3. Guide users to provide:\n"
    "   - Specific timeframes (e.g., 'in 2022' instead of 'recently')\n"
    "   - Clear entity types (e.g., 'movies' instead of 'things')\n"
    "   - Specific properties (e.g., 'won Best Picture' instead of 'achievements')\n"
    "4. Only proceed to query construction when the question is specific enough\n\n"
    "Example interactions:\n"
    "User: 'Which movies won awards?'\n"
    "You: 'Could you please specify which awards you're interested in (e.g., Academy Awards, Golden Globes) and for which years?'\n\n"
    "User: 'Tell me about recent scientific discoveries'\n"
    "You: 'To help you better, could you specify which field of science, what type of discoveries, and a specific time period?'\n\n"
    "When the question is specific enough, respond with 'BUILD QUERY' to start the query construction process.\n\n"
    "Current date: " + datetime.now(timezone.utc).isoformat()
)

# Initialize database
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

# Call this when the script runs
init_db()

def handle_chat(user_message):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print(f"[DEBUG] Processing user message: {user_message}")

        client = openai.OpenAI()
        # Send the user's message along with the fixed system message.
        print(f"[DEBUG] Sending message to LLM with user_message: {user_message}")
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": INITIAL_SYSTEM_MESSAGE},
                {"role": "user", "content": user_message}
            ]
        )
        bot_reply = response.choices[0].message.content
        print(f"[DEBUG] Bot reply: {bot_reply}")

        # If the reply asks for clarification or signals query building, handle accordingly.
        if bot_reply.startswith("CLARIFY:"):
            print("[DEBUG] LLM requested clarification; returning clarifying response directly.")
            final_reply = bot_reply
        elif "BUILD QUERY" in bot_reply:
            print("[DEBUG] LLM requested query building workflow.")
            final_reply = query_building_workflow(user_message)
        else:
            final_reply = bot_reply

        # Store the conversation in the database.
        timestamp = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO chats (timestamp, user, bot, entity_context) VALUES (?, ?, ?, ?)",
            (timestamp, user_message, final_reply, None)
        )
        conn.commit()

        cursor.execute("SELECT user, bot FROM chats ORDER BY id DESC LIMIT 10")
        chat_history = [{"user": row[0], "bot": row[1]} for row in cursor.fetchall()]
        conn.close()

        return jsonify({"reply": final_reply, "history": chat_history})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    from flask import Flask
    import json
    app = Flask(__name__)
    with app.app_context():
        user_input = input("Enter a user message: ")
        response = handle_chat(user_input)
        # If response is a tuple, get its first element.
        if isinstance(response, tuple):
            response = response[0]
        try:
            data = response.get_json()
            print("Response from handle_chat:")
            print(json.dumps(data, indent=2))
        except Exception as e:
            print("Error processing response:", e)
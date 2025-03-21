import sqlite3
import openai
import os
from flask import jsonify
from datetime import datetime
from main_scripts.fuzzy_entity_search import get_potential_entities, ask_llm_to_select_entity, find_sub_entities, \
    query_building_workflow

DB_PATH = "../chat_history.db"

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

# def analyze_query(user_message, previous_entity=None):
#     print(f"Analyzing user message: {user_message}")
#     entity_candidates = get_potential_entities(user_message)
#
#     if not entity_candidates:
#         print("No relevant entities found.")
#         return False, "I couldn't identify any relevant entities. Can you provide more details?", None
#
#     print(f"Entities found: {entity_candidates}")
#
#     if len(entity_candidates) > 1:
#         # Ask LLM to refine the entity selection
#         refined_entity = ask_llm_to_select_entity(user_message, entity_candidates, previous_entity)
#         if refined_entity:
#             print(f"LLM selected entity: {refined_entity}")
#             return True, f"Selected entity: {refined_entity}", refined_entity
#         return False, f"I found multiple possible entities: {entity_candidates}. Could you specify which one you mean?", None
#
#     selected_entity = entity_candidates[0]
#     # If the user refines their search based on a previous entity
#     if previous_entity:
#         sub_entities = find_sub_entities(previous_entity)
#         for sub_entity in sub_entities:
#             if sub_entity["label"].lower() == user_message.lower():
#                 print(f"Found sub-entity: {sub_entity}")
#                 return True, f"Refined entity found: {sub_entity}", sub_entity
#
#     print(f"Final selected entity: {selected_entity}")
#     return True, f"Identified entity: {selected_entity}", selected_entity

def handle_chat(user_message):
    try:
        # Retrieve previous entity context if available
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT entity_context FROM chats ORDER BY id DESC LIMIT 1")
        last_context = cursor.fetchone()
        previous_entity = last_context[0] if last_context and last_context[0] else None

        print(f"[DEBUG] Analyzing user message: {user_message}")

        # Send the user message to the LLM with an instructive system message.
        client = openai.OpenAI()
        print(f"[DEBUG] Sending message to LLM with user_message: {user_message}")
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. When the user's question is ambiguous and may refer to multiple entities, "
                        "do NOT provide a direct answer. Instead, respond with a clarifying question that starts with 'CLARIFY:' "
                        "to ask which interpretation they mean. If the question is unambiguous, answer as normal."
                    )
                },
                {"role": "user", "content": user_message}
            ]
        )
        bot_reply = response.choices[0].message.content
        print(f"[DEBUG] Bot reply: {bot_reply}")

        # Option 1: If the reply starts with "CLARIFY:", return that immediately.
        if bot_reply.startswith("CLARIFY:"):
            print("LLM requested clarification; returning the clarifying response directly.")
            final_reply = bot_reply
        # Otherwise, if it signals query building, handle that.
        elif "BUILD QUERY" in bot_reply:
            print("LLM requested query building workflow.")
            final_response = query_building_workflow(user_message)
            final_reply = final_response
        else:
            # Otherwise, use the bot reply as is.
            final_reply = bot_reply

        # Store the conversation in the database.
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO chats (timestamp, user, bot, entity_context) VALUES (?, ?, ?, ?)",
            (timestamp, user_message, final_reply, previous_entity)
        )
        conn.commit()

        # Retrieve the latest chat history.
        cursor.execute("SELECT user, bot FROM chats ORDER BY id DESC LIMIT 10")
        chat_history = [{"user": row[0], "bot": row[1]} for row in cursor.fetchall()]
        conn.close()

        return jsonify({"reply": final_reply, "history": chat_history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    import json
    from flask import Flask
    # Create a simple Flask application instance
    test_app = Flask(__name__)
    # Push an application context so that jsonify works
    with test_app.app_context():
        user_message = input("Enter a chat message: ")
        response = handle_chat(user_message)
        try:
            data = response.get_json()
            print("Response from handle_chat:")
            print(json.dumps(data, indent=2))
        except Exception as e:
            print("Error processing response:", e)
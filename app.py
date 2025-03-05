from flask import Flask, request, jsonify
from main_scripts.fuzzy_entity_search import get_potential_entities, ask_llm_to_select_entity
import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OpenAI API key not found.")

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

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

if __name__ == '__main__':
    app.run()

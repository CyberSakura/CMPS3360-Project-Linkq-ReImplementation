import os
import re
import requests
import openai
import spacy
import json
from dotenv import load_dotenv
# from main_scripts.components.query_build import query_building_workflow

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key:
    raise ValueError("Missing OpenAI API Key! Please set it in the .env file.")

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
SEARCH_ENDPOINT = "https://www.wikidata.org/w/api.php"
HEADERS = {
    "User-Agent": "LinkQ-Entity-Search/1.0",
    "Accept": "application/json"
}

# Example mapping of user-friendly terms to Wikidata entity types (for debugging)
ENTITY_TYPES = {
    "cat": "Q146",    # Domestic Cat
    "dog": "Q144",    # Domestic Dog
    "city": "Q515",   # Cities
    "country": "Q6256",  # Countries
    "person": "Q5",   # Humans
    "book": "Q571"    # Books
}

# Initialize spaCy model for English (make sure to download en_core_web_sm)
nlp = spacy.load("en_core_web_sm")

def extract_search_term(message):
    prefixes = [
        "tell me about",
        "what is",
        "give me details on",
        "information about",
        "i want to know about"
    ]
    lower_message = message.lower().strip()
    extracted = message.strip()
    for prefix in prefixes:
        if lower_message.startswith(prefix):
            extracted = message[len(prefix):].strip()
            break
    # Use spaCy to extract a named entity from the extracted text.
    doc = nlp(extracted)
    # If any entity is found, return its text.
    for ent in doc.ents:
        return ent.text.strip()
    # Fallback: return the extracted text
    return extracted

def get_potential_entities(search_term, limit=10):
    extracted_term = extract_search_term(search_term)
    print(f"[DEBUG] Searching for entities related to: {extracted_term}")
    params = {
        "action": "wbsearchentities",
        "search": extracted_term,
        "language": "en",
        "format": "json",
        "limit": limit
    }
    try:
        response = requests.get(SEARCH_ENDPOINT, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("[DEBUG] Raw JSON response:")
        print(json.dumps(data, indent=2))
        entities = []
        # for item in data.get("results", {}).get("bindings", []):
        #     # Adjust extraction as needed; here we assume a common structure.
        #     entity_value = item.get("entity", {}).get("value", "")
        #     entity_id = entity_value.split("/")[-1] if entity_value else ""
        #     label = item.get("entityLabel", {}).get("value", "No label available")
        #     description = item.get("description", {}).get("value", "No description available")
        #     entities.append({"entity_id": entity_id, "label": label, "description": description})

        if "search" in data:
            for item in data.get("search", []):
                entity_id = item.get("id", "")
                label = item.get("label", "No label available")
                description = item.get("description", "No description available")
                entities.append({"entity_id": entity_id, "label": label, "description": description})
        else:
            # Fallback if the structure is different (e.g., a SPARQL-like result)
            for item in data.get("results", {}).get("bindings", []):
                entity_value = item.get("entity", {}).get("value", "")
                entity_id = entity_value.split("/")[-1] if entity_value else ""
                label = item.get("entityLabel", {}).get("value", "No label available")
                description = item.get("description", {}).get("value", "No description available")
                entities.append({"entity_id": entity_id, "label": label, "description": description})

        return entities
    except requests.RequestException as e:
        print(f"[DEBUG] Error fetching entities: {e}")
        return []

def execute_sparql_query(query):
    try:
        response = requests.get(SPARQL_ENDPOINT, headers=HEADERS, params={"query": query, "format": "json"}, timeout=10)
        response.raise_for_status()
        data = response.json()
        entities = []
        for item in data.get("results", {}).get("bindings", []):
            entity_id = item.get("entity", {}).get("value", "").split("/")[-1]
            label = item.get("entityLabel", {}).get("value", "No label available")
            description = item.get("description", {}).get("value", "No description available")
            entities.append({"entity_id": entity_id, "label": label, "description": description})
        return entities
    except requests.RequestException as e:
        print(f"[DEBUG] Error fetching SPARQL query: {e}")
        return []

def find_sub_entities(entity_id, limit=10):
    sparql_query = f"""
        SELECT ?subEntity ?subEntityLabel ?description WHERE {{
          ?subEntity wdt:P31 wd:{entity_id}.
          OPTIONAL {{ ?subEntity schema:description ?description FILTER (lang(?description) = "en") }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT {limit}
    """
    return execute_sparql_query(sparql_query)

def ask_llm_to_select_entity(user_query, entities, previous_entity=None):
    if len(entities) > 1:
        clarification_prompt = (
            f"The user query \"{user_query}\" returned multiple possible entities:\n"
        )
        for e in entities:
            clarification_prompt += f"- {e['label']}: {e['description']}\n"
        clarification_prompt += (
            "Please clarify which entity is most relevant by returning a command "
            "in the following format:\n"
            "CLARIFY: <Your clarifying question here>"
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an entity selection assistant. If there are multiple candidates, ask the user for clarification."
                    },
                    {"role": "user", "content": clarification_prompt}
                ],
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[DEBUG] Error calling OpenAI API in ask_llm_to_select_entity (clarification): {e}")
            return None
    else:
        entity_options = "\n".join(
            [f"- {e['label']} ({e['entity_id']}): {e['description']}" for e in entities]
        )
        llm_prompt = f"""
            The user asked: "{user_query}". Based on this, please extract the relevant entity (for example, cats) and rank the top 3 matching Wikidata entities.
    
            Below is a list of possible Wikidata entities that match the term:
            {entity_options}
    
            Additional Context:
            - The user's previous entity selection was: "{previous_entity}" (if applicable).
            - If the new search term is related to the previous entity, prioritize sub-entities.
    
            Your task:
            1. Rank the top 3 most relevant entities based on the search term.
            2. If none match well, return [].
            3. Respond ONLY in JSON format (example below):
    
            Example JSON output format:
            [
              {{"entity_id": "QXXXXXX", "label": "Entity Name", "description": "Entity Description"}}
            ]
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an entity selection assistant."},
                    {"role": "user", "content": llm_prompt}
                ],
                temperature=0
            )
            selected_entity = response.choices[0].message.content.strip()
            return selected_entity
        except Exception as e:
            print(f"[DEBUG] Error calling OpenAI API in ask_llm_to_select_entity: {e}")
            return None
    
def parse_command(response_text):
    response_text = response_text.strip()

    # Create a dictionary mapping command keywords to their regex patterns
    commands = {
        "STOP": r"\bSTOP\b",
        "ENTITY_SEARCH": r"ENTITY_SEARCH:\s*(.+)",
        "PROPERTIES_SEARCH": r"PROPERTIES_SEARCH:\s*(.+)",
        "TAIL_SEARCH": r"TAIL_SEARCH:\s*(.+)",
        "CLARIFY": r"CLARIFY:\s*(.+)"
    }

    # Check for STOP (if response is exactly "STOP", or even if found somewhere)
    if re.search(commands["STOP"], response_text, re.IGNORECASE):
        return "STOP", ""

    # Try to find any of the commands in the text
    for command, pattern in commands.items():
        if command == "STOP":
            continue  # already handled STOP
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            return command, match.group(1).strip()

    return "UNKNOWN", response_text

if __name__ == "__main__":
    import json
    test_message = input("Enter a user question for query building: ")
    final_query = query_building_workflow(test_message)
    print("Final query built:")
    print(json.dumps(final_query, indent=2))
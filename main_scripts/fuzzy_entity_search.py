import os
import requests
import openai
import spacy
from dotenv import load_dotenv

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
        entities = []
        for item in data.get("search", []):
            entity_id = item.get("id", "")
            label = item.get("label", "No label available")
            description = item.get("description", "No description available")
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
    if response_text.upper() == "STOP":
        return "STOP", ""
    elif response_text.startswith("ENTITY_SEARCH:"):
        return "ENTITY_SEARCH", response_text[len("ENTITY_SEARCH:"):].strip()
    elif response_text.startswith("PROPERTIES_SEARCH:"):
        return "PROPERTIES_SEARCH", response_text[len("PROPERTIES_SEARCH:"):].strip()
    elif response_text.startswith("TAIL_SEARCH:"):
        return "TAIL_SEARCH", response_text[len("TAIL_SEARCH:"):].strip()
    elif response_text.startswith("CLARIFY:"):
        return "CLARIFY", response_text[len("CLARIFY:"):].strip()
    else:
        return "UNKNOWN", response_text

def query_building_workflow(user_message):
    max_iterations = 20
    iteration = 0
    client_instance = openai.OpenAI()
    collected_data = {}

    initial_system_message = (
        "You are a query building assistant for our knowledge base. Your task is to analyze "
        "the user's question and determine the necessary entities and relationships needed "
        "to build a query. When you need to perform an action, respond with one of these commands:\n"
        "  - ENTITY_SEARCH: <search term>\n"
        "  - PROPERTIES_SEARCH: <entity id>\n"
        "  - TAIL_SEARCH: <entity id>, <property id>\n"
        "When you have gathered all required information, respond with STOP.\n"
        f"User question: {user_message}"
    )

    current_prompt = initial_system_message

    while iteration < max_iterations:
        iteration += 1
        response = client_instance.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": current_prompt}]
        )
        resp_text = response.choices[0].message.content.strip()
        print(f"[Query Strategist] Iteration {iteration}: {resp_text}")
        command, param = parse_command(resp_text)

        print("[DEBUG]: command: ", command)

        if command == "CLARIFY":
            print("[Query Strategist] Received CLARIFY command. Breaking out of iterations and returning clarification.")
            return f"Clarification: {param}"

        if command == "STOP":
            print("[Query Strategist] Received STOP command. Ending iteration.")
            break
        elif command == "ENTITY_SEARCH":
            results = get_potential_entities(param)
            collected_data["entities"] = results
            result_text = f"Entity results: {results}"
        elif command == "PROPERTIES_SEARCH":
            # For demonstration, simulate a property lookup.
            result_text = "Property results: [{'property': 'dummy_property', 'value': 'dummy_value'}]"
            collected_data["properties"] = result_text
        elif command == "TAIL_SEARCH":
            parts = param.split(",")
            if len(parts) >= 2:
                ent_id = parts[0].strip()
                tail_results = find_sub_entities(ent_id)
                collected_data["tail"] = tail_results
                result_text = f"Tail results: {tail_results}"
            else:
                result_text = "Error: TAIL_SEARCH format invalid."
        else:
            result_text = "Error: Unrecognized command."

        # Update the prompt with the latest result
        current_prompt = initial_system_message + "\nPrevious Result: " + result_text
        print(f"[Query Strategist] Updated prompt:\n{current_prompt}\n")

    final_prompt = (
            initial_system_message + "\nCollected Data: " + str(collected_data) + "\n" +
            f"Based on the above, construct the final query to answer the user's question: {user_message}"
    )
    final_response = client_instance.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": final_prompt}]
    )
    final_query = final_response.choices[0].message.content.strip()
    print(f"[Query Strategist] Final query: {final_query}")
    return final_query

if __name__ == "__main__":
    import json
    test_message = input("Enter a user question for query building: ")
    final_query = query_building_workflow(test_message)
    print("Final query built:")
    print(json.dumps(final_query, indent=2))
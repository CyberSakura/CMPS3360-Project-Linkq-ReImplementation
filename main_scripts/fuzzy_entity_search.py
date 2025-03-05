import os
import requests
import openai
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

# Mapping user-friendly terms to Wikidata entity types
ENTITY_TYPES = {
    "cat": "Q146",  # Domestic Cat
    "dog": "Q144",  # Domestic Dog
    "city": "Q515",  # Cities
    "country": "Q6256",  # Countries
    "person": "Q5",  # Humans
    "book": "Q571"  # Books
}

def get_potential_entities(search_term, limit=10):
    """
    Fetch potential entities based on whether the search term matches a predefined entity type.
    If the entity type is found, query within that type; otherwise, perform a general search.
    """
    entity_type = ENTITY_TYPES.get(search_term.lower())  # Get entity type ID

    if entity_type:
        # Query within a specific entity type
        sparql_query = f"""
        SELECT ?entity ?entityLabel ?description WHERE {{
          ?entity wdt:P31 wd:{entity_type}.  # Filter by specific entity type
          OPTIONAL {{ ?entity schema:description ?description FILTER (lang(?description) = "en") }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT {limit}
        """
    else:
        # General entity lookup when no predefined type is found
        sparql_query = f"""
        SELECT ?entity ?entityLabel ?description WHERE {{
          ?entity rdfs:label ?entityLabel .
          FILTER(CONTAINS(LCASE(?entityLabel), "{search_term.lower()}")).
          OPTIONAL {{ ?entity schema:description ?description FILTER (lang(?description) = "en") }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT {limit}
        """

    return execute_sparql_query(sparql_query)

def execute_sparql_query(query):
    """
    Sends a SPARQL query to Wikidata and processes the response.
    """
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
        print(f"Error fetching entities: {e}")
        return []

def ask_llm_to_select_entity(user_query, entities):
    """
    Pass the retrieved entity list to the LLM and let it select the most relevant one.
    """
    entity_options = "\n".join(
        [f"- {e['label']} ({e['entity_id']}): {e['description']}" for e in entities]
    )

    llm_prompt = f"""
    The user has entered the search term: "{user_query}"

    Below is a list of possible Wikidata entities that match the term:
    {entity_options}

    Your task:
    1. **Rank the top 5 most relevant entities** based on the search term.
    2. **Respond ONLY in the following JSON format**:
    
    Example JSON output format:
    [
      {{"entity_id": "QXXXXXX", "label": "Entity Name", "description": "Entity Description"}},
      {{"entity_id": "QYYYYYY", "label": "Entity Name", "description": "Entity Description"}},
      {{"entity_id": "QZZZZZZ", "label": "Entity Name", "description": "Entity Description"}}
    ]

    3. **Do not return explanations**. Just return the JSON response exactly as formatted.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system",
                       "content": "You are an assistant that selects the best Wikidata entity based on a search term."},
                      {"role": "user", "content": llm_prompt}],
            temperature=0
        )

        selected_entity = response.choices[0].message.content.strip()
        return selected_entity

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

# Standalone script for testing
if __name__ == "__main__":
    user_query = input("Enter a search term: ")
    entity_candidates = get_potential_entities(user_query)

    if not entity_candidates:
        print("No entities found.")
    else:
        selected_entity_id = ask_llm_to_select_entity(user_query, entity_candidates)
        print(f"\n[SELECTED ENTITY]: {selected_entity_id}")
import os
import requests
import openai
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not client.api_key:
    raise ValueError("Missing OpenAI API Key! Please set it in the .env file.")

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "LinkQ-Property-Search/1.0",
    "Accept": "application/json"
}

def get_entity_properties(entity_id):
    """
    Queries Wikidata for all properties linked to a given entity (e.g., "The Godfather").
    """
    sparql_query = f"""
    SELECT ?property ?propertyLabel ?propertyDescription WHERE {{
      wd:{entity_id} ?property ?value.  # Retrieve only statements linked to the entity
      FILTER(STRSTARTS(STR(?property), "http://www.wikidata.org/prop/direct/"))  # Only direct properties

      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
      OPTIONAL {{ ?property schema:description ?propertyDescription FILTER (LANG(?propertyDescription) = "en") }}
    }}
    LIMIT 50
    """

    try:
        response = requests.get(SPARQL_ENDPOINT, headers=HEADERS, params={"query": sparql_query, "format": "json"}, timeout=10)
        response.raise_for_status()
        data = response.json()

        properties = []
        for item in data.get("results", {}).get("bindings", []):
            property_id = item.get("property", {}).get("value", "").split("/")[-1]
            label = item.get("propertyLabel", {}).get("value", "No label available")
            description = item.get("propertyDescription", {}).get("value", "No description available")

            properties.append({
                "property_id": property_id,
                "label": label,
                "description": description
            })

        return properties

    except requests.RequestException as e:
        print(f"Error fetching properties: {e}")
        return []

def ask_llm_to_filter_properties(user_question, entity_label, properties):
    """
    Uses LLM to filter the most relevant properties matching the user's question.
    """
    property_list = "\n".join(
        [f"- {p['label']} ({p['property_id']}) - {p['description']}" for p in properties]
    )

    llm_prompt = f"""
    The user has asked: "{user_question}"

    The selected entity is: "{entity_label}"

    Below is a list of all properties linked to this entity:

    {property_list}

    Your task:
    1. **Identify the top 5 most relevant properties** that best match the user's question.
    2. **Consider both the property name and description** when selecting the most relevant.
    3. **Return ONLY in JSON format as follows**:

    [
      {{"property_id": "PXXXXXX", "label": "Property Name", "description": "Property description"}},
      {{"property_id": "PYYYYYY", "label": "Property Name", "description": "Property description"}}
    ]

    4. **DO NOT provide explanations**, just return the JSON response.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an assistant that filters the most relevant properties based on a user's question."},
                      {"role": "user", "content": llm_prompt}],
            temperature=0
        )

        # Extract JSON response
        json_response = response.choices[0].message.content.strip()
        filtered_properties = json.loads(json_response)

        return filtered_properties  # Return top 5 most relevant properties

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return []

# Standalone script for testing
if __name__ == "__main__":
    user_question = input("Enter your question: ")
    entity_id = input("Enter the entity ID: ")  # Example: Q47703 for "The Godfather"
    entity_label = input("Enter the entity label: ")  # Example: "The Godfather"

    # Step 1: Get all properties for the entity
    entity_properties = get_entity_properties(entity_id)

    if not entity_properties:
        print("No properties found.")
    else:
        # Step 2: Use LLM to filter properties
        relevant_properties = ask_llm_to_filter_properties(user_question, entity_label, entity_properties)

        print("\n[SELECTED PROPERTIES]:")
        for prop in relevant_properties:
            print(f"- {prop['label']} ({prop['property_id']}) - {prop['description']}")
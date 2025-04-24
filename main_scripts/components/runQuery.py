import requests
import json
import re

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

print("[DEBUG] runQuery.py imported successfully")

def extract_entities(query):
    """Extract entity IDs (Q and P numbers) from a SPARQL query."""
    try:
        # Look for patterns like wd:Q... or wdt:P... or ps:P... or p:P...
        entity_regex = r'(?:wd:|wdt:|ps:|p:|pq:)(Q|P)\d+'
        matches = list(re.finditer(entity_regex, query))
        print(f"[DEBUG] Raw entity matches: {[m.group() for m in matches]}")
        entities = [match.group() for match in matches]
        # Remove the prefix (wd:, wdt:, etc.) to get just the entity ID
        entities = [e.split(':')[1] for e in entities]
        return list(set(entities))
    except Exception as e:
        print(f"[ERROR] Failed to extract entities: {str(e)}")
        return []

def run_sparql_query(query: str):
    """
    Execute a SPARQL query against the Wikidata endpoint
    and return the JSON results.
    """
    try:
        print(f"[DEBUG] Running query: {query}")
        
        # First, extract entities from the query
        entities = extract_entities(query)
        print(f"[DEBUG] Extracted entities: {entities}")
        
        # Create entity info query only if we have entities
        entity_info = None
        if entities:
            try:
                # Create a query to get entity information
                entity_info_query = f"""
                SELECT ?id ?label ?description WHERE {{
                  VALUES ?id {{ {' '.join(f'wd:{id}' for id in entities)} }}
                  ?id rdfs:label ?label;
                      schema:description ?description.
                  FILTER(LANG(?label) = "en")
                  FILTER(LANG(?description) = "en")
                }}
                """
                
                # Run the entity info query
                entity_response = requests.get(
                    WIKIDATA_ENDPOINT,
                    params={'query': entity_info_query, 'format': 'json'},
                    headers={
                        'User-Agent': 'LinkQ/1.0 (https://github.com/yourusername/linkq; your@email.com)',
                        'Accept': 'application/json'
                    }
                )
                entity_response.raise_for_status()
                entity_info = entity_response.json()
                print(f"[DEBUG] Entity info retrieved successfully")
            except Exception as e:
                print(f"[WARNING] Failed to get entity info: {str(e)}")
                # Continue even if entity info fails
                pass

        # Run the main query
        main_response = requests.get(
            WIKIDATA_ENDPOINT,
            params={'query': query, 'format': 'json'},
            headers={
                'User-Agent': 'LinkQ/1.0 (https://github.com/yourusername/linkq; your@email.com)',
                'Accept': 'application/json'
            }
        )
        main_response.raise_for_status()
        main_results = main_response.json()
        print(f"[DEBUG] Main query executed successfully")

        # Return both results
        return {
            'query': query,
            'main_results': main_results,
            'entity_info': entity_info
        }

    except requests.exceptions.RequestException as e:
        error_msg = f"Error from Wikidata: {e.response.status_code} - {e.response.text}" if hasattr(e, 'response') else str(e)
        print(f"[ERROR] {error_msg}")
        return {'error': error_msg}
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse response: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] Full exception: {repr(e)}")
        return {"error": error_msg}
import requests

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

print("[DEBUG] runQuery.py imported successfully")
def run_sparql_query(query: str):
    """
    Execute a SPARQL query against the Wikidata endpoint
    and return the JSON results.
    """
    params = {
        "query": query,
        "format": "json"
    }
    response = requests.get(WIKIDATA_ENDPOINT, params=params)
    response.raise_for_status()  # Raises HTTPError if status != 200
    return response.json()
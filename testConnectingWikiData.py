import requests

# Wikidata SPARQL endpoint
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# SPARQL Query to get entities related to "cat" (Q146)
SPARQL_QUERY = """
SELECT ?cat ?catLabel ?description WHERE {
  ?cat wdt:P31 wd:Q146.  # Instances of 'cat' (Q146)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
LIMIT 10
"""

# Set headers to request JSON format
HEADERS = {
    "User-Agent": "Wikidata-Query-Test/1.0 (contact@example.com)",  # Replace with your email
    "Accept": "application/sparql-results+json"
}


def fetch_wikidata():
    """Fetch data from Wikidata using SPARQL query."""
    response = requests.get(SPARQL_ENDPOINT, params={"query": SPARQL_QUERY, "format": "json"}, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", {}).get("bindings", [])
        for item in results:
            cat_id = item.get("cat", {}).get("value", "Unknown")
            cat_label = item.get("catLabel", {}).get("value", "No label")
            description = item.get("description", {}).get("value", "No description available")
            print(f"Entity: {cat_label} ({cat_id}) - {description}")
    else:
        print(f"Error: Unable to fetch data (Status Code: {response.status_code})")


# Run the function
if __name__ == "__main__":
    fetch_wikidata()
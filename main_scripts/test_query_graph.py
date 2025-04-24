from components.query_graph import parse_sparql_for_graph
from components.runQuery import run_sparql_query

def test_query_graph_parsing():
    # Test Case: Japanese Film Directors with Palme d'Or
    test_query = """
    SELECT DISTINCT ?director ?directorLabel WHERE {
      ?director wdt:P27  wd:Q17;          # Japanese citizenship
               wdt:P106 wd:Q2526255;     # film director
               wdt:P166 wd:Q179808.      # Palme d'Or
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    """
    
    print("Testing query graph parsing...")
    print("\nInput Query:")
    print(test_query)
    
    # Get graph structure
    graph_data = parse_sparql_for_graph(test_query)
    
    print("\nParsed Graph Structure:")
    print("Nodes:")
    for node in graph_data['nodes']:
        print(f"  - {node['type']}: {node['id']} ({node['label']})")
    
    print("\nEdges:")
    for edge in graph_data['edges']:
        print(f"  - {edge['source']} --[{edge['label']}]--> {edge['target']}")
    
    # Test with actual Wikidata data
    print("\nFetching entity information...")
    query_result = run_sparql_query(test_query)
    
    if 'entity_info' in query_result:
        from components.query_graph import enrich_graph_data
        enriched_graph = enrich_graph_data(graph_data, query_result['entity_info'])
        
        print("\nEnriched Graph Structure:")
        print("Nodes with Wikidata labels:")
        for node in enriched_graph['nodes']:
            print(f"  - {node['type']}: {node['id']} ({node['label']})")
            if node['description']:
                print(f"    Description: {node['description']}")
        
        print("\nEdges with Wikidata labels:")
        for edge in enriched_graph['edges']:
            print(f"  - {edge['source']} --[{edge['label']}]--> {edge['target']}")

if __name__ == "__main__":
    test_query_graph_parsing() 
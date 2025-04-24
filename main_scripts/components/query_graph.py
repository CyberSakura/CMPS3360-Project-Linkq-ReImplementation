import re
from typing import Dict, List, TypedDict, Optional, Set
from dataclasses import dataclass

class Node(TypedDict):
    id: str
    type: str  # 'Variable' or 'Term'
    label: str
    description: Optional[str]

class Edge(TypedDict):
    source: str
    target: str
    label: str
    type: str

class GraphData(TypedDict):
    nodes: List[Node]
    edges: List[Edge]

def clean_entity_id(entity: str) -> str:
    """Clean entity ID by removing trailing punctuation."""
    return re.sub(r'[;.]$', '', entity)

def add_node(node_id: str, nodes: List[Node], node_ids: Set[str]) -> None:
    """Add a node to the graph if it doesn't exist."""
    print(f"[DEBUG] Adding node: {node_id}")
    cleaned_id = clean_entity_id(node_id)
    if cleaned_id in node_ids:
        print(f"[DEBUG] Node {cleaned_id} already exists")
        return
        
    node_type = "Variable" if node_id.startswith("?") else "Term"
    print(f"[DEBUG] Node type: {node_type}")
    
    nodes.append(Node(id=cleaned_id, type=node_type))
    node_ids.add(cleaned_id)
    print(f"[DEBUG] Added node: {cleaned_id}")

def add_edge(subject: str, predicate: str, obj: str, edges: List[Edge], edge_ids: Set[str]) -> None:
    """Add an edge to the graph if it doesn't exist."""
    print(f"[DEBUG] Adding edge: {subject} --[{predicate}]--> {obj}")
    subject_id = clean_entity_id(subject)
    obj_id = clean_entity_id(obj)
    edge_id = f"{subject_id}-{predicate}-{obj_id}"
    
    if edge_id in edge_ids:
        print(f"[DEBUG] Edge {edge_id} already exists")
        return
        
    edges.append(Edge(
        source=subject_id,
        target=obj_id,
        predicate=predicate
    ))
    edge_ids.add(edge_id)
    print(f"[DEBUG] Added edge: {edge_id}")

def parse_sparql_for_graph(query: str) -> GraphData:
    """Parse SPARQL query into a graph structure."""
    print("\n[DEBUG] Parsing SPARQL query for graph structure")
    print(f"[DEBUG] Input query:\n{query}")
    
    nodes = []
    edges = []
    node_ids = set()
    edge_ids = set()
    
    # Split query into blocks
    where_block = re.search(r'WHERE\s*\{([^}]*)\}', query, re.DOTALL)
    if not where_block:
        print("[DEBUG] No WHERE block found in query")
        return GraphData(nodes=[], edges=[])
    
    where_content = where_block.group(1)
    print(f"[DEBUG] WHERE content:\n{where_content}")
    
    # Split into statements
    statements = [s.strip() for s in where_content.split('.') if s.strip()]
    print(f"[DEBUG] Found {len(statements)} statements")
    
    for statement in statements:
        # Skip FILTER and SERVICE clauses
        if statement.startswith('FILTER') or statement.startswith('SERVICE'):
            print(f"[DEBUG] Skipping statement: {statement}")
            continue
            
        # Split into subject, predicate, object
        parts = statement.split()
        if len(parts) < 3:
            print(f"[DEBUG] Invalid statement format: {statement}")
            continue
            
        subject, predicate, obj = parts[:3]
        print(f"[DEBUG] Processing triple: {subject} {predicate} {obj}")
        
        # Add nodes
        add_node(subject, nodes, node_ids)
        add_node(obj, nodes, node_ids)
        
        # Add edge
        add_edge(subject, predicate, obj, edges, edge_ids)
    
    print(f"[DEBUG] Final graph structure:")
    print(f"Nodes: {nodes}")
    print(f"Edges: {edges}")
    
    return GraphData(nodes=nodes, edges=edges)

def enrich_graph_data(graph_data: GraphData, entity_info: dict) -> GraphData:
    """
    Enrich graph data with entity information from Wikidata.
    """
    if not entity_info or 'results' not in entity_info:
        return graph_data
        
    # Create a mapping of entity IDs to their labels and descriptions
    entity_details = {}
    for binding in entity_info['results']['bindings']:
        entity_id = binding['id']['value'].split('/')[-1]
        entity_details[entity_id] = {
            'label': binding['label']['value'],
            'description': binding.get('description', {}).get('value')
        }
    
    # Update nodes with entity information
    for node in graph_data['nodes']:
        if node['type'] == 'Term' and node['id'] in entity_details:
            node['label'] = entity_details[node['id']]['label']
            node['description'] = entity_details[node['id']]['description']
    
    # Update edges with property labels
    for edge in graph_data['edges']:
        if edge['label'] in entity_details:
            edge['label'] = entity_details[edge['label']]['label']
    
    return graph_data 
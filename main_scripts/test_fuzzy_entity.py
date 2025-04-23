from fuzzy_entity_search import get_potential_entities

user_query = "Godfather"
entities = get_potential_entities(user_query)

print("Entities found:", entities)
import openai
import os
import json
import re
from main_scripts.fuzzy_entity_search import (
    get_potential_entities,
    find_sub_entities,
)
from main_scripts.utils.command_parser import parse_command
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key:
    raise ValueError("Missing OpenAI API Key! Please set it in the .env file.")

def parse_final_query_and_summary(text: str):
    code_match = re.search(r'```sparql\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    sparql_query = code_match.group(1).strip() if code_match else ""

    summary_match = re.search(r'(?:Summary|Explanation):\s*(.*)', text, re.IGNORECASE)
    summary = summary_match.group(1).strip() if summary_match else ""

    return {
        "sparqlQuery": sparql_query,
        "summary": summary,
        "finalAnswer": text,  # The entire final text from the LLM
    }

def query_building_workflow(user_message):
    max_iterations = 5  # Reduced from 20 to prevent excessive iterations
    iteration = 0
    collected_data = {}

    # Build the initial system message.
    messages = [
        {
            "role": "system",
            "content": (
                "You are a SPARQL query building assistant for Wikidata. Your role is to help construct precise SPARQL queries.\n\n"
                "Before starting query construction, ensure the question is specific enough by checking:\n"
                "1. Are there specific timeframes? (e.g., 'in 2022' not 'recently')\n"
                "2. Are the entities clearly defined? (e.g., 'Academy Awards' not 'awards')\n"
                "3. Are the properties specific? (e.g., 'won Best Picture' not 'achievements')\n\n"
                "If the question is not specific enough, respond with:\n"
                "CLARIFY: <specific questions to make the query more precise>\n\n"
                "Only proceed with query construction when the question is specific enough.\n"
                "When ready, use these commands:\n"
                "  - ENTITY_SEARCH: <search term>  (to find relevant entities)\n"
                "  - PROPERTIES_SEARCH: <entity id>  (to find properties of an entity)\n"
                "  - TAIL_SEARCH: <entity id>, <property id>  (to find related entities)\n"
                "  - STOP  (when ready to generate final query)\n\n"
                f"User question: {user_message}"
            )
        }
    ]

    while iteration < max_iterations:
        iteration += 1

        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages
        )
        resp_text = response.choices[0].message.content.strip()
        print(f"[Query Strategist] Iteration {iteration}: {resp_text}")

        command, param = parse_command(resp_text)
        print("[DEBUG]: command:", command)

        if command == "CLARIFY":
            print("[Query Strategist] Received CLARIFY command.")
            return f"CLARIFY: {param}"

        if command == "STOP":
            print("[Query Strategist] Received STOP command. Finalizing query generation.")
            # Build a new, clean context for final query generation:
            final_messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a SPARQL query expert. Based on the collected data, construct a SPARQL query "
                        "to answer the user's question. Include a brief explanation of the query.\n\n"
                        f"User question: {user_message}\n"
                        f"Collected Data: {json.dumps(collected_data)}\n\n"
                        "Return the response in this format:\n"
                        "```sparql\n[SPARQL QUERY]\n```\n"
                        "Explanation: [Brief explanation of the query]"
                    )
                }
            ]
            final_response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=final_messages
            )
            final_query = final_response.choices[0].message.content.strip()
            print(f"[Query Strategist] Final query: {final_query}")
            return final_query

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

        # Append the latest result as a new system message.
        messages.append({
            "role": "system",
            "content": f"Previous result: {result_text}"
        })

        if iteration >= max_iterations:
            # If we've reached max iterations, force a STOP
            command = "STOP"
            continue

    # If we exit the loop without a STOP command, generate a final query
    final_messages = [
        {
            "role": "system",
            "content": (
                "You are a SPARQL query expert. Based on the collected data, construct a SPARQL query "
                "to answer the user's question. Include a brief explanation of the query.\n\n"
                f"User question: {user_message}\n"
                f"Collected Data: {json.dumps(collected_data)}\n\n"
                "Return the response in this format:\n"
                "```sparql\n[SPARQL QUERY]\n```\n"
                "Explanation: [Brief explanation of the query]"
            )
        }
    ]
    final_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=final_messages
    )
    final_query = final_response.choices[0].message.content.strip()
    print(f"[Query Strategist] Final query: {final_query}")
    return final_query

if __name__ == "__main__":
    while True:
        user_query = input("Enter your question: ")
        final_sparql_query = query_building_workflow(user_query)

        # Check if the workflow returned a clarification
        if final_sparql_query.startswith("Clarification:"):
            print("\nThe system requires further clarification:")
            print(final_sparql_query)
            print("Please provide a more detailed question.\n")
        else:
            print("\nFinal SPARQL Query and explanation:")
            print(final_sparql_query)
            break
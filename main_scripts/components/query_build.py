import openai
import os
import json
import re
from main_scripts.fuzzy_entity_search import (
    parse_command,
    get_potential_entities,
    find_sub_entities,
)
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

# def query_building_workflow(user_message):
#     """
#     Your existing query-building logic goes here.
#     In the end, we parse the final LLM text into a structured dict.
#     """
#     max_iterations = 20
#     iteration = 0
#     collected_data = {}
#
#     messages = [
#         {
#             "role": "system",
#             "content": (
#                 "You are a SPARQL query building assistant for our knowledge base. Analyze the user's question and determine the necessary "
#                 "entities and relationships needed to build a SPARQL query. Respond with **only one** of the following commands:\n"
#                 "  - ENTITY_SEARCH: <search term>\n"
#                 "  - PROPERTIES_SEARCH: <entity id>\n"
#                 "  - TAIL_SEARCH: <entity id>, <property id>\n"
#                 "  - STOP\n"
#                 "  - CLARIFY: <your clarification question>\n\n"
#                 "If the question is specific and clear enough, respond with STOP so that the final query is generated immediately.\n"
#                 f"User question: {user_message}"
#             )
#         }
#     ]
#
#     while iteration < max_iterations:
#         iteration += 1
#         client = openai.OpenAI()
#         response = client.chat.completions.create(
#             model="gpt-4-turbo",
#             messages=messages
#         )
#         resp_text = response.choices[0].message.content.strip()
#
#         command, param = parse_command(resp_text)
#
#         # If we receive STOP, we break out and parse the final query from this same text
#         if command == "STOP":
#             # We'll parse the LLM text as our final query
#             parsed = parse_final_query_and_summary(resp_text)
#             return parsed
#
#         # Otherwise handle other commands (ENTITY_SEARCH, etc.)
#         if command == "ENTITY_SEARCH":
#             results = get_potential_entities(param)
#             collected_data.setdefault("entities", []).append(results)
#             result_text = f"Entity results: {results}"
#         elif command == "PROPERTIES_SEARCH":
#             result_text = "Property results: [{'property': 'dummy_property', 'value': 'dummy_value'}]"
#             collected_data.setdefault("properties", []).append(result_text)
#         elif command == "TAIL_SEARCH":
#             parts = param.split(",")
#             if len(parts) >= 2:
#                 ent_id = parts[0].strip()
#                 tail_results = find_sub_entities(ent_id)
#                 collected_data.setdefault("tail", []).append(tail_results)
#                 result_text = f"Tail results: {tail_results}"
#             else:
#                 result_text = "Error: TAIL_SEARCH format invalid."
#         elif command == "CLARIFY":
#             # If LLM is clarifying, you might treat it as final or append a message telling it to proceed
#             result_text = f"Clarification noted: {param}"
#         else:
#             # Unknown or unrecognized command
#             result_text = "Error: Unrecognized command."
#
#         messages.append({
#             "role": "system",
#             "content": f"Previous result: {result_text}"
#         })
#
#     # If we exit the loop without STOP, force a final parse of the last LLM response
#     # Or create a new message that says "Construct the final SPARQL query..."
#     fallback_response = client.chat.completions.create(
#         model="gpt-4-turbo",
#         messages=messages + [
#             {
#                 "role": "system",
#                 "content": (
#                     f"Collected Data: {json.dumps(collected_data)}\n"
#                     f"Now please construct the final SPARQL query. Provide a short summary as well."
#                 )
#             }
#         ]
#     )
#     fallback_text = fallback_response.choices[0].message.content.strip()
#     parsed = parse_final_query_and_summary(fallback_text)
#     return parsed

def query_building_workflow(user_message):
    max_iterations = 20
    iteration = 0
    collected_data = {}

    # Build the initial system message.
    messages = [
        {
            "role": "system",
            "content": (
                "You are a SPARQL query building assistant for our knowledge base. Analyze the user's question and determine the necessary "
                "entities and relationships needed to build a SPARQL query. Respond with **only one** of the following commands (and nothing else):\n"
                "  - ENTITY_SEARCH: <search term>\n"
                "  - PROPERTIES_SEARCH: <entity id>\n"
                "  - TAIL_SEARCH: <entity id>, <property id>\n"
                "  - STOP\n"
                "  - CLARIFY: <your clarification question>\n\n"
                "If the question is specific and clear enough, respond with STOP so that the final query is generated immediately.\n"
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

        # Instead of breaking immediately on CLARIFY, log it.
        if command == "CLARIFY":
            print("[Query Strategist] Received CLARIFY command. Logging it but forcing STOP after a threshold.")
            # Optionally, you can log this clarification:
            messages.append({
                "role": "system",
                "content": f"Clarification noted: {param}. Proceeding as if the query is clear."
            })
            # Force the workflow to treat it as a STOP after one or two clarifications.
            if iteration >= 2:  # or use a counter for clarifications
                command = "STOP"

        if command == "STOP":
            print("[Query Strategist] Received STOP command. Finalizing query generation.")
            # Build a new, clean context for final query generation:
            final_messages = [
                {
                    "role": "system",
                    "content": f"User question: {user_message}"
                },
                {
                    "role": "system",
                    "content": f"Collected Data: {json.dumps(collected_data)}"
                },
                {
                    "role": "system",
                    "content": (
                        "Disregard all previous iterative messages. "
                        "Based solely on the above, please construct the final SPARQL query to answer the user's question and provide a brief explanation. "
                        "Return only the SPARQL query and the explanation."
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
        print(f"[Query Strategist] Updated messages:\n{messages}\n")

        if iteration >= max_iterations or not collected_data.get("entities"):
            messages.append({
                "role": "system",
                "content": (
                    "No useful entity data has been collected. Despite this, construct a default SPARQL query "
                    f"to answer the user's question: {user_message}"
                )
            })
            break

    # Append a final message to instruct the LLM to construct the final query.
    final_messages = [
        {
            "role": "system",
            "content": f"User question: {user_message}"
        },
        {
            "role": "system",
            "content": f"Collected Data: {json.dumps(collected_data)}"
        },
        {
            "role": "system",
            "content": (
                "Disregard previous iterative messages. Based solely on the above, please construct the final SPARQL query "
                "to answer the user's question and provide a brief explanation."
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
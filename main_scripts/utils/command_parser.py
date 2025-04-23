import re

def parse_command(response_text):
    response_text = response_text.strip()

    # Create a dictionary mapping command keywords to their regex patterns
    commands = {
        "STOP": r"\bSTOP\b",
        "ENTITY_SEARCH": r"ENTITY_SEARCH:\s*(.+)",
        "PROPERTIES_SEARCH": r"PROPERTIES_SEARCH:\s*(.+)",
        "TAIL_SEARCH": r"TAIL_SEARCH:\s*(.+)",
        "CLARIFY": r"CLARIFY:\s*(.+)"
    }

    # Check for STOP (if response is exactly "STOP", or even if found somewhere)
    if re.search(commands["STOP"], response_text, re.IGNORECASE):
        return "STOP", ""

    # Try to find any of the commands in the text
    for command, pattern in commands.items():
        if command == "STOP":
            continue  # already handled STOP
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            return command, match.group(1).strip()

    return "UNKNOWN", response_text 
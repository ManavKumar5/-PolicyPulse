import re
import json
from pathlib import Path


def load_rules(rule_file="rules.json"):
    """Load policy rules from a JSON file."""
    with open(rule_file, "r", encoding="utf-8") as f:
        return json.load(f)


def scan_text(text, rules):
    """
    Scan the given text against rules.
    Returns a list of flagged items.
    """
    flagged = []
    for rule in rules:
        pattern = re.compile(rule["pattern"], re.IGNORECASE)
        matches = pattern.findall(text)
        for match in matches:
            flagged.append(
                {
                    "rule_id": rule["id"],
                    "description": rule["description"],
                    "match": match,
                }
            )
    return flagged

"""JSON schemas for LLM responses."""

import json
from typing import Any

# Define schema as Python dict for better maintainability
NAME_SUGGESTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "original_name": {
            "type": "string",
            "description": "The original symbol name being analyzed",
        },
        "suggested_name": {
            "type": "string",
            "description": "The suggested improved name (empty string if no change needed)",
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Confidence score for this suggestion (0.0 to 1.0)",
        },
        "rationale": {
            "type": "string",
            "description": "Explanation of why this name is better",
        },
        "rules_addressed": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of rule IDs that this suggestion addresses",
        },
    },
    "required": ["original_name", "suggested_name", "confidence", "rationale"],
    "additionalProperties": False,
}


def get_name_suggestion_schema() -> str:
    """Get the NameSuggestion JSON schema as a formatted string.

    Returns:
        Pretty-printed JSON schema string for LLM prompt
    """
    return json.dumps(NAME_SUGGESTION_SCHEMA, indent=2)


def load_schema(schema_name: str) -> dict[str, Any]:
    """Load a JSON schema by name.

    Args:
        schema_name: Name of the schema (e.g., 'name_suggestion')

    Returns:
        Schema dictionary

    Raises:
        ValueError: If schema_name is not recognized
    """
    schemas = {
        "name_suggestion": NAME_SUGGESTION_SCHEMA,
    }

    if schema_name not in schemas:
        raise ValueError(f"Unknown schema: {schema_name}. Available: {list(schemas.keys())}")

    return schemas[schema_name]


def validate_response(response: dict[str, Any], schema_name: str = "name_suggestion") -> bool:
    """Validate an LLM response against a schema.

    Args:
        response: The response dictionary to validate
        schema_name: Name of schema to validate against

    Returns:
        True if valid, False otherwise

    Note:
        For production use, consider using jsonschema library for full validation
    """
    schema = load_schema(schema_name)
    required_fields = schema.get("required", [])

    # Basic validation - check required fields exist
    for field in required_fields:
        if field not in response:
            return False

    return True

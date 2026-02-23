from .utils import load_openapi, get_response_schema, validate_response


def test_templates_response_schema():
    openapi = load_openapi()
    schema = get_response_schema(openapi, "/templates", "get")

    mock_response = {
        "templates": [
            {
                "id": "lesson_outline_basic",
                "name": "Basic Lesson Outline",
                "description": "Standard structured outline template"
            }
        ]
    }

    validate_response(openapi, schema, mock_response)
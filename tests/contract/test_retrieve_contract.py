from .utils import load_openapi, get_response_schema, validate_response


def test_retrieve_response_schema():
    openapi = load_openapi()
    schema = get_response_schema(openapi, "/retrieve", "post")

    mock_response = {
        "chunks": [
            {
                "text": "Example text",
                "chapter": "1",
                "section": "1.1",
                "score": 0.95
            }
        ]
    }

    validate_response(openapi, schema, mock_response)

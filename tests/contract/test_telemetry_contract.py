from .utils import load_openapi


def test_telemetry_response_contract():
    openapi = load_openapi()
    responses = openapi["paths"]["/telemetry/log"]["post"]["responses"]

    # Ensure 204 status exists
    assert "204" in responses

    # Ensure 204 has no content body defined (No Content contract)
    assert "content" not in responses["204"]
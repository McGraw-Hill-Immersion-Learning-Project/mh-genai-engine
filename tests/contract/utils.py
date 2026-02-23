import yaml
import jsonschema
from pathlib import Path
from jsonschema import Draft202012Validator


def load_openapi():
    openapi_path = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.yaml"
    with open(openapi_path, "r") as f:
        return yaml.safe_load(f)


def get_response_schema(openapi_spec, path, method, status_code="200"):
    return (
        openapi_spec["paths"][path][method]["responses"][status_code]
        ["content"]["application/json"]["schema"]
    )


def validate_response(openapi_spec, schema, data):
    validator = Draft202012Validator(schema, resolver=jsonschema.RefResolver.from_schema(openapi_spec))
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    if errors:
        raise AssertionError(f"Schema validation failed: {errors[0].message}")
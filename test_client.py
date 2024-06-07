import json
import random
import string
import sys
from bravado.client import SwaggerClient
from bravado.requests_client import RequestsClient
import pytest


def load_swagger_spec(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def generate_dummy_value(param):
    """Generate dummy values based on parameter types."""
    if param['type'] == 'string':
        return ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    elif param['type'] == 'integer':
        return random.randint(1, 100)
    elif param['type'] == 'boolean':
        return random.choice([True, False])
    elif param['type'] == 'array':
        return [generate_dummy_value(param['items'])]
    elif param['type'] == 'object':
        return {k: generate_dummy_value(v) for k, v in param['properties'].items()}
    else:
        return 'test_value'


def get_parameters(parameters):
    """Generate parameters with dummy values for testing."""
    params = {}
    for param in parameters:
        if param['in'] == 'query':
            params[param['name']] = generate_dummy_value(param)
        elif param['in'] == 'path':
            params[param['name']] = generate_dummy_value(param)
        elif param['in'] == 'body':
            params[param['name']] = generate_dummy_value(param['schema'])
    return params


def create_test_cases(swagger_spec_path):
    swagger_spec = load_swagger_spec(swagger_spec_path)

    http_client = RequestsClient()
    client = SwaggerClient.from_spec(swagger_spec, http_client=http_client, config={
                                     'validate_responses': False})

    for path, methods in swagger_spec['paths'].items():
        for method, operation in methods.items():
            operation_id = operation['operationId']
            parameters = operation.get('parameters', [])
            param_values = get_parameters(parameters)

            yield operation_id, method, path, param_values, client


@pytest.mark.parametrize("swagger_spec_path", [sys.argv[1]])
def test_api(swagger_spec_path):
    for operation_id, method, path, param_values, client in create_test_cases(swagger_spec_path):
        try:
            api_method = getattr(client, operation_id)
            response = api_method(**param_values).response().result
            print(f'Success: {method.upper()} {path} -> {response}')
        except Exception as e:
            print(f'Error: {method.upper()} {path} -> {e}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <swagger_json_file>")
        sys.exit(1)
    pytest.main([__file__])


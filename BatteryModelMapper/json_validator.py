from jsonschema import validate, ValidationError
from .json_loader import JSONLoader

class JSONValidator:
    @staticmethod
    def validate(data, schema_url):
        schema = JSONLoader.load(schema_url)
        try:
            validate(instance=data, schema=schema)
            print("JSON is valid.")
        except ValidationError as e:
            print(f"JSON validation error: {e.message}")
            raise

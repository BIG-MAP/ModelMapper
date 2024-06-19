import json
import ast
import requests
from rdflib import Graph, URIRef

class OntologyParser:
    def __init__(self, ontology_url):
        self.graph = Graph()
        response = requests.get(ontology_url)
        response.raise_for_status()
        self.graph.parse(data=response.text, format='ttl')
        self.key_map = {
            'bpx': URIRef("https://w3id.org/emmo/domain/battery-model-lithium-ion#bmli_0a5b99ee_995b_4899_a79b_925a4086da37"),
            'cidemod': URIRef("https://w3id.org/emmo/domain/battery-model-lithium-ion#bmli_1b718841_5d72_4071_bb71_fc4a754f5e30"),
            'battmo': URIRef("https://w3id.org/emmo/domain/battery-model-lithium-ion#bmli_2c718841_6d73_5082_bb81_gc5b754f6e40")  # Placeholder URI
        }

    def parse_key(self, key):
        try:
            return ast.literal_eval(key)
        except (ValueError, SyntaxError) as e:
            print(f"Error parsing key: {key} - {e}")
            return []

    def get_mappings(self, input_type, output_type):
        input_key = self.key_map.get(input_type)
        output_key = self.key_map.get(output_type)
        if not input_key or not output_key:
            raise ValueError(f"Invalid input or output type: {input_type}, {output_type}")

        mappings = {}
        for subject in self.graph.subjects():
            input_value = None
            output_value = None
            for predicate, obj in self.graph.predicate_objects(subject):
                if predicate == input_key:
                    input_value = self.parse_key(str(obj))
                elif predicate == output_key:
                    output_value = self.parse_key(str(obj))
            if input_value and output_value:
                mappings[tuple(input_value)] = tuple(output_value)
                print(f"Mapping added: {tuple(input_value)} -> {tuple(output_value)}")
        return mappings

class JSONLoader:
    @staticmethod
    def load(json_url):
        response = requests.get(json_url)
        response.raise_for_status()
        return response.json()

class ParameterMapper:
    def __init__(self, mappings):
        self.mappings = mappings

    def map_parameters(self, input_data):
        output_data = {}
        for input_key, output_key in self.mappings.items():
            value = self.get_value_from_path(input_data, input_key)
            if value is not None:
                self.set_value_from_path(output_data, output_key, value)
        return output_data

    def get_value_from_path(self, data, keys):
        try:
            for key in keys:
                if isinstance(key, str):
                    key = key.strip()
                if isinstance(data, dict):
                    data = data[key]
                elif isinstance(data, list):
                    key = int(key)  # Convert key to integer for list index
                    data = data[key]
                else:
                    return None
            return data
        except (KeyError, IndexError, ValueError, TypeError) as e:
            print(f"Error accessing key {key} in path {keys}: {e}")
            return None

    def set_value_from_path(self, data, keys, value):
        try:
            for key in keys[:-1]:
                if isinstance(key, str):
                    key = key.strip()
                if key.isdigit():
                    key = int(key)
                    while len(data) <= key:
                        data.append({})
                    data = data[key]
                else:
                    if key not in data:
                        data[key] = {}
                    data = data[key]
            final_key = keys[-1]
            if isinstance(final_key, str):
                final_key = final_key.strip()
            if isinstance(final_key, str) and final_key.isdigit():
                final_key = int(final_key)
            data[final_key] = value
            print(f"Set value for path {keys}: {value}")
        except (KeyError, IndexError, ValueError, TypeError) as e:
            print(f"Error setting value for path {keys}: {e}")

class JSONWriter:
    @staticmethod
    def write(data, output_path):
        with open(output_path, 'w') as file:
            json.dump(data, file, indent=4)

if __name__ == "__main__":
    ontology_url = 'https://w3id.org/emmo/domain/battery-model-lithium-ion/latest'
    input_json_url = 'https://raw.githubusercontent.com/cidetec-energy-storage/cideMOD/main/data/data_Chen_2020/params_tuned_vOCPexpression.json'
    output_json_path = 'converted_battery_parameters.json'
    input_type = 'cidemod'  # Replace with the input type (bpx, cidemod, battmo)
    output_type = 'bpx'  # Replace with the output type (bpx, cidemod, battmo)

    # Initialize the OntologyParser
    ontology_parser = OntologyParser(ontology_url)
    mappings = ontology_parser.get_mappings(input_type, output_type)
    print("Mappings:", json.dumps({str(k): str(v) for k, v in mappings.items()}, indent=4))

    # Load the input JSON file
    input_data = JSONLoader.load(input_json_url)
    print("Input Data:", json.dumps(input_data, indent=4))

    # Map the parameters using the mappings from the ontology
    parameter_mapper = ParameterMapper(mappings)
    output_data = parameter_mapper.map_parameters(input_data)
    print("Output Data:", json.dumps(output_data, indent=4))

    # Write the output JSON file
    JSONWriter.write(output_data, output_json_path)
    print(f"Converted JSON saved to {output_json_path}")

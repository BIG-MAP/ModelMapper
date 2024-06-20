import json
import ast
import requests
from rdflib import Graph, URIRef
from jsonschema import validate, ValidationError
import re

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

class JSONWriter:
    @staticmethod
    def write(data, output_path):
        with open(output_path, 'w') as file:
            json.dump(data, file, indent=4)

class ParameterMapper:
    def __init__(self, mappings, template, input_url, output_type):
        self.mappings = mappings
        self.template = template
        self.input_url = input_url
        self.output_type = output_type
        self.defaults_used = []

    def map_parameters(self, input_data):
        output_data = self.template.copy()
        for input_key, output_key in self.mappings.items():
            value = self.get_value_from_path(input_data, input_key)
            if value is not None:
                if isinstance(value, str):
                    value = self.replace_variables(value)
                self.set_value_from_path(output_data, output_key, value)
                self.remove_default_from_used(output_key)
        self.set_bpx_header(output_data)
        return output_data

    def replace_variables(self, value):
        if isinstance(value, str):
            value = re.sub(r'\bx_s\b', 'x', value)
            value = re.sub(r'\bc_e\b', 'x', value)
        return value

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
                if isinstance(key, int) or key.isdigit():
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
            if isinstance(final_key, int) or (isinstance(final_key, str) and final_key.isdigit()):
                final_key = int(final_key)
            data[final_key] = value
            print(f"Set value for path {keys}: {value}")
        except (KeyError, IndexError, ValueError, TypeError) as e:
            print(f"Error setting value for path {keys}: {e}")

    def remove_default_from_used(self, keys):
        path = "Parameterisation"
        for key in keys:
            if isinstance(key, str):
                path += f".{key.strip()}"
            elif isinstance(key, int):
                path += f"[{key}]"
        if path in self.defaults_used:
            self.defaults_used.remove(path)

    def set_bpx_header(self, data):
        data["Header"] = {
            "BPX": 0.1,
            "Title": "An autoconverted parameter set using BatteryModelMapper",
            "Description": f"This data set was automatically generated from {self.input_url}. Please check carefully.",
            "Model": "DFN"
        }

if __name__ == "__main__":
    ontology_url = 'https://w3id.org/emmo/domain/battery-model-lithium-ion/latest'
    input_json_url = 'https://raw.githubusercontent.com/cidetec-energy-storage/cideMOD/main/data/data_Chen_2020/params_tuned_vOCPexpression.json'
    output_json_path = 'converted_battery_parameters.json'
    template_url = 'https://raw.githubusercontent.com/FaradayInstitution/BPX/main/examples/nmc_pouch_cell_BPX.json'
    input_type = 'cidemod'
    output_type = 'bpx'

    # Initialize the OntologyParser
    ontology_parser = OntologyParser(ontology_url)
    mappings = ontology_parser.get_mappings(input_type, output_type)
    print("Mappings:", json.dumps({str(k): str(v) for k, v in mappings.items()}, indent=4))

    # Load the input JSON file
    input_data = JSONLoader.load(input_json_url)
    print("Input Data:", json.dumps(input_data, indent=4))

    # Load the template JSON file
    template_data = JSONLoader.load(template_url)

    # Map the parameters using the mappings from the ontology
    parameter_mapper = ParameterMapper(mappings, template_data, input_json_url, output_type)
    output_data = parameter_mapper.map_parameters(input_data)
    output_data["defaults_used"] = list(parameter_mapper.defaults_used)
    print("Output Data:", json.dumps(output_data, indent=4))

    # Write the output JSON file
    JSONWriter.write(output_data, output_json_path)

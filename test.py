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
        self.bpxKey = URIRef("https://w3id.org/emmo/domain/battery-model-lithium-ion#bmli_0a5b99ee_995b_4899_a79b_925a4086da37")
        self.cidemodKey = URIRef("https://w3id.org/emmo/domain/battery-model-lithium-ion#bmli_1b718841_5d72_4071_bb71_fc4a754f5e30")

    def parse_key(self, key):
        try:
            return ast.literal_eval(key)
        except (ValueError, SyntaxError) as e:
            print(f"Error parsing key: {key} - {e}")
            return []

    def get_mappings(self):
        mappings = {}
        for subject in self.graph.subjects():
            bpxKey = None
            cidemodKey = None
            for predicate, obj in self.graph.predicate_objects(subject):
                if predicate == self.bpxKey:
                    bpxKey = self.parse_key(str(obj))
                elif predicate == self.cidemodKey:
                    cidemodKey = self.parse_key(str(obj))
            if bpxKey and cidemodKey:
                mappings[tuple(bpxKey)] = tuple(cidemodKey)
                print(f"Mapping added: {tuple(bpxKey)} -> {tuple(cidemodKey)}")
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
        for bpx_key, cidemod_key in self.mappings.items():
            value = self.get_value_from_path(input_data, bpx_key)
            if value is not None:
                self.set_value_from_path(output_data, cidemod_key, value)
        return output_data

    def get_value_from_path(self, data, keys):
        for key in keys:
            key = key.strip()  # Ensure there are no leading/trailing spaces
            if isinstance(data, dict):
                data = data.get(key)
                if data is None:
                    print(f"Key {key} not found in path {keys}")
                    return None
            else:
                return None
        return data

    def set_value_from_path(self, data, keys, value):
        for key in keys[:-1]:
            key = key.strip()  # Ensure there are no leading/trailing spaces
            if key not in data:
                data[key] = {}
            data = data[key]
        data[keys[-1].strip()] = value
        print(f"Set value for path {keys}: {value}")

class JSONWriter:
    @staticmethod
    def write(data, output_path):
        with open(output_path, 'w') as file:
            json.dump(data, file, indent=4)

if __name__ == "__main__":
    ontology_url = 'https://w3id.org/emmo/domain/battery-model-lithium-ion/latest'  # Replace with your ontology URL
    input_json_url = 'https://raw.githubusercontent.com/FaradayInstitution/BPX/main/examples/lfp_18650_cell_BPX.json'  # Replace with your JSON URL
    output_json_path = 'converted_battery_parameters.json'

    # Initialize the OntologyParser
    ontology_parser = OntologyParser(ontology_url)
    mappings = ontology_parser.get_mappings()
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

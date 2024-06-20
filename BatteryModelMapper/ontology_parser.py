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

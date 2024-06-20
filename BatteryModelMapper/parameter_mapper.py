import json
import re

class ParameterMapper:
    def __init__(self, mappings, template, input_url, output_type, input_type):
        self.mappings = mappings
        self.template = template
        self.input_url = input_url
        self.output_type = output_type
        self.input_type = input_type
        self.defaults_used = set(self.get_all_paths(template))

    def map_parameters(self, input_data):
        output_data = self.template.copy()
        for input_key, output_key in self.mappings.items():
            value = self.get_value_from_path(input_data, input_key)
            if value is not None:
                if isinstance(value, str):
                    value = self.replace_variables(value)
                if self.input_type == 'cidemod' and 'kinetic_constant' in input_key:
                    value = self.scale_kinetic_constant(value)
                self.set_value_from_path(output_data, output_key, value)
                self.remove_default_from_used(output_key)
        self.set_bpx_header(output_data)
        self.remove_high_level_defaults()
        return output_data

    def replace_variables(self, value):
        if isinstance(value, str):
            value = re.sub(r'\bx_s\b', 'x', value)
            value = re.sub(r'\bc_e\b', 'x', value)
        return value

    def scale_kinetic_constant(self, value):
        try:
            return value * 1e6
        except TypeError:
            print(f"Error scaling kinetic_constant value: {value}")
            return value

    def get_all_paths(self, data, path=""):
        paths = set()
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                paths.add(current_path)
                paths.update(self.get_all_paths(value, current_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                paths.add(current_path)
                paths.update(self.get_all_paths(item, current_path))
        return paths

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
        self.defaults_used.discard(path)

    def set_bpx_header(self, data):
        data["Header"] = {
            "BPX": 0.1,
            "Title": "An autoconverted parameter set using BatteryModelMapper",
            "Description": f"This data set was automatically generated from {self.input_url}. Please check carefully.",
            "Model": "DFN"
        }
        data.pop("Validation", None)

    def remove_high_level_defaults(self):
        self.defaults_used = {path for path in self.defaults_used if not any(k in path for k in ["Parameterisation", "Header"])}

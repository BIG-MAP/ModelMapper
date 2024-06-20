import json

class JSONWriter:
    @staticmethod
    def write(data, output_path):
        with open(output_path, 'w') as file:
            json.dump(data, file, indent=4)

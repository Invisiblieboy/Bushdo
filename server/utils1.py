import json


class Server:
    def __init__(self):
        self.path_data = rf'../data/data.json'
        self.data = self.update_data(get_from_file=True)

    def update_data(self, get_from_file=False, get_from_memory=False):
        if get_from_file:
            with open(self.path_data, 'r') as file:
                self.data = json.load(file)
        elif get_from_memory:
            pass
        else:
            with open(self.path_data, 'w') as file:
                json.dump(self.data, file, indent=2)
        return self.data

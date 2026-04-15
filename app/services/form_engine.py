import json

class FormEngine:
    def __init__(self, path):
        with open(path, "r") as f:
            self.form = json.load(f)
        self.fields = self.form["fields"]

    def get_question(self, index):
        if index < len(self.fields):
            return self.fields[index]
        return None

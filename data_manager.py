import yaml
import os

DATA_PATH = "data.yaml"

def load_data():
    if not os.path.exists(DATA_PATH):
        return {"pinball_machines": [], "players": [], "scores": []}
    with open(DATA_PATH, "r") as file:
        return yaml.safe_load(file)

def save_data(data):
    with open(DATA_PATH, "w") as file:
        yaml.dump(data, file)

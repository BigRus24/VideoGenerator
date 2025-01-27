import tomli
import os

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.toml")
    
    with open(config_path, "r+b") as config_file:
        return tomli.load(config_file)
    
config = load_config()
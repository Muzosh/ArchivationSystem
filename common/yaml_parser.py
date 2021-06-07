import yaml

def parse_yaml_config(path):
    with open(path) as f:
        return yaml.load(f, Loader= yaml.SafeLoader) 

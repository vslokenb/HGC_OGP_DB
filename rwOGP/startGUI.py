import yaml
from src.file_selector import fire_GUI
from main import load_config, create_default_config
from src.upload_inspect import DBClient

def main_func():
    settings = load_config()
    if settings is None:
        print("Program will now exit. Please update the configuration file and run the program again.")
        create_default_config()
        return
    else:
        config_path = settings['config_path']
        invent_path = settings['inventory_path']
        print("Using configuration file to create database client...")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    
    client = DBClient(config)
    fire_GUI(client)

if __name__ == "__main__":
    main_func()
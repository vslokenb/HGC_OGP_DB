import os, yaml, sys

pjoin = os.path.join

file_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = pjoin(file_dir, 'read-write-ogp', 'src')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.upload_inspect import DBClient
from src.parse_data import DataParser
from src.file_selector import fire_GUI

def create_default_config(file_path):
    """Create a default YAML configuration file."""
    print("Creating default configuration file...")
    default_config = {
        'host': 'localhost',
        'database': 'hgcdb',
        'user': 'ogp_user',
        'password': 'hgcalpass',
        'inst_code': 'CM',
        'institution_name': 'Carnegie Mellon University'
    }
    with open(file_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)

    print(f"Configuration file created at {file_path}")
    print("Please update the configuration file with the correct database connection information!")

def main():
    config_file = 'config.yaml'
    if not os.path.exists(config_file):
        create_default_config(config_file)
        print("Program will now exit. Please update the configuration file and run the program again.")
        return
    else:
        print("Using configuration file to create database client...")

    dbclient = DBClient(config_file)
    fire_GUI(dbclient)

if __name__ == '__main__':
    main()
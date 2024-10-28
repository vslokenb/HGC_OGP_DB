import os, yaml, sys, glob, re

pjoin = os.path.join

file_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = pjoin(file_dir, 'rwOGP')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.upload_inspect import DBClient
from src.parse_data import DataParser
from src.process_im import SurveyProcessor
from src.file_selector import fire_GUI

SETTINGS_FILE = pjoin(os.path.expanduser('~'), ".my-cli-tool", "settings.yaml")

def create_default_config():
    """Create a default YAML configuration file and a SETTINGS file to keep track of program environment vars. Only needs to be set up once ideally."""

    print("Do you want to create the config file at a custom location? (y/n)")
    choice = input().strip().lower()

    home_dir = os.path.expanduser('~')

    if choice == 'y':
        print("Please enter the directory where you want to create the config file:")
        custom_path = os.path.expanduser(input().strip())
        if os.path.isdir(custom_path):
            config_file = pjoin(custom_path, "config.yaml")
    else:
        print("Creating the config file in the default location...")
        config_dir = pjoin(home_dir, '.config')
        config_file = pjoin(config_dir, 'config.yaml')

    print("Creating default configuration file...")
    default_config = {
        'host': 'localhost',
        'database': 'hgcdb',
        'user': 'ogp_user',
        'password': 'hgcalpass',
        'inst_code': 'CM',
        'institution_name': 'Carnegie Mellon University',
        'ogp_survey_dir': '/path/to/ogp/survey/directory',
    }

    with open(config_file, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)

    print(f"Configuration file created at {config_file}")
    print("Please update the configuration file with the correct database connection information!")

    os.makedirs(pjoin(home_dir, '.my-cli-tool'), exist_ok=True)
    inventory_path = pjoin(home_dir, '.my-cli-tool', 'inventory.json')

    with open(SETTINGS_FILE, 'w') as f:
        yaml.dump({'config_path': config_file, 'inventory_path': inventory_path}, f)

def load_config():
    """Load the configuration file from the default location."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = yaml.safe_load(f)
        return settings['config_path']
    return None

def main_func():
    config_path = load_config()
    if config_path is None:
        print("Program will now exit. Please update the configuration file and run the program again.")
        create_default_config()
        return
    else:
        print("Using configuration file to create database client...")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
    # OGP_outputs = glob.glob(config['ogp_survey_dir'] + '/*.txt')
    # parsed_dir = pjoin(config['ogp_survey_dir'], 'parsed')

    # dp = DataParser(OGP_outputs, parsed_dir)
    # dp()

    # parsed_outputs = glob.glob(parsed_dir + '/*.csv')
    # uploader = SurveyProcessor(parsed_outputs, config_file)
    # uploader()
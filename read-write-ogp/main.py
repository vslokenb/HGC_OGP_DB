import os, yaml, sys, glob, re

pjoin = os.path.join

file_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = pjoin(file_dir, 'read-write-ogp')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.upload_inspect import DBClient
from src.parse_data import DataParser
from src.process_im import SurveyProcessor
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

def main_func():
    config_file = 'config.yaml'
    if not os.path.exists(config_file):
        create_default_config(config_file)
        print("Program will now exit. Please update the configuration file and run the program again.")
        return
    else:
        print("Using configuration file to create database client...")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    OGP_outputs = glob.glob(config['ogp_survey_dir'] + '/*.txt')
    parsed_dir = pjoin(config['ogp_survey_dir'], 'parsed')

    dp = DataParser(OGP_outputs, parsed_dir)
    dp()

    parsed_outputs = glob.glob(parsed_dir + '/*.csv')
    uploader = SurveyProcessor(parsed_outputs, config_file)
    uploader()
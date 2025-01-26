import os, yaml, sys, json
import argparse

pjoin = os.path.join

file_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = pjoin(file_dir, 'rwOGP')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.auto_upload import InventoryUpdater

SETTINGS_FILE = pjoin(os.path.expanduser('~'), ".my-cli-tool", "settings.yaml")

def get_config_location():
    """Get the configuration file location based on user preference."""
    print("Do you want to create the config file at a custom location? (y/n)")
    choice = input().strip().lower()

    home_dir = os.path.expanduser('~')

    if choice == 'y':
        print("Please enter the directory where you want to create the config file:")
        custom_path = os.path.expanduser(input().strip())
        if os.path.isdir(custom_path):
            return pjoin(custom_path, "rwOGP_DBconfig.yaml")
    
    # Default location
        config_dir = pjoin(home_dir, '.config')
    os.makedirs(config_dir, exist_ok=True)
    return pjoin(config_dir, 'rwOGP_DBconfig.yaml')

def get_default_config():
    """Return the default configuration dictionary."""
    return {
        'host': 'localhost',
        'database': 'hgcdb',
        'user': 'ogp_user',
        'password': 'hgcalpass',
        'inst_code': 'CM',
        'institution_name': 'Carnegie Mellon University',
        'ogp_survey_dir': '/path/to/ogp/survey/directory',
        'ogp_parsed_dir': '/path/to/ogp/parsed/directory',
        'ogp_tray_dir': '/path/to/ogp/tray/directory'
    }

def create_settings_file(config_file):
    """Create settings file with config and inventory paths."""
    home_dir = os.path.expanduser('~')
    settings_dir = pjoin(home_dir, '.my-cli-tool')
    os.makedirs(settings_dir, exist_ok=True)
    
    inventory_path = pjoin(settings_dir, 'inventory.json')
    settings = {
        'config_path': config_file,
        'inventory_path': inventory_path
    }
    with open(SETTINGS_FILE, 'w') as f:
        yaml.dump(settings, f)

def create_default_config():
    """Create a default YAML configuration file and a SETTINGS file."""
    config_file = get_config_location()
    
    print("Creating default configuration file...")
    with open(config_file, 'w') as f:
        yaml.dump(get_default_config(), f, default_flow_style=False)

    print(f"Configuration file created at {config_file}")
    print("Please update the configuration file with the correct database connection information!")

    create_settings_file(config_file)

def load_config():
    """Load the configuration file from the default location."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return yaml.safe_load(f)
    return None

def main_func():
    """Main function to run the program."""
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
    
    updater = InventoryUpdater(invent_path, config)
    updater()

def invent_print():
    """Print the current inventory."""
    settings = load_config()
    if settings is None:
        print("Program will now exit. Please run uploadOGPresults first!")
    else:
        invent_path = settings['inventory_path']
        print(f"Printing the current inventory {invent_path}...")
        inventory = InventoryUpdater.deal_corrupt(invent_path)
        print(inventory)

def clear_invent():
    """Clear the current inventory file."""
    settings = load_config()
    if settings is None:
        print("Program will now exit. Please run uploadOGPresults first!")
    else:
        invent_path = settings['inventory_path']
        print("=" * 90)
        userinput = input("Enter the component type you want to clear: (e.g. baseplates) \n")
        print(f"Clearing the current inventory {invent_path}...")

        inventory = InventoryUpdater.deal_corrupt(invent_path)

        if userinput in inventory:
            inventory[userinput] = []
        else:
            print("Component type not found in inventory.")
            print("The current component types are:")
            print(inventory.keys())
            sys.exit(1) 
        
        with open(invent_path, 'w') as f:
            json.dump(inventory, f)
        print(f"Inventory for {userinput} cleared.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the rwOGP program.")
    parser.add_argument("--print", action='store_true', help="Print the current inventory.")
    parser.add_argument("--clear", action='store_true', help="Clear the current inventory.")
    args = parser.parse_args()
    
    if args.print:
        invent_print()
    if args.clear:
        clear_invent()

    main_func()

from src.config_utils import load_config
from src.auto_upload import InventoryUpdater
import json, sys, logging

def invent_print():
    """Print the current inventory."""
    settings = load_config()
    if settings is None:
        logging.warning("No configuration file found. Program will now exit. Please run without arguments first!")
    else:
        invent_path = settings['inventory_path']
        print(f"Printing the current inventory {invent_path}...")
        inventory = InventoryUpdater.deal_corrupt(invent_path)
        print(inventory)

def clear_invent():
    """Clear the current inventory file."""
    settings = load_config()
    if settings is None:
        logging.error("Program will now exit. Please run without arguments first!")
    else:
        invent_path = settings['inventory_path']
        inventory = InventoryUpdater.deal_corrupt(invent_path)
        userinput = input("Enter the component type you want to clear: (e.g. baseplates) \n")
        if userinput not in inventory:
            logging.error("Component type not found in inventory.")
            logging.error(f"The current component types are: {inventory.keys()}")
            sys.exit(1)
        else:
            if_entire = input(f"Would you want to clear the entire inventory for this component type? (y/n) \n")
            if if_entire == 'y':
                logging.info(f"Clearing the current inventory {invent_path}...")
                inventory[userinput] = []
            else:
                filenames = input(f"Please enter specific filenames to clear from the inventory for {userinput}: (e.g. file1, file2, ...)\n")
                filenames = filenames.split(',')
                for filename in filenames:
                    if filename in inventory[userinput]:
                        inventory[userinput].remove(filename)
                    else:
                        logging.warning(f"Filename {filename} not found in inventory for {userinput}.")
        
        with open(invent_path, 'w') as f:
            json.dump(inventory, f)
        logging.info(f"Inventory for {userinput} cleared.")
from src.config_utils import load_config
from src.auto_upload import InventoryUpdater
import json, sys

def invent_print():
    """Print the current inventory."""
    settings = load_config()
    if settings is None:
        print("=" * 90)
        print("No configuration file found.")
        print("Program will now exit. Please run without arguments first!")
    else:
        invent_path = settings['inventory_path']
        print(f"Printing the current inventory {invent_path}...")
        inventory = InventoryUpdater.deal_corrupt(invent_path)
        print(inventory)

def clear_invent():
    """Clear the current inventory file."""
    settings = load_config()
    if settings is None:
        print("Program will now exit. Please run without arguments first!")
    else:
        invent_path = settings['inventory_path']
        print("=" * 90)
        inventory = InventoryUpdater.deal_corrupt(invent_path)
        userinput = input("Enter the component type you want to clear: (e.g. baseplates) \n")
        if userinput not in inventory:
            print("Component type not found in inventory.")
            print("The current component types are:")
            print(inventory.keys())
            sys.exit(1)
        else:
            if_entire = input(f"Would you want to clear the entire inventory for this component type? (y/n) \n")
            if if_entire == 'y':
                print(f"Clearing the current inventory {invent_path}...")
                inventory[userinput] = []
            else:
                filenames = input(f"Please enter specific filenames to clear from the inventory for {userinput}: (e.g. file1, file2, ...)\n")
                filenames = filenames.split(',')
                for filename in filenames:
                    if filename in inventory[userinput]:
                        inventory[userinput].remove(filename)
                    else:
                        print(f"Filename {filename} not found in inventory for {userinput}.")
        
        with open(invent_path, 'w') as f:
            json.dump(inventory, f)
        print(f"Inventory for {userinput} cleared.")
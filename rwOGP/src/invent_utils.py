from src.config_utils import load_config
from src.auto_upload import InventoryUpdater
import json

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
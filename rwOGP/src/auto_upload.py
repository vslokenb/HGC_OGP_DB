import os, subprocess, json, sys
from .parse_data import DataParser
from .process_survey import SurveyProcessor

pexist = os.path.exists
pjoin = os.path.join

class InventoryUpdater():
    """Update the inventory of OGP results and upload new files to the database."""
    def __init__(self, inventory_path, config_yaml):
        """Initialize the file uploader.
        
        Parameters
        - `inventory_path`: path to the inventory json file."""
        self.inventory_p = inventory_path
        self.config = config_yaml
        self.checkdir = self.config.get('ogp_survey_dir')
        self.parsed_dir = self.config.get('ogp_parsed_dir')
    
    def __call__(self):
        if not pexist(self.inventory_p):
            self.__deal_empty()
            return
            
        with open(self.inventory_p, 'r') as f:
            self.inventory = json.load(f)
        
        new_files = self.__update_inventory()
        self.upload_files(new_files)

        with open(self.inventory_p, 'w') as f:
            json.dump(self.__create_new(), f)
    
    def __create_new(self) -> dict:
        """Create a new inventory dictionary. 
        With structure like {subdir:[files]} 
        
        Return
        - dictionary of subdirectories and their corresponding txt files."""
        txt_files_by_subdir = {}
        for item in os.listdir(self.checkdir):
            subdir_path = pjoin(self.checkdir, item)
            if os.path.isdir(subdir_path):
                txt_files = [
                    file for file in os.listdir(subdir_path) 
                    if file.endswith('.txt')
                ]
                
                if txt_files:
                    txt_files_by_subdir[item] = txt_files

        return txt_files_by_subdir
    
    def __deal_empty(self) -> bool:
        """Check if inventory is empty and prompt user to upload all existing OGP results to database.
        
        Return 
        - bool: whether all existing OGP results are uploaded to database."""
        txt_files_by_subdir = self.__create_new()

        with open(self.inventory_p, 'w') as f:
            json.dump(txt_files_by_subdir, f)

        print("Initialize Inventory of OGP results for the first time...Would you like to process and upload all the existing OGP results to database? (Y/N)")
        choice = input().strip().lower()

        if choice == 'y':
            print("Uploading all existing OGP results to database...")
            self.upload_files(txt_files_by_subdir)
            return True
        else:
            print("Exiting...")
            return False
    
    def __update_inventory(self) -> dict:
        """Update the inventory of OGP results and return the changed files in inventory structure. Write the updated inventory to the inventory file.
        
        Return 
        - changed_inventory: dictionary of subdirectories and their corresponding changed files."""
        new_inventory = self.__create_new()

        old_inventory = self.inventory.copy()

        changed_inventory = {}

        for subdir, files in new_inventory.items():
            if subdir not in old_inventory:
                print(f"New subdirectory detected: {subdir}")
                changed_inventory[subdir] = files
            else:
                new_files = set(files) - set(old_inventory[subdir])
                removed_files = set(old_inventory[subdir]) - set(files)
                if new_files:
                    print(f"New files in {subdir}: {new_files}")
                if removed_files:
                    print(f"Removed files in {subdir}: {removed_files}")
                changed_inventory[subdir] = new_files
        
        with open(self.inventory_p, 'w') as f:
            json.dump(new_inventory, f)
                    
        return changed_inventory
    
    def upload_files(self, invent):
        """Parse, postprocess and upload files to the database.
        
        Parameters
        - `invent`: dictionary of {subdir:[files]} to be uploaded. subdir should be names of components, e.g. baseplate, modules, etc."""
        for subdir, files in invent.items():
            inputs = [pjoin(self.checkdir, subdir, file) for file in files]
            if inputs:
                dp = DataParser(inputs, self.parsed_dir)
                gen_meta, gen_features = dp()
                
                uploader = SurveyProcessor(gen_features, gen_meta, self.config)
                uploader(subdir)
            else:
                print(f"No files from {subdir} to process/upload to database.")
        
    def run_on_new_files(self, files, action):
        """Run the action on each file in the list of files
        
        Parameters
        - `files`: list of files to run the action on, without parent directory prefix."""
        for file in files:
            subprocess.Popen(['python', action, os.path.join(self.checkdir, file)])
    
    @staticmethod
    def deal_corrupt(json_path):
        """Deal with corrupt json files.
        
        Parameters
        - `json_path`: path to the corrupt json file."""
        with open(json_path, 'r') as f:
            try:
                data = json.load(f)
                return data
            except json.JSONDecodeError:
                print("!" * 90)
                print(f"Corrupt json file: {json_path}")
                print("Please remove the file and run the program again.")

import os, subprocess, json, glob, yaml
import argparse
from .parse_data import DataParser
from .process_im import SurveyProcessor

pexist = os.path.exists
pjoin = os.path.join

class InventoryUpdater():
    """Update the inventory of OGP results and upload new files to the database."""
    
    def __init__(self, inventory_path, config_yaml):
        """Initialize the file uploader"""
        self.inventory_p = inventory_path
        self.config = config_yaml
        self.checkdir = self.config.get('ogp_survey_dir')
        self.parsed_dir = self.config.get('ogp_parsed_dir')
    
    def __call__(self):
        if pexist(self.inventory_p):
            self.__deal_empty()
            return
            
        with open(self.inventory_p, 'r') as f:
            self.inventory = json.load(f)
    
    def __create_new(self) -> dict:
        """Create a new inventory dictionary. 
        With structure like {subdir:[files]} 
        
        Return
        - txt_files_by_subdir: dictionary of subdirectories and their corresponding txt files."""
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
        """Check if inventory is empty and prompt user to upload all existing OGP results to database."""
        txt_files_by_subdir = self.__create_new()

        with json.open(self.inventory_p, 'w') as f:
            json.dump(txt_files_by_subdir, f)

        print("Initialize Inventory of OGP results for the first time...Would you like to process and upload all the existing OGP results to database? (Y/N)")
        choice = input().strip().lower()

        if choice == 'y':
            pass
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
        """Upload files to the database.
        
        Parameters
        - `invent`: dictionary of {subdir:[files]} to be uploaded."""
        for subdir, files in invent.items():
            inputs = [pjoin(self.checkdir, subdir, file) for file in files]
            dp = DataParser(inputs, self.parsed_dir)
            gen_meta, gen_features = dp()

            uploader = SurveyProcessor(gen_features, self.config)
        
    def run_on_new_files(self, files, action):
        """Run the action on each file in the list of files
        
        Parameters
        - `files`: list of files to run the action on, without parent directory prefix."""
        for file in files:
            subprocess.Popen(['python', action, os.path.join(self.checkdir, file)])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Watch a directory for new files and process them.')
    parser.add_argument('-d', '--directory', type=str, help='Directory to watch for new files', default="C:/Users/Admin/Desktop/module_assembly_surveys/offsets/OGP_results")
    args = parser.parse_args()
    
    directory_to_watch = parser.d
    print("============================================")
    print(f'Watching directory: {directory_to_watch}')

    parent_dir = os.path.dirname(os.path.abspath(__file__))
    process_file_path = os.path.join(parent_dir, 'process_im.py')

    uploader = FileUploader(directory_to_watch)
    uploader(process_file_path)

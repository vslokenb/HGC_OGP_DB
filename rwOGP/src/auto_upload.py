import os, subprocess, json, glob
import argparse
from .parse_data import DataParser
from .process_im import SurveyProcessor

pexist = os.path.exists
pjoin = os.path.join

class InventoryUpdater():
    def __init__(self, ogp_survey_dir, inventory_path, config_path):
        """Initialize the file uploader"""
        self.inventory_p = inventory_path
        self.checkdir = ogp_survey_dir
        self.config_path = config_path
    
    def __call__(self):
        if pexist(self.inventory_p):
            self.__deal_empty()
            return
            
        with open(self.inventory_p, 'r') as f:
            self.inventory = json.load(f)
    
    def __create_new(self) -> dict:
        """Create a new inventory dictionary. 
        With structure like {subdir:[files]}"""
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
        """Update the inventory of OGP results and return the changed inventory. Write the updated inventory to the inventory file."""
        new_inventory = self.__create_new()

        updated_inventory = self.inventory.copy()

        changed_inventory = {}

        for subdir, files in new_inventory.items():
            if subdir not in updated_inventory:
                print(f"New subdirectory detected: {subdir}")
                changed_inventory[subdir] = files
            else:
                new_files = set(files) - set(updated_inventory[subdir])
                removed_files = set(updated_inventory[subdir]) - set(files)
                if new_files:
                    print(f"New files in {subdir}: {new_files}")
                if removed_files:
                    print(f"Removed files in {subdir}: {removed_files}")
                changed_inventory[subdir] = new_files
        
        with open(self.inventory_p, 'w') as f:
            json.dump(new_inventory, f)
                    
        return changed_inventory
    
    def upload_files(self, new_files):
        """Upload files to the database"""
        
        for subdir, files in new_files.items():
            inputs = [pjoin(self.checkdir, subdir, file) for file in files]
            output_dir = pjoin(self.checkdir, 'parsed', subdir)
            dp = DataParser(inputs, output_dir)
            dp()

            parsed_outputs = glob.glob(output_dir + '/*.csv')
            uploader = SurveyProcessor(parsed_outputs, self.config_path)
        
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

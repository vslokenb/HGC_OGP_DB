import os, subprocess, json, sys
from .parse_data import DataParser
from .process_survey import SurveyProcessor

pexist = os.path.exists
pjoin = os.path.join

class InventoryUpdater():
    """Update the inventory of OGP results and upload new files to the database."""
    def __init__(self, inventory_path, config_yaml, comp_type=''):
        """Initialize the file uploader.
        
        Parameters
        - `inventory_path`: path to the inventory json file."""
        self.inventory_p = inventory_path
        self.config = config_yaml
        self.checkdir = self.config.get('ogp_survey_dir')
        self.parsed_dir = self.config.get('ogp_parsed_dir')
        self.comp_type = comp_type
        print("Reading inventory from:", self.inventory_p)
        print("Parsing OGP survey files from directory:", self.checkdir)
        print("Saving parsed data to directory:", self.parsed_dir)
    
    async def __call__(self):
        if not pexist(self.inventory_p):
            self.__deal_empty()
            return
            
        with open(self.inventory_p, 'r') as f:
            self.inventory = json.load(f)
        
        new_files = self.__check_inventory()
        success_invent = await self.upload_files(new_files)
        self.__update_inven(success_invent)
    
    def __update_inven(self, success_invent, removed_invent):
        """Update the inventory with the successfully uploaded files."""
        for subdir, files in success_invent.items():
            if subdir not in self.inventory:
                self.inventory[subdir] = files
            else:
                self.inventory[subdir].extend(files)
                self.inventory[subdir] = list(dict.fromkeys(self.inventory[subdir]))
        
        for subdir, files in removed_invent.items():
            if subdir in self.inventory:
                self.inventory[subdir] = [file for file in self.inventory[subdir] if file not in files]
                if not self.inventory[subdir]:
                    del self.inventory[subdir]
        
        with open(self.inventory_p, 'w') as f:
            json.dump(self.inventory, f)
        
        print("\n=== Inventory Update Summary ===")
        print(f"Successfully updated inventory with {sum(len(files) for files in success_invent.values())} new files")
        print(f"Removed {sum(len(files) for files in removed_invent.values())} files from inventory")

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
    
    async def __deal_empty(self) -> bool:
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
            await self.upload_files(txt_files_by_subdir)
            return True
        else:
            print("Exiting...")
            return False
    
    def __check_inventory(self) -> dict:
        """Check for changes in the inventory of OGP results.
        If self.comp_type is specified, only check that specific subdirectory.

        Returns:
        - dict: Subdirectories and their corresponding new files to be processed.
        """
        print("\n=== Checking for OGP Survey File Changes ===")
        new_inventory = self.__create_new()
        old_inventory = self.inventory.copy()
        changed_inventory = {}
        removed_inventory = {}

        total_new_files = 0
        total_removed_files = 0
        new_subdirs = []

        if self.comp_type:
            if self.comp_type in new_inventory:
                new_inventory = {self.comp_type: new_inventory[self.comp_type]}
            else:
                new_inventory = {}
                print("No new files to process for component type:", self.comp_type)
                sys.exit()
            if self.comp_type in old_inventory:
                old_inventory = {self.comp_type: old_inventory[self.comp_type]}
            else:
                old_inventory = {}

        for subdir, files in new_inventory.items():
            if subdir not in old_inventory:
                new_subdirs.append(subdir)
                changed_inventory[subdir] = files
                total_new_files += len(files)
            else:
                new_files = set(files) - set(old_inventory[subdir])
                removed_files = set(old_inventory[subdir]) - set(files)
                if new_files or removed_files:
                    print(f"\nChanges in subdirectory '{subdir}':")
                    if new_files:
                        print(f"  + Added: {', '.join(sorted(new_files))}")
                        total_new_files += len(new_files)
                    if removed_files:
                        print(f"  - Removed: {', '.join(sorted(removed_files))}")
                        total_removed_files += len(removed_files)

                if new_files:
                    changed_inventory[subdir] = list(new_files)
                if removed_files:
                    removed_inventory[subdir] = list(removed_files)
        
        # check for removed subdirectories
        for subdir in old_inventory:
            if subdir not in new_inventory:
                removed_inventory[subdir] = old_inventory[subdir]
                total_removed_files += len(old_inventory[subdir])

        print("\n=== Summary of Changes ===")
        if new_subdirs:
            print(f"New subdirectories detected: {', '.join(new_subdirs)}")
        print(f"Total new files to process: {total_new_files}")
        print(f"Total files removed: {total_removed_files}")

        return changed_inventory, removed_inventory
    
    async def upload_files(self, invent):
        """Parse, postprocess and upload files to the database.
        
        Parameters
        - `invent`: dictionary of {subdir:[files]} to be uploaded. subdir should be names of components, e.g. baseplate, modules, etc.
        
        Returns
        - dict: inventory of successfully uploaded files in the same format as input {subdir:[files]}
        """
        successful_uploads = {}
        
        for subdir, files in invent.items():
            inputs = [pjoin(self.checkdir, subdir, file) for file in files]
            if inputs:
                dp = DataParser(inputs, self.parsed_dir)
                gen_meta, gen_features = dp()
                
                uploader = SurveyProcessor(gen_features, gen_meta, self.config)
                success, indx = await uploader(subdir)
                if success:
                    successful_uploads[subdir] = files
                elif indx != -1:
                    # Some files were uploaded successfully (up to the index that failed)
                    successful_files = files[:indx+1]
                    if successful_files:  # Only add if there were successful uploads
                        successful_uploads[subdir] = successful_files
                    print(f"Failed to upload file: {inputs[indx + 1]}")
                else:
                    print(f"Failed to upload files from {subdir}")
            else:
                print(f"No files from {subdir} to process/upload to database.")
        
        if successful_uploads: print("These files were successfully uploaded:", successful_uploads)
        
        return successful_uploads
        
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

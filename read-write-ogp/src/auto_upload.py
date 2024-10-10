import time, os, subprocess
import argparse

class FileUploader():
    def __init__(self, checkdir, log_file = 'filelog.txt'):
        self.log_file = log_file
        self.checkdir = checkdir
    
    def __call__(self, action: 'str') -> None:
        """Run the file uploader
        
        Parameters
        - `action`: the path to the script to run on new files
        """
        if os.path.exists(self.log_file):
            logged_files = self.read_log_file()
        else: logged_files = []

        curr_files = self.lst_dir()
        new_files = [file for file in curr_files if file not in logged_files]

        if new_files:
            print(f'New files detected: {new_files}')
            self.rec_files(new_files, self.log_file)
            self.run_on_new_files(new_files, action)
        else:
            print('No new files detected.')
            
    def read_log_file(self):
        with open(self.log_file, 'r') as f:
            return [line.strip() for line in f.readlines()]

    def lst_dir(self):
        items = os.listdir(self.checkdir)
        files = [item for item in items if os.path.isfile(os.path.join(self.checkdir, item))]
        return files
    
    def rec_files(self, files, log_file):
        with open(log_file, 'w') as f:
            for file in files:
                f.write(file + '\n')

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

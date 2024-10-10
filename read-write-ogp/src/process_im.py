import numpy as np
import pandas as pd
import asyncio, send2trash, glob, re, yaml, os
import matplotlib
matplotlib.use('Agg')
from src.ogp_height_plotter import PlotTool, get_offsets
from src.upload_inspect import DBClient
from src.parse_data import DataParser
from make_accuracy_plot import make_accuracy_plot
from datetime import datetime

pbase = os.path.basename
pdir = os.path.dirname

baseplates_params = {"key":"Surface", "vmini": 1.2, "vmaxi": 2.2, "new_angle": 0, "db_table_name": 'bp_inspect', "material": 'cf'}
hexaboards_params = {"key":"Flatness", "vmini": 1.2, "vmaxi": 2.9, "new_angle": 0, "db_table_name": 'hxb_inspect'}
protomodules_params = {"key":"Thick", "vmini": 1.37, "vmaxi": 1.79, "new_angle": 270, "db_table_name": 'proto_inspect'}
others_params = {"key":"Thick", "vmini": 2.75, "vmaxi": 4.0, "new_angle": 270, "db_table_name": 'module_inspect'}

class SurveyProcessor():
    """Process OGP Survey file and extract data for plotting and uploading to database."""
    def __init__(self, OGPSurveyFilePath, yamlconfig):
        """Initialize ImageProcessor object.
        
        Parameters:
        - OGPSurveyFilePath (str/list): (list of) Path(s) to OGP Survey output file."""
        if isinstance(OGPSurveyFilePath, str):
            self.OGPSurveyFile = [OGPSurveyFilePath]
        for i, file in enumerate(self.OGPSurveyFile):
            if not file.endswith('.csv'):
                raise ValueError('OGP Survey output file must be a csv file.')
            self.OGPSurveyFile[i] = file.replace('\\', '/')

        print(f'filename to process/upload: {self.OGPSurveyFile}')
        self.client = DBClient(yamlconfig)
        pass

    def __call__(self):
        self.getTrayFile()  
        self.process_and_upload()

    def getTrayFile(self):
        """Get Gantry Tray file and Tray files for NSH. 
        
        Return 
        - GantryTrayFile (str): Path to Gantry Tray file.
        - tray_files (list): List of paths to Tray files for NSH.
        - trash_file (bool): True if OGP Survey file is to be trashed."""

        base_path = self.OGPSurveyFile[0].split('OGP_results')[0]
        GantryTrayFile = base_path + 'OGP_results/assembly_trays/assembly_tray_input.xls'

        tray_files_pattern = base_path + 'data/Tray * for NSH.xls' 
        tray_files = glob.glob(tray_files_pattern)

        if tray_files == []: 
            raise FileNotFoundError(f'Tray files not found. Please put pin measurement files for trays as {base_path}data/Tray * for NSH.xls')
        
        tray_files.sort(key=lambda x: int(re.search(r'Tray (\d+)', x).group(1)))

        # placeholder
        trash_file = False

        self.tray_files = tray_files
        self.GantryTrayFile = GantryTrayFile

        return GantryTrayFile, tray_files, trash_file
    
    def __getMeta__(self, ex_file) -> dict:
        """Get metadata based on OGP survey feature files.
        
        Return 
        - metadata (dict): Metadata extracted from the meta file."""
        name = pbase(ex_file).split('.')[0]
        dirname = pdir(ex_file)
        ex_metafile = f'{dirname}/{name}_meta.yaml'

        with open(ex_metafile, 'r') as f:
            metadata = yaml.safe_load(f)
        
        return metadata
    
    def __getArgs__(self, ex_file):
        """Get arguments for plotting and uploading based on file name."""
        filesuffix, home_folder, modname = self.getDirNames(ex_file)
        
        if home_folder == 'HD full':
            if 'P' in modname:
                comp_type = 'protomodules';
            if 'M' in modname: 
                comp_type = 'modules'
        
        print('')
        print(f"###### NEW {comp_type} UPLOAD #######")
        print(f"###### FROM: {modname} #######")
        print('')

        print(f'Component type: {comp_type}')

        db_upload = {}

        metadata = self.__getMeta__(ex_file)
        modtitle = metadata['ComponentID']

        df = pd.read_csv(ex_file)

        if comp_type == 'baseplates':
            db_upload.update({'bp_name': modtitle})
            component_params = baseplates_params
        elif comp_type == 'hexaboards':
            db_upload.update({'hxb_name':modtitle})
            component_params = hexaboards_params
        elif comp_type == 'protomodules':
            component_params = protomodules_params
            Traysheets = [pd.read_csv(tray) for tray in self.tray_files]
            XOffset, YOffset, AngleOff = get_offsets([self.GantryTrayFile, self.OGPSurveyFile], Traysheets)
            db_upload.update({'proto_name': modtitle, 'x_offset_mu':np.round(XOffset*1000), 'y_offset_mu':np.round(YOffset*1000), 'ang_offset_deg':np.round(AngleOff,3)})
        else:
            component_params = others_params
            try:
                PMoffsets = asyncio.run(self.client.GrabSensorOffsets(modtitle))
                print(PMoffsets)
            except:
                PMoffsets =(asyncio.get_event_loop()).run_until_complete(self.client.GrabSensorOffsets(modtitle))
            
            SensorXOffset, SensorYOffset, SensorAngleOff = PMoffsets

            print('Retreived Protomodule Offset Info: ', SensorXOffset, SensorYOffset, SensorAngleOff)
            print('Making Accuracy Plot With:', modtitle, SensorXOffset, SensorYOffset, XOffset, YOffset, SensorAngleOff, AngleOff)
            acc_bytes = make_accuracy_plot(modtitle, SensorXOffset, SensorYOffset, int(XOffset*1000), int(YOffset*1000), SensorAngleOff, AngleOff)

        print("key:", component_params['key'])

        im_args = {"vmini":component_params['vmini'], "vmaxi":component_params['vmaxi'], 
                   "new_angle": component_params['new_angle'], "savename":f"{comp_type}\{filesuffix}_heights",
                   "mod_flat": metadata['Flatness'], "title": metadata['ComponentID']}
        
        x_points = DataParser.get_feature_from_df(df, 'X_coordinate')
        y_points = DataParser.get_feature_from_df(df, 'Y_coordinate')
        z_points = DataParser.get_feature_from_df(df, 'Z_coordinate')

        im_bytes = PlotTool.plot2d(x_points, y_points, z_points, limit = 0, **im_args,
            center = 25, rotate = 345, value = 1,details=1, show_plot = False)

        # placeholder for comment till further update of templates
        comment = ''

        db_upload = {
            'flatness': metadata['Flatness'], 
            'thickness': np.round(np.mean(z_points),3), 
            'x_points':(x_points).tolist(), 
            'y_points':(y_points).tolist(), 
            'z_points':(z_points).tolist(),
            'hexplot':im_bytes, 
            'inspector': metadata['Operator'], 
            'comment':comment}
        
        db_upload.update(self.getDateTime(metadata))

        db_table_name = component_params['db_table_name']

        return db_upload, db_table_name, modtitle  
    
    def process_and_upload(self):
        """Process all OGP Survey files and upload to database."""
        for ex_file in self.OGPSurveyFile:
            db_upload, db_table_name, modtitle = self.__getArgs__(ex_file)
            mappings = np.array([None],dtype=object)
            try:
                asyncio.run(self.client.upload_PostgreSQL(db_table_name, db_upload)) ## python 3.7
            except:
                (asyncio.get_event_loop()).run_until_complete(self.client.upload_PostgreSQL(db_table_name, db_upload)) ## python 3.6
            print(modtitle, 'uploaded!')
            # if trash_file:
                # send2trash.send2trash(ex_file)
            print(f'Moved {ex_file} to recycle bin.')

    # this could be replaced by a simple basename function from os module
    @staticmethod
    def getDirNames(ex_file):
        """Get directory names from file path."""
        if '/' in ex_file:
            filesuffix = (ex_file.split('/')[-1]).split('.')[0]
            home_folder = ex_file.split('/')[-2]
            modname = ex_file.split('/')[-1]
        elif '\\' in ex_file:    ############ this may not be needed.
            filesuffix = (ex_file.split('\\')[-1]).split('.')[0]
            home_folder = ex_file.split('\\')[-2]
            modname = ex_file.split('/')[-1]
        else:
            filesuffix = ex_file.split('.')[0]
            modname = ex_file.split('/')[-1]
            home_folder = None
        
        return filesuffix, home_folder, modname
    
    @staticmethod
    def getDateTime(metadata):
        """Get date and time from metadata."""
        date_inspect = datetime.strptime(metadata['RunDate'], '%Y-%m-%d').date()
        time_inspect = datetime.strptime(metadata['RunTime'], '%H:%M:%S').time()
        
        return {"date_inspec": date_inspect, "time_inspect": time_inspect}
        
    

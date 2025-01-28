import os, yaml, sys
from ttp import ttp
import pandas as pd
from io import StringIO

from src.param import header_template, data_template, required_keys, warning_keys, default_params, pin_mapping

pjoin = os.path.join

class DataParser():
    """Parse data file(s) using TTP template. 
    Output metadata, which contains info such as geometry and density, and feature results, which are dataframes containing the parsed data."""
    def __init__(self, data_file, output_dir):
        """Initialize DataParser object.
        
        Parameters:
        - data_file (str/list[str]): Path(s) to the data output file by OGP surveys to be parsed.
        - output_dir (str): Path to the output directory of the parsed data."""
        if isinstance(data_file, str):
            data_file = [data_file]
        
        self.data_file = data_file
        self.output_dir = output_dir
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def __call__(self) -> tuple:
        """Parse data file produced by default OGP template. Create metadata file and output feature results to a csv file.
        
        Return 
        - gen_meta (list): List of metadata files generated.
        - gen_features (list): List of feature files generated."""
        gen_meta = []
        gen_features = []
        for filename in self.data_file:
            self.data = open(filename, 'r').read()
            print("=" * 100)
            print("Parsing data for file: ", filename)
            self.read_temp_sep()
            filename = self.output_meta()
            self.output_features(f'{filename}.csv')
            gen_features.append(pjoin(self.output_dir, f'{filename}.csv'))
            gen_meta.append(pjoin(self.output_dir, f'{filename}_meta.yaml'))
        return gen_meta, gen_features

    def read_temp_sep(self, header_template=header_template, feature_template=data_template, delimiter='---'):
        """Read data file produced with header and feature templates separated by a delimiter."""
        parts = self.data.split(delimiter)
        
        assert len(parts) == 2, 'Exactly One delimiter is required'
        parser = ttp(data=parts[0], template=header_template)
        parser.parse()
        header_results = parser.result(structure="flat_list")
        parser = ttp(data=parts[1], template=feature_template)
        parser.parse()
        feature_results = parser.result(format='csv', structure="flat_list")

        self.header_results = {}
        for header in header_results:
            self.header_results.update(header)

        self.feature_results = pd.read_csv(StringIO(feature_results[0])).drop_duplicates()

        if 'Flatness' not in self.header_results:
            print(self.header_results)
            raise ValueError('Flatness not found in header. Please check the OGP template.')
        
        self.header_results['Flatness'] = float(self.header_results['Flatness'])
        return header_results, feature_results
    
    def output_features(self, output_filename):
        """Output feature results to a csv file."""
        self.feature_results.to_csv(pjoin(self.output_dir, output_filename), index=False)
    
    def output_meta(self) -> str:
        """Output metadata to a file, with filename based on ComponentID and Operator.
        
        Return 
        - filename (str): Filename prefix of the metadata file."""
        header_dict = self.header_results

        header_dict = self.check_missing_keys(header_dict)
        header_dict = self.check_types(header_dict)
        header_dict = self.check_missing_mappings(header_dict)

        filename = f"{header_dict['ComponentID']}_{header_dict['Operator']}"
        meta_file = f'{filename}_meta.yaml'
        with open(f'{self.output_dir}/{meta_file}', 'w') as f:
            yaml.dump(header_dict, f, default_flow_style=False)
        return filename
    
    def check_missing_keys(self, header_dict):
        """Check for missing keys in the parsed header. 
        If missing, adopt default values for the missing keys or exit the program."""
        if set(required_keys) - set(header_dict.keys()):
            print("DataParser did not parse all the required keys due to mismatching in naming or missing data.")
            print("Parsed data: ", header_dict)
            print("Missing keys: ", set(required_keys) - set(header_dict.keys()))
            header_dict = self.adopt_default(header_dict)
            user_input = input("Do you want to adopt the default values for the missing keys? (y/n): ")
            if user_input.lower() != 'y':
                print("Exiting...")
                sys.exit()

        if set(warning_keys) - set(header_dict.keys()):
            print("DataParser did not parse all the optional keys due to mismatching in naming or missing data.")
            print("Missing keys: ", set(warning_keys) - set(header_dict.keys()))
        
        return header_dict
    
    def check_missing_mappings(self, header_dict):
        """Check for missing mappings in the parsed header. 
        If unrecognized in pin mapping, adopt default values for the missing keys or exit the program."""
        Geometry = header_dict['Geometry']
        density = header_dict['Density']
        if pin_mapping.get(Geometry) is None:
            print(f"Geometry {Geometry} not recognized. Default to Full.")
            user_input = input("Do you want to adopt the default values for Geometry? (y/n): ")
            if user_input.lower() != 'y':
                print("Exiting... Please check the Geometry value or update the pin mapping in param.py.")
                sys.exit()
            header_dict['Geometry'] = 'Full'
            Geometry = 'Full'
        if pin_mapping.get(Geometry).get(density) is None:
            print(f"Density {density} not recognized for Geometry {Geometry}. Default to LD.")
            user_input = input("Do you want to adopt the default values for Density? (y/n): ")
            if user_input.lower() != 'y':
                print("Exiting... Please check the Density value or update the pin mapping in param.py.")
                sys.exit()
            header_dict['Density'] = 'LD'
        return header_dict

    def check_types(self, header_dict):
        """If the data types in header_dict are not correct, convert the types to the correct ones."""
        header_dict['PositionID'] = int(header_dict['PositionID'])
        header_dict['TrayNo'] = int(header_dict['TrayNo'])
        header_dict['Density'] = str(header_dict['Density']).upper()
        header_dict['Geometry'] = str(header_dict['Geometry']).capitalize()
        return header_dict
        
    def adopt_default(self, header_dict):
        """Adopt default values for the missing keys."""
        for key in set(required_keys) - set(header_dict.keys()):
            print(f"Default value {default_params[key]} will be adopted for missing key: ", key)
            header_dict[key] = default_params[key]
        return header_dict
    
    @staticmethod
    def get_xyz(df: pd.DataFrame) -> pd.DataFrame:
        """Get X, Y, Z coordinates from the dataframe."""
        return df.dropna(subset=['X_coordinate', 'Y_coordinate', 'Z_coordinate'])
    
    @staticmethod
    def get_feature_from_df(df: 'pd.DataFrame', feature_name, filterType=None) -> pd.Series:
        """Get feature from the dataframe.
        
        Parameters:
        - df (pd.DataFrame): Dataframe containing the parsed data.
        - feature_name (str): Name of the feature to be extracted."""
        assert feature_name in df.columns, 'Feature not found'

        if filterType is None: filtered_df = df
        else: filtered_df = df[df['FeatureType'] == filterType]

        return filtered_df[feature_name].dropna()
    
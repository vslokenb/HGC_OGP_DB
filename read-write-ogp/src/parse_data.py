import re, os, yaml
from ttp import ttp
import pandas as pd
import chardet
from io import StringIO

pjoin = os.path.join

# WIP
def read_ogp_template(template_file, output_file):
    """Read OGP template file and convert it to TTP template file."""
    with open(template_file, 'rb') as f:
        raw_data = f.read()
    result = chardet.detect(raw_data)
    
    with open(template_file, 'r', encoding=result['encoding'], errors='ignore') as f:
        template = f.read()
    template = template.replace('{', '{{').replace('}', '}}')

    template = re.sub(r'<(?!reportheader|feature)(\w+)>', '', template)
    template = re.sub(r'</(?!reportheader|feature)(\w+)>', '', template)

    template = re.sub(r'<(\w+)>', r"<group name='\1'>", template)

    lines = template.splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith('//')]
    template = '\n'.join(filtered_lines)
    template = re.sub(r'(?<=\b[A-Z])[A-Z]+\.[A-Z]+', r'_coordinate', template)
    print(template)

    # with open(output_file, 'w', encoding='utf-8') as f:
        # f.write(template)

header_template = """
{{ ProjectName }}
LastModified: {{ LastModifiedDate }} {{ LastModifiedTime }}
RunTime: {{ RunDate }} {{ RunTime }}
Component ID: {{ ComponentID }}
Operator: {{ Operator }}
Geometry: {{ Geometry }}
Density: {{ Density }}
Sensor size: {{ SensorSize }}
Flatness: {{ Flatness }}
"""

data_template = """
{{FeatureType}} {{FeatureName}}
Point     {{X_coordinate}}    {{Y_coordinate}}    {{Z_coordinate}}
direction cosine:    {{I_coordinate}}    {{J_coordinate}}    {{K_coordinate}}
Radius            {{Radius}}
"""

## currently not used
default_template = """
<group name="reportheader">
{{ ProjectName }}
LastModified: {{ LastModifiedDate }} {{ LastModifiedTime }}
RunTime: {{ RunDate }} {{ RunTime }}
Component ID: {{ ComponentID }}
Operator: {{ Operator }}
Geometry: {{ Geometry }}
Density: {{ Density }}
Sensor size: {{ SensorSize }}
</group>

<group name="feature">
{{FeatureType}} {{FeatureName}}
Point     {{X_coordinate}}    {{Y_coordinate}}    {{Z_coordinate}}
direction cosine:    {{I_coordinate}}    {{J_coordinate}}    {{K_coordinate}}
Radius            {{Radius}}
</group>
"""

class DataParser():
    """Parse data file using TTP template."""
    def __init__(self, data_file, output_dir):
        with open(data_file, 'r') as f:
            self.data = f.read()
        
        self.output_dir = output_dir
    
    def __call__(self):
        """Parse data file produced by default OGP template."""
        self.read_temp_sep()
        filename = self.output_meta()
        self.output_features(f'{filename}.csv')

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

        self.header_results = header_results[0]
        self.feature_results = feature_results[0]

        if 'Flatness' not in self.header_results:
            raise ValueError('Flatness not found in header. Please check the OGP template.')

        return header_results, feature_results
    
    def output_features(self, output_filename):
        """Output feature results to a csv file."""
        with open(pjoin(self.output_dir, output_filename), 'w') as f:
            f.write(self.feature_results)
    
    def output_meta(self) -> str:
        """Output metadata to a file, with filename based on ComponentID and Operator.
        
        Return 
        - filename (str): Filename prefix of the metadata file."""
        header_dict = self.header_results
        filename = f"{header_dict['ComponentID']}_{header_dict['Operator']}"
        meta_file = f'{filename}_meta.yaml'
        with open(f'{self.output_dir}/{meta_file}', 'w') as f:
            yaml.dump(header_dict, f, default_flow_style=False)
        return filename
        
    def get_feature(self, feature_name, filterType=None):
        """Get feature by name."""
        csv_io = StringIO(self.feature_results)
        df = pd.read_csv(csv_io)

        return self.get_feature_from_df(df, feature_name, filterType)
    
    @staticmethod
    def get_feature_from_df(df, feature_name, filterType=None):
        assert feature_name in df.columns, 'Feature not found'

        if filterType is None: filtered_df = df
        else: filtered_df = df[df['FeatureType'] == filterType]

        return filtered_df[feature_name].dropna()
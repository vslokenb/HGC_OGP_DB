import re, os
from ttp import ttp
import pandas as pd
import chardet
from io import StringIO

pjoin = os.path.join

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
"""

data_template = """
{{FeatureType}} {{FeatureName}}
Point     {{X_coordinate}}    {{Y_coordinate}}    {{Z_coordinate}}
direction cosine:    {{I_coordinate}}    {{J_coordinate}}    {{KKKK.KKKKKKKKKK}}
Radius            {{RRRR.RRR}}
"""

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
direction cosine:    {{I_coordinate}}    {{J_coordinate}}    {{KKKK.KKKKKKKKKK}}
Radius            {{RRRR.RRR}}
</group>
"""

class DataParser():
    """Parse data file using TTP template."""
    def __init__(self, data_file):
        with open(data_file, 'r') as f:
            self.data = f.read()

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

        self.header_results = header_results
        self.feature_results = feature_results

        return header_results, feature_results
    
    def output_features(self, output_file):
        """Output feature results to a csv file."""
        with open(output_file, 'w') as f:
            f.write(self.feature_results[0])
        
    def get_feature(self, feature_name, filterType=None):
        """Get feature by name."""
        csv_io = StringIO(self.feature_results[0])
        df = pd.read_csv(csv_io)
        print(df.columns)
        assert feature_name in df.columns, 'Feature not found'

        if filterType is None: filtered_df = df
        else: filtered_df = df[df['FeatureType'] == filterType]

        return filtered_df[feature_name].dropna()
        
if __name__ == '__main__':
    file_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = pjoin(file_dir, 'templates')
    data_file = pjoin(template_dir, 'ex_fullOut.txt')
    
    dp = DataParser(data_file)
    header, features = dp.read_temp_sep()
    print(features)

    # read_ogp_template(ogp_template_path, output_path)
    # read_data(default_template, data_file)
    # read_data(header_template, example_header)
    
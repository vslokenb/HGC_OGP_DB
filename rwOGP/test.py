import os, yaml, sys
import pandas as pd

pjoin = os.path.join

file_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = pjoin(file_dir, 'rwOGP')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.parse_data import DataParser
from src.ogp_height_plotter import PlotTool
from src.param import modules_params as component_params

if __name__ == '__main__':
    parser = DataParser(pjoin('rwOGP', 'templates', 'samples', 'module_110.txt'), 'tests')
    meta, features = parser()

    with open(meta[0], 'r') as f:
        metadata = yaml.safe_load(f)

    feature_df = pd.read_csv(features[0])
    PT = PlotTool(metadata, feature_df, 'rwOGP/templates/trays', 'tests')
    
    im_args = {"vmini":component_params['vmini'], "vmaxi":component_params['vmaxi'], 
            "new_angle": component_params['new_angle'], "savename": "ex_heights",
            "mod_flat": metadata['Flatness'], "title": metadata['ComponentID'], "show_plot": True}
    PT.get_offsets()
    PT(**im_args)



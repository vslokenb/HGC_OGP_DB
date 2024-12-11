import os, yaml, sys, json
import pandas as pd

pjoin = os.path.join

file_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = pjoin(file_dir, 'rwOGP')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.parse_data import DataParser
from src.ogp_height_plotter import PlotTool

if __name__ == '__main__':
    parser = DataParser(pjoin('rwOGP', 'templates', 'dummy4.txt'), 'tests')
    meta, features = parser()
    print(meta, features)

    with open(meta[0], 'r') as f:
        metadata = yaml.safe_load(f)

    feature_df = pd.read_csv(features[0])
    PT = PlotTool(metadata, feature_df, 'rwOGP/templates/trays', 'tests')
    PT.get_offsets()


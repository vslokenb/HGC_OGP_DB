import os
import sys

file_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(file_dir)
sys.path.append(parent_dir)

from parse_data import DataParser, pjoin
from ogp_height_plotter import plot2d

if __name__ == "__main__":
    template_dir = pjoin(parent_dir, 'templates')
    data_file = pjoin(template_dir, 'ex_fullOut.txt')
    
    dp = DataParser(data_file)
    header, features = dp.read_temp_sep()

    dp.output_features(pjoin(parent_dir, 'templates', 'features.csv'))

    plot2d(dp.get_feature('X_coordinate'), dp.get_feature('Y_coordinate'), dp.get_feature('Z_coordinate'))
    
    
    
    
    
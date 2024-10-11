import os
import sys

file_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(file_dir)
sys.path.append(parent_dir)

from src.parse_data import DataParser, pjoin
from src.ogp_height_plotter import PlotTool

if __name__ == "__main__":
    template_dir = pjoin(parent_dir, 'templates')
    data_file = pjoin(template_dir, 'ex_fullOut.txt')
    
    dp = DataParser(data_file, template_dir)
    dp()

    PlotTool.plot2d(dp.get_feature('X_coordinate'), dp.get_feature('Y_coordinate'), dp.get_feature('Z_coordinate'), center=5)
    
    
    
    
    
import os, yaml, sys, logging
import pandas as pd

pjoin = os.path.join

file_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = pjoin(file_dir, 'rwOGP')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.parse_data import DataParser
from src.ogp_height_plotter import PlotTool
from src.param import modules_params as component_params
from src.param import pin_mapping
from src.legacy_func import calculate_sensor_alignment
from src.config_utils import setup_logging
from rich.console import Console
from rich.table import Table
# from src.make_accuracy_plot import make_accuracy_plot

def test_angle_calculations(sample_name):
    """Compare angle calculations between legacy and new implementation."""
    # Setup the same test data used in both functions
    logging.warning("New Method results ...")
    parser = DataParser(pjoin('rwOGP', 'templates', 'samples', sample_name), 'tests')
    meta, features = parser()

    with open(meta[0], 'r') as f:
        metadata = yaml.safe_load(f)
        
    setup_logging(level=logging.INFO)
    feature_df = pd.read_csv(features[0])
    
    # Get results from new implementation (PlotTool)
    PT = PlotTool(metadata, "protomodules", feature_df, 'rwOGP/templates/trays', 'tests')
    FD_points = PT.get_FDs()

    hole_xy, slot_xy = PT.get_pin_coordinates()
    position = PT.meta['PositionID']
    
    # Calculate using new method
    centeroff_new, angleoff_new, xoff_new, yoff_new = PT.angle(hole_xy, slot_xy, FD_points)

    logging.warning("Legacy function results ...")
    
    # Prepare data for legacy function
    legacy_points = {
        "Center.X": hole_xy[0],
        "Center.Y": hole_xy[1],
        "OffCenter.X": slot_xy[0],
        "OffCenter.Y": slot_xy[1]
    }
    
    # Add FD points
    for i in range(4):
        legacy_points[i] = FD_points[i]
    
    # Calculate using legacy method
    centeroff_legacy, angleoff_legacy = calculate_sensor_alignment(
        legacy_points, 
        FDpoints=4,
        OffCenterPin="Left" if position == 1 else "Right"
    )
    
    # Compare results
    logging.info("\nComparison of angle calculation methods:")
    logging.info(f"{'':20} {'New':>10} {'Legacy':>10} {'Diff':>10}")
    logging.info("-" * 50)
    logging.info(f"{'Center Offset (mm)':20} {centeroff_new:10.3f} {centeroff_legacy:10.3f} {abs(centeroff_new-centeroff_legacy):10.3f}")
    logging.info(f"{'Angle Offset (deg)':20} {angleoff_new:10.3f} {angleoff_legacy:10.3f} {abs(angleoff_new-angleoff_legacy):10.3f}")

if __name__ == '__main__':
    logging.info("Running tests for 320PLF3W2CM0121.txt")
    test_angle_calculations("320PLF3W2CM0121.txt")
    
    logging.info("Running tests for 320PLF3W2CM0122.txt")
    test_angle_calculations("320PLF3W2CM0122.txt")
    
#     parser = DataParser(pjoin('rwOGP', 'templates', 'samples', '320PLF3W2CM0121.txt'), 'tests')
    # meta, features = parser()

    # with open(meta[0], 'r') as f:
        # metadata = yaml.safe_load(f)
        
    # setup_logging()

    # feature_df = pd.read_csv(features[0])
    # PT = PlotTool(metadata, "protomodules", feature_df, 'rwOGP/templates/trays', 'tests')
    
    # im_args = {"vmini":component_params['vmini'], "vmaxi":component_params['vmaxi'], 
            # "new_angle": component_params['new_angle'], "savename": "ex_heights",
            # "mod_flat": metadata['Flatness'], "title": metadata['ComponentID'], "show_plot": True}

    # XOffset, Yoffset, AngleOff = PT.get_offsets()
    # logging.info(f"XOffset: {XOffset}, YOffset: {Yoffset}, AngleOff: {AngleOff}")
    # make_accuracy_plot(metadata['ComponentID'], XOffset, Yoffset, AngleOff, 0, 0, 0)

    # PT(**im_args)



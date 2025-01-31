import numpy as np
import pandas as pd
import os, re
import yaml
import matplotlib.pyplot as plt
import matplotlib.colors as cls
from src.parse_data import DataParser
from src.param import pin_mapping, plot2d_dim, ADJUSTMENTS

pjoin = os.path.join

class PlotTool:
    def __init__(self, meta, component_type, features: 'pd.DataFrame', tray_dir, save_dir=None):
        """
        Parameters
        - `meta`: metadata of the features, including Tray ID, Operator, and Component ID
        - `component_type`: type of the component, either 'protomodules' or 'modules'
        - `features`: dataframe of features to plot
        - `save_dir`: directory to save the plots to"""
        self.save_dir = save_dir
        self.meta = meta
        self.comp_type = component_type
        self.tray_dir = tray_dir
        #! this is a hack
        self.features = DataParser.get_xyz(features, ['Tray'])
        self.x_points = self.features['X_coordinate']
        self.y_points = self.features['Y_coordinate']
        self.z_points = self.features['Z_coordinate']

        self.__check_save_dir()
    
    def __call__(self, **args):
        """Plot the 2D height map of the given data."""
        centerxy = self.get_center()
        im_bytes = self.plot2d(self.x_points, self.y_points, self.z_points, centerxy, **args)
        return im_bytes
     
    def __check_save_dir(self):
        if self.save_dir is not None:
            if not os.path.exists(self.save_dir):
                print(f"Directory {self.save_dir} does not exist.")
                print("Creating save directory:", self.save_dir)
                os.makedirs(self.save_dir)
    
    def get_center(self) -> int:
        """Get the index of the fiducial center in the dataframe by taking the average of the x and y coordinates."""
        # ! The plot2d function is not centered. Check validity of this function
        center_x = (max(self.x_points) + min(self.x_points)) / 2
        center_y = (max(self.y_points) + min(self.y_points)) / 2
        print(f"Center of the sensor is at ({center_x:.3f}, {center_y:.3f}) mm")
        return (center_x, center_y)
    
    @staticmethod
    def _calculate_height_stats(zheight):
        """Calculate basic height statistics."""
        mean_h = np.mean(zheight)
        std_h = np.std(zheight)
        max_h = max(zheight)
        min_h = min(zheight)
        
        print(f"Average Height is {mean_h:.3f} mm")
        print(f"Maximum Height is {max_h:.3f} mm")
        print(f"Minimum Height is {min_h:.3f} mm")
        print(f"Height --> {mean_h:.3f} + ({max_h - mean_h:.3f}) - ({mean_h - min_h:.3f}) mm. \n")
        
        return mean_h, std_h, max_h, min_h
    
    @staticmethod
    def _prepare_coordinates(x, y, centerxy, rotate, new_angle):
        """Prepare and transform coordinates."""
        center_x, center_y = centerxy
        x = x - center_x
        y = y - center_y

        assert rotate >= 0 and rotate < len(x), "The specified index for rotation has to be within the range of the data."
        if rotate != 0:
            rotate_angle = vec_angle(x[rotate-1], y[rotate-1]) if rotate != 0 else 0
            for i in range(len(x)):
                x[i], y[i] = vec_rotate(x[i], y[i], rotate_angle, new_angle)
        
        return x, y
    
    @staticmethod
    def _create_stats_text(mean_h, std_h, max_h, min_h, mod_flat=None):
        """Create statistics text for the plot."""
        base_stats = [
            f'mean: {mean_h:.3f} mm',
            f'std:     {std_h:.3f} mm',
            '',
            f'height: {mean_h:.3f} mm',
            f'       $+$ ({max_h - mean_h:.3f}) mm',
            f'       $-$ ({mean_h - min_h:.3f}) mm',
            '',
            f'$\Delta$H = {max_h - min_h:.3f} mm',
            '',
            f'maxH: {max_h:.3f} mm',
            f'minH:  {min_h:.3f} mm'
        ]
        
        if mod_flat is not None:
            base_stats.extend(['', f'flatness: {mod_flat:.3f}'])
        
        return '\n'.join(base_stats)
    
    @staticmethod
    def _save_plot_output(fig, savename):
        """Save plot to file and return bytes.
        
        Parameters
        ----------
        fig : matplotlib.figure.Figure
            The figure object to save
        savename : str
            Path where to save the figure
            
        Returns
        -------
        bytes
            The figure data in bytes format
        """
        from io import BytesIO
        buffer = BytesIO()
        fig.savefig(savename, bbox_inches='tight')
        fig.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_bytes = buffer.read()
        buffer.close()
        plt.close(fig)
        return image_bytes
    
    @staticmethod
    def plot2d(x, y, zheight, centerxy, vmini, vmaxi, new_angle, title, savename, mod_flat, show_plot, value=1, rotate=0):
        """Plot 2D height map of the given data.
        [... existing docstring ...]
        """
        mean_h, std_h, max_h, min_h = PlotTool._calculate_height_stats(zheight)
        
        x, y = PlotTool._prepare_coordinates(x, y, centerxy, rotate, new_angle)
        
        # Create plot
        fig = plt.figure(dpi=150, figsize=(9,5))
        axs = fig.add_subplot(111)
        axs.set_aspect('equal')
        
        # Plot data
        axs.hexbin(x, y, zheight, gridsize=20, vmin=vmini, vmax=vmaxi, cmap=plt.cm.coolwarm)
        norm = cls.Normalize(vmin=vmini, vmax=vmaxi)
        sm = plt.cm.ScalarMappable(norm=norm, cmap=plt.cm.coolwarm)
        cb = plt.colorbar(sm, ax=axs)
        cb.minorticks_on()
        
        # Set plot properties
        axs.set_xlabel("x (mm)")
        axs.set_ylabel("y (mm)")
        axs.minorticks_on()
        axs.set_xlim(plot2d_dim)
        axs.set_ylim(plot2d_dim)
        cb.set_label("Height (mm)")
        axs.set_title(title)
        
        # Add statistics text
        textstr = PlotTool._create_stats_text(mean_h, std_h, max_h, min_h, mod_flat)
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        axs.text(1.3, 1.0, textstr, transform=axs.transAxes, fontsize=10, verticalalignment='top', bbox=props)

        for xi, yi, zi in zip(x, y, zheight):
            axs.text(xi, yi, f"{zi:.2f}", fontsize=8, color='black', ha='center', va='bottom')
        
        if show_plot:
            plt.show()
            plt.close(fig)
            return None
            
        return PlotTool._save_plot_output(fig, savename)

    def angle(self, holeXY:tuple, slotXY:tuple, FDPoints:np.array):
        """Calculate the angle and offset of the sensor from the tray fiducials.
        
        Parameters
        - `holeXY`: the location of the pin that corresponds to the HOLE in the base plate. the center pin for Full, LD/HD.
        - `slotXY`: the location of the pin that corresponds to the SLOT in the base plate. the offcenter pin for Full, LD/HD.
        - `FDPoints`: array of fiducial points: 2, 4, 6, or 8, FD points are accepted

        Return
        - `CenterOffset`: offset of the sensor from the tray center
        - `AngleOffset`: angle of the sensor from the tray fiducials
        - `XOffset`: x-offset of the sensor from the tray center
        - `YOffset`: y-offset of the sensor from the tray center"""

        geometry, density, position, CompType = self.meta['Geometry'], self.meta['Density'], self.meta['PositionID'], self.comp_type

        holeX, holeY = holeXY
        slotX, slotY = slotXY

        pinX = slotX - holeX     #X component of a vector pointing from hole to slot
        pinY = slotY - holeY     #Y component "" ""

        Hole = np.array([holeX, holeY])
        print(f'pinX: {pinX}  &  pinY: {pinY}')

        if geometry == 'Full' or geometry == 'Bottom' or geometry == 'Top':
            if density == 'HD':
                if position == 1:
                    angle_Pin = np.degrees(np.arctan2(-pinY,-pinX))
                if position == 2:
                    angle_Pin = np.degrees(np.arctan2(pinY,pinX))
            if density == 'LD':
                if position == 1:
                    angle_Pin = np.degrees(np.arctan2(-pinY,-pinX))
                if position == 2:
                    angle_Pin = np.degrees(np.arctan2(pinY,pinX))
        elif geometry == 'Left' or geometry == 'Right' or geometry == 'Five':
            angle_Pin= np.degrees(np.arctan2(-pinY, -pinX))

        print(f'Angle pin: {angle_Pin}')
    
        if density == 'HD':   
            if geometry == 'Full':
                FDCenter = np.nanmean(FDPoints, axis=0) #Average of All FDs
            else:
                FDCenter = np.mean(FDPoints[[0,2]], axis=0)  #Average of FD1 and FD3, this applies to modules except HD Full
        if density == 'LD':
            if geometry == 'Full':
                FDCenter = np.mean(FDPoints[[2,5]], axis=0)
            else:
                FDCenter = np.mean(FDPoints[[0,2]], axis=0)  #Average of FD1 and FD3, this applies to all modules except LD Full
        
        adjustmentX, adjustmentY = ADJUSTMENTS[CompType][geometry][density][position]
        
        XOffset = FDCenter[0]-Hole[0]-adjustmentX
        YOffset = FDCenter[1]-Hole[1]-adjustmentY
        print(f"Hole Vs FDCenter: {Hole} vs {FDCenter}")

        print(f"Assembly Survey X Offset: {XOffset:.3f} mm.")
        print(f"Assembly Survey Y Offset: {YOffset:.3f} mm. \n")

        CenterOffset = np.sqrt(XOffset**2 + YOffset**2)

        FD3to1 = FDPoints[0] - FDPoints[2]  #Vector from FD3 to FD1
        
        if geometry == 'Bottom' or geometry == 'Top':       #if geometry is Top or bottom, FD3to1 will point either left or right
            angle_FD3to1 = np.degrees(np.arctan2(FD3to1[1],FD3to1[0]))
        elif geometry == 'Left' or geometry == 'Right' or geometry == 'Five':     #if geometry is Five, Right or Left, FD3to1 will point either up or down
            angle_FD3to1 = (np.degrees(np.arctan2(FD3to1[0],FD3to1[1])) * -1);
        elif geometry == 'Full' and density == 'HD':
            if position == 1:
                FD3to1 = FDPoints[1] - FDPoints[0]
                print("Angle calculated with FD1 & FD2")
                angle_FD3to1 = (np.degrees(np.arctan2(FD3to1[0],FD3to1[1])) * -1);
            if position == 2:
                FD3to1 = FDPoints[1] - FDPoints[0]
                print("Angle calculated with FD1 & FD2")
                angle_FD3to1 = (np.degrees(np.arctan2(-FD3to1[0],-FD3to1[1])) * -1);
            print("Current Angle:", angle_FD3to1)
        elif geometry == 'Full' and density == 'LD':
            print("Angle calculated with FD6 & FD3")
            FD3to1 = FDPoints[2] - FDPoints[5]
            if position == 1:
                angle_FD3to1 = (np.degrees(np.arctan2(FD3to1[0],FD3to1[1])) * -1);
            if position == 2:
                angle_FD3to1 = (np.degrees(np.arctan2(-FD3to1[0],-FD3to1[1])) * -1);

        AngleOffset = angle_FD3to1 - angle_Pin

        return CenterOffset, AngleOffset, XOffset, YOffset

    def get_FDs(self) -> np.array:
        """Get the fiducial points from the features dataframe, ordered by the FD number.
        
        Return 
        - `FD_points`: 8 by 2 array of fiducial points, empty points are filled with np.nan"""
        print("Reading the fiducial points from the features dataframe.")
        FD_points = self.features[self.features['FeatureName'].str.contains('FD')].copy()
        FD_points.loc[:, 'FD_number'] = FD_points['FeatureName'].apply(lambda x: int(re.search(r'FD(\d+)', x).group(1)) if re.search(r'FD(\d+)', x) else 0)
        FD_names = FD_points['FeatureName'].values
        FD_numbers = FD_points['FD_number'].values
        x_y_coords = FD_points[['X_coordinate', 'Y_coordinate']].values
        num_FDs = len(x_y_coords)
        assert num_FDs in {2, 4, 6, 8}, "The number of fiducial points measured must be 2, 4, 6, or 8."
        
        # Sort points based on FD numbers
        sort_indices = np.argsort(FD_numbers)
        FD_points = x_y_coords[sort_indices]
        print(f"Found {num_FDs} fiducial points: {FD_names}")

        FD_array = np.full((8,2), np.nan)
        for i, (x,y) in zip(FD_numbers, FD_points):
            print(f"FD{i}: ({x:.3f}, {y:.3f})")
            FD_array[i-1] = [x,y]

        return FD_array

    def get_offsets(self):
        """Get the offsets of the sensor from the tray fiducials.
        
        Return 
        - `XOffset`: x-offset of the sensor from the tray center
        - `YOffset`: y-offset of the sensor from the tray center
        - `AngleOff`: angle of the sensor from the tray fiducials"""
        PositionID, Geometry, density, TrayNo = self.meta['PositionID'], self.meta['Geometry'], self.meta['Density'], self.meta['TrayNo']

        TrayFile = pjoin(self.tray_dir, f"Tray{TrayNo}.yaml") 

        print("Loading TrayFile:", TrayFile)
        with open(TrayFile, 'r') as f:
            trayinfo = yaml.safe_load(f)
        
        if PositionID == 1:
            pos = 'left'
        else: pos = 'right'

        HolePin, SlotPin = pin_mapping.get(Geometry, {}).get(density, {}).get(PositionID, ('', ''))

        if HolePin == '' or SlotPin == '':
            print(f"Could not find the HolePin and SlotPin for the given Geometry: {Geometry} and Density: {density}.")

        HolePin_xy = tuple(trayinfo[f'{HolePin}_xy'])  
        SlotPin_xy = tuple(trayinfo[f'{SlotPin}_xy'])

        FD_points = self.get_FDs()

        plotFD(FD_points, HolePin_xy, SlotPin_xy, True, pjoin(self.save_dir, f"{self.meta['ComponentID']}_FDpoints.png"))
        
        print("=" * 100)
        print(f'Calculating Angle and Offsets with:  {HolePin} @: {HolePin_xy} & {SlotPin} @: {SlotPin_xy} \n')
        print(f"Geometry: {Geometry}; Density: {density}; PositionID: {PositionID}")

        CenterOff, AngleOff, XOffset, YOffset = self.angle(HolePin_xy, SlotPin_xy, FD_points)

        print(f"Assembly Survey Rotational Offset is {AngleOff:.5f} degrees")
        print(f"Assembly Survey Center Offset is {CenterOff:.3f} mm")

        if abs(AngleOff) > 20:
            raise ValueError("The calculated angle offset is too large. Check the fiducial points and the sensor position (Pos 1 vs. 2)")
        if abs(XOffset) > 1 or abs(YOffset) > 1:
            raise ValueError("The calculated offset is too large. Check the fiducial points and the sensor position (Pos 1 vs. 2)")

        return XOffset, YOffset, AngleOff

def vec_angle(x,y):
    angle_arctan = np.degrees(np.arctan2(y,x))
    return angle_arctan

def vec_rotate(old_x, old_y, old_angle, new_angle = 120):
    """Rotate a vector by a given angle.

    Parameters
    - `old_x`: x-coordinate of the vector
    - `old_y`: y-coordinate of the vector
    - `old_angle`: angle of the vector
    - `new_angle`: angle to rotate the vector to"""
    rad = np.radians(new_angle - old_angle)
    new_x = old_x*np.cos(rad)-old_y*np.sin(rad)
    new_y = old_x*np.sin(rad)+old_y*np.cos(rad)
    return new_x, new_y
    
def plotFD(FDpoints:np.array, holeXY:tuple, slotXY:tuple, save=False, save_name='') -> None:
    """Plot the fiducial points and the center of the sensor.
    
    Parameters
    - `FDpoints`: array of fiducial points
    - `holeXY`: HOLE in the BP. The center pin for Full, LD/HD.
    - `slotXY`: SLOT in the BP. The offcenter pin for Full, LD/HD.
    - `save`: whether to save the plot. Incompatible with showing the plot.
    - `save_name`: name to save the plot as"""
    CenterX, CenterY = holeXY
    OffX, OffY = slotXY

    plt.figure()
    FDnames = ['FD1', 'FD2', 'FD3', 'FD4', 'FD5', 'FD6', 'FD7', 'FD8']
    plt.plot(FDpoints[:,0], FDpoints[:,1], 'ro', ms=2)
    plt.plot(CenterX, CenterY, 'ro', ms=2)
    plt.annotate('CenterPin', (CenterX, CenterY))
    plt.plot(OffX, OffY, 'bo', ms=2)
    plt.annotate('OffcenterPin', (OffX, OffY))
    plt.arrow(OffX, OffY, CenterX-OffX, CenterY-OffY, lw=0.5, color='g')
    for i, (x, y) in enumerate(FDpoints):
        if not np.isnan(x) and not np.isnan(y):
            plt.annotate(FDnames[i], (x, y))
    
    plt.xlim(50,190)
    plt.xlabel("x [mm]")
    plt.ylabel("y [mm]")

    plt.title("Fiducial Points")
    if save: plt.savefig(save_name)
    else: plt.show()
    plt.close()

def vec_angle(x,y):
    angle_arctan = np.degrees(np.arctan2(y,x))
    return angle_arctan

def vec_rotate(old_x, old_y, old_angle, new_angle = 120):
    """Rotate a vector by a given angle.

    Parameters
    - `old_x`: x-coordinate of the vector
    - `old_y`: y-coordinate of the vector
    - `old_angle`: angle of the vector
    - `new_angle`: angle to rotate the vector to"""
    rad = np.radians(new_angle - old_angle)
    new_x = old_x*np.cos(rad)-old_y*np.sin(rad)
    new_y = old_x*np.sin(rad)+old_y*np.cos(rad)
    return new_x, new_y

        
def quality(Center, Rotation, position = "P1", details =0, note = 0):
    '''
    QC designation for different measurements
    Measurement      |         GREEN          |        YELLOW         |          RED          |
    _________________|________________________|_______________________|_______________________|
    Angle of Plac.   |0 < abs(x - 90.) <= 0.03 |0.03 < abs(x - 90.) <= .06| 0.06 < abs(x - 90.)<90| 
    Placement        |      0 < x <= 0.05     |    0.05 < x <= 0.1    |      0.1 < x <= 10.   | 
    Height           |0 < abs(x - Nom) <= 0.05|0.05 <abs(x - Nom)<=0.1|0.1 < abs(x - Nom)<=10.| 
    Max Hght from Nom|      0 < x <= 0.05     |    0.05 < x <= 0.1    |    0.1 < x <= 10.     | 
    Min Hght ffrom Nom|      0 < x <= 0.05     |    0.05 < x <= 0.1    |    0.1 < x <= 10.     | 
    
#     '''
#     if details == 1:
#         print(f"The Center Offset is {Center:.3f} mm")
#         print(f"The Rotational Offset is {Rotation:.5f} degrees ")
#         print()
        
#     for i, p in enumerate(centers):
#         if Center < p:
#             print(f"The placement in position {position} is {colorClassify[str(i)]}")
#             break
#         elif Center > centers[-1]:
#             print(f"The placement in position {position} is more than {centers[-1]} mm")
#             break
            
#     for j, d in enumerate(degrees):
#         if abs(Rotation) < d:
#             print(f"The angle in position {position} is {colorClassify[str(j)]}")
#             break
#         elif abs(Rotation) > degrees[-1]:
#             print(f"The angle in position {position} is more than {degrees[-1]} degree")
#             break
#     return colorClassify[str(i)], colorClassify[str(j)]
#     # if note == 1:
#     #     print()
#     #     help(QualityControl)

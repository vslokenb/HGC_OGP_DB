import numpy as np
import pandas as pd
import os
import yaml
import matplotlib.pyplot as plt
import matplotlib.colors as cls
from src.parse_data import DataParser
from src.param import one_tray_param
import warnings

pjoin = os.path.join

class PlotTool:
    def __init__(self, meta, features: 'pd.DataFrame', tray_dir, save_dir=None):
        """
        Parameters
        - `meta`: metadata of the features, including Tray ID, Operator, and Component ID
        - `features`: dataframe of features to plot
        - `save_dir`: directory to save the plots to"""
        self.save_dir = save_dir
        self.meta = meta
        self.tray_dir = tray_dir
        self.features = DataParser.get_xyz(features)
        self.x_points = self.features['X_coordinate']
        self.y_points = self.features['Y_coordinate']
        self.z_points = self.features['Z_coordinate']
    
    def __call__(self, **args):
        """Plot the 2D height map of the given data."""
        centerxy = self.get_center()
        im_bytes = self.plot2d(self.x_points, self.y_points, self.z_points, centerxy, **args)
        return im_bytes
    
    def get_center(self) -> int:
        """Get the index of the fiducial center in the dataframe by taking the average of the x and y coordinates."""
        center_x = (max(self.x_points) + min(self.x_points)) / 2
        center_y = (max(self.y_points) + min(self.y_points)) / 2
        return (center_x, center_y)

    @staticmethod
    def plot2d(x, y, zheight, centerxy, vmini, vmaxi, new_angle, title, savename, mod_flat, show_plot, value = 1, rotate=0):
        """Plot 2D height map of the given data.
        Parameters
        - `x`: x-coordinates
        - `y`: y-coordinates
        - `zheight`: height values
        - `centerxy`: tuple of the center coordinates (x,y)
        - `vmini`: minimum height value
        - `vmaxi`: maximum height value
        - `rotate`: index of the fiducial to rotate the plot around
        - `new_angle`: angle to rotate the plot to
        - `title`: title of the plot
        - `show_plot`: whether to show the plot. Imcompatible with saving the plot.
        - `value`: 1 for plotting height values, 0 for plotting deviation from mean"""
        mean_h = np.mean(zheight)
        std_h = np.std(zheight)
        max_h = max(zheight)
        min_h = min(zheight)
        print(f"Average Height is {mean_h:.3f} mm")
        print(f"Maximum Height is {max_h:.3f} mm")
        print(f"Minimum Height is {min_h:.3f} mm")
        print(f"Height --> {mean_h:.3f} + ({max_h - mean_h:.3f}) - ({mean_h - min_h:.3f}) mm. \n")
        
        center_x, center_y = centerxy

        x = x- center_x
        y = y- center_y

        assert rotate >= 0 and rotate < len(x), "The specified index for rotation has to be within the range of the data."
        if rotate != 0:
            rotate_angle = vec_angle(x[rotate-1], y[rotate-1]) if rotate != 0 else 0
            for i in range(len(x)):
                x[i], y[i] = vec_rotate(x[i],y[i],rotate_angle, new_angle)

        fig=plt.figure(dpi=150, figsize=(9,5))
        axs=fig.add_subplot(111); axs.set_aspect('equal')
        
        axs.hexbin(x,y,zheight,gridsize=20, vmin = vmini, vmax = vmaxi, cmap=plt.cm.coolwarm)
        norm = cls.Normalize(vmin=vmini, vmax=vmaxi)
        sm = plt.cm.ScalarMappable(norm=norm, cmap=plt.cm.coolwarm)
        cb=plt.colorbar(sm, ax= axs); cb.minorticks_on()
        # else:
        #     if title == '815 PCB fiducials':
        #         thickness = np.array([10,11,12,13,14,15,16,17,18,1,2,3,4,5,6,7,8,9,19,20,21,22,23,24,25])
        #         axs.annotate(f"{thickness[i]}",(x[i],y[i]),color="black")
        # #axs.annotate(f"{i+1}",(temp[0][i],temp[1][i]),color="black")
        #     else:
        #         axs.annotate(f"{i+1}",(x[i],y[i]),color="black")

        axs.set_xlabel("x (mm)")
        axs.set_ylabel("y (mm)")
        axs.minorticks_on()
        axs.set_xlim(left=-100, right=100)
        axs.set_ylim(bottom=-100, top=100)
        cb.set_label("Height (mm)")
        axs.set_title(title)
        if mod_flat is not None:
            textstr = '\n'.join((f'mean: {mean_h:.3f} mm',f'std:     {std_h:.3f} mm','', f'height: {mean_h:.3f} mm', f'       $+$ ({max_h - mean_h:.3f}) mm', f'       $-$ ({mean_h - min_h:.3f}) mm',
                                '',f'$\Delta$H = {max_h - min_h:.3f} mm','', f'maxH: {max_h:.3f} mm', f'minH:  {min_h:.3f} mm','', f'flatness: {mod_flat:.3f}'))
        else:
            textstr = '\n'.join((f'mean: {mean_h:.3f} mm',f'std:     {std_h:.3f} mm','', f'height: {mean_h:.3f} mm', f'       $+$ ({max_h - mean_h:.3f}) mm', f'       $-$ ({mean_h - min_h:.3f}) mm',
                            '',f'$\Delta$H = {max_h - min_h:.3f} mm','', f'maxH: {max_h:.3f} mm', f'minH:  {min_h:.3f} mm',''))
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        axs.text(1.3, 1.0, textstr, transform=axs.transAxes, fontsize=10, verticalalignment='top', bbox=props)

        if show_plot:
            print("Not saving the plot or the image bytes as show_plot is set to True.")
            plt.show(); 
            plt.close()
        
        from io import BytesIO  
        buffer = BytesIO()
        plt.savefig(savename, bbox_inches='tight')
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        return buffer.read()

    def get_offsets(self):
        """Get the offsets of the sensor from the tray fiducials.
        
        Return 
        - `XOffset`: x-offset of the sensor from the tray center
        - `YOffset`: y-offset of the sensor from the tray center
        - `AngleOff`: angle of the sensor from the tray fiducials"""
        if not self.meta.get('PositionID'): 
            warnings.warn("PositionID not found in metadata. Default to Position ID 1.")
            PositionID = 1
        else:
            PositionID = int(self.meta['PositionID'])

        if not self.meta.get('TrayNo'):
            warnings.warn("TrayNo not found in metadata. Default to Tray 1.")
            TrayNo = 1
        else:
            TrayNo = int(self.meta['TrayNo'])

        TrayFile = pjoin(self.tray_dir, f"Tray{TrayNo}.yaml") 
        with open(TrayFile, 'r') as f:
            trayinfo = yaml.safe_load(f)
        
        if PositionID == 1:
            pos = 'left'
        else: pos = 'right'
        
        centerxy = tuple(trayinfo[f'p{PositionID}_center_pin_xy'])
        offsetxy = tuple(trayinfo[f'p{PositionID}_offcenter_pin_{pos}_xy'])

        FD_points = self.features[self.features['FeatureName'].str.contains('FD')]
        FD_points = FD_points[['X_coordinate', 'Y_coordinate']].values
    
        CenterOff, AngleOff, XOffset, YOffset = angle(centerxy, offsetxy, FD_points)    
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
    
def plotFD(FDpoints:np.array, FDCenter:tuple, CenterXY:tuple, OffXY:tuple) -> None:
    """Plot the fiducial points and the center of the sensor.
    
    Parameters
    - `FDpoints`: array of fiducial points
    - `FDCenter`: center of the fiducial points
    - `CenterXY`: center of the sensor
    - `OffXY`: offset of the sensor"""
    CenterX, CenterY = CenterXY
    OffX, OffY = OffXY
    x_values = np.append(FDpoints[:,0], [CenterX, OffX])
    y_values = np.append(FDpoints[:,1], [CenterY, OffY])
    names = [f'FD{no}' for no in range(1, len(FDpoints)+1)]
    names.extend(['Center', 'Offcenter'])

    plt.figure(dpi=250)
    plt.plot(x_values,y_values,'o',ms=2)
    plt.arrow(OffX, OffY, CenterX-OffX, CenterY-OffY, lw=0.5, color='g')
    plt.plot(FDCenter[0], FDCenter[1], 'ro', label='FDCenter', ms=2)
    for i in range(len(x_values)):
        plt.annotate(names[i], (x_values[i], y_values[i]))
    
    plt.legend()
    plt.xlim(60,160)
    plt.xlabel("x [mm]")
    plt.ylabel("y [mm]")

    plt.title("Fiducial Points")

#! Messy part: serve as reference for future development
    # if FDpoints == 2:
    #     plt.arrow(Xp[2],Yp[2],Xp[3]-Xp[2],Yp[3]-Yp[2],lw=0.5,color='orange')

    # if FDpoints == 4:
    #     plt.arrow(Xp[2],Yp[2],Xp[4]-Xp[2],Yp[4]-Yp[2],lw=0.5,color='orange')
    #     plt.arrow(Xp[3],Yp[3],Xp[5]-Xp[3],Yp[5]-Yp[3],lw=0.5,color='orange')
    #     plt.plot(FDCenter[0],FDCenter[1],'ro',label='FDCenter',ms=2)
    #     names = ['P1CenterPin','P1OffcenterPin','FD1','FD2','FD3','FD4']

def angle(centerXY:tuple, offsetXY:tuple, FDPoints:np.array):
    """Calculate the angle and offset of the sensor from the tray fiducials.
    
    Parameters
    - `centerXY`: center of the sensor
    - `offsetXY`: offset of the sensor
    - `FDPoints`: array of fiducial points
    
    Return
    - `CenterOffset`: offset of the sensor from the tray center
    - `AngleOffset`: angle of the sensor from the tray fiducials
    - `XOffset`: x-offset of the sensor from the tray center
    - `YOffset`: y-offset of the sensor from the tray center"""
    
    centerX, centerY = centerXY
    offsetX, offsetY = offsetXY
    pinX = abs(centerX - offsetX)
    pinY = abs(centerY - offsetY)

    assert len(FDPoints) == 2 or len(FDPoints) == 4, "The number of fiducial points must be either 2 or 4."
    
    PinCenter = np.array([centerX, centerY])
    angle_Pin= np.degrees(np.arctan2(pinY, pinX))

    FDCenter = np.mean(FDPoints, axis=0)

    XOffset = FDCenter[0]-PinCenter[0]
    YOffset = FDCenter[1]-PinCenter[1]

    print(f"Assembly Survey Y Offset: {YOffset:.3f} mm. \n")
    print(f"Assembly Survey Y Offset: {YOffset:.3f} mm. \n")

    CenterOffset = np.sqrt(XOffset**2 + YOffset**2)

    Pin = np.array([pinX, pinY])
    u_Pin = Pin/np.linalg.norm(Pin)
    angle_Pin= np.degrees(np.arctan2(Pin[1],Pin[0]))

    if len(FDPoints) == 2:
        FD1 = FDPoints[0] - FDPoints[1]
        angle_FD1= np.degrees(np.arctan2(FD1[1],FD1[0]))-90 if FD1[1] > 0 else np.degrees(np.arctan2(FD1[1],FD1[0]))+90
        print(f"FD1-2 X'' axis is at angle {angle_FD1:.5f} degrees. \n")
        print(f"FDCenter at x:{FDCenter[0]:.3f} mm, y:{FDCenter[1]:.3f} mm")
        print(f"PinCenter at x:{PinCenter[0]:.3f} mm, y:{PinCenter[1]:.3f} mm")
        
        #! What's the purpose of these lines?
        # AngleOffset = angle_FD1 - angle_Pin
        # print(f"Assembly Survey Rotational Offset is {AngleOffset:.5f} degrees")
    
    if len(FDPoints) == 4:
        FD1 = FDPoints[0] - FDPoints[2]
        angle_FD1 = np.degrees(np.arctan2(FD1[1],FD1[0]))-90 if FD1[1] > 0 else np.degrees(np.arctan2(FD1[1],FD1[0]))+90
        FD2 = FDPoints[1] - FDPoints[3]
        angle_FD2 = np.degrees(np.arctan2(FD2[1],FD2[0]))-90 if FD2[1] > 0 else np.degrees(np.arctan2(FD2[1],FD2[0]))+90
        FD = (FD1+FD2)/2
        print(f"FD1-3 X'' axis is at angle {angle_FD1:.5f} degrees")
        print(f"angle of FD1-3 X'' relative to Assembly Tray Pin X' is {angle_FD1 - angle_Pin:.5f} degrees")
        print(f"FD2-4 X'' axis is at angle {angle_FD2:.5f} degrees")
        print(f"angle of FD2-4 X'' relative to Assembly Tray Pin X' is {angle_FD2 - angle_Pin:.5f} degrees. \n")
        print(f"FDCenter at x:{FDCenter[0]:.3f} mm, y:{FDCenter[1]:.3f} mm")
        print(f"PinCenter at x:{PinCenter[0]:.3f} mm, y:{PinCenter[1]:.3f} mm. \n")
        #! What's the purpose of these lines?
        #print(f"Pin X' axis is at angle {angle_Pin:.3f} degrees. \n")
        # u_FD = FD/np.linalg.norm(FD)
        # angle_FD= np.degrees(np.arctan2(FD[1],FD[0]))-90
        # print(f"Pin X' axis is at angle {angle_Pin:.5f} degrees. \n")
        # print(f"FD1-4 X'' axis is at angle {angle_FD:.5f} degrees")
        #print(f"Assembly Survey Rotational Offset is {angle_FD - angle_Pin:.5f} degrees. \n")
        #angle_FD1= np.degrees(np.arctan2(FD1[1],FD1[0]))
        #print(f"FD1-2 X'' axis is at angle {angle_FD1} degrees")


    AngleOffset = angle_FD1 - angle_Pin
    #! ADDED For Rotation if NEEDED
    # if OffCenterPin == "Left":
    #     NEWY = XOffset*-1;
    #     NEWX = YOffset; 
    # elif OffCenterPin == "Right":
    #     NEWY = XOffset;
    #     NEWX = YOffset*1; 
    # print(f"Assembly Survey X Offset: {NEWX:.3f} mm (rotated)")
    # print(f"Assembly Survey Y Offset: {NEWY:.3f} mm (rotated)")
    
    # print(f"Assembly Survey Rotational Offset is {AngleOffset:.5f} degrees")

    return CenterOffset, AngleOffset, XOffset, YOffset

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
    
    '''
    if details == 1:
        print(f"The Center Offset is {Center:.3f} mm")
        print(f"The Rotational Offset is {Rotation:.5f} degrees ")
        print()
        
    for i, p in enumerate(centers):
        if Center < p:
            print(f"The placement in position {position} is {colorClassify[str(i)]}")
            break
        elif Center > centers[-1]:
            print(f"The placement in position {position} is more than {centers[-1]} mm")
            break
            
    for j, d in enumerate(degrees):
        if abs(Rotation) < d:
            print(f"The angle in position {position} is {colorClassify[str(j)]}")
            break
        elif abs(Rotation) > degrees[-1]:
            print(f"The angle in position {position} is more than {degrees[-1]} degree")
            break
    return colorClassify[str(i)], colorClassify[str(j)]
    # if note == 1:
    #     print()
    #     help(QualityControl)

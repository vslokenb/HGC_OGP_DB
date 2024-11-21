import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.colors as cls
from src.parse_data import DataParser

class PlotTool:
    def __init__(self, features: 'pd.DataFrame', save_dir=None):
        """
        Parameters
        - `features`: dataframe of features to plot
        - `save_dir`: directory to save the plots to"""
        self.save_dir = save_dir
        self.features = DataParser.get_xyz(features)
        self.x_points = self.features['X_coordinate']
        self.y_points = self.features['Y_coordinate']
        self.z_points = self.features['Z_coordinate']
    
    def __call__(self, **kwds):
        """Plot the 2D height map of the given data."""
        centerxy = self.get_center()
        im_bytes = self.plot2d(self.x_points, self.y_points, self.z_points, centerxy, **kwds)
        return im_bytes
    
    def get_center(self) -> int:
        """Get the index of the fiducial center in the dataframe by taking the average of the x and y coordinates."""
        center_x = (max(self.x_points) + min(self.x_points)) / 2
        center_y = (max(self.y_points) + min(self.y_points)) / 2
        return (center_x, center_y)

    @staticmethod
    def plot2d(x, y, zheight, centerxy, vmini=1.05, vmaxi=4.5, rotate = 0 , new_angle = 120, title="", savename="", value = 1, day_count = None, mod_flat = None, show_plot = True):
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
        - `value`: 1 for plotting height values, 0 for plotting deviation from mean"""
        mean_h = np.mean(zheight)
        std_h = np.std(zheight)
        max_h = max(zheight)
        min_h = min(zheight)
        print(f"Average Height is {mean_h:.3f} mm")
        print(f"Maximum Height is {max_h:.3f} mm")
        print(f"Minimum Height is {min_h:.3f} mm")
        print(f"Height --> {mean_h:.3f} + ({max_h - mean_h:.3f}) - ({mean_h - min_h:.3f}) mm")
        print()
        
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
        if day_count is not None:
            legendstr = '\n'.join((f'Day',f'{day_count}'))
            axs.text(1.3, 0.20, legendstr, transform=axs.transAxes, fontsize=20, verticalalignment='top', color = 'blue')

        if show_plot:
            plt.show(); 
            plt.close()
        
        from io import BytesIO  
        buffer = BytesIO()
        plt.savefig(f"{(savename.split('/'))[-1]}.png", bbox_inches='tight') # uncomment here for saving the 2d plot
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        return buffer.read()

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
    

def check(file):
    if os.path.exists(file):
        return True
    else:
        print('FILEPATHS MAY BE WRONG!! CANNOT FIND ' + file)
        print()
        return False

def plotFD(FDpoints,FDCenter,Center, Off, points, fd, sheetnames = ['','']):
    CenterX = f"{Center}.X"
    CenterY = f"{Center}.Y"
    OffX = f"{Off}.X"
    OffY = f"{Off}.Y"
    if FDpoints == 2:
        Xp = [points[CenterX],points[OffX], points[fd[0]][0],points[fd[1]][0]]
        Yp = [points[CenterY],points[OffY], points[fd[0]][1],points[fd[1]][1]]
        plt.figure(dpi=250)
        plt.plot(Xp,Yp,'o',ms=2)
        plt.arrow(Xp[1],Yp[1],Xp[0]-Xp[1],Yp[0]-Yp[1],lw=0.5,color='g')
        plt.arrow(Xp[2],Yp[2],Xp[3]-Xp[2],Yp[3]-Yp[2],lw=0.5,color='orange')
        plt.plot(FDCenter[0],FDCenter[1],'ro',label='FDCenter',ms=2)
        names = ['P1CenterPin','P1OffcenterPin','FD1','FD2']
        for i in range(len(Xp)): 
            plt.annotate(names[i],(Xp[i],Yp[i]))
        plt.legend()
        plt.xlim(60,160)
        plt.title(sheetnames[1])
        plt.xlabel("x [mm]")
        plt.ylabel("y [mm]")
    if FDpoints == 4:
        Xp = [points[CenterX],points[OffX], points[fd[0]][0],points[fd[1]][0],points[fd[2]][0],points[fd[3]][0]]
        Yp = [points[CenterY],points[OffY], points[fd[0]][1],points[fd[1]][1],points[fd[2]][1],points[fd[3]][1]]
        plt.figure(dpi=250)
        plt.plot(Xp,Yp,'o',ms=2)
        plt.arrow(Xp[1],Yp[1],Xp[0]-Xp[1],Yp[0]-Yp[1],lw=0.5,color='g')
        #plt.plot([(Xp[3]+Xp[2])/2],[(Yp[3]+Yp[2])/2],lw=0.5)
        plt.arrow(Xp[2],Yp[2],Xp[4]-Xp[2],Yp[4]-Yp[2],lw=0.5,color='orange')
        plt.arrow(Xp[3],Yp[3],Xp[5]-Xp[3],Yp[5]-Yp[3],lw=0.5,color='orange')
        plt.plot(FDCenter[0],FDCenter[1],'ro',label='FDCenter',ms=2)
        names = ['P1CenterPin','P1OffcenterPin','FD1','FD2','FD3','FD4']
        for i in range(len(Xp)): 
            plt.annotate(names[i],(Xp[i],Yp[i]))
        plt.legend()
        plt.xlim(60,160)
        plt.title(sheetnames[1])
        plt.xlabel("x [mm]")
        plt.ylabel("y [mm]")
    print()


def angle(points,FDpoints=4,OffCenterPin = "Left", details = 0, plot = 0, Center = None, Off = None, fd = None):
    CenterX = f"{Center}.X"
    CenterY = f"{Center}.Y"
    OffX = f"{Off}.X"
    OffY = f"{Off}.Y"
    
    if (FDpoints != 2) and (FDpoints != 4):
        print(f"{FDpoints} Fiducial Points. Invalid Number. Please use either 2 or 4 Fiducial Points")
        #print("Detailing the Sensor FD points searching process for debugging")
        return 
    else:
        print(f"Using {FDpoints} Fiducial Points ")
    print()
    if (OffCenterPin != "Left") and (OffCenterPin != "Right"):
        print("Invalid OffCenter Pin Position")
        print("Please indicate whether OffCenter Pin is on the Left or Right to the Center Pin")
        #break
        return
    else:
        if OffCenterPin == "Left":
            Pin = np.array([points[CenterX],points[CenterY]]) - np.array([points[OffX],points[OffY]])
            print("OffCenter Pin is on the Left relative to the Center Pin")
        if OffCenterPin == "Right":
            Pin = np.array([points[OffX],points[OffY]]) - np.array([points[CenterX],points[CenterY]]) 
            print("OffCenter Pin is on the Right relative to the Center Pin")
    #elif (OffCenterPin != "Left") and (OffCenterPin != "Right"):
        #print("Please indicate whether OffCenter Pin is on the Left or Right to the Center Pin")
        #break
        print()
        PinCenter = np.array([points[CenterX],points[CenterY]])
        angle_Pin= np.degrees(np.arctan2(Pin[1],Pin[0]))
    #print(f"Pin X' axis is at angle {angle_Pin:.3f} degrees")
    if FDpoints==2:
        FD1 = points[fd[0]]-points[fd[1]]
        if FD1[1] > 0:
            angle_FD1= np.degrees(np.arctan2(FD1[1],FD1[0]))-90
        else:
            angle_FD1= np.degrees(np.arctan2(FD1[1],FD1[0]))+90
        FDCenter = (points[fd[0]]+points[fd[1]])/2
        if details == 1:
            print(f"FD1-2 X'' axis is at angle {angle_FD1:.5f} degrees")
            print()
            print(f"FDCenter at x:{FDCenter[0]:.3f} mm, y:{FDCenter[1]:.3f} mm")
            print(f"PinCenter at x:{PinCenter[0]:.3f} mm, y:{PinCenter[1]:.3f} mm")
        print()
        """XOffset = FDCenter[0]-PinCenter[0]
        YOffset = FDCenter[1]-PinCenter[1]
        print(f"Assembly Survey X Offset: {XOffset:.3f} mm")
        print(f"Assembly Survey Y Offset: {YOffset:.3f} mm")
        print()
        AngleOffset = angle_FD1 - angle_Pin
        print(f"Assembly Survey Rotational Offset is {AngleOffset:.5f} degrees")"""
    if FDpoints==4:
        FD1 = points[fd[0]]-points[fd[2]]
        if FD1[1] > 0:
            angle_FD1= np.degrees(np.arctan2(FD1[1],FD1[0])) -90
        else:
            angle_FD1= np.degrees(np.arctan2(FD1[1],FD1[0])) +90
        FD2 = points[fd[1]]-points[fd[3]]
        FD = (points[fd[0]]+points[fd[1]])/2 - (points[fd[2]]+points[fd[3]])/2
        FDCenter = (points[fd[0]]+points[fd[1]]+points[fd[2]]+points[fd[3]])/4
        if FD2[1] > 0:
            angle_FD2= np.degrees(np.arctan2(FD2[1],FD2[0]))-90
        else:
            angle_FD2= np.degrees(np.arctan2(FD2[1],FD2[0]))+90
        if details == 1:
            print(f"FD1-3 X'' axis is at angle {angle_FD1:.5f} degrees")
            print(f"angle of FD1-3 X'' relative to Assembly Tray Pin X' is {angle_FD1 - angle_Pin:.5f} degrees")
            print(f"FD2-4 X'' axis is at angle {angle_FD2:.5f} degrees")
            print(f"angle of FD2-4 X'' relative to Assembly Tray Pin X' is {angle_FD2 - angle_Pin:.5f} degrees")
            print()
            print(f"FDCenter at x:{FDCenter[0]:.3f} mm, y:{FDCenter[1]:.3f} mm")
            print(f"PinCenter at x:{PinCenter[0]:.3f} mm, y:{PinCenter[1]:.3f} mm")
            print()
        """XOffset = FDCenter[0]-PinCenter[0]
        YOffset = FDCenter[1]-PinCenter[1]
        print(f"Assembly Survey X Offset: {XOffset:.3f} mm")
        print(f"Assembly Survey Y Offset: {YOffset:.3f} mm")
        print()
        #print('arctan Method')
        print()"""
        u_Pin = Pin/np.linalg.norm(Pin)
        angle_Pin= np.degrees(np.arctan2(Pin[1],Pin[0]))
        #if details == 1:
            #print(f"Pin X' axis is at angle {angle_Pin:.3f} degrees")
            #print()
        u_FD = FD/np.linalg.norm(FD)
        angle_FD= np.degrees(np.arctan2(FD[1],FD[0]))-90
        if details == 1:
            print(f"Pin X' axis is at angle {angle_Pin:.5f} degrees")
            print()
            print(f"FD1-4 X'' axis is at angle {angle_FD:.5f} degrees")
        #print(f"Assembly Survey Rotational Offset is {angle_FD - angle_Pin:.5f} degrees")
        #print()
        #angle_FD1= np.degrees(np.arctan2(FD1[1],FD1[0]))
        #print(f"FD1-2 X'' axis is at angle {angle_FD1} degrees")
    XOffset = FDCenter[0]-PinCenter[0]
    YOffset = FDCenter[1]-PinCenter[1]
    print(f"Assembly Survey X Offset: {XOffset:.3f} mm")
    print(f"Assembly Survey Y Offset: {YOffset:.3f} mm")
    print()
    #ADDED For Rotation if NEEDED
    if OffCenterPin == "Left":
        NEWY = XOffset*-1;
        NEWX = YOffset; 
    elif OffCenterPin == "Right":
        NEWY = XOffset;
        NEWX = YOffset*1; 
    print(f"Assembly Survey X Offset: {NEWX:.3f} mm (rotated)")
    print(f"Assembly Survey Y Offset: {NEWY:.3f} mm (rotated)")
    print()
    AngleOffset = angle_FD1 - angle_Pin
    print(f"Assembly Survey Rotational Offset is {AngleOffset:.5f} degrees")
    if plot == 1:
        plotFD(FDpoints,FDCenter,Center, Off, points, fd,)
    CenterOffset = np.sqrt(XOffset**2 + YOffset**2)
    return CenterOffset, AngleOffset, XOffset, YOffset



def get_offsets(filenames, Traysheets):
    sheetnames = loadsheet(filenames)
    autoTray = 0
    points = {}
    TrayKeys = ["Tray","T"]
    sensorKeys = ["Sensor", "Corner","P1","FD3","FD6","FDthree","FDsix"]  ### Key words for searching Sensor FD points in the file
    fd=[]

    searchSensorFD(sheetnames[1],sensorKeys,details = 0, Tray = autoTray, Traykeys = TrayKeys, fd=fd,points = points)
    Center = 'P1Center'
    Off = 'P1OffcenterPin'
    keys = [Center, Off]
    traypin=[]

    searchTrayPin(sheetnames[0],keys,details=0,Tray = autoTray, points = points)
    #print(points)
    DiffKeys = True; CXchk1 = False; CYchk1 = False; DictKeys = points.keys();
    for dictkey in points.keys():
        if dictkey == 'CenterX':
            CXchk1 = True;
        if dictkey == 'CenterY':
            CYchk1 = True; 
        if CYchk1 and CXchk1: DiffKeys = False;
    
    ####IMPORTANT  (Left or Right)  -edited by paolo
    pinsetting = "Right";

    ###### this NEEDS to be worked on for more trays and more positions, -Paolo 
    ###### hard coded tray offsets from : "Tray 2 low light more points June 2023"
    if DiffKeys: 
        points.update({
            'P1Center.X': 142.648,
            'P1Center.Y': 298.465,
            'P2Center.X': 91.899,
            'P2Center.Y': 107.959,
            'P1LEFT.X': 67.688,
            'P1LEFT.Y': 298.445,
            'P2LEFT.X': 16.949,
            'P2LEFT.Y': 107.939,
            'P1RIGHT.X': 217.585,
            'P1RIGHT.Y': 298.455,
            'P2RIGHT.X': 166.848,
            'P2RIGHT.Y': 107.969,
        }) 

    #print(points);
    """for sheetname in sheetnames:
        TrayNum = TrayID(sheetname);
        PosNum = PositionID(sheetname);"""
    #print(fd);

    PositionID = 1;
    if PositionID == 1:
        CenterOff, AngleOff, XOffset, YOffset = angle(points, FDpoints=len(fd), OffCenterPin='Left', details=0,plot=1, Center = "P1Center", Off = "P1LEFT", fd = fd)    
    elif PositionID == 2:
        CenterOff, AngleOff, XOffset, YOffset = angle(points, FDpoints=len(fd), OffCenterPin='Right', details=0,plot=1, Center = "P2Center", Off = "P2RIGHT", fd = fd)
    return XOffset, YOffset, AngleOff




import re
import colorama
from colorama import Fore, Style

colorClassify = {'-1': Fore.MAGENTA + 'NO INFO' + Fore.BLACK, 
                       '0': Fore.GREEN + 'GREEN' + Fore.BLACK,
                       '1': Fore.YELLOW + 'YELLOW' + Fore.BLACK, 
                       '2': Fore.RED + 'RED' + Fore.BLACK}
classify = {'-1': 'NO INFO',
                         '0': 'GREEN',
                         '1': 'YELLOW',
                         '2': 'RED'}
degrees = [0.03, 0.06, 90]
centers = [0.050, 0.100, 10.0]

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

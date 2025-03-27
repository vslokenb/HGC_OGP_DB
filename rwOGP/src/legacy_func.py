import logging
import numpy as np

# Global variables
Center = "Center"
Off = "OffCenter"
fd = [0, 1, 2, 3]  # Fiducial point indices

def calculate_sensor_alignment(points, FDpoints=4, OffCenterPin="Left", details=0, plot=0):
    """
    Calculate sensor alignment metrics using fiducial points and pin positions.

    Args:
        points: Dictionary containing coordinate points with keys {Center.X, Center.Y, Off.X, Off.Y}
        FDpoints: Number of fiducial points (2 or 4)
        OffCenterPin: Position of offset pin relative to center ("Left" or "Right")
        details: Flag to enable detailed logging (0 or 1)
        plot: Flag to enable plotting (0 or 1)

    Returns:
        tuple: (CenterOffset, AngleOffset)
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    CenterX = f"{Center}.X"
    CenterY = f"{Center}.Y"
    OffX = f"{Off}.X"
    OffY = f"{Off}.Y"
   
    # Require 2 or 4 fiducial points 
    if FDpoints not in [2, 4]:
        logger.error(f"{FDpoints} Fiducial Points. Invalid Number. Please use either 2 or 4 Fiducial Points")
        return None
    logger.info(f"Using {FDpoints} Fiducial Points")

    if OffCenterPin not in ["Left", "Right"]:
        logger.error("Invalid OffCenter Pin Position. Must be 'Left' or 'Right'")
        return None
    if OffCenterPin == "Left":
        Pin = np.array([points[CenterX], points[CenterY]]) - np.array([points[OffX], points[OffY]])
        logger.info("OffCenter Pin is on the Left relative to the Center Pin")
    else:
        Pin = np.array([points[OffX], points[OffY]]) - np.array([points[CenterX], points[CenterY]])
        logger.info("OffCenter Pin is on the Right relative to the Center Pin")
     
    PinCenter = np.array([points[CenterX], points[CenterY]])
    angle_Pin = np.degrees(np.arctan2(Pin[1], Pin[0]))

    if FDpoints == 2:
        FD1 = points[fd[0]] - points[fd[1]]
        angle_FD1 = np.degrees(np.arctan2(FD1[1], FD1[0])) + (90 if FD1[1] < 0 else -90)
        FDCenter = (points[fd[0]] + points[fd[1]]) / 2
    else:
        FD1 = points[fd[0]] - points[fd[2]]
        FD2 = points[fd[1]] - points[fd[3]]
        angle_FD1 = np.degrees(np.arctan2(FD1[1], FD1[0])) + (90 if FD1[1] < 0 else -90)
        FDCenter = (points[fd[0]] + points[fd[1]] + points[fd[2]] + points[fd[3]]) / 4
    
    XOffset = FDCenter[0] - PinCenter[0]
    YOffset = FDCenter[1] - PinCenter[1]
    AngleOffset = angle_FD1 - angle_Pin
    CenterOffset = np.sqrt(XOffset**2 + YOffset**2)

    logger.info(f"Assembly Survey X Offset: {XOffset:.3f} mm")
    logger.info(f"Assembly Survey Y Offset: {YOffset:.3f} mm")
    logger.info(f"Assembly Survey Rotational Offset is {AngleOffset:.5f} degrees")

    # if plot:
        # plotFD(FDpoints, FDCenter)  # Assuming plotFD is defined elsewhere

    return CenterOffset, AngleOffset
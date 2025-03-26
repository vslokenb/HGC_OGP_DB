import numpy as np
import logging

def calc_basic_angle(fd3to1) -> float:
    """Calculate the basic angle between two points
    
    Parameters
    ----------
    fd3to1 : array-like
        Vector difference between two fiducial points
    *args, **kwargs : additional arguments (unused but accepted for consistency)
    
    Returns
    -------
    float
        Angle in degrees
    """
    return np.degrees(np.arctan2(fd3to1[0], fd3to1[1]) * -1)

def calc_five_angle(fd3to1, is_second=False) -> float:
    """Calculate the angle for the Five component
    
    Parameters
    ----------
    fd3to1 : array-like
        Vector difference between two fiducial points
    is_second : bool, optional. Indicate Position (1/2)"""
    sign = 1 if is_second else -1
    return np.degrees(np.arctan2(sign * fd3to1[1], sign * fd3to1[0]))

def calc_full_angle(fdpoints, comp_type, is_second=False) -> float:
    sign = -1 if is_second else 1
    if comp_type == 'protomodule':
        points_diff = fdpoints[1] - fdpoints[0] # vector from FD1 to FD2
        angle = np.degrees(np.arctan2(
            sign * points_diff[1],
            sign * points_diff[0]))
        if sign == 1:
            logging.debug(f"Using Angle of FD1 -> FD2 for rotational offset: {angle}")
        else:
            logging.debug(f"Using Angle of FD2 -> FD1 for rotational offset: {angle}")
    else:
        points_diff = fdpoints[2] - fdpoints[5] # vector from FD6 to FD3
        angle = np.degrees(np.arctan2(
            sign * points_diff[1],
            sign * points_diff[0]) * -1)
        if sign == 1:
            logging.debug(f"Using Angle of FD6 -> FD3 for rotational offset: {angle}")
    return angle

def calc_HDfull_angle(fdpoints, comp_type, is_second=False) -> float:
    if fdpoints[0][1] >= 200: points_diff = fdpoints[1] - fdpoints[0]; B = 1;  # vector from FD1 to FD2
    else: points_diff = fdpoints[0] - fdpoints[1]; B = -1; # vector from FD2 to FD1
    sign = 1 if is_second else -1
    angle = B*np.degrees(np.arctan2(
        sign * points_diff[0],
        sign * points_diff[1]))
    logging.debug(f"Angle of FD1 -> FD2: {angle}")
    return angle








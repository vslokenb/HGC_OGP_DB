import numpy as np

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
        print(f"Angle of FD1 -> FD2: {angle}")
    else:
        points_diff = fdpoints[2] - fdpoints[5]
        angle = np.degrees(np.arctan2(
            sign * points_diff[1],
            sign * points_diff[0]) * -1)
    return angle

def calc_HDfull_angle(fdpoints, comp_type, is_second=False) -> float:
    sign = -1 if is_second else 1
    points_diff = fdpoints[1] - fdpoints[0] # vector from FD1 to FD2
    angle = np.degrees(np.arctan2(
        sign * points_diff[0],
        sign * points_diff[1]))
    print(f"Angle of FD1 -> FD2: {angle}")
    return angle








from colorama import Fore
import numpy as np
import logging

baseplates_params = {"vmini": 1.2, "vmaxi": 2.2, "new_angle": 0, "db_table_name": 'bp_inspect', 
                     "mother_table": 'baseplate', "prefix": 'bp'}
hexaboards_params = {"vmini": 1.2, "vmaxi": 2.9, "new_angle": 0, "db_table_name": 'hxb_inspect', 
                     "mother_table": 'hexaboard', 'prefix': 'hxb'}
protomodules_params = {"vmini": 1.37, "vmaxi": 1.79, "new_angle": 270, "db_table_name": 'proto_inspect', 
                       "mother_table": 'proto_assembly', 'prefix': 'proto'}
modules_params = {"vmini": 2.75, "vmaxi": 4.0, "new_angle": 270, "db_table_name": 'module_inspect', 
                  "mother_table": 'module_info', 'prefix': 'module'}

# Map channel numbers to physical FD indices (0-based position in this list = FD number - 1).
# CH197 and CH191 are the top-edge sensor holes. Their relative assignment to FD4/FD5
# does NOT affect the angle calculation (which selects the same-column pair by X proximity)
# or the center (which averages all four). Do NOT swap these entries.
fd_maps = [1, 8, 111, 197, 191] # FD1, FD2, FD3, FD4, FD5

COMP_PREFIX = {'baseplate': 'bp', 'hexaboard': 'hxb', 'protomodule': 'proto', 'module': 'module'}

default_params = {"PositionID": 1, "Geometry": "Full", "Density": "LD", "TrayNo": 1}

COMPONENT_PARAMS = {'baseplate': baseplates_params, 'hexaboard': hexaboards_params, 'protomodule': protomodules_params, 'module': modules_params}

plot2d_dim = (-100, 100)

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

pin_mapping = {
    'Full': {'LD': {1: ('p1_center_pin', 'p1O'), 2: ('p2_center_pin', 'p2M')}, # hole pin, slot pin
             'HD': {1: ('p1_center_pin', 'p1O'), 2: ('p2_center_pin', 'p2M')}},
    'Left': {'LD': {1: ('p1C', 'p1I'), 2: ('p2A', 'p2K')},
             'HD': {1: ('p1F', 'p1P'), 2: ('p2H', 'p2N')}},
    'Right': {'LD': {1: ('p1A', 'p1K'), 2: ('p2C', 'p2I')},
              'HD': {1: ('p1H', 'p1N'), 2: ('p2F', 'p2P')}},
    'Top': {'LD': {1: ('p1D', 'p1O'), 2: ('p2B', 'p2M')},
            'HD': {1: ('p1E', 'p1O'), 2: ('p2G', 'p2M')}},
    'Bottom': {'LD': {1: ('p1B', 'p1M'), 2: ('p2D', 'p2O')},
               'HD': {1: ('p1_center_pin', 'p1M'), 2: ('p2_center_pin', 'p2O')}},
    'Five': {'LD': {1: ('p1_center_pin', 'p1I'), 2: ('p2_center_pin', 'p2K')},
             'HD': {1: ('p1_center_pin', 'p1I'), 2: ('p2_center_pin', 'p2K')}}
}

ADJUSTMENTS = {
    'protomodule': {
        'Full':   {'LD': {1: (0, 0),      2: (0, 0)},      'HD': {1: (0, 0),       2: (0, 0)}},
        'Five':   {'LD': {1: (0, 0),      2: (0, 0)},      'HD': {1: (0, 0),       2: (0, 0)}},
        'Top':    {'LD': {1: (9.72, 0),  2: (-9.72, 0)},   'HD': {1: (8.44, 0),   2: (-8.44, 0)}},
        'Bottom': {'LD': {1: (-9.72, 0),   2: (9.72, 0)},  'HD': {1: (-16, 0),     2: (16, 0)}},
        'Right':  {'LD': {1: (0, -9.72),   2: (0, 9.72)},  'HD': {1: (0, 6.52),    2: (0, -6.52)}},
        'Left':   {'LD': {1: (0, 9.72),  2: (0, -9.72)},   'HD': {1: (0, -6.52),   2: (0, 6.52)}}
    },
    'module': {
        'Full':   {'LD': {1: (0, 0),      2: (0, 0)},      'HD': {1: (0, 0),       2: (0, 0)}},
        'Five':   {'LD': {1: (0, 0),      2: (0, 0)},      'HD': {1: (0, 0),       2: (0, 0)}},
        'Top':    {'LD': {1: (8, 0),     2: (-8, 0)},      'HD': {1: (4, 0),      2: (-4, 0)}},
        'Bottom': {'LD': {1: (-9, 0),      2: (9, 0)},     'HD': {1: (-15, 0),     2: (15, 0)}},
        'Right':  {'LD': {1: (0, 18),     2: (0, -18)},    'HD': {1: (0, 5),       2: (0, -5)}},
        'Left':   {'LD': {1: (0, 8),    2: (0, -8)},     'HD': {1: (0, -5),      2: (0, 5)}}
    }
}


# Define the angle calculation of FD points.
# All lambdas accept an optional 4th positional argument `angle_pin` (float, degrees).
# Lambdas that do not use it capture it via *_ to stay forward-compatible.
ANGLE_CALC_CONFIG = {
    'Bottom':  {
        1: lambda fd3to1, *_: calc_basic_angle(-fd3to1),
        2: lambda fd3to1, *_: calc_basic_angle(fd3to1),
    },
    'Top': {
        'LD': {
            1: lambda fd3to1, *_: calc_basic_angle(-fd3to1),
            2: lambda fd3to1, *_: calc_basic_angle(fd3to1),
        },
        'HD': {
            1: lambda fd3to1, *_: calc_basic_angle(-fd3to1),
            2: lambda fd3to1, *_: calc_basic_angle(fd3to1),
        }
    },
    'Five': {
        1: lambda fd3to1, fdpoints, comp_type, *_: calc_five_angle(fdpoints, fd3to1, comp_type),
        2: lambda fd3to1, fdpoints, comp_type, *_: calc_five_angle(fdpoints, fd3to1, comp_type, True),
    },
    'Left': {
        'LD': {
            1: lambda fd3to1, *_: calc_semi_angle(fd3to1),
            2: lambda fd3to1, *_: calc_semi_angle(fd3to1, True),
        }
    },
    'Right': {
        'LD': {
            1: lambda fd3to1, *_: calc_semi_angle(fd3to1),
            2: lambda fd3to1, *_: calc_semi_angle(-fd3to1),
        }
    },
    'Full': {
        'HD': {
            1: lambda fd3to1, fdpoints, *_: calc_HDfull_angle(fdpoints, None),
            2: lambda fd3to1, fdpoints, *_: calc_HDfull_angle(fdpoints, None, True),
        },
        'LD': {
            # angle_pin is passed through so calc_full_angle can disambiguate
            # correctly for both LR (horizontal pin) and TB (vertical pin) trays.
            1: lambda fd3to1, fdpoints, comp_type, angle_pin=0: calc_full_angle(fdpoints, comp_type, angle_pin=angle_pin),
            2: lambda fd3to1, fdpoints, comp_type, angle_pin=0: calc_full_angle(fdpoints, comp_type, True, angle_pin=angle_pin),
        }
    }
}

def calc_ref_angle(pinx, pinY, sign):
    if sign == 1:
        logging.debug("Using Angle of Hole(Center) --> Slot(OffCenter) for rotational reference")
    else:
        logging.debug("Using Angle of Slot(OffCenter) --> Hole(Center) for rotational reference")
    return np.degrees(np.arctan2(sign * pinY, sign * pinx))


# Define the hole-to-slot angle calculation functions
angle_lookup = {
    'Full': {
        'HD': {
            1: lambda pinX, pinY: calc_ref_angle(pinX, pinY, -1),
            2: lambda pinX, pinY: calc_ref_angle(pinX, pinY, 1)
        },
        'LD': {
            1: lambda pinX, pinY: calc_ref_angle(pinX, pinY, -1),
            2: lambda pinX, pinY: calc_ref_angle(pinX, pinY, 1)
        }
    },
    'Bottom': {
        'LD': {
            1: lambda pinX, pinY: calc_ref_angle(pinX, pinY, 1), 
            2: lambda pinX, pinY: calc_ref_angle(pinX, pinY, -1)
        }
    },
    'Five': {
        'default': {
            1: lambda pinX, pinY: np.degrees(np.arctan2(-pinX, -pinY)),
            2: lambda pinX, pinY: np.degrees(np.arctan2(pinX, pinY))
        }
    },
    'Left': {
        'LD': {
            1: lambda pinX, pinY: np.degrees(np.arctan2(-pinX, -pinY)),
            2: lambda pinX, pinY: np.degrees(np.arctan2(pinX, pinY))
        },
        'HD': {
            1: lambda pinX, pinY: np.degrees(np.arctan2(pinX, pinY)),
            2: lambda pinX, pinY: np.degrees(np.arctan2(-pinX, -pinY))
        }
    },
    'Right': {
        'LD': {
            1: lambda pinX, pinY: np.degrees(np.arctan2(pinX, pinY)),
            2: lambda pinX, pinY: np.degrees(np.arctan2(-pinX, -pinY))
        },
        'HD': {
            1: lambda pinX, pinY: np.degrees(np.arctan2(pinX, pinY)),
            2: lambda pinX, pinY: np.degrees(np.arctan2(-pinX, -pinY))
        }
    },
    'Top': {
        'default': {
            1: lambda pinX, pinY: np.degrees(np.arctan2(-pinY, -pinX)),
            2: lambda pinX, pinY: np.degrees(np.arctan2(pinY, pinX))
        }
    }
}

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

def calc_semi_angle(fd3to1, is_second=False) -> float:
    """Calculate the angle for the LEFT AND RIGHT component
    
    Parameters
    ----------
    fd3to1 : array-like
        Vector difference between two fiducial points
    is_second : bool, optional. Indicate Position (1/2)"""
    sign = 1 if is_second else -1
    return np.degrees(np.arctan2(sign * fd3to1[1], sign * fd3to1[0]))


def calc_five_angle(fdpoints, fd3to1, comp_type, is_second=False) -> float:
    """Calculate the angle deviation for LD FIVE geometry."""
    if comp_type == 'protomodule':
        if fdpoints[0][1] >= 200: points_diff = fdpoints[1] - fdpoints[0]; B = 1;  # vector from FD1 to FD2
        else: points_diff = fdpoints[0] - fdpoints[1]; B = -1; # vector from FD2 to FD1
        angle = B*np.degrees(np.arctan2(
            points_diff[0],
            points_diff[1]))
        logging.debug(f"Angle of FD1 -> FD2: {angle}")
        return angle
    elif comp_type == 'module':
        sign = 1 if is_second else -1
        return np.degrees(np.arctan2(sign * fd3to1[1], sign * fd3to1[0]))


def calc_full_angle(fdpoints, comp_type, is_second=False, angle_pin=0) -> float:
    """Calculate the angle deviation for protomodules/modules with Full geometry.

    Parameters
    ----------
    fdpoints : np.ndarray
        Array of fiducial points, shape (8, 2).
        Module:      FD3 at index 2, FD6 at index 5.
        Protomodule: FD1 at index 0, FD5 at index 4.
    comp_type : str
        'protomodule' or 'module'
    is_second : bool
        True for Position 2 (sign = -1), False for Position 1 (sign = +1).
    angle_pin : float
        The pin reference angle in degrees (angle_Pin from angle_lookup).
        Used to resolve directional ambiguity for both LR (pin ~0°) and
        TB (pin ~90°) tray orientations. Defaults to 0 for backward compat.

    Returns
    -------
    float
        Angle in degrees; AngleOffset = returned value - angle_pin.

    Notes
    -----
    Both module and protomodule use the same 4-candidate disambiguation:
      {FD_a - FD_b,  FD_b - FD_a} × {no correction, -90° correction}
    The candidate whose normalised value is closest to angle_pin wins.

    For modules the FD3-FD6 vector is always perpendicular to the pin axis
    (both LR and TB), so a -90° correction is always needed; the flip
    handles the ±180° ambiguity.

    For protomodules the FD5-FD1 vector is parallel to the pin on TB trays
    (no correction needed) and perpendicular on LR trays (-90° needed).
    The 4-candidate search selects correctly in both cases without any
    hard-coded tray-orientation assumption.
    """
    sign = -1 if is_second else 1

    def _normalize(a):
        """Fold angle `a` into the ±180° window centred on angle_pin."""
        delta = (a - angle_pin + 180) % 360 - 180
        return angle_pin + delta

    def _best_candidate(diff):
        """Return the angle candidate (from diff and its flip, ±90°) that
        produces the smallest |AngleOffset| relative to angle_pin."""
        d1, d2 = diff, -diff
        candidates = [
            np.degrees(np.arctan2(sign * d1[1], sign * d1[0])),         # forward, no correction
            np.degrees(np.arctan2(sign * d1[1], sign * d1[0])) - 90,    # forward, -90°
            np.degrees(np.arctan2(sign * d2[1], sign * d2[0])),         # flip,    no correction
            np.degrees(np.arctan2(sign * d2[1], sign * d2[0])) - 90,    # flip,    -90°
        ]
        normed = [_normalize(c) for c in candidates]
        return min(normed, key=lambda a: abs(a - angle_pin))

    if comp_type == 'protomodule':
        # Select the FD (FD4 or FD5) that lies on the same column as FD1
        # (smallest X-distance). This gives a near-vertical vector regardless
        # of tray orientation (LR or TB) and position (1 or 2).
        # Using the diagonal pair (always FD5-FD1) fails for configurations
        # where FD5 is diagonally opposite FD1 rather than directly above/below it.
        fd1 = fdpoints[0]
        fd4 = fdpoints[3]
        fd5 = fdpoints[4]
        if abs(fd4[0] - fd1[0]) <= abs(fd5[0] - fd1[0]):
            diff = fd4 - fd1
            logging.debug(f"Protomodule Full: using FD4-FD1 (same column, |dx|={abs(fd4[0]-fd1[0]):.2f}mm)")
        else:
            diff = fd5 - fd1
            logging.debug(f"Protomodule Full: using FD5-FD1 (same column, |dx|={abs(fd5[0]-fd1[0]):.2f}mm)")
        angle = _best_candidate(diff)
        logging.debug(f"Protomodule Full angle_FD={angle:.4f}° "
                      f"(angle_pin={angle_pin:.4f}°, diff={diff})")

    elif comp_type == 'module':
        diff = fdpoints[2] - fdpoints[5]   # FD3 - FD6
        angle = _best_candidate(diff)
        logging.debug(f"Module Full angle_FD={angle:.4f}° "
                      f"(angle_pin={angle_pin:.4f}°, FD3-FD6={diff})")

    else:
        logging.error(f"Component type {comp_type} not recognized for angle calculation.")
        raise ValueError(f"Unsupported comp_type '{comp_type}' in calc_full_angle.")

    return angle

def calc_HDfull_angle(fdpoints, comp_type, is_second=False) -> float:
    """Calculate the angle deviation for HD Full geometry."""
    if fdpoints[0][1] >= 200: points_diff = fdpoints[1] - fdpoints[0]; B = 1;  # vector from FD1 to FD2
    else: points_diff = fdpoints[0] - fdpoints[1]; B = -1; # vector from FD2 to FD1
    angle = B*np.degrees(np.arctan2(
        points_diff[0],
        points_diff[1]))
    logging.debug(f"Angle of FD1 -> FD2: {angle}")
    return angle

from colorama import Fore
import numpy as np
from src.helper import calc_basic_angle, calc_five_angle, calc_full_angle

baseplates_params = {"vmini": 1.2, "vmaxi": 2.2, "new_angle": 0, "db_table_name": 'bp_inspect', 
                     "mother_table": 'baseplate', "prefix": 'bp'}
hexaboards_params = {"vmini": 1.2, "vmaxi": 2.9, "new_angle": 0, "db_table_name": 'hxb_inspect', 
                     "mother_table": 'hexaboard', 'prefix': 'hxb'}
protomodules_params = {"vmini": 1.37, "vmaxi": 1.79, "new_angle": 270, "db_table_name": 'proto_inspect', 
                       "mother_table": 'proto_assembly', 'prefix': 'proto'}
modules_params = {"vmini": 2.75, "vmaxi": 4.0, "new_angle": 270, "db_table_name": 'module_inspect', 
                  "mother_table": 'module_info', 'prefix': 'module'}

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
    'Full': {'LD': {1: ('p1_center_pin', 'p1O'), 2: ('p2_center_pin', 'p2M')},
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
        'Top':    {'LD': {1: (-9.72, 0),  2: (9.72, 0)},   'HD': {1: (-8.44, 0),   2: (8.44, 0)}},
        'Bottom': {'LD': {1: (9.72, 0),   2: (-9.72, 0)},  'HD': {1: (-16, 0),     2: (16, 0)}},
        'Right':  {'LD': {1: (0, 9.72),   2: (0, -9.72)},  'HD': {1: (0, 6.52),    2: (0, -6.52)}},
        'Left':   {'LD': {1: (0, -9.72),  2: (0, 9.72)},   'HD': {1: (0, -6.52),   2: (0, 6.52)}}
    },
    'module': {
        'Full':   {'LD': {1: (0, 0),      2: (0, 0)},      'HD': {1: (0, 0),       2: (0, 0)}},
        'Five':   {'LD': {1: (0, 0),      2: (0, 0)},      'HD': {1: (0, 0),       2: (0, 0)}},
        'Top':    {'LD': {1: (-8, 0),     2: (8, 0)},      'HD': {1: (-4, 0),      2: (4, 0)}},
        'Bottom': {'LD': {1: (9, 0),      2: (-9, 0)},     'HD': {1: (-15, 0),     2: (15, 0)}},
        'Right':  {'LD': {1: (0, 18),     2: (0, -18)},    'HD': {1: (0, 5),       2: (0, -5)}},
        'Left':   {'LD': {1: (0, -18),    2: (0, 18)},     'HD': {1: (0, -5),      2: (0, 5)}}
    }
}

ANGLE_CALC_CONFIG = {
    'Bottom': lambda fd3to1, *_: calc_basic_angle(fd3to1),
    'Top': {
        'LD': {
            1: lambda fd3to1, *_: calc_basic_angle(fd3to1),
            2: lambda fd3to1, *_: calc_basic_angle(fd3to1),
        },
        'HD': {
            1: lambda fd3to1, *_: calc_basic_angle(-fd3to1),
            2: lambda fd3to1, *_: calc_basic_angle(fd3to1),
        }
    },
    'Five': {
        1: lambda fd3to1, *_: calc_five_angle(fd3to1),
        2: lambda fd3to1, *_: calc_five_angle(fd3to1, True),
    },
    'Left': {
        'LD': {
            1: lambda fd3to1, *_: calc_five_angle(fd3to1),
            2: lambda fd3to1, *_: calc_five_angle(fd3to1, True),
        }
    },
    'Right': {
        'LD': {
            1: lambda fd3to1, *_: calc_five_angle(fd3to1),
            2: lambda fd3to1, *_: calc_five_angle(fd3to1),
        }
    },
    'Full': {
        'HD': {
            1: lambda fd3to1, fdpoints, *_: calc_full_angle(fdpoints, None),
            2: lambda fd3to1, fdpoints, *_: calc_full_angle(fdpoints, None, True),
        },
        'LD': {
            1: lambda fd3to1, fdpoints, comp_type: calc_full_angle(fdpoints, comp_type),
            2: lambda fd3to1, fdpoints, comp_type: calc_full_angle(fdpoints, comp_type, True),
        }
    }
}

angle_lookup = {
    'Full': {
        'HD': {
            1: lambda pinX, pinY: np.degrees(np.arctan2(-pinY, -pinX)),
            2: lambda pinX, pinY: np.degrees(np.arctan2(pinY, pinX))
        },
        'LD': {
            1: lambda pinX, pinY: np.degrees(np.arctan2(-pinY, -pinX)),
            2: lambda pinX, pinY: np.degrees(np.arctan2(pinY, pinX))
        }
    },
    'Bottom': {
        'LD': {
            1: lambda pinX, pinY: np.degrees(np.arctan2(pinY, pinX)),
            2: lambda pinX, pinY: np.degrees(np.arctan2(-pinY, -pinX))
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

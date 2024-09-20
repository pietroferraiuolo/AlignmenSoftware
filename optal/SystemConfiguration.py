"""
Author(s)
---------
    - Pietro Ferraiuolo : written in 2024

Alignment Software Configuration File
=====================================
Description
-----------
This python file is a configuration file to be passed to the main alignment code.
This file contains all the informations about the kinematic motors that move the
system and how to acces them through higher level calls.

Variables Explanation
---------------------
cmdDof                : list of int | int
    This variable represents the total degrees of freedom each device has, so
    it will be the length of the accepted command vector by the devices.
    Example:
        Normally a device could move up to 6 degreed of freedom, 3 linear and 3
        angular, so cmdDof would be 6.
        If a device accepts a vector of different size for its actuation, then 
        this variable should be a list of integers, each would indicate the dimention
        of the vector corresponding to the respective device.

dof                   : list of lists
    This variable, initialized as an empty list, will contain the degrees of
    freedom each device can actually move.
    Example:
        If a device can move only 3 DoF, say piston, tip and tilt, then, if the
        cmdDof if 6 (i.e the device accept a vector of 6 elements), the 'dof' list
        should be the index at which these degrees of freedom are located in the accepted
        command vector. In this case, the list could be [2, 3, 4] (as in the case for the
        M4's OTT).

slices                : list of slices
    This variable is a list of slices that will be used to extract the right dof
    positions from the command matrix full vector. 
    Example:
        If the command matrix is a column vector (the full command) of 8 elements, in which
        the first 3 elements are for the 'device_1' dof, the second 2 for 'device_2' dof and the last
        3 for 'device_3' dof, then the slices list should be [slice(0,3), slice(3,5), slice(5,8)].

zernike_to_use        : list of int

push_pull_template    : list of int

commandMatrix         : str

devices_move_calls    : list of str

devices_read_calls    : list of str

names                 : list of str

ccd_acquisition       : list of str

base_read_data_path   : str

base_write_data_path  : str

calibrated_parabola   : str


Important Notes
---------------

Subsequent Example: M4's OTT
----------------------------

"""

cmdDof = 6                # Total DoF per device
        # or []
        # cmdDof.append(6)
        # ...
dof = []                  # Available Degrees of Freedom (DoF)
dof.append([2, 3, 4])     # Parabola DoF
dof.append([3, 4])        # Reference Mirror DoF
dof.append([3, 4])        # M4 Exapode DoF
slices = []               # Full cmd vector devices indices
slices.append(slice(0,3)) # Parabola
slices.append(slice(3,5)) # Reference Mirror
slices.append(slice(5,7)) # M4 Exapode

zernike_to_use = [1,2,3,6,7]
push_pull_template = [+1,-2,+1]

commandMatrix = '/home/pietrof/git/M4/scripts/ottalign/cmdMat.fits'

devices_move_calls = [
    'parabola.setPosition',
    'referenceMirror.setPosition',
    'm4Exapode.setPosition'
    ]

devices_read_calls = [
    'parabola.getPosition',
    'referenceMirror.getPosition',
    'm4Exapode.getPosition'
    ]

names = [
    'Parabola',
    'Reference Mirror',
    'M4 Exapode'
    ]

ccd_acquisition = [
    'acquire_phasemap'
    ]


base_read_data_path = '/home/pietrof/git/M4/m4/data/M4Data/OPTData/AlignmentCalibration'
base_write_data_path= '/home/pietrof/git/M4/m4/data/M4Data/OPTData/AlignmentCalibration'

calibrated_parabola = ''

# Alignment Software
**Not definitive! Draft documentation**

## Author(s)
- Pietro Ferraiuolo : written in 2024

## Description
This repository contains the `Alignment` class and related functions for performing alignment procedures, including calibration and correction. It also includes a configuration file for M4's alignment procedure, detailing the kinematic motors and their control through a higher-level library.

## Modules

### `alignment.py`
This module provides the `Alignment` class and related functions.

#### Class: `Alignment`
- **Description**: Class for the alignment procedure: calibration and correction.
- **Initialization Parameters**:
    - `mechanical_devices`: The mechanical devices used for alignment.
    - `acquisition_devices`: The acquisition devices used for alignment.

#### Methods:
- `correct_alignment(modes2correct, zern2correct, n_frames=15)`: Corrects the alignment based on the current settings.
- `calibrate_alignment(cmdAmp, template=None, n_repetitions=1)`: Calibrates the alignment using the provided command amplitude and template.
- `read_positions()`: Reads the positions of the devices.
- `reload_parabola_tn(filepath)`: Reloads the parabola from a given file path.
- `_images_production(template, n_repetitions)`: Produces images based on the template and number of repetitions.
- `_zern_routine(imglist)`: Processes images to extract Zernike coefficients.
- `_create_rec_mat(intMat)`: Creates a reconstruction matrix from the interaction matrix.
- `_apply_command(fullCmd)`: Applies the full command to the devices.
- `_extract_cmds_to_apply(fullCmd)`: Extracts commands to apply from the full command.
- `_img_acquisition(k, template)`: Acquires images based on the template.
- `_push_pull_redux(imglist, template)`: Reduces push-pull images based on the template.

#### Helper Functions:
- `_read_fits_data(fits_file_path)`: Reads data from a FITS file.
- `_save_fits_data(filename, data, header=None, overwrite=False)`: Saves data to a FITS file.

### `systemconfiguration.py`
This configuration file contains all the information about the kinematic motors that move the system and how to access them through the higher-level library.

#### Configuration Details:
- **Mechanical Motors - Available Degrees of Freedom**:
    - `dof`: List containing the arrays of available degrees of freedom for each device.
    - `cmdDof`: Total degrees of freedom the device accepts as a command.
    - `slices`: List of slices relative to the corresponding device in the full command vector.

- **Functions to Actuate the Motors**:
    - `devices_move_calls`: List of functions to command each device.
    - `devices_read_calls`: List of functions to read the position of each device.

- **Device Names**:
    - `names`: List of device names for print fanciness.

- **Image Acquisition Function**:
    - `ccd_acquisition`: Function for image acquisition through the system CCD/interferometer.

- **Paths**:
    - `base_read_data_path`: Base path for reading data.
    - `base_write_data_path`: Base path for writing data.
    - `calibrated_parabola`: Path to the calibrated parabola file.

## How to Use
Check the `opt_alignment.py` library to see how the configuration file is used.

## License
This project is licensed under the MIT License.

## Acknowledgments
Special thanks to the contributors and the open-source community.

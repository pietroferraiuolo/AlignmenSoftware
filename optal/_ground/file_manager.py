import os
import numpy as np
from astropy.io import fits
import datetime as dt
from optal import SystemConfiguration

_save_path = SystemConfiguration.base_write_data_path

def read_fits_data(fits_file_path, masked_data:bool=False):
    """
    Reads data from a FITS file.

    Parameters
    ----------
    fits_file_path : str
        The file path to the FITS file.

    Returns
    -------
    object : ndarray or MaskedArray
        The loaded data object.
    """
    with fits.open(fits_file_path) as hduList:
        obj = hduList[0].data
        if len(hduList)==2:
            mask = hduList[1].data.astype(bool)
            obj = np.ma.masked_array(obj, mask=mask)
        elif len(hduList)>2:
            print(f"{NotImplemented}: The FITS file {fits_file_path.split('/')[-1]} contains more than 2 HDUs. Skipping")
    return obj

def save_fits_data(fits_name, data, header=None, overwrite:bool=False):
    """
    Saves data to a FITS file.

    Parameters
    ----------
    filename : str
        The name of the file to be saved.
    data : ndarray or MaskedArray
        The data to save.
    header : str, optional
        The header information to save with the data. The default is None, which means 
        an appropriate header for the data will be created (see astropy documentation
        for more info).
    overwrite : bool, optional
        Whether to overwrite the file if it already exists. The default is False.
    """
    filename = os.path.join(_save_path, new_tn(), fits_name)
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    if os.path.exists(filename) and not overwrite:
        raise FileExistsError(f"The file {filename} already exists. Set overwrite=True to overwrite it.")
    if hasattr(data, 'mask'):
        fits.writeto(filename, data.data, header, overwrite=overwrite)
        fits.append(filename, data.mask.astype(np.uint8), header, overwrite=overwrite)
    else:
        fits.writeto(filename, data, header, overwrite=overwrite)

def new_tn():
    """
    Generates a new tracking number in the format YYYYMMDD_hhmmss.

    Returns
    -------
    str
        The new time-stamped filename.
    """
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")
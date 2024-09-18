import numpy as np
from astropy.io import fits

def _read_fits_data(fits_file_path):
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
        if hasattr(obj, 'mask'):
            obj = np.ma.masked_array(obj, mask=obj.mask)
    return obj

def _save_fits_data(filename, data, header=None, overwrite:bool=False):
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
    if hasattr(data, 'mask'):
        fits.writeto(filename, data.data, header, overwrite=overwrite)
        fits.append(filename, data.mask.astype(np.uint8), header, overwrite=overwrite)
    else:
        fits.writeto(filename, data, header, overwrite=overwrite)

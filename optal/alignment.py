"""
Author(s):
    - Pietro Ferraiuolo : written in 2024

Description
-----------
This module provides the `Alignment` class and related functions for performing
alignment procedures, including calibration and correction. 

How to Use it
-------------
"""
import logging
import numpy as np
import optal.SystemConfiguration as sc
from ._ground import zernike as zern, file_manager as io

class Alignment():
    """
    Class for the alignment procedure: calibration and correction.
    """
    def __init__(self, mechanical_devices, acquisition_devices):
        """
        Initializes the Alignment class with mechanical and acquisition devices.

        Parameters
        ----------
        mechanical_devices : object or list
            The mechanical devices used for alignment. Can be either
            a single object which calls more devices or a list of 
            single devices.
        acquisition_devices : object
            The acquisition devices used for alignment.
        """
        self.mdev       = mechanical_devices
        self.ccd        = acquisition_devices
        self.cmdMat     = io.read_fits_data(sc.commandMatrix)
        self.intMat     = None
        self._cmdAmp    = None
        self._auxMask   = io.read_fits_data(sc.calibrated_parabola) if not sc.calibrated_parabola=='' else None
        self._moveFnc   = self.__get_callables(self.mdev, sc.devices_move_calls)
        self._readFnc   = self.__get_callables(self.mdev, sc.devices_read_calls)
        self._acquire   = self.__get_callables(self.ccd,  sc.ccd_acquisition)
        self._devName   = self.__get_dev_names(sc.names, ndev=len(self.mdev))
        self._dof       = [np.array(dof) if not isinstance(dof, np.ndarray) else dof for dof in sc.dof]
        self._dofTot    = sc.cmdDof if isinstance(sc.cmdDof, list) else [sc.cmdDof]*len(self.mdev)
        self._idx       = sc.slices
        self._zvec2fit  = np.arange(1,11)
        self._zvec2use  = sc.zernike_to_use
        self._template  = sc.push_pull_template
        self._readPath  = sc.base_read_data_path
        self._writePath = sc.base_write_data_path
        logging.basicConfig(filename=(self._writePath+'/alignment.log'),
                                      level=logging.DEBUG,
                                      format='%(asctime)s - %(levelname)s - %(message)s')

    def correct_alignment(self, modes2correct, zern2correct, apply:bool=False, n_frames:int=15):
        """
        Corrects the alignment of the system based on Zernike coefficients.

        Parameters
        ----------
        modes2correct : array-like
            Indices of the modes to correct.
        zern2correct : array-like
            Indices of the Zernike coefficients to correct.
        apply : bool, optional
            If True, the correction command will be applied to the system. 
            If False (default), the correction command will be returned.
        n_frames : int, optional
            Number of frames acquired and averaged the alignment correction. Default is 15.

        Returns
        -------
        numpy.ndarray or str
            If `apply` is False, returns the correction command as a numpy array.
            If `apply` is True, applies the correction command and returns a string 
            indicating that the alignment has been corrected along with the current 
            positions.

        Notes
        -----
        This method acquires an image, calculates the Zernike coefficients, reads the 
        interaction matrix from a FITS file, reduces the interaction matrix and command 
        matrix based on the specified modes and Zernike coefficients, creates a 
        reconstruction matrix, calculates the reduced command, and either applies the 
        correction command or returns it.
        """
        image = self._acquire[0](n_frames)
        zernike_coeff = self._zern_routine(image)
        intMat = io.read_fits_data(self._readPath+'/intMat.fits')
        reduced_intMat = intMat[np.ix_(modes2correct,zern2correct)]
        reduced_cmdMat = self.cmdMat[:,modes2correct]
        recMat = self._create_rec_mat(reduced_intMat)
        reduced_cmd = np.dot(recMat, zernike_coeff[zern2correct])
        f_cmd = np.dot(reduced_cmdMat, reduced_cmd)
        print(f"Resulting Command: {f_cmd}")
        if apply:
            print("Applying correction command...")
            self._apply_command(f_cmd)
            return "Alignment Corrected\n"+self.read_positions()
        else:
            return f_cmd

    def calibrate_alignment(self, cmdAmp, template:list=None, n_repetitions:int=1, save:bool=False):
        """
        Calibrate the alignment of the system using the provided command amplitude and template.

        Parameters
        ----------
        cmdAmp : float
            The command amplitude used for calibration.
        template : list, optional
            A list representing the template for calibration. If not provided, the default template will be used.
        n_repetitions : int, optional
            The number of repetitions for the calibration process. Default is 1.
        save : bool, optional
            If True, the resulting internal matrix will be saved to a FITS file. Default is False.

        Returns
        -------
        str
            A message indicating that the system is ready for alignment.

        Notes
        -----
        This method performs the following steps:
        1. Sets the command amplitude.
        2. Uses the provided template or the default template if none is provided.
        3. Produces a list of images based on the template and number of repetitions.
        4. Executes a Zernike routine on the image list to generate an internal matrix.
        5. Optionally saves the internal matrix to a FITS file.
        """
        self._cmdAmp = cmdAmp
        template = template if template is not None else self._template
        imglist = self._images_production(template, n_repetitions)
        intMat = self._zern_routine(imglist)
        self.intMat = intMat
        if save:
            io.save_fits_data('intMat.fits', self.intMat, overwrite=True)
        return "Ready for Alignment..."
    
    def read_positions(self):
        """
        Reads the current positions of the devices.

        Returns
        -------
        pos : list
            The list of current positions of the devices.
        """
        logMsg = ''
        pos = []
        logMsg += "Current Positions\n"
        for fnc,dev_name in zip(self._readFnc, self._devName):
            temp = fnc()
            pos.append(_Command(temp))
            logMsg += f"{dev_name}"+' '*(16-len(dev_name))+f" : {temp}\n"
        logMsg += '-'*30
        logging.info(logMsg)
        print(logMsg) #!!! debug only
        return pos

    def reload_calibrated_parabola(self, filepath):
        """
        Reloads the parabola from the given file path.

        Parameters
        ----------
        filepath : str
            The file path to the parabola file.

        Returns
        -------
        str
            A message indicating the successful loading of the file.
        """
        par = io.read_fits_data(filepath)
        self.auxMask = par.mask #!!! to check
        return f"Correctly loaded '{filepath}'"

    def _images_production(self, template, n_repetitions):
        """
        Produces images based on the provided template and number of repetitions.

        Parameters
        ----------
        template : list
            The template used for image production.
        n_repetitions : int
            The number of repetitions for image production.

        Returns
        -------
        n_results : list
            The list of produced images.
        """
        results = []
        n_results = []
        for i in range(n_repetitions):
            logMsg = ''
            logMsg += f"Repetition n.{i}\n"
            logging.info(logMsg)
            print(logMsg) ## debug only
            for k in range(self.cmdMat.shape[1]):
                logMsg2= ''
                logMsg2 += f"Matrix Column {k+1} : {self.cmdMat.T[k]}"
                print(f"Matrix Column {k+1} : {self.cmdMat.T[k]}\n") ## debug only
                logging.info(logMsg2)
                imglist = self._img_acquisition(k, template)
                image = self._push_pull_redux(imglist, template)
                results.append(image)
            if n_repetitions!=1:
                n_results.append(results)
            else:
                n_results = results
        return n_results

    def _zern_routine(self, imglist):
        """
        Creates the interaction matrix from the provided image list.

        Parameters
        ----------
        imglist : list
            The list of images used to create the interaction matrix.

        Returns
        -------
        intMat : ndarray
            The interaction matrix created from the images.
        """
        coefflist = []
        if not isinstance(imglist, list):
            imglist = [imglist]
        for img in imglist:
            if self._auxMask is None:
                coeff, _ = zern.zernikeFit(img, self._zvec2fit)
            else:
                coeff, _ = zern.zernikeFitAuxmask(img, self._auxMask, self._zvec2fit)
            coefflist.append(coeff[self._zvec2use])
        if len(coefflist) == 1:
            coefflist = np.array(coefflist[0])
        return np.array(coefflist)  #intmat

    def _create_rec_mat(self, intMat):
        """
        Creates the reconstruction matrix off the inversion of the interaction
        matrix obtained in the alignment calibration procedure.

        Returns
        -------
        recMat : ndarray
            Reconstruction matrix.
        """
        recMat = np.linalg.pinv(intMat)
        self.recMat = recMat
        return recMat

    def _apply_command(self, fullCmd):
        """
        Applies the full command to the devices.

        Parameters
        ----------
        fullCmd : list or ndarray
            Full command of the interaction matrix which commands all device's 
            available motors.

        Returns
        -------
        None
        """
        device_commands = self._extract_cmds_to_apply(fullCmd)
        logMsg = '' #!!!
        for cmd,fnc,dev in zip(device_commands,self._moveFnc,self._devName):
            if cmd.to_ignore:
                logMsg += f'Skipping null command for {dev}\n' # debug
            else:
                try:
                    logMsg += f"Commanding {cmd} to {dev}\n"# debug
                    fnc(cmd.vect)
                except Exception as e:
                    logging.warning(f"Someting went wrong with {dev}: {e}")
        logMsg += '-'*30 # debug
        logging.info(logMsg)
        print(logMsg) #!!! debug only


    def _extract_cmds_to_apply(self, fullCmd):
        """
        Extracts the commands to be applied from the full command.

        Parameters
        ----------
        fullCmd : list or ndarray
            The full command from which individual device commands are extracted.

        Returns
        -------
        device_commands : list
            The list of commands to be applied to each device.
        """
        commands = []
        for d,dof in enumerate(self._dof):
            dev_cmd = np.zeros(self._dofTot[d])
            dev_idx = fullCmd[self._idx[d]]
            for i,idx in enumerate(dev_idx):
                dev_cmd[dof[i]] = idx
            commands.append(_Command(dev_cmd))
        positions= self.read_positions()
        device_commands = []
        for pos,cmd in zip(positions, commands):
            res_cmd = pos+cmd
            device_commands.append(res_cmd)
        return device_commands

    def _img_acquisition(self, k, template):
        """
        Acquires images based on the given template.

        Parameters
        ----------
        k : int
            The index of the command matrix column.
        template : list
            The template used for image acquisition.

        Returns
        -------
        imglist : list
            The list of acquired images.
        """
        imglist = [self._acquire[0](15)]
        for t in template:
            logMsg = ''
            logMsg += f"t = {t}"
            cmd = self.cmdMat.T[k] * self._cmdAmp * t
            logMsg += f" - Full Command : {cmd}"
            logging.info(logMsg)
            print(logMsg) #!!! debug only
            self._apply_command(cmd)
            imglist.append(self._acquire[0](15))
        return imglist

    def _push_pull_redux(self, imglist, template):
        """
        Reduces the push-pull images based on the given template.

        Parameters
        ----------
        imglist : list
            The list of images to be reduced.
        template : list
            The template used for image reduction.

        Returns
        -------
        image : np.ndarray
            The reduced image.
        """
        template.insert(0,-1)
        image = np.zeros((imglist[0].shape[0], imglist[0].shape[1]))
        for x in range(1, len(imglist)):
            opd2add = imglist[x] * template[x] + imglist[x-1] * template[x-1]
            mask2add = np.ma.mask_or(imglist[x].mask, imglist[x-1].mask)
            if x==1:
                master_mask = mask2add
            else:
                master_mask = np.ma.mask_or(master_mask, mask2add)
            image += opd2add
        image = np.ma.masked_array(image, mask=master_mask) / self._cmdAmp
        template.pop(0)
        return image

    @staticmethod
    def __get_callables(devices, callables):
        """
        Returns a list of callables for the instanced object, taken from the 
        configuration.py file.

        Parameters
        ----------
        devices : object
            The device object for which callables are retrieved.
        callables : list
            The list of callable names to be retrieved.

        Returns
        -------
        functions : list
            List of callables, which interacts with the input object of the class.
        """
        if not isinstance(devices, list):
            devices = [devices]
        functions = []
        for dev in devices:
            for dev_call in callables:
                obj, *methods = dev_call.split('.')
                call = getattr(dev, obj)
                for method in methods:
                    call = getattr(call, method)
                functions.append(call)
        return functions
    
    @staticmethod
    def __get_dev_names(names, ndev):
        """
        Returns the names of the devices.

        Parameters
        ----------
        names : list
            The list of device names.

        Returns
        -------
        names : list
            The list of device names.
        """
        dev_names = []
        try:
            for x in names:
                dev_names.append(x)
        except TypeError:
            for x in range(ndev):
                dev_names.append(f"Device {x}")
        return dev_names

class _Command:
    """
    The _Command class represents a command with a vector and a reset flag. It 
    provides methods for updating the command, checking if it is null, and 
    combining it with other commands.
    Attributes:
        vect (np.ndarray): The vector representing the command.
        is_reset (bool): A flag indicating whether the command is a reset command.
    Methods:
        __init__(vector=None, is_reset=False):
            Initializes a new instance of the _Command class.
        __repr__():
            Returns a string representation of the _Command instance.
        __str__():
            Returns the string representation of the command vector.
        __add__(other):
            Combines the current command with another _Command instance.
        is_null():
            Determines whether the command is null, i.e., a sequence of zeros.
        to_ignore():
            Returns True if the command is flagged to be ignored, False if it 
            is null but should not be ignored.
        to_ignore(value: bool):
            Setter for the 'to_ignore' property.
        update(vector, is_reset=None):
            Recycles the class to reuse the instance, updating its vector and 
            reset flag.
    """
    def __init__(self, vector=None, to_ignore:bool=None):
        """
        Initializes a new instance of the _Command class.
    
        Parameters
        ----------
        vector : list or np.ndarray, optional
            The vector representing the command. If a list is provided, it will
            be converted to a numpy array.
        to_ignore : bool, optional
            A flag indicating whether the command should be ignored.
        """
        self.vect = np.array(vector) if isinstance(vector, list) else vector
        self.to_ignore = to_ignore
    
    def __repr__(self):
        """
        Returns a string representation of the _Command instance.
    
        Returns
        -------
        str
            A string representation of the _Command instance.
        """
        if self.to_ignore is not None:
            return f"Command({self.vect}, to_ignore={self.to_ignore})"
        else:
            return f"Command({self.vect},)"
    
    def __str__(self):
        """
        Returns the string representation of the command vector.
    
        Returns
        -------
        str
            The string representation of the command vector.
        """
        return self.vect.__str__()
    
    def __add__(self, other):
        """
        Combines the current command with another _Command instance.
    
        Parameters
        ----------
        other : _Command
            Another instance of the _Command class.
    
        Returns
        -------
        _Command
            A new _Command instance with the combined vector and updated 
            'to_ignore 'flag.
    
        Raises
        ------
        NotImplementedError
            If the vectors of the commands are not numpy arrays.
        """
        if not isinstance(other, _Command):
            return NotImplemented
        if not isinstance(self.vect, np.ndarray) and not isinstance(other.vect, np.ndarray):
            raise NotImplementedError(f"Operation not supported for operands types {type(self.vect)} and {type(other)}")
        combined_vect = self.vect + other.vect
        to_ignore = self._process_command_logic(self, other, combined_vect)
        return _Command(combined_vect, to_ignore)
    
    @property
    def is_null(self):
        """
        Determines whether the command is null, i.e., a sequence of zeros.
    
        Returns
        -------
        bool
            True if the command is null, False otherwise.
        """
        return np.all(self.vect == 0)
    
    def _process_command_logic(self, P, C, S):
        """
        Processes the command logic to determine the to_ignore flag.
    
        Parameters
        ----------
        P : _Command
            The previous command instance.
        C : _Command
            The current command instance.
        S : np.ndarray
            The sum of the vectors of the previous and current commands.
    
        Returns
        -------
        bool
            The decision for the to_ignore flag based on the command logic.
        """
        # P = current device position
        # C = received device command
        # S = sum of P and C - command to apply (absolute)
        #_________________________________________________#
        # If S = 0
        if np.all(S == 0):
            # C ≠ 0 and P ≠ 0 → TO_NOT_IGNORE
            if not P.is_null and not C.is_null and np.array_equal(C.vect,-1*P.vect):
                decision = False
            # C = 0 and P = 0 → TO_IGNORE
            elif C.is_null and P.is_null:
                decision = True
        # If S ≠ 0
        else:
            # P ≠ 0 and C = 0 → TO_IGNORE
            if not P.is_null and C.is_null and np.array_equal(S,P.vect):
                decision = True
            # C ≠ 0 and P ≠ 0 → TO_NOT_IGNORE
            elif not C.is_null and not P.is_null:
                decision = False
            # P = 0 and C ≠ 0 → TO_NOT_IGNORE
            elif P.is_null and not C.is_null and np.array_equal(S,C.vect):
                decision = False
        return decision


# -----------------------
# Volume transfer class #
# -----------------------

import pandas as pd
import numpy as np
from utils import * # file with helper methods


class VolumeTransfer():
    """
    Produces CSV files with all the steps to carry out a volume transfer in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.csv_files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\6. Volume transfer' # network path where all the CSV files will be saved in.
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions 

        # CSV file names
        self.sample_dilutions_csv_name = r"\1. Volume transfer - "

        # Volume transfer parameters
        self.n_samples = 0 # amount of samples for the sample transfer
        self.n_sample_dilution_steps = 0 # number of sample dilution steps to achieve final concentration
        self.sample_lw_origin = "" # origin labware of samples
        self.sample_lw_dest = "" # destination labware of samples
        self.sample_dest_positions = 0 # positions of Eppendorf tubes where the diluted samples end up
        self.n_sample_repetitions = 0 # number of times that each origin sample will be transfered to the destination labwares
        self.volume_transfered = 0 # volume to transfer in uL

    def next_labware_pos(self, labware_name:str):
        """
        Adds one to the last labware position to keep track of already used ones. 

        Parameters
        ----------
        ``labware_name`` : str
            Labware name as in TECAN Fluent worktable.

        Returns
        ----------
        ``curr_pos``: int
            Current position number.
        """

        try:
            if labware_name in LabwareNames:
                    if (self.used_labware_pos[labware_name] + 1 <= AvailableLabware[labware_name]): # if max pos has not been reached
                        self.used_labware_pos[labware_name] = self.used_labware_pos[labware_name] + 1
                        return self.used_labware_pos[labware_name] # return current one before adding an unit
            else:
                return -1
        except Exception as e:
            return -1


    # def pos_2_str(self, name: str, pos: int):
    #     """
    #     Converts name and position number to string format with brackets.

    #     Parameters
    #     ----------
    #     name : str
    #         Labware name as in TECAN Fluent worktable.
    #     pos : int
    #         Position number to be converted.

    #     Returns
    #     -------
    #     new_name : str
    #         Concatenation of Labware name and its position.
        
    #     Example
    #     --------
    #     >>> pos_2_str("Eppendorf", 3)
    #     "Eppendorf[003]"

    #     >>> pos_2_str("Eppendorf", 13)
    #     "Eppendorf[013]"
    #     """

    #     if isinstance(pos, list):
    #         pos = pos[0]

    #     if pos < 10:
    #         new_name = name + "[00"+str(pos)+"]"
    #     else:
    #         new_name = name + "[0"+str(pos)+"]"

    #     return new_name
        

    # def dilution_position_def(self, labware_name: str, initial_pos: int, nsamples: int):
    #     """
    #     Creates two arrays, for the source labware name and position.

    #     Parameters
    #     ----------
    #     labware_name : str
    #         Labware name as in TECAN Fluent worktable.
    #     initial_pos : int
    #         Labware position/well of the initial sample.
    #     n_samples : int
    #         Number of samples used, same as returned array length.

    #     Returns
    #     ----------
    #     Label: array
    #         Array of the labware names, including square brackets.
    #     Pos: array
    #         Array of the list of positions for the labware.
    #     """


    #     Label = np.array([])
    #     Pos = np.array([])
 
    #     if labware_name in LabwarePlates:
    #         for i in range(0,nsamples):
    #             # Label = np.append(Label,['96 Deep Well 2ml[001]']) # labware name is fixed for eppendorf
    #             Label = np.append(Label,[LabwareNames[labware_name]]) # labware name is fixed for eppendorf
    #             Pos = np.append(Pos, int(initial_pos+i))

    #     else:
    #         for i in range(0,nsamples):
    #             name = pos_2_str(labware_name,initial_pos+i) # the labware name gets updated for eppendorf
    #             Label = np.append(Label,[name])
    #             Pos = np.append(Pos, int(1)) # this type of labware only has one position, so it is fixed to 1.

    #     return Label, Pos.astype(int)
        

    def sample_dilutions(self):
        """
        Performs the volume transfer.

        Outputs
        ----------
            CSV files containing instructions for the Tecan.
        """

        csv_data_sample = []
        csv_number = 0 # # to name generated files sequentially
        dest_positions = [] # list to store destination positions used for the final dilution

        LabSource, SourceWell = dilution_position_def(self.sample_lw_origin, 1, self.n_samples)
        
        for i in range(self.n_samples):
            LabDest, DestWell = dilution_position_def(self.sample_lw_dest, self.used_labware_pos[self.sample_lw_dest] + 1, self.n_sample_repetitions)
        
            # LabSource, SourceWell = LabDest, DestWell # source of next step is destination of previous one

            # if i + 1 == self.n_sample_dilution_steps: # if this is the final dilution step
            #     LabDest, DestWell = dilution_position_def(self.sample_lw_dest, self.used_labware_pos[self.sample_lw_dest] + 1, (self.n_samples * (i+1) + 1))
            # else:
            #     LabDest, DestWell = dilution_position_def("DeepWell", self.used_labware_pos["DeepWell"] + 1, (self.n_samples * (i+1) + 1))

            for j in range(self.n_sample_repetitions):
                csv_data_sample.append(
                {
                    'LabSource': LabSource[i],
                    'SourceWell': SourceWell[i],
                    'LabDest': LabDest[j],
                    'DestWell': DestWell[j],
                    'Volume': float(self.volume_transfered)
                }
                )

                self.next_labware_pos(self.sample_lw_dest)
                dest_positions.append(self.used_labware_pos[self.sample_lw_dest])

        path = self.csv_files_path + self.sample_dilutions_csv_name + str(csv_number) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)
        csv_number = csv_number + 1

        # if less than 3 dilutions steps are needed, blank out the remaining CSV files so that the Tecan ignores them basically
        # for i in range(csv_number, 6 + 1):
        #     path = self.csv_files_path + self.sample_dilutions_csv_name + str(csv_number) + ".csv"
        #     pd.DataFrame(list()).to_csv(path, index=False, header=False) # create empty dataframe and save it into an empty CSV
        #     csv_number = csv_number + 1


        return dest_positions
    

    def count_starting_lw_pos(self):
        """
        Counts the positions of the sample origin labware, so that
        if the destination labware is the same, new tubes are used.
        """

        if self.sample_lw_origin in LabwareNames:
            for i in range(0, self.n_samples):
                self.next_labware_pos(LabwareNames[self.sample_lw_origin])
  
    
    def volume_transfer(self):
        """
        Class main method.
        ----------

        Calls other methods to perform the dilution correctly and generates CSV files for them.
        """

        # self.set_all_parameters(external)

        self.count_starting_lw_pos()

        self.sample_dest_positions = self.sample_dilutions()

        return self.sample_dest_positions

        
    def set_all_parameters(self, external):
        """
        Sets all parameters from self class to be able to generate all CSV files.
        
        Parameters
        ----------
        external : class obj
            Reference to external class object where all parameters will be get from.
        """
        # Reset parameters
        self.used_labware_pos = dict.fromkeys(self.used_labware_pos, 0)

        # Sample
        self.sample_lw_origin = external.optionmenu_1_vt.get()
        self.n_samples = int(external.entry_slider2_vt.get())
        self.sample_lw_dest = external.vt_dest.get()
        self.n_sample_repetitions = int(external.entry_slider3_vt.get())
        self.volume_transfered = int(external.vt_volume.get())


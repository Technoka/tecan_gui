
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


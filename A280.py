
# -----------------------
# A280 method class #
# -----------------------

import pandas as pd
import numpy as np
from utils import * # file with helper methods


class A280Method():
    """
    Produces CSV files with all the steps to carry out the A280 method in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\8. A280' # network path where all the files will be saved in.
        self.sample_dilution_file_name = r"\1. Sample dilutions - "
        self.sample_transfer_file_name = r"\1. Sample transfer - "
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions 

        # Sample transfer parameters
        self.n_samples = 0 # amount of samples for the sample transfer
        self.sample_concentration = 100 # initial concentration in mg/mL
        self.concentration_limit = 100 # mg/mL. If it is more than this, we need to dilute
        self.sample_lw_origin = "" # origin labware of samples
        self.sample_lw_dest = "soloVPE cuvettes" # destination labware of samples
        self.sample_dest_positions = [0] # positions where the diluted samples end up


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
        

    def count_starting_lw_pos(self):
        """
        Counts the positions of the sample origin labware, so that
        if the destination labware is the same, new tubes are used.
        """

        if self.sample_lw_origin in LabwareNames:
            for i in range(0, self.n_samples):
                self.next_labware_pos(LabwareNames[self.sample_lw_origin])
  

    def sample_dilution(self):
        """
        
        """
        
        pass


    def sample_transfer(self):
        """
        
        """

        pass



    def a280(self):
        """
        Class main method.
        ----------

        Executes all stages of the A280 method step by step and generates CSV files for them.
        """

        self.count_starting_lw_pos()

        if self.sample_concentration >= self.concentration_limit:
            self.sample_dilution()
            print("Sample dilutions done")

        self.sample_transfer()
        print("Sample transfer done")


        return 0

        
    def set_all_parameters(self, external):
        """
        Sets all parameters from self class to be able to generate all CSV files.
        
        Parameters
        ----------
        external : class obj
            Reference to external class object where all parameters will be get from.
        """

        # Reset parameters
        self.used_labware_pos = dict.fromkeys(self.used_labware_pos, 0) # reset dict

        # General
        self.n_samples = external.a280_n_samples.get() # amount of samples for the sample transfer
        self.sample_concentration = external.a280_concentration.get() # volume (uL) to transfer to each well
        self.sample_lw_origin = external.a280_lw_origin.get() # origin labware of samples
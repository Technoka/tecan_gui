
# -----------------------
# SEC-HPLC method class #
# -----------------------

import pandas as pd
import numpy as np
from utils import * # file with helper methods


class sec_HPLCMethod():
    """
    Produces CSV files with all the steps to carry out the Size Exclusion HPLC method in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\9. SEC-HPLC' # network path where all the files will be saved in.
        self.gwl_file_name = r"\sample_transfer"
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions 

        self.has_detectability_standard = False # only some products have it

        # Sample transfer parameters
        self.n_samples = 1 # amount of samples for the sample transfer
        self.sample_initial_concentration = 1
        self.sample_volume_per_well = 1 # volume (uL) to transfer to each well
        self.sample_lw_origin = "" # origin labware of samples
        self.sample_lw_dest = "" # destination labware of samples
        self.sample_dest_positions = [0] # positions of 384 plate where the diluted samples end up


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
  

    def is_sample_dilution_needed(self):
        """
        Calculates if the samples need to be diluted or not.
        
        Returns
        ----------
        dict
            True or False depending if the samples have to be diluted
        """

        # dict to return containing essential data
        sample_dilution_data = {"sample_dilution_needed": False, # if this is False, the other parameters are useless
                                  "final_concentration": 0, # in mg/mL
                                  "injection_volume": 20} # in uL

        # as in the table in the TMD
        if self.sample_initial_concentration > 10:
             new_values = [True, 10, 20]
        elif self.sample_initial_concentration == 10:
             new_values = [False, 0, 0]
        elif self.sample_initial_concentration > 4 and self.sample_initial_concentration < 10:
             new_values = [True, 4, 50]
        elif self.sample_initial_concentration > 2 and self.sample_initial_concentration < 4:
             # special case, needs extra calculations
             column_load = 0.2 # 200nL, ask nicolas
             volume = column_load / self.sample_initial_concentration # ???
             final_concentration = "???" # ask nicolas
             
             new_values = [True, final_concentration, volume]


        elif self.sample_initial_concentration == 2:
             new_values = [False, 2, 100]
        else:
            raise ValueError("The sample initial concentration needs to be at least 2mg/mL")

        
        sample_dilution_data = {k: v for k, v in zip(sample_dilution_data.keys(), new_values)}
        

        return sample_dilution_data


    def sample_dilution(self, sample_dilution_data):
        """
        Only called if samples need to be diluted. Generates the CSV files for the dilution.
        """

        

        pass


    def sec_HPLC(self):
        """
        Class main method.
        ----------

        Executes all stages of the nanoDSF method step by step and generates CSV files for them.
        """

        self.count_starting_lw_pos()

        sample_dilution_data = self.is_sample_dilution_needed()
        print("Sample dilution data:", sample_dilution_data)




        return

        
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
        self.n_samples = external.sec_HPLC_n_samples.get() # amount of samples for the sample transfer
        self.sample_lw_origin = external.sec_HPLC_lw_origin.get() # origin labware of samples
        self.sample_initial_concentration = int(external.sec_HPLC_initial_concentration.get()) # origin labware of samples
        self.sample_lw_dest = external.sec_HPLC_lw_dest.get() # origin labware of samples
        

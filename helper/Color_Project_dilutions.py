
# ----------------------------------------------------------------------------- #
# Color Project Dilutions class                                                 #
#   > One time thing to help Rifat with measurements and data for the ML model. #
# ----------------------------------------------------------------------------- #

import pandas as pd
import numpy as np
from helper.utils import * # file with helper methods


class ColorProjectDilutions():
    """
    Produces CSV files with all the steps to carry out dilutions for the Color Project for Rifat in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\10. Color Project' # network path where all the files will be saved in.
        self.solution_filename = r"\XX_solution_YY - "
        self.diluent_filename = r"\XX_solution_YY - "
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions 

        # Solution transfer parameters
        self.n_samples = 1 # amount of samples for the sample transfer
        self.initial_solution_volume = 50 # volume (uL) of solution to transfer to the first cuvette
        self.solution_volume_diff = 2 # volume (uL) difference between each solution transfer
        self.n_replicates_per_solution = 1 # number of replicates to do per solution transfer

        self.solution_lw_origin = "" # origin labware of samples
        self.lw_dest = LabwareNames["UV cuvette holder"] # # 2 options: 2mL Vial, 96-well plate, vial by default
        self.solution_dest_positions = [0] # positions of 384 plate where the diluted samples end up
        
        # Buffer parameters
        self.buffer_lw_origin = "100ml_1" # origin labware of buffer, hard coded for now


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
                        return self.used_labware_pos[labware_name] # return next positions after adding an unit
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
  


    def color_project_dilutions(self):
        """
        Class main method.
        ----------

        Executes all stages of the Color Project dilutions step by step and generates CSV files for them.
        """

        logger.info("-------------------------------------")
        logger.info(f"N. of samples: {self.n_samples}")
        logger.info("-------------------------------------")

        self.count_starting_lw_pos()

        
        logger.info(f"Dilutions finished successfully.")

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

        # Sample
        self.n_samples = external.sec_HPLC_n_samples.get() # amount of samples for the sample transfer
        self.sample_lw_origin = external.sec_HPLC_sample_lw_origin.get() # origin labware of samples
        self.sample_initial_concentration = int(external.sec_HPLC_sample_initial_concentration.get()) # origin labware of samples
        self.lw_dest = external.sec_HPLC_lw_dest.get() # origin labware of samples
        
        # Pos Ctr
        self.pos_ctr_lw_origin = external.sec_HPLC_pos_ctr_lw_origin.get() # origin labware of samples
        

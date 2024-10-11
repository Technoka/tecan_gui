
# ----------------------------------------------------------------------------- #
# Color Project Dilutions class                                                 #
#   > One time thing to help Rifat with measurements and data for the ML model. #
# ----------------------------------------------------------------------------- #

import pandas as pd
import numpy as np
from helper.utils import * # file with helper methods


class ColorProjectDilutionsMethod():
    """
    Produces CSV files with all the steps to carry out dilutions for the Color Project for Rifat in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\10. Color Project' # network path where all the files will be saved in.
        self.sample_filename = r"\XX_solution_YY - "
        self.diluent_filename = r"\XX_diluent_YY - "
        self.config_file_name = r"\config.txt"
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions 

        # Solution transfer parameters
        self.n_samples = 1 # amount of samples for the sample transfer
        self.initial_sample_volume = 50 # volume (uL) of solution to transfer to the first cuvette
        self.initial_diluent_volume = 1950 # volume (uL) of diluent to transfer to the first cuvette
        # self.solution_volume_diff = 2 # volume (uL) difference between each solution transfer
        self.n_replicates = 1 # number of replicates to do per solution transfer

        self.sample_lw_origin = "100ml_2" # origin labware of samples
        self.lw_dest = "UV Cuvette holder"
        self.lw_origin_tiny_vol = "DeepWell" # if volume to transfer is < 10uL, pipette from here so that the 10uL tips can reach the bottom

        
        # Diluent parameters
        self.diluent_lw_origin = "100ml_1" # origin labware of diluent, hard coded for now


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
                        raise ValueError(f"Total number of positions of labware {labware_name} exceeded: pos {self.used_labware_pos[labware_name] + 1} wanted, but {AvailableLabware[labware_name]} is maximum.")
            else:
                raise ValueError(f"Labware {labware_name} not in LabwareNames.")
        except Exception as e:
            print(e)
            logger.error(f"Total number of positions of labware {labware_name} exceeded: pos {self.used_labware_pos[labware_name] + 1} wanted, but {AvailableLabware[labware_name]} is maximum.")
            raise ValueError(f"labware pos exceeded maximum one")
        

    def count_starting_lw_pos(self):
        """
        Counts the positions of the sample origin labware, so that
        if the destination labware is the same, new tubes are used.
        """

        if self.sample_lw_origin in LabwareNames:
            for i in range(0, self.n_samples):
                self.next_labware_pos(LabwareNames[self.sample_lw_origin])
  

    def generate_volume_sequences(self, starting_sample_vol: float, starting_diluent_vol: float, num_samples: int, diff: int = 2,) -> tuple[float, float]:
        """
        Generates two arrays of volumes where one volume decreases and the other increases.

        Parameters
        ----------
        ``start_sample_vol``: float
            Starting volume for the first array (decreases with each sample).

        ``start_diluent_vol``: float
            Starting volume for the second array (increases with each sample).

        ``diff``: float
            The difference to add/subtract for each sample.

        ``num_samples``: int
            The number of samples to generate in the arrays.

        Outputs
        ----------
        Returns two lists:
            - First list contains volumes starting from ``start_sample_vol``, decreasing by ``diff`` for each sample.
            - Second list contains volumes starting from ``start_diluent_vol``, increasing by ``diff`` for each sample.
        """
        sample_volumes = []
        diluent_volumes = []

        for i in range(num_samples):
            sample_vol = starting_sample_vol - (i * diff)  # Decreasing volume for sample_vol
            if starting_diluent_vol > 1000: # it vol cannot fit in 1 tip, divide by 2, it is then repeated 2 times in tecan
                diluent_vol = round(starting_diluent_vol/2) + (i * round(diff/2))  # Increasing volume for diluent_vol
            else:
                diluent_vol = starting_diluent_vol + (i * diff)  # Increasing volume for diluent_vol
            
            sample_volumes.append(sample_vol)
            diluent_volumes.append(diluent_vol)

        # Asserting that all elements in both lists are greater than or equal to 0
        assert all(x >= 0 for x in sample_volumes), f"Not all elements in sample_volumes are >= 0: {sample_volumes}"
        assert all(x >= 0 for x in diluent_volumes), f"Not all elements in diluent_volumes are >= 0: {diluent_volumes}"
        
        return sample_volumes, diluent_volumes


    def generate_GWL_files(self, sample_volumes, diluent_volumes):
        """
        Generates the GWL files for the sample and diluent dilutions.

        """

        # Reagent distribution parameters (fixed for all tests, therefore hardcoded here instead of being variables)
        n_diti_reuses = 1
        n_multi_dispense = 1

        # we do it 1 time so that it doesnt start in 0 but in 1.
        self.next_labware_pos(self.lw_dest)

        # Flag variable to say if there is some volume transfer smaller than 10uL
        has_tiny_volumes = False
        # Sum of all volumes less than 10 in sample transfer
        sample_vol_less_10uL = sum(x for x in sample_volumes if x < 10)

        if sample_vol_less_10uL > 0: # at least 1 volume to transfer is smaller than 10uL
            has_tiny_volumes = True # update flag
            total_sample_vol_less_10uL = sample_vol_less_10uL * self.n_replicates # total vol accounting replicates also
            # pre transfer some volume to DeepWell pos 1, where 10uL tips will take from later
            path = self.files_path + rf"\{self.sample_filename}.gwl"
            vol_to_transfer = min(total_sample_vol_less_10uL + 50, 1800) # we add 50uL for dead volume, and cap it at 1800uL because max of deepwell is 2mL. Anyway, it should never reach such a high value
            generate_reagent_distribution_gwl(path, "w", self.sample_lw_origin, LabwareNames[self.lw_origin_tiny_vol], 1, 1, 1, 1, vol_to_transfer, n_diti_reuses, n_multi_dispense)
                

        # for each sample
        for i in range(1, self.n_samples + 1):

            # Sample transfer
            path = self.files_path + rf"\{self.sample_filename}.gwl"
            open_mode = "w" if (i == 1 and not has_tiny_volumes) else "a" # write mode in first sample to get a clean file, append mode after to keep adding lines
            dest_pos_start = self.used_labware_pos[self.lw_dest]
            dest_pos_end = dest_pos_start + self.n_replicates - 1

            # if volume to transfer is less than 10uL, use 10uL tip and take from DeepWell instead of 100mL reservoir, so that tip can reach the bottom
            if sample_volumes[i-1] < 10:
                generate_reagent_distribution_gwl(path, open_mode, LabwareNames[self.lw_origin_tiny_vol], LabwareNames[self.lw_dest], 1, 1, dest_pos_start, dest_pos_end, sample_volumes[i-1], n_diti_reuses, n_multi_dispense)
            
            else:
                # generate_sample_transfer_gwl(path, open_mode, self.sample_lw_origin, LabwareNames[self.lw_dest], 1, 1, dest_pos_start, dest_pos_end, sample_volumes[i-1], n_diti_reuses, n_multi_dispense, 1, self.n_replicates, 1, 1)
                generate_reagent_distribution_gwl(path, open_mode, self.sample_lw_origin, LabwareNames[self.lw_dest], 1, 1, dest_pos_start, dest_pos_end, sample_volumes[i-1], n_diti_reuses, n_multi_dispense)
                
            # Diluent transfer
            # path = self.files_path + "/" + self.diluent_filename + ".gwl"
            path = self.files_path + rf"\{self.diluent_filename}.gwl"

            # generate_sample_transfer_gwl(path, open_mode, self.diluent_lw_origin, LabwareNames[self.lw_dest], 1, 1, dest_pos_start, dest_pos_end, diluent_volumes[i-1], n_diti_reuses, n_multi_dispense, 1, self.n_replicates, 1, 1)
            generate_reagent_distribution_gwl(path, open_mode, self.diluent_lw_origin, LabwareNames[self.lw_dest], 1, 1, dest_pos_start, dest_pos_end, diluent_volumes[i-1], n_diti_reuses, n_multi_dispense)

            # to account for the used cuvettes of the reagent distr. replicate use
            for _ in range(self.n_replicates):
                self.next_labware_pos(self.lw_dest)

            # if in next iteration, the max pos of the replicates is > 40, change labware destination to second cuvette holder
            if (dest_pos_end + self.n_replicates) > 40:
                if self.lw_dest == "UV Cuvette holder 2":
                    raise ValueError(f"The max number of positions for UV Cuvette holders is reached.")
                
                self.lw_dest = "UV Cuvette holder 2" # change labware dest to second one
                self.next_labware_pos(self.lw_dest) # start in pos 1 instead of 0


    def generate_config_file(self):
        """
        Generates the config file for the current run.
        """

        # If there are repeated keys in the dictionary, the last one and its value is the dominant one !!!

        config_parameters = {"sample_filename": str(self.sample_filename),
                             "diluent_filename": str(self.diluent_filename)
                     }

        with open(self.files_path + self.config_file_name, 'w') as file:
            # Write the keys
            keys = "; ".join(config_parameters.keys())
            file.write(keys + ";\n")
            
            # Write the values
            values = "; ".join(map(str, config_parameters.values()))
            file.write(values + ";\n")


    def color_project_dilutions(self):
        """
        Class main method.
        ----------

        Executes all stages of the Color Project dilutions step by step and generates CSV files for them.
        """

        logger.info("-------------------------------------")
        logger.info(f"N. of samples: {self.n_samples}")
        logger.info("-------------------------------------")


        self.generate_config_file()
        logger.info("Config file generated.")
        self.count_starting_lw_pos()

        sample_volumes, diluent_volumes = self.generate_volume_sequences(self.initial_sample_volume, self.initial_diluent_volume, self.n_samples)
        logger.debug(f"Volume sequences calculated. Sample volumes: {sample_volumes}.   Diluent volumes: {diluent_volumes}")

        self.generate_GWL_files(sample_volumes, diluent_volumes)
        logger.info("GWL files generated.")

        
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

        # General
        self.n_samples = external.color_proj_n_samples.get() # amount of samples for the sample transfer
        self.initial_sample_volume = int(external.color_proj_starting_vol_sample.get())
        self.initial_diluent_volume = int(external.color_proj_starting_vol_diluent.get())
        self.n_replicates = external.color_proj_n_replicates.get()
        self.sample_filename = external.color_proj_sample_filename.get()
        self.diluent_filename = external.color_proj_diluent_filename.get()
        
        

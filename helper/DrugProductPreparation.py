
# -----------------------
# Drug Product Preparation class #
# -----------------------

import pandas as pd
import numpy as np
from helper.utils import * # file with helper methods


class DrugProductPreparationMethod():
    """
    Produces CSV files with all the steps to carry out a general dilution in the TECAN.
    """

    def __init__(self):

        # General parameters
        self.csv_files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\11. Drug Product Preparation' # network path where all the CSV files will be saved in.
        self.csv_filename = r"\dpp_step - "
        self.config_file_name = r"\config.txt"
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions
        self.csv_number = 1 # to keep track of generated CSV files

        # Sample transfer parameters
        self.n_samples = 1 # amount of samples for the sample transfer
        self.sample_initial_concentration = 1
        self.final_concentration = 1 # mg/mL, it is always like this
        self.sample_volume_transfer = 1 # volume (uL) to transfer to each well
        self.sample_lw_origin = "" # origin labware of samples
        self.lw_dest = "Eppendorf"
        self.total_volume = 1000 # total volume to have in destination labware

        # Labware names
        self.buffer_lw_origin = LabwareNames["GeneralBuffer"] # origin labware of buffer, hard coded for now

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
                self.next_labware_pos(self.sample_lw_origin)
  

    def sample_dilutions(self):
        """
        Performs the dilutions to get the sample final concentration.

        Outputs
        ----------
            CSV files containing instructions for the Tecan.
        """

        csv_data_sample = []
        csv_data_buffer = []

        sample_volume, buffer_volume = calculate_dilution_parameter(self.sample_initial_concentration, self.final_concentration, None, self.total_volume)

        LabDest, DestWell = dilution_position_def(self.lw_dest, self.next_labware_pos(self.lw_dest), 1)

        # sample to dest labware
        LabSource, SourceWell = dilution_position_def(LabwareNames[self.sample_lw_origin], 1, self.n_samples) # samples are always placed in positions 1..n_samples
        csv_data_sample.append(
        {
            'LabSource': LabSource[0],
            'SourceWell': SourceWell[0],
            'LabDest': LabDest[0],
            'DestWell': DestWell[0],
            'Volume': sample_volume
        })
        
        # buffer to dest labware
        csv_data_buffer.append(
        {
            'LabSource': self.buffer_lw_origin,
            'SourceWell': 1,
            'LabDest': LabDest[0],
            'DestWell': DestWell[0],
            'Volume': buffer_volume
        })


        path = self.csv_files_path + self.csv_filename + str(self.csv_number) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)
        path = self.csv_files_path + self.csv_filename + str(self.csv_number + 1) + ".csv"
        pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False)
        self.csv_number += 2

    
    def generate_config_file(self):
        """
        Generates the config file for the current run.
        """

        # If there are repeated keys in the dictionary, the last one and its value is the dominant one !!!

        config_parameters = {"n_steps": self.csv_number - 1 # we remove 1 because it is already added beforehand
                     }

        with open(self.csv_files_path + self.config_file_name, 'w') as file:
            # Write the keys
            keys = "; ".join(config_parameters.keys())
            file.write(keys + ";\n")
            
            # Write the values
            values = "; ".join(map(str, config_parameters.values()))
            file.write(values + ";\n")
    
    
    def DrugProductPreparation(self):
        """
        Class main method.
        ----------

        Calls other methods to perform the dilution correctly and generates CSV files for them.
        """

        # Reset parameters
        self.used_labware_pos = dict.fromkeys(self.used_labware_pos, 0)
        self.csv_number = 1

        logger.info("-------------------------------------")
        logger.info(f"Samples initial labware: {self.sample_lw_origin}")
        logger.info(f"Samples destination labware: {self.lw_dest}")
        logger.info(f"Samples initial concentration: {self.sample_initial_concentration} mg/mL")
        logger.info(f"Final concentration: {self.final_concentration} mg/mL")
        logger.info("-------------------------------------")
        
        self.count_starting_lw_pos()

        self.sample_dilutions()
        logger.info(f"Dilution CSV files generated.")

        self.generate_config_file()
        logger.info("Config file generated.")
        
        logger.info(f"Method finished successfully.")

        
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
        self.csv_number = 1

        # Sample
        self.sample_lw_origin = external.drug_prod_prep_sample_lw_origin.get()
        self.lw_dest = external.drug_prod_prep_lw_dest.get()
        


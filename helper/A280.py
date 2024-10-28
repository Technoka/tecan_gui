
# -----------------------
# A280 method class #
# -----------------------

import pandas as pd
import numpy as np
from helper.utils import * # file with helper methods


class A280Method():
    """
    Produces CSV files with all the steps to carry out the A280 method dilutions and transfer in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.csv_files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\8. A280' # network path where all the files will be saved in.
        self.sample_dilution_file_name = r"\1. Sample dilutions - "
        self.sample_transfer_file_name = r"\1. Sample transfer - "
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions 

        # Sample transfer parameters
        self.n_samples = 0 # amount of samples for the sample transfer
        self.sample_concentration = 100 # initial concentration in mg/mL
        self.concentration_limit = 100 # mg/mL. If it is more than this, we need to dilute
        self.sample_lw_origin = "" # origin labware of samples
        self.sample_lw_dest = "soloVPE cuvette holder custom" # destination labware of samples
        self.sample_diluted_positions = [0] # positions where the diluted samples end up
        self.is_dilution_needed = False
        self.sample_transfer_volume = 100 # volume in uL to transfer to each cuvette

        self.buffer_lw = LabwareNames["GeneralBuffer"]
        self.dilution_extra_volume = 100 # extra volume in uL to assure that tip will have enough volume to take
        self.dilution_labware = "FakeFalcon15"
        self.dilution_pos = 0

        self.config_file_name = r"\config.txt"


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
                        return self.used_labware_pos[labware_name] # return current one
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
            self.next_labware_pos(LabwareNames[self.sample_lw_origin])


    def sample_dilution(self):
        """
        Dilute samples from labware origin to Eppendorf tubes.
        """
        
        
        csv_number = 1 # # to name generated files sequentially
        csv_data_sample = []
        csv_data_buffer = []

        total_volume = self.n_samples * 100 + self.dilution_extra_volume # total diluted volume needed for the transfer to the cuvettes
        sample_volume, buffer_volume = calculate_dilution_parameter(self.sample_concentration, self.sample_concentration / 4, None, total_volume)

        # buffer_lw, buffer_pos = dilution_position_def("Eppendorf", self.next_labware_pos("Eppendorf"), 1) # buffer is placed in Eppendorf tube
        # initial_pos = self.next_labware_pos(find_best_container(buffer_total_volume/1000))
        # print("initial pos:", initial_pos)
        # buffer_lw, buffer_pos = dilution_position_def(find_best_container(buffer_total_volume/1000), initial_pos, 1) # buffer is placed in Eppendorf tube
        # self.buffer_lw_pos = (buffer_lw, buffer_pos)

        # print(f"buffer_lw and pos: {buffer_lw}, {buffer_pos}")

        LabSource, SourceWell = dilution_position_def(self.sample_lw_origin, 1, 1) # samples are always placed in positions 1..n_samples
        LabDest, DestWell = dilution_position_def(self.dilution_labware, self.next_labware_pos(LabwareNames[self.dilution_labware]), 1)

        for j in range(self.n_samples):
            csv_data_sample.append(
            {
                'LabSource': LabSource[0],
                'SourceWell': 1,
                'LabDest': LabDest[0],
                'DestWell': DestWell[0],
                'Volume': sample_volume
            }
            )
            
            csv_data_buffer.append(
            {
                'LabSource': self.buffer_lw,
                'SourceWell': 1,
                'LabDest': LabDest[0],
                'DestWell':  DestWell[0],
                'Volume': buffer_volume
            }
            )

            # self.next_labware_pos("Eppendorf") # to keep track of used labware positions

        path = self.csv_files_path + self.sample_dilution_file_name + str(csv_number) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)
        path = self.csv_files_path + self.sample_dilution_file_name + str(csv_number + 1) + ".csv"
        pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False)
        csv_number = csv_number + 2

        return (LabDest, DestWell)
    


    def sample_transfer(self):
        """
        Transfer samples to cuvette plate.
        """

        
        if self.is_dilution_needed:
            LabSource, SourceWell = self.dilution_labware, self.dilution_pos # samples are always placed in positions 1..n_samples
        
        else:
            LabSource, SourceWell = dilution_position_def(LabwareNames[self.sample_lw_origin], 1, 1) # samples are always placed in positions 1..n_samples

        csv_number = 1 # # to name generated files sequentially
        csv_data_sample = []

        LabDest, DestWell = dilution_position_def(self.sample_lw_dest, 1, self.n_samples) # position starts in 1 because labware has not been used yet

        for j in range(self.n_samples):
            csv_data_sample.append(
            {
                'LabSource': LabSource[0],
                'SourceWell': SourceWell[0],
                'LabDest': LabDest[j],
                'DestWell': DestWell[j],
                'Volume': self.sample_transfer_volume
            }
            )

        path = self.csv_files_path + self.sample_transfer_file_name + str(csv_number) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)

        return DestWell


    def generate_config_file(self):
        """
        Generates the config file for the current run.
        """

        # If there are repeated keys in the dictionary, the last one and its value is the dominant one !!!

        config_parameters = {"is_dilution_needed": self.is_dilution_needed # we remove 1 because it is already added beforehand
                     }

        with open(self.csv_files_path + self.config_file_name, 'w') as file:
            # Write the keys
            keys = ";".join(config_parameters.keys())
            file.write(keys + ";\n")
            
            # Write the values
            values = ";".join(map(str, config_parameters.values()))
            file.write(values + ";\n")


    def a280(self):
        """
        Class main method.
        ----------

        Executes all stages of the A280 method step by step and generates CSV files for them.
        """

        # Reset parameters
        self.used_labware_pos = dict.fromkeys(self.used_labware_pos, 0) # reset dict
        
        if self.sample_concentration >= self.concentration_limit:
            self.is_dilution_needed = True # update flag

        logger.info("-------------------------------------")
        logger.info(f"N. of samples: {self.n_samples}")
        logger.info(f"Samples initial labware: {self.sample_lw_origin}")
        logger.info(f"Samples initial concentration: {self.sample_concentration} mg/mL")
        logger.info(f"Sample dilution needed: {str(self.is_dilution_needed)}")
        logger.info("-------------------------------------")

        self.count_starting_lw_pos()

        if self.is_dilution_needed:
            _, self.dilution_pos = self.sample_dilution()
            logger.info(f"Sample dilution done.")

        dest_positions = self.sample_transfer()
        print("Sample transfer done. Destination positions:", dest_positions)
        logger.info(f"Sample transfer done. Destination positions: {dest_positions}")

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
        self.used_labware_pos = dict.fromkeys(self.used_labware_pos, 0) # reset dict

        # General
        self.n_samples = external.a280_n_samples.get() # amount of samples for the sample transfer
        self.sample_concentration = float(external.a280_concentration.get()) # volume (uL) to transfer to each well
        self.sample_lw_origin = external.a280_lw_origin.get() # origin labware of samples

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
        self.csv_files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\8. A280' # network path where all the files will be saved in.
        self.sample_dilution_file_name = r"\1. Sample dilutions - "
        self.sample_transfer_file_name = r"\1. Sample transfer - "
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions 

        # Sample transfer parameters
        self.n_samples = 0 # amount of samples for the sample transfer
        self.sample_concentration = 100 # initial concentration in mg/mL
        self.concentration_limit = 100 # mg/mL. If it is more than this, we need to dilute
        self.sample_lw_origin = "" # origin labware of samples
        self.sample_lw_dest = "soloVPE cuvettes" # destination labware of samples
        self.sample_diluted_positions = [0] # positions where the diluted samples end up

        self.buffer_lw_pos = ("buffer lw", "x") # buffer labware and position if dilution is needed


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
            for i in range(0, self.n_samples):
                self.next_labware_pos(LabwareNames[self.sample_lw_origin])
  


    def sample_dilution(self):
        """
        Dilute samples from labware origin to Eppendorf tubes.
        """
        
        
        csv_number = 1 # # to name generated files sequentially
        csv_data_sample = []
        csv_data_buffer = []

        sample_volume_to_transfer = 125 # uL
        buffer_volume_per_sample = 375 # uL

        buffer_total_volume = buffer_volume_per_sample * self.n_samples
        # calculate buffer labware depending in the volume used

        # buffer_lw, buffer_pos = dilution_position_def("Eppendorf", self.next_labware_pos("Eppendorf"), 1) # buffer is placed in Eppendorf tube
        buffer_lw, buffer_pos = dilution_position_def(find_best_container(buffer_total_volume/1000), self.next_labware_pos(find_best_container(buffer_total_volume)), 1) # buffer is placed in Eppendorf tube
        self.buffer_lw_pos = (buffer_lw, buffer_pos)

        LabSource, SourceWell = dilution_position_def(self.sample_lw_origin, 1, self.n_samples) # samples are always placed in positions 1..n_samples
        LabDest, DestWell = dilution_position_def("Eppendorf", self.used_labware_pos["Eppendorf"] + 1, self.n_samples)

        for j in range(self.n_samples):
            csv_data_sample.append(
            {
                'LabSource': LabSource[j],
                'SourceWell': SourceWell[j],
                'LabDest': LabDest[j],
                'DestWell': DestWell[j],
                'Volume': sample_volume_to_transfer
            }
            )
            
            csv_data_buffer.append(
            {
                'LabSource': buffer_lw[0], # index 0 because
                'SourceWell': buffer_pos[0],
                'LabDest': LabDest[j],
                'DestWell':  DestWell[j],
                'Volume': buffer_volume_per_sample
            }
            )

            self.next_labware_pos("Eppendorf") # to keep track of used labware positions

        path = self.csv_files_path + self.sample_dilution_file_name + str(csv_number) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)
        path = self.csv_files_path + self.sample_dilution_file_name + str(csv_number + 1) + ".csv"
        pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False)
        csv_number = csv_number + 2

        return DestWell
    


    def sample_transfer(self):
        """
        Transfer samples to cuvette plate.
        """

        
        if self.sample_concentration >= self.concentration_limit:
            self.sample_lw_origin = "Eppendorf"
            LabSource, SourceWell = dilution_position_def(self.sample_lw_origin, self.used_labware_pos[self.sample_lw_origin] - (self.n_samples - 1), self.n_samples) # samples are always placed in positions 1..n_samples
        
        else:
            LabSource, SourceWell = dilution_position_def(self.sample_lw_origin, 1, self.n_samples) # samples are always placed in positions 1..n_samples
        print("labsource sample transfer:", LabSource)

        csv_number = 1 # # to name generated files sequentially
        csv_data_sample = []

        sample_volume_to_transfer = 100 # uL

        LabDest, DestWell = dilution_position_def(self.sample_lw_dest, 1, self.n_samples) # position starts in 1 because labware has not been used yet

        for j in range(self.n_samples):
            csv_data_sample.append(
            {
                'LabSource': LabSource[j],
                'SourceWell': SourceWell[j],
                'LabDest': LabDest[j],
                'DestWell': DestWell[j],
                'Volume': sample_volume_to_transfer
            }
            )

            self.next_labware_pos(self.sample_lw_origin) # to keep track of used labware positions

        path = self.csv_files_path + self.sample_transfer_file_name + str(csv_number) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)

        return DestWell




    def a280(self):
        """
        Class main method.
        ----------

        Executes all stages of the A280 method step by step and generates CSV files for them.
        """

        self.count_starting_lw_pos()

        if self.sample_concentration >= self.concentration_limit:
            self.sample_diluted_positions = self.sample_dilution()
            print("Sample dilutions done. Positions in Eppendorf:", self.sample_diluted_positions)
            print(f"Buffer labware and position: {self.buffer_lw_pos[0][0]}, {self.buffer_lw_pos[1]}")

        dest_positions = self.sample_transfer()
        print("Sample transfer done. Destination positions:", dest_positions)


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
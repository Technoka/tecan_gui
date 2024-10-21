
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
        self.config_file_name = r"\config.txt"
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions
        self.csv_number = 1 # to keep track of generated CSV files

        # Sample transfer parameters
        self.n_samples = 1 # amount of samples for the sample transfer
        self.sample_initial_concentration = 1
        self.sample_final_concentration = 1 # mg/mL, it is always like this
        self.sample_volume_per_well = 1 # volume (uL) to transfer to each well
        self.sample_lw_origin = "" # origin labware of samples
        self.lw_dest = LabwareNames["Eppendorf"]

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
                self.next_labware_pos(LabwareNames[self.sample_lw_origin])
  

    def sample_dilutions(self):
        """
        Performs the dilutions to get the sample final concentration.

        Parameters
        ----------
        ``initial_sample_transfer``: int
            At the beginning, transfer once this amount of volume (uL) of the samples to the wells, so that for later steps,
            all the volumes of the samples can be taken from here with smaller tips rather than changing tip all the time.

        Outputs
        ----------
            CSV files containing instructions for the Tecan.
        """

        csv_data_init = []
        csv_number = 0 # # to name generated files sequentially
        dest_positions = [] # list to store destination positions used for the final dilution
        
        LabSource, SourceWell = self.dilution_position_def(self.sample_lw_origin, 1, self.n_samples)
        LabDest, DestWell = self.dilution_position_def(self.sample_int_dil_destination, self.used_labware_pos["DeepWell"] + 1, self.n_samples)

            # Initial transfer of sample to deep wells, to do intermediate dilutions
        if self.samples_initial_volume_transfer != 0:
            for j in range(0, self.n_samples):

                # LabSource = self.pos_2_str(self.sample_lw_origin, j+1)
                csv_data_init.append(
                {
                    'LabSource': LabSource[j],
                    'SourceWell': SourceWell[j],
                    'LabDest': LabDest[j],
                    'DestWell': DestWell[j],
                    'Volume': float(self.samples_initial_volume_transfer)
                }
                )
                self.next_labware_pos("DeepWell") # to keep the position updated
                
            path = self.csv_files_path + self.sample_dilutions_csv_name + str(csv_number) + ".csv"
            pd.DataFrame(csv_data_init).to_csv(path, index=False, header=False)
            csv_number = csv_number + 1
        
        for i in range(self.n_sample_dilution_steps):
            csv_data_sample = []
            csv_data_buffer = []

            LabSource, SourceWell = LabDest, DestWell # source of next step is destination of previous one

            if i + 1 == self.n_sample_dilution_steps: # if this is the final dilution step
                LabDest, DestWell = self.dilution_position_def(self.sample_lw_dest, self.used_labware_pos[self.sample_lw_dest] + 1, (self.n_samples * (i+1) + 1))
            else:
                LabDest, DestWell = self.dilution_position_def("DeepWell", self.used_labware_pos["DeepWell"] + 1, (self.n_samples * (i+1) + 1))

            for j in range(self.n_samples):
                csv_data_sample.append(
                {
                    'LabSource': LabSource[j],
                    'SourceWell': SourceWell[j],
                    'LabDest': LabDest[j],
                    'DestWell': DestWell[j],
                    'Volume': float(self.sample_dilution_data["Sample volume"][i])
                }
                )
                
                csv_data_buffer.append(
                {
                    'LabSource': utils.LabwareNames["AssayBuffer"],
                    'SourceWell': int(1),
                    'LabDest': LabDest[j],
                    'DestWell':  DestWell[j],
                    'Volume': float(self.sample_dilution_data["Assay buffer volume"][i])
                }
                )
                if i + 1 == self.n_sample_dilution_steps: # if this is the last dilution step
                    self.next_labware_pos(self.sample_lw_dest)
                    dest_positions.append(self.used_labware_pos[self.sample_lw_dest])
                else:
                    self.next_labware_pos("DeepWell")

            path = self.csv_files_path + self.sample_dilutions_csv_name + str(csv_number) + ".csv"
            pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)
            path = self.csv_files_path + self.sample_dilutions_csv_name + str(csv_number + 1) + ".csv"
            pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False)
            csv_number = csv_number + 2

        # if less than 3 dilutions steps are needed, blank out the remaining CSV files so that the Tecan ignores them basically
        for i in range(csv_number, 6 + 1):
            path = self.csv_files_path + self.sample_dilutions_csv_name + str(csv_number) + ".csv"
            pd.DataFrame(list()).to_csv(path, index=False, header=False) # create empty dataframe and save it into an empty CSV
            csv_number = csv_number + 1


        return dest_positions
    
    
    def general_dilution(self):
        """
        Class main method.
        ----------

        Calls other methods to perform the dilution correctly and generates CSV files for them.
        """

        # Reset parameters
        self.used_labware_pos = dict.fromkeys(self.used_labware_pos, 0)

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

        # General
        self.sample_dilution_data = external.sample_dilution_data
        self.n_sample_dilution_steps = len(self.sample_dilution_data["Assay buffer volume"])

        # Sample
        self.sample_lw_origin = external.optionmenu_1_gd.get()
        self.n_samples = int(external.entry_slider2_gd.get())
        self.buffer_type = str(external.optionmenu_buffer1_gd.get())
        self.sample_lw_dest = external.gd_dil_dest.get()
        
        # self.samples_initial_volume_transfer = external.entry_slider3.get()


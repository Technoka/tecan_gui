
# -----------------------
# SEC-HPLC method class #
# -----------------------

import pandas as pd
import numpy as np
from helper.utils import * # file with helper methods


class sec_HPLCMethod():
    """
    Produces CSV files with all the steps to carry out the Size Exclusion HPLC method in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\9. SEC-HPLC' # network path where all the files will be saved in.
        self.sample_dilution_filename = r"\sample_dilution - "
        self.sample_transfer_filename = r"\sample_transfer - "
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions 

        self.has_detectability_standard = False # only some products have it

        # Sample transfer parameters
        self.n_samples = 1 # amount of samples for the sample transfer
        self.sample_initial_concentration = 1
        self.sample_volume_per_well = 1 # volume (uL) to transfer to each well
        self.sample_lw_origin = "" # origin labware of samples
        self.sample_lw_dest = "" # destination labware of samples
        self.sample_dest_positions = [0] # positions of 384 plate where the diluted samples end up
        
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
             new_values = [False, 10, 20]
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
        Only called if samples need to be diluted. Generates the CSV files for the dilution and transfer (done in same step since there is only 1 dilution step).
        """

        csv_number = 1 # # to name generated files sequentially
        csv_data_sample = []
        csv_data_buffer = []

        sample_volume = sample_dilution_data["injection_volume"]
        total_volume = self.sample_initial_concentration * sample_volume / sample_dilution_data["final_concentration"]
        buffer_volume = total_volume - sample_volume

        LabDest, DestWell = dilution_position_def(self.sample_lw_dest, self.next_labware_pos(self.sample_lw_dest), self.n_samples)

        # sample to dest labware
        LabSource, SourceWell = dilution_position_def(self.sample_lw_origin, 1, self.n_samples) # samples are always placed in positions 1..n_samples
        for j in range(self.n_samples):
            csv_data_sample.append(
            {
                'LabSource': LabSource[j],
                'SourceWell': SourceWell[j],
                'LabDest': LabDest[j],
                'DestWell': DestWell[j],
                'Volume': sample_volume
            })

            self.next_labware_pos(self.sample_lw_origin) # to keep track of used labware positions
        
        # buffer to dest labware
        for j in range(self.n_samples):
            csv_data_buffer.append(
            {
                'LabSource': self.buffer_lw_origin,
                'SourceWell': 1,
                'LabDest': LabDest[j],
                'DestWell': DestWell[j],
                'Volume': buffer_volume
            })

            self.next_labware_pos(self.sample_lw_origin) # to keep track of used labware positions


        path = self.files_path + self.sample_dilution_filename + str(csv_number) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)
        path = self.files_path + self.sample_dilution_filename + str(csv_number + 1) + ".csv"
        pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False)
        csv_number += 2

        return DestWell


    def sample_transfer(self, sample_dilution_data):
        """
        Transfer samples to vials.
        """

        LabSource, SourceWell = dilution_position_def(self.sample_lw_origin, 1, self.n_samples) # samples are always placed in positions 1..n_samples
        print("labsource sample transfer:", LabSource)

        csv_number = 1 # # to name generated files sequentially
        csv_data_sample = []

        sample_volume_to_transfer = sample_dilution_data["injection_volume"]

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

        path = self.files_path + self.sample_transfer_filename + str(csv_number) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)

        return DestWell


    def sec_HPLC(self):
        """
        Class main method.
        ----------

        Executes all stages of the Size Exclusion HPLC method step by step and generates CSV files for them.
        """

        logger.info(f"has_detectability_standard: {str(self.has_detectability_standard)}")
        logger.info("-------------------------------------")
        logger.info(f"N. of samples: {self.n_samples}")
        logger.info(f"Samples initial labware: {self.sample_lw_origin}")
        logger.info(f"Samples destination labware: {self.sample_lw_dest}")
        logger.info(f"Samples initial concentration: {self.sample_initial_concentration} mg/mL")
        logger.info("-------------------------------------")

        self.count_starting_lw_pos()

        sample_dilution_data = self.is_sample_dilution_needed()
        print("Sample dilution data:", sample_dilution_data)
        logger.info(f"Sample dilution needed: {sample_dilution_data['sample_dilution_needed']}")

        if sample_dilution_data["sample_dilution_needed"] == True:
            self.sample_dilution(sample_dilution_data)
            logger.info(f"Sample dilutions and transfer done.")

        else:
            self.sample_transfer(sample_dilution_data)
            logger.info(f"Sample transfer done.")
        
        logger.info(f"Method finished successfully.")

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
        

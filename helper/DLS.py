
# -----------------------
# DLS method class      #
# -----------------------

import pandas as pd
import numpy as np
from helper.utils import * # file with helper methods


class DLSMethod():
    """
    Produces CSV files with all the steps to carry out the Dynamic Light Scattering (DLS) method in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\1. DLS' # network path where all the files will be saved in.
        self.csv_filename = r"\transfer - "
        self.config_file_name = r"\config.txt"
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions
        self.csv_number = 1 # to keep track of generated CSV files

        # Sample transfer parameters
        self.n_samples = 1 # amount of samples for the sample transfer
        self.sample_initial_concentration = 1
        self.sample_volume_per_well = 35 # volume (uL) to transfer to each well
        self.sample_lw_origin = "" # origin labware of samples
        self.lw_dest = LabwareNames["384_Well"]
        self.reagents_pos = {} # positions of 384 plate where the reagents end up

        self.sample_final_concentration = 5 # mg/mL, it is always like this
        self.sample_transfer_volume = 35 # uL, always like this, it is the same for sst and blank

        # Buffer parameters
        self.buffer_lw_origin = LabwareNames["GeneralBuffer"] # origin labware of buffer, hard coded for now

        # Standards parameters
        self.blank_transfer_volume = 1000


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
  

    def is_sample_dilution_needed(self):
        """
        Calculates if the samples need to be diluted or not.
        
        Returns
        ----------
        bool
            True or False depending if the samples have to be diluted
        """

        if self.sample_initial_concentration > self.sample_final_concentration:
            logger.info(f"Sample dilution needed: True. From {self.sample_initial_concentration} mg/mL to {self.final_concentration} mg/mL.")
            return True
        else:
            logger.info(f"Sample dilution needed: False")
            return False


    def sample_dilution(self, sample_dilution_data):
        """
        Only called if samples need to be diluted. Generates the CSV files for the dilution and transfer (done in same step since there is only 1 dilution step).
        """

        # self.csv_number = 1 # # to name generated files sequentially
        csv_data_sample = []
        csv_data_buffer = []

        # sample_volume = sample_dilution_data["injection_volume"]
        # total_volume = self.sample_initial_concentration * sample_volume / sample_dilution_data["final_concentration"]
        # buffer_volume = total_volume - sample_volume

        # labware dest is the same for samples and buffer: dilution done in only 1 step
        LabDest, DestWell = dilution_position_def(self.lw_dest, self.next_labware_pos(self.lw_dest), self.n_samples)
        total_volume = 1000

        # if samples have to be diluted
        if sample_dilution_data["sample_dilution_needed"] == True:
            sample_volume, buffer_volume = calculate_dilution_parameter(self.sample_initial_concentration, sample_dilution_data["final_concentration"], None, total_volume)

            # buffer to dest labware - only if samples have to be diluted we add buffer
            for j in range(self.n_samples):
                csv_data_buffer.append(
                {
                    'LabSource': self.buffer_lw_origin,
                    'SourceWell': 1,
                    'LabDest': LabDest[j],
                    'DestWell': DestWell[j],
                    'Volume': buffer_volume
                })
                
                # should be buffer in any case??? not sample? plus buffer is in 100mL reservoir so pos doesnt matter, it is always 1
                # self.next_labware_pos(self.sample_lw_origin) # to keep track of used labware positions

        # sample to dest labware
        LabSource, SourceWell = dilution_position_def(self.sample_lw_origin, 1, self.n_samples) # samples are always placed in positions 1..n_samples

        # if sample_dilution_data["sample_dilution_needed"] == False:
        #     sample_volume = total_volume # as they don't have to be diluted, the volume transfered should be the total one

        for j in range(self.n_samples):
            csv_data_sample.append(
            {
                'LabSource': LabSource[j],
                'SourceWell': SourceWell[j],
                'LabDest': LabDest[j],
                'DestWell': DestWell[j],
                'Volume': sample_volume if sample_dilution_data["sample_dilution_needed"] else total_volume
            })

            self.next_labware_pos(self.sample_lw_origin) # to keep track of used labware positions


        path = self.files_path + self.csv_filename + str(self.csv_number) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)

        # if less than 3 dilutions steps are needed, blank out the remaining CSV files so that the Tecan ignores them basically
        path = self.files_path + self.csv_filename + str(self.csv_number + 1) + ".csv"
        if sample_dilution_data["sample_dilution_needed"] == True:
            pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False)
        else: # if dilution not needed, blank buffer csv so that Tecan ignores it
            pd.DataFrame(list()).to_csv(path, index=False, header=False) # create empty dataframe and save it into an empty CSV
        self.csv_number += 2

        return DestWell

    def calculate_pump_labware_positions(self):
        """
        Calculate well positions of SST, blank and samples for the 384 well plate.

        Returns
        --------
        Dictionary containing well positions.

        Example
        --------
        >>> self.sample_eppendorf_positions = [3,4,5,6]
            calculate_pump_labware_positions()
        {'sst': [1, 9, 17],
        'blank': [2, 10, 18],
        'sample_pos': [[3, 11, 19], [4, 12, 20], [5, 13, 21], [6, 14, 22]]}

        """

        sst_pos = []
        blank_pos = []
        sample_pos = [[]]
        
        sst_pos.append(get_deep_well_pos(1, plate_type=384, sample_direction="horizontal", sample_transfer="triplicate")) # always in first place
        blank_pos.append(get_deep_well_pos(2, plate_type=384, sample_direction="horizontal", sample_transfer="triplicate")) # always in second place

        # Sample positions
        samples_per_block = 8 # fixed. number of triplicate vertical spaces in a 96 well plate.

        for sample in range(self.n_samples):
            sample_pos.append(get_deep_well_pos(2+sample, plate_type=384, sample_direction="horizontal", sample_transfer="triplicate"))

        final_pos = {"pos_ctr_pos": sst_pos,
                     "neg_ctr_pos": blank_pos,
                     "samples_pos": sample_pos}

        self.reagents_pos =  final_pos

        logger.debug(f"SST wells: {sst_pos}")
        logger.debug(f"Blank wells: {blank_pos}")
        logger.debug(f"Sample wells: {sample_pos}")

        return final_pos
    

    def standards_transfer(self):
        """
        Generates files for the transfer of blanks, reference material, detectability standard (if needed) and standards to the vials.

        """

        # We skip first vial because it is transfered manually (MW conditioning)
        self.next_labware_pos(self.lw_dest) # to keep track of used labware positions

        # csv_number = 1 # # to name generated files sequentially
        csv_data_sample = []
        csv_data_buffer = []

        # blank (just mobile phase)
        LabDest, DestWell = dilution_position_def(LabwareNames[self.lw_dest], self.next_labware_pos(self.lw_dest), 1)
        csv_data_buffer.append(
            {
                'LabSource': self.buffer_lw_origin,
                'SourceWell': 1,
                'LabDest': LabDest[0],
                'DestWell': DestWell[0],
                'Volume': self.blank_transfer_volume
            })
        
        # We skip third vial because it is transfered manually (MW SST)
        self.next_labware_pos(self.lw_dest) # to keep track of used labware positions

        if self.has_detectability_standard:
            detectability_standard_dest = self.next_labware_pos(self.lw_dest) # we save this position for later

        # reference material (with dilution if needed)
        PosCtrLabDest, PosCtrDestWell = self.pos_ctr_dilution()
        
        if self.has_detectability_standard:
            self.detectability_standard_dilution(detectability_standard_dest, PosCtrLabDest, PosCtrDestWell)

        
        path = self.files_path + self.csv_filename + str(self.csv_number) + ".csv"
        pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False)
        self.csv_number += 1


    def generate_config_file(self):
        """
        Generates the config file for the current run.
        """

        # If there are repeated keys in the dictionary, the last one and its value is the dominant one !!!

        config_parameters = {"n_steps": self.csv_number - 1 # we remove 1 because it is already added beforehand
                     }

        with open(self.files_path + self.config_file_name, 'w') as file:
            # Write the keys
            keys = ";".join(config_parameters.keys())
            file.write(keys + ";\n")
            
            # Write the values
            values = ";".join(map(str, config_parameters.values()))
            file.write(values + ";\n")


    def DLS(self):
        """
        Class main method.
        ----------

        Executes all stages of the Dynamic Light Scattering (DLS) method step by step and generates CSV files for them.
        """
        # Reset parameters
        self.used_labware_pos = dict.fromkeys(self.used_labware_pos, 0) # reset dict
        self.csv_number = 1

        logger.info("-------------------------------------")
        logger.info(f"N. of samples: {self.n_samples}")
        logger.info(f"Samples initial labware: {self.sample_lw_origin}")
        logger.info(f"Samples destination labware: {self.lw_dest}")
        logger.info(f"Samples initial concentration: {self.sample_initial_concentration} mg/mL")
        logger.info("-------------------------------------")

        self.count_starting_lw_pos()

        ### Method functions

        self.generate_config_file()
        logger.info("Config file generated.")
        
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
        self.csv_number = 1

        # Sample
        self.n_samples = external.DLS_n_samples.get() # amount of samples for the sample transfer
        self.sample_lw_origin = external.DLS_sample_lw_origin.get() # origin labware of samples
        self.sample_initial_concentration = int(external.DLS_sample_initial_concentration.get()) # origin labware of samples
        

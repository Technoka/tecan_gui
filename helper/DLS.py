
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

    def __init__(self, debug=False):
        # General parameters
        self.DEBUG = debug

        self.files_path = r"L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\0. Debug" if self.DEBUG else r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\1. DLS' # network path where all the files will be saved in.
        self.csv_filename = r"\transfer - "
        self.sample_dil_csv_filename = r"\sample_dilution - "
        self.config_file_name = r"\config.txt"
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions
        self.csv_number = 1 # to keep track of generated CSV files

        # Sample transfer parameters
        self.n_samples = 1 # amount of samples for the sample transfer
        self.sample_initial_concentration = 1
        self.sample_volume_per_well = 35 # volume (uL) to transfer to each well
        self.sample_lw_origin = "" # origin labware of samples
        self.lw_dest = LabwareNames["384 Well DLS"]
        self.reagents_pos = {} # positions of 384 plate where the reagents end up
        self.sample_dilution_lw = LabwareNames["Eppendorf"] # labware where the sample dilutions will be done in case they are needed.

        self.sample_final_concentration = 5 # mg/mL, it is always like this
        self.sample_transfer_volume = 35 # uL, always like this, it is the same for sst and blank

        # Buffer parameters
        self.buffer_lw_origin = LabwareNames["GeneralBuffer"] # origin labware of buffer, hard coded for now

        # Standards parameters
        self.sst_lw_origin = LabwareNames["Falcon15"]


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
            logger.info(f"Sample dilution needed: True. From {self.sample_initial_concentration} mg/mL to {self.sample_final_concentration} mg/mL.")
            return True
        else:
            logger.info(f"Sample dilution needed: False")
            return False


    def sample_dilution(self):
        """
        Only called if samples need to be diluted. Generates the CSV files for the dilution and transfer (done in same step since there is only 1 dilution step).
        """

        # self.csv_number = 1 # # to name generated files sequentially
        csv_data_sample = []
        csv_data_buffer = []

        total_volume = 500

        # if samples have to be diluted
        sample_volume, buffer_volume = calculate_dilution_parameter(self.sample_initial_concentration, self.sample_final_concentration, None, total_volume)

        # sample to dest labware
        LabSource, SourceWell = dilution_position_def(self.sample_lw_origin, 1, self.n_samples) # samples are always placed in positions 1..n_samples
        # labware dest is the same for samples and buffer: dilution done in only 1 step
        LabDest, DestWell = dilution_position_def(self.sample_dilution_lw, self.next_labware_pos(self.sample_dilution_lw), self.n_samples)
        

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

            csv_data_buffer.append(
            {
                'LabSource': self.buffer_lw_origin,
                'SourceWell': 1,
                'LabDest': LabDest[j],
                'DestWell': DestWell[j],
                'Volume': buffer_volume
            })
            

        path = self.files_path + self.sample_dil_csv_filename + str(1) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)

        path = self.files_path + self.sample_dil_csv_filename + str(2) + ".csv"
        pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False)

        return DestWell

    def calculate_well_positions(self):
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
        sample_pos = []
        
        sst_pos.append(get_deep_well_pos(1, plate_type=384, sample_direction="horizontal", sample_transfer="triplicate")) # always in first place
        blank_pos.append(get_deep_well_pos(2, plate_type=384, sample_direction="horizontal", sample_transfer="triplicate")) # always in second place

        # Sample positions
        for sample in range(1, self.n_samples+1):
            sample_pos.append(get_deep_well_pos(2+sample, plate_type=384, sample_direction="horizontal", sample_transfer="triplicate"))

        final_pos = {"sst": sst_pos,
                     "blank": blank_pos,
                     "sample": sample_pos}

        self.reagents_pos =  final_pos

        logger.debug(f"SST wells: {sst_pos}")
        logger.debug(f"Blank wells: {blank_pos}")
        logger.debug(f"Sample wells: {sample_pos}")

        return final_pos
    

    def standards_transfer(self):
        """
        Generates files for the transfer of SST, blanks and samples to the 384 well plate.

        """

        # SST transfer
        path = self.files_path + self.csv_filename + str(self.csv_number) + ".gwl"
        LabSource, SourceWell = dilution_position_def(self.sst_lw_origin, self.next_labware_pos(self.sst_lw_origin), 1)
        n_multi_dispense = 3
        (min_pos, max_pos, excluded_pos) = get_reag_dist_positions(self.reagents_pos["sst"][0])
        generate_reagent_distribution_gwl(path, "w", LabSource[0], self.lw_dest, SourceWell[0], SourceWell[0], min_pos, max_pos, self.sample_volume_per_well, 1, n_multi_dispense, excluded_pos)    
        self.csv_number += 1        
        
        # blank transfer
        path = self.files_path + self.csv_filename + str(self.csv_number) + ".gwl"
        (min_pos, max_pos, excluded_pos) = get_reag_dist_positions(self.reagents_pos["blank"][0])
        generate_reagent_distribution_gwl(path, "w", self.buffer_lw_origin, self.lw_dest, 1, 1, min_pos, max_pos, self.sample_volume_per_well, 1, n_multi_dispense, excluded_pos)   
        self.csv_number += 1                 


    def sample_transfer(self):
        """
        Dilutes samples if needed, and then performs the sample trasnfer to 384 plate.
        
        """

        # default, if sample dilution not needed
        LabSource = self.sample_lw_origin

        if self.is_sample_dilution_needed():
            self.sample_dilution()
            if self.sample_lw_origin == "Eppendorf":
                LabSource = "1x24 Eppendorf Tube Runner no Tubes[001]" # if dilution needed, update parameter
            elif self.sample_lw_origin == "FakeFalcon15":
                LabSource = "1x16 16mm Tube Runner No Tubes[001]" # if dilution needed, update parameter



        n_multi_dispense = 3
        source_pos_start = 1

        # samples transfer
        if self.sample_lw_origin == self.sample_dilution_lw: # if samples come in the same labwware type than the dilution labware, add to starting positions the n_samples
            source_pos_start += self.n_samples

        # for i, sample_triplicate in enumerate(self.reagents_pos["sample"]):
        path = self.files_path + self.csv_filename + str(self.csv_number) + ".gwl"
        (min_pos, max_pos, excluded_pos) = get_reag_dist_positions(flatten(self.reagents_pos["sample"]))
        # mode = "w" if i == 0 else "a"
        # generate_reagent_distribution_gwl(path, mode, LabSource, self.lw_dest, 1, self.n_samples, min_pos, max_pos, self.sample_volume_per_well, 1, n_multi_dispense, excluded_pos)  
        generate_sample_transfer_gwl(path, "w", LabSource, self.lw_dest, source_pos_start, source_pos_start + self.n_samples-1, min_pos, max_pos, self.sample_volume_per_well, 1, n_multi_dispense, self.n_samples, 3, 0, 1, excluded_pos)

        self.csv_number += 1  


        # sample transfer


    def generate_config_file(self):
        """
        Generates the config file for the current run.
        """

        # If there are repeated keys in the dictionary, the last one and its value is the dominant one !!!

        config_parameters = {"n_steps": self.csv_number - 1, # we remove 1 because it is already added beforehand
                             "sample_dilution_needed": str(self.is_sample_dilution_needed())
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
        self.calculate_well_positions()

        self.standards_transfer()
        logger.info("Standards transfer done.")

        self.sample_transfer()
        logger.info("Sample transfer done.")

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
        

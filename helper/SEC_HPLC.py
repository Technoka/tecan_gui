
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
        self.std_transfer_filename = r"\std_transfer - "
        self.pos_ctr_dilution_filename = r"\pos_ctr_dilution - "
        self.det_std_dilution_filename = r"\det_std - "
        self.config_file_name = r"\config.txt"
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions
        self.csv_filename = r"\transfer - "
        self.csv_number = 1 # to keep track of generated CSV files

        self.has_detectability_standard = False # only some products have it

        # Sample transfer parameters
        self.n_samples = 1 # amount of samples for the sample transfer
        self.pos_ctr_initial_concentration = 1
        self.pos_ctr_final_concentration = 10 # hard-coded, as in TMD document
        self.sample_initial_concentration = 1
        self.sample_volume_per_well = 1 # volume (uL) to transfer to each well
        self.sample_lw_origin = "" # origin labware of samples
        self.lw_dest = "2mL Vial" # # 2 options: 2mL Vial, 96-well plate, vial by default
        self.sample_dest_positions = [0] # positions of 384 plate where the diluted samples end up

        # Pos ctr parameters
        self.pos_ctr_lw_origin = ""
        
        # Buffer parameters
        self.buffer_lw_origin = LabwareNames["Mobile Phase"] # origin labware of buffer, hard coded for now

        # Standards parameters
        self.blank_transfer_volume = 2000


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
             final_concentration = 9.99 # ask nicolas
             
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

        # self.csv_number = 1 # # to name generated files sequentially
        csv_data_sample = []
        csv_data_buffer = []

        # sample_volume = sample_dilution_data["injection_volume"]
        # total_volume = self.sample_initial_concentration * sample_volume / sample_dilution_data["final_concentration"]
        # buffer_volume = total_volume - sample_volume

        # labware dest is the same for samples and buffer: dilution done in only 1 step
        LabDest, DestWell = dilution_position_def(LabwareNames[self.lw_dest], self.next_labware_pos(self.lw_dest), self.n_samples)
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

    
    def pos_ctr_dilution(self):
        """
            Checks if the reference material has to be diluted, and if so, performs the calculations and generates the required files.
        """

        # pos ctr concentration is already the required one
        if self.pos_ctr_initial_concentration == self.pos_ctr_final_concentration:
            logger.info(f"Reference material has already desired final concentration of {self.pos_ctr_final_concentration} mg/mL. No dilution required.")
        else:
            print(f"Reference material dilution needed. From {self.pos_ctr_initial_concentration} mg/mL to {self.pos_ctr_final_concentration} mg/mL")
            logger.info(f"Reference material dilution needed. From {self.pos_ctr_initial_concentration} mg/mL to {self.pos_ctr_final_concentration} mg/mL")


        # csv_number = 1 # # to name generated files sequentially
        csv_data_sample = []
        csv_data_buffer = []

        total_volume = 1000 # 1000uL total volume 
        sample_volume, buffer_volume = calculate_dilution_parameter(self.pos_ctr_initial_concentration, self.pos_ctr_final_concentration, None, total_volume)

        LabSource, SourceWell = dilution_position_def(LabwareNames[self.pos_ctr_lw_origin], self.next_labware_pos(self.pos_ctr_lw_origin), 1)
        LabDest, DestWell = dilution_position_def(LabwareNames[self.lw_dest], self.next_labware_pos(self.lw_dest), 1)
        
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

        path = self.files_path + self.csv_filename + str(self.csv_number) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)
        path = self.files_path + self.csv_filename + str(self.csv_number + 1) + ".csv"
        pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False)
        self.csv_number += 2

        return LabDest, DestWell


    def detectability_standard_dilution(self, detectability_standard_dest, PosCtrLabDest, PosCtrDestWell):
        """
        Performs detectability standard dilution starting from RM one.
        """

        # csv_number = 1
        csv_data_sample = []
        csv_data_buffer = []

        total_volume = 1000 # 1000uL total volume 
        sample_volume, buffer_volume = calculate_dilution_parameter(self.pos_ctr_final_concentration, 0.1, None, total_volume)

        LabDest, DestWell = dilution_position_def(LabwareNames[self.lw_dest], detectability_standard_dest, 1)
        # LabDest, DestWell = self.lw_dest, detectability_standard_dest

        # sample to dest labware
        # LabSource, SourceWell = dilution_position_def(self.sample_lw_origin, 1, self.n_samples) # samples are always placed in positions 1..n_samples
        csv_data_sample.append(
        {
            'LabSource': PosCtrLabDest[0],
            'SourceWell': PosCtrDestWell[0],
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


        path = self.files_path + self.csv_filename + str(self.csv_number) + ".csv"
        pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)
        path = self.files_path + self.csv_filename + str(self.csv_number + 1) + ".csv"
        pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False)
        self.csv_number += 2


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

        config_parameters = {"has_detectability_standard": str(self.has_detectability_standard),
                             "n_steps": self.csv_number - 1 # we remove 1 because it is already added beforehand
                     }

        with open(self.files_path + self.config_file_name, 'w') as file:
            # Write the keys
            keys = "; ".join(config_parameters.keys())
            file.write(keys + ";\n")
            
            # Write the values
            values = "; ".join(map(str, config_parameters.values()))
            file.write(values + ";\n")


    def sec_HPLC(self):
        """
        Class main method.
        ----------

        Executes all stages of the Size Exclusion HPLC method step by step and generates CSV files for them.
        """
        # Reset parameters
        self.used_labware_pos = dict.fromkeys(self.used_labware_pos, 0) # reset dict
        self.csv_number = 1

        logger.info(f"has_detectability_standard: {str(self.has_detectability_standard)}")
        logger.info("-------------------------------------")
        logger.info(f"N. of samples: {self.n_samples}")
        logger.info(f"Samples initial labware: {self.sample_lw_origin}")
        logger.info(f"Samples destination labware: {self.lw_dest}")
        logger.info(f"Samples initial concentration: {self.sample_initial_concentration} mg/mL")
        logger.info("-------------------------------------")

        self.count_starting_lw_pos()

        self.standards_transfer()
        logger.info(f"Standards transfer dilutions done.")

        sample_dilution_data = self.is_sample_dilution_needed()
        print(f"Sample dilution needed: {sample_dilution_data['sample_dilution_needed']}. From {self.sample_initial_concentration} mg/mL to {sample_dilution_data['final_concentration']} mg/mL.")
        logger.info(f"Sample dilution needed: {sample_dilution_data['sample_dilution_needed']}. From {self.sample_initial_concentration} mg/mL to {sample_dilution_data['final_concentration']} mg/mL.")

        self.sample_dilution(sample_dilution_data)
        logger.info(f"Sample dilutions and transfer done.")

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
        self.n_samples = external.sec_HPLC_n_samples.get() # amount of samples for the sample transfer
        self.sample_lw_origin = external.sec_HPLC_sample_lw_origin.get() # origin labware of samples
        self.sample_initial_concentration = int(external.sec_HPLC_sample_initial_concentration.get()) # origin labware of samples
        self.lw_dest = external.sec_HPLC_lw_dest.get() # origin labware of samples
        
        # Pos Ctr
        self.pos_ctr_lw_origin = external.sec_HPLC_pos_ctr_lw_origin.get() # origin labware of samples
        self.pos_ctr_initial_concentration = int(external.sec_HPLC_pos_ctr_initial_concentration.get())
        

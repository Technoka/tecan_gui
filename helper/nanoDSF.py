
# -----------------------
# nano DSF method class #
# -----------------------

import pandas as pd
import numpy as np
from helper.utils import * # file with helper methods
from math import ceil


class nanoDSFMethod():
    """
    Produces CSV files with all the steps to carry out the nano DSF method in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\7. nanoDSF' # network path where all the files will be saved in.
        self.gwl_sample_transfer = r"\sample_transfer"
        self.gwl_bsa_transfer = r"\bsa_transfer"
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions 
        self.config_file_name = r"\config.txt"

        # Sample transfer parameters
        self.n_samples = 0 # amount of samples for the sample transfer
        self.sample_volume_per_well = 20 # volume (uL) to transfer to each well
        self.sample_triplicates = False
        self.sample_lw_origin = "" # origin labware of samples
        self.sample_lw_dest = "384 Well" # destination labware of samples
        self.sample_dest_positions = [0] # positions of 384 plate where the diluted samples end up

        self.add_BSA = False # if BSA has to be added
        self.BSA_wells = [] # wells in 384 well plate where BSA has to be added

        self.BSA_lw = "BSA tube" # origin labware where BSA tube is placed on. Fixed position.
        self.starting_row_pos = 1 # the row in the 384 well plate where you want to start the transfer


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

        self.next_labware_pos(LabwareNames[self.BSA_lw])

        if self.sample_lw_origin in LabwareNames:
            for i in range(0, self.n_samples):
                self.next_labware_pos(LabwareNames[self.sample_lw_origin])
  

    def calculate_deep_well_positions(self):
        """
        Calculate well positions of pos/neg control and samples for the pump labware.

        Returns
        --------
        List containing well positions of samples.

        Example
        --------
        >>> self.n_samples = 6
            calculate_deep_well_positions()
        [[1, 17, 33], [49, 65, 81], [97, 113, 129], [145, 161, 177], [193, 209, 225], [241, 257, 273]]

        """
        
        sample_wells = []
        wells_per_row = 24 # for a 384 well plate
        init_sample_pos = [i for i in range(1, self.n_samples+1)] # initial sample numbers

        # add positions depending to match the wanted starting row
        init_sample_pos = [i + wells_per_row * (self.starting_row_pos - 1) for i in init_sample_pos]
        
        # print("init sample pos after adding:", init_sample_pos)

        # if BSA has to be added, shift well values to leave room to place BSA in the first column of each used row
        if self.add_BSA:
            assert self.sample_triplicates == False, "BSA can only be added if sample transfer is single, not in triplicates."

            index = 0

            # if self.starting_row_pos > 1: # starting row is not top one
            #     1
            

            pos = init_sample_pos

            while (index < len(pos)): # at least the loop is run once

                pos[index:] = [value + 1 for value in pos[index:]] # shift values to the right (+1)

                # increase BSA pos in deep well to match wanted starting row
                # if index == 0 and self.starting_row_pos > 1: # if it is the first time that we enter this loop
                    # pos.insert(index, index + self.starting_row_pos) # insert the well number of the first column of the row
                # else:
                    # pos.insert(index, index+1) # insert the well number of the first column of the row
                # print("index in insert:", index)
                pos.insert(index, index+1) # insert the well number of the first column of the row
                # normal positions, not actual wells
                self.BSA_wells.append(pos[index]) # add newly inserted BSA position to the list
                index += wells_per_row
                # print(f"after INT BSA added positions: {pos}")
            
            # print(f"after BSA added positions: {pos}")
            init_sample_pos = pos # update list with added BSA positions

            # add 
            # if self.starting_row_pos > 1:
            #     self.BSA_wells = [i + self.starting_row_pos - 1 for i in self.BSA_wells]

            # print("bsa wells position not well:", self.BSA_wells)
            # remove BSA wells from init_sample_pos
            init_sample_pos = list(set(init_sample_pos) - set(self.BSA_wells))
            # transfer positions into deep well well numbers
            # print("bsa well pos calc:", self.BSA_wells[0] + wells_per_row * (self.starting_row_pos - 1))
            self.BSA_wells = [get_deep_well_pos(well + wells_per_row * (self.starting_row_pos - 1), 384, sample_direction="horizontal", sample_transfer="single") for well in self.BSA_wells]

        
        # print("init sample pos before sample dest positions:", init_sample_pos)
        for sample in init_sample_pos: # create list from 1 to number of samples

            if self.sample_triplicates:
                sample_wells.append(get_deep_well_pos(sample, 384, sample_direction="horizontal", sample_transfer="tripicate"))
            
            else:
                sample_wells.append(get_deep_well_pos(sample, 384, sample_direction="horizontal", sample_transfer="single"))

        # self.sample_dest_positions = sample_wells # update variable

        # only sample wells, without BSA ones
        logger.debug(f"sample wells: {sample_wells}")
        self.sample_dest_positions = sorted(list(set(sample_wells) - set(self.BSA_wells)))
        print("BSA wells:", self.BSA_wells)
        print("Sample wells:", self.sample_dest_positions)
 
        return sample_wells


    def generate_gwl_file(self, change_tip:bool = False):
        """
        Generates GWL file for the transfer to the 384 well plate.
        
        Parameters
        ----------
        ``change_tip`` : bool
            True if tips should be changed for every sample, False to just flush tips.

        """

        # Sample transfer
        output_file_path = self.files_path + self.gwl_sample_transfer + ".gwl"
        n_diti_reuses = 1 # no reuse
        n_multi_dispense = 1 # no multi dispense
        sample_direction = 0 # left to right
        replicate_direction = 0 # left to right
        replication_count = 3 if self.sample_triplicates else 1
        # LabSource = LabwareNames["16 weird tube runner"]
        LabSource = LabwareNames["16 falcon15 tube runner"]
        LabDest = LabwareNames["384_Well_Tall"]
        complete_well_list = np.arange(1, max(self.sample_dest_positions) + 1) # list with all wells from 1 to the max sample pos

        if self.add_BSA:
            excluded_pos = list(set(complete_well_list) - set(self.sample_dest_positions) - set(self.BSA_wells))
        else:
            excluded_pos = list(set(complete_well_list) - set(self.sample_dest_positions))

        sample_origin_pos = list(i for i in range(1, self.n_samples + 1))
        # print("sample labware pos:", sample_origin_pos)

        generate_sample_transfer_gwl(output_file_path, "w", pos_2_str(LabSource, 1), LabDest, sample_origin_pos[0], sample_origin_pos[-1], min(self.sample_dest_positions), max(self.sample_dest_positions), self.sample_volume_per_well, n_diti_reuses, n_multi_dispense, self.n_samples, replication_count, sample_direction, replicate_direction, excluded_positions=excluded_pos)
            

        # BSA transfer
        if self.add_BSA:
            output_file_path = self.files_path + self.gwl_bsa_transfer + ".gwl"
            n_diti_reuses = 12
            n_multi_dispense = 12
            # LabSource = self.BSA_lw
            LabSource = pos_2_str(LabwareNames[self.BSA_lw], 1)
            LabDest = LabwareNames["384_Well_Tall"]

            generate_reagent_distribution_gwl(output_file_path, "w", LabSource, LabDest, 1, 1, min(self.BSA_wells), max(self.BSA_wells), self.sample_volume_per_well, n_diti_reuses, n_multi_dispense, excluded_positions=self.sample_dest_positions)
                
        return
    

    def generate_config_file(self):
        """
        Generates the config file for the current run.
        """

        # If there are repeated keys in the dictionary, the last one and its value is the dominant one !!!

        config_parameters = {"add_BSA": str(self.add_BSA)
                     }

        with open(self.files_path + self.config_file_name, 'w') as file:
            # Write the keys
            keys = "; ".join(config_parameters.keys())
            file.write(keys + ";\n")
            
            # Write the values
            values = "; ".join(map(str, config_parameters.values()))
            file.write(values + ";\n")


    def nanoDSF(self):
        """
        Class main method.
        ----------

        Executes all stages of the nanoDSF method step by step and generates CSV files for them.
        """
        
        logger.info("-------------------------------------")
        logger.info(f"N. of samples: {self.n_samples}")
        logger.info(f"Samples initial labware: {self.sample_lw_origin}")
        logger.info(f"Sample transfer is {'n triplicates' if self.sample_triplicates else 'single'}")
        logger.info(f"Add BSA: {self.add_BSA}")
        logger.info("-------------------------------------")

        logger.info("Starting nanoDSF method calculations")
        self.generate_config_file()
        logger.info("Config file generated.")
        self.count_starting_lw_pos()

        self.calculate_deep_well_positions()

        if self.add_BSA:
            logger.info(f"Well positions of BSA are: {self.BSA_wells}")

        print("Calculated 384 well positions:", self.sample_dest_positions)
        logger.info(f"Calculated deep well positions: {self.sample_dest_positions}")

        self.generate_gwl_file()
        logger.info(f"Generated GWL files.\n\n")
        print("Generated GWL file.")

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
        self.BSA_wells = []

        # General
        self.n_samples = external.nDSF_n_samples.get() # amount of samples for the sample transfer
        self.sample_volume_per_well = int(external.nDSF_volume.get()) # volume (uL) to transfer to each well
        self.sample_lw_origin = external.nDSF_lw_origin.get() # origin labware of samples
        self.sample_triplicates = True if external.nDSF_sample_triplicates.get() == "Triplicate transfer" else False
        self.add_BSA = external.nDSF_add_BSA.get()
        self.starting_row_pos = external.nDSF_starting_row.get()
        # print(f"add bsa: {self.add_BSA}")
        

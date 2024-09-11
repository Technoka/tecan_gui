
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
        init_sample_pos = [i for i in range(1, self.n_samples+1)] # initial sample numbers

        # if BSA has to be added, shift well values to leave room to place BSA in the first column of each used row
        if self.add_BSA:
            assert self.sample_triplicates == False, "BSA can only be added if sample transfer is single, not in triplicates."

            index = 0
            wells_per_row = 24 # for a 384 well plate

            pos = init_sample_pos

            while (index < len(pos)): # at least the loop is run once

                pos[index:] = [value + 1 for value in pos[index:]] # shift values to the right (+1)
                pos.insert(index, index+1) # insert the well number of the first column of the row
                self.BSA_wells.append(get_deep_well_pos(pos[index], 384, sample_direction="horizontal", sample_transfer="single")) # add newly inserted BSA position to the list
                index += wells_per_row
                # print(f"after INT BSA added positions: {pos}")
            
            # print(f"after BSA added positions: {pos}")
            init_sample_pos = pos

        
        for sample in init_sample_pos: # create list from 1 to number of samples

            if self.sample_triplicates:
                sample_wells.append(get_deep_well_pos(sample, 384, sample_direction="horizontal", sample_transfer="tripicate"))
            
            else:
                sample_wells.append(get_deep_well_pos(sample, 384, sample_direction="horizontal", sample_transfer="single"))

        # self.sample_dest_positions = sample_wells # update variable

        # only sample wells, without BSA ones
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
        print("sample labware pos:", sample_origin_pos)

        generate_sample_transfer_gwl(output_file_path, "w", pos_2_str(LabSource, 1), LabDest, sample_origin_pos[0], sample_origin_pos[-1], min(self.sample_dest_positions), max(self.sample_dest_positions), self.sample_volume_per_well, n_diti_reuses, n_multi_dispense, self.n_samples, replication_count, sample_direction, replicate_direction, excluded_positions=excluded_pos)
            

        # BSA transfer
        output_file_path = self.files_path + self.gwl_bsa_transfer + ".gwl"
        n_diti_reuses = 12
        n_multi_dispense = 12
        # LabSource = self.BSA_lw
        LabSource = pos_2_str(LabwareNames[self.BSA_lw], 1)
        LabDest = LabwareNames["384_Well_Tall"]

        generate_reagent_distribution_gwl(output_file_path, LabSource, LabDest, 1, 1, min(self.BSA_wells), max(self.BSA_wells), self.sample_volume_per_well, n_diti_reuses, n_multi_dispense, excluded_positions=self.sample_dest_positions)
                


        return

        # LabDest, DestWell = dilution_position_def("DeepWell", self.next_deep_well_pos(), 1) # define destination labware as deep well

        output_file_path = self.files_path + self.gwl_file_name + ".gwl"

        with open(output_file_path, 'w') as output_file:
            # Read all lines from the input file

            output_lines = []
            
            
            LabSource, SourceWell = dilution_position_def(self.sample_lw_origin, 1, self.n_samples)
            # Extract the values
            for sample in [i for i in range(self.n_samples)]: # create list from 1 to number of samples
                LabDest, _ = dilution_position_def(self.sample_lw_dest, 1, 1) # ignore received position as we already have it in self.sample_dest_positions
                DestWell = self.sample_dest_positions[sample]
                Volume = self.sample_volume_per_well
                
                # Create the three lines for the output
                if self.sample_triplicates:
                    a_line = f"A;{LabSource[sample]};;;{SourceWell[sample]};;{Volume*3};;;;\n" # 3x volume to save time
                    d_line_1 = f"D;{LabDest[0]};;;{DestWell[0]};;{Volume};;;;\n"
                    d_line_2 = f"D;{LabDest[0]};;;{DestWell[1]};;{Volume};;;;\n"
                    d_line_3 = f"D;{LabDest[0]};;;{DestWell[2]};;{Volume};;;;\n"
                else:
                    a_line = f"A;{LabSource[sample]};;;{SourceWell[sample]};;{Volume};;;;\n"
                    d_line_1 = f"D;{LabDest[0]};;;{DestWell};;{Volume};;;;\n"

                w_line = "W;\n" if change_tip else "F;\n" # use F to flush tip remaining contents, W to change tips instead of changing tip
                
                # Append the lines to the output lines list
                output_lines.append(a_line)
                output_lines.append(d_line_1)
                if self.sample_triplicates: # if triplicates do 2 more
                    output_lines.append(d_line_2)
                    output_lines.append(d_line_3)
                output_lines.append(w_line)

            output_file.writelines(output_lines)


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
        self.count_starting_lw_pos()

        self.calculate_deep_well_positions()
        print("Calculated 384 well positions:", self.sample_dest_positions)
        logger.info(f"Calculated deep well positions: {self.sample_dest_positions}")

        if self.add_BSA:
            logger.info(f"Well positions of BSA are: {self.BSA_wells}")

        self.generate_gwl_file()
        logger.info(f"Generated GWL files.")
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

        # General
        self.n_samples = external.nDSF_n_samples.get() # amount of samples for the sample transfer
        self.sample_volume_per_well = int(external.nDSF_volume.get()) # volume (uL) to transfer to each well
        self.sample_lw_origin = external.nDSF_lw_origin.get() # origin labware of samples
        self.sample_triplicates = True if external.nDSF_sample_triplicates.get() == "Triplicate transfer" else False
        self.add_BSA = external.nDSF_add_BSA.get()
        print(f"add bsa: {self.add_BSA}")
        


# -----------------------
# nano DSF method class #
# -----------------------

import pandas as pd
import numpy as np
from utils import * # file with helper methods


class nanoDSFMethod():
    """
    Produces CSV files with all the steps to carry out the nano DSF method in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\7. nanoDSF' # network path where all the files will be saved in.
        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions 

        # Sample transfer parameters
        self.n_samples = 0 # amount of samples for the sample transfer
        self.sample_volume_per_well = 20 # volume (uL) to transfer to each well
        self.sample_lw_origin = "" # origin labware of samples
        self.sample_lw_dest = "384 Well" # destination labware of samples
        self.sample_dest_positions = [0] # positions of 384 plate where the diluted samples end up


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
        
        sample_pos = []

        for sample in [i for i in range(1, self.n_samples+1)]: # create list from 1 to number of samples
            sample_pos.append(get_deep_well_pos(sample, 384, sample_direction="horizontal"))

        # final_pos = flatten(sample_pos)

        self.sample_dest_positions = sample_pos # update variable

        return sample_pos


    def generate_gwl_file(self, change_tip:bool = False):
        """
        Generates GWL file for the transfer to the 384 well plate.
        
        Parameters
        ----------
        ``change_tip`` : bool
            True if tips should be changed for every sample, False to just flush tips.

        """

        # LabDest, DestWell = dilution_position_def("DeepWell", self.next_deep_well_pos(), 1) # define destination labware as deep well

        output_file_path = self.files_path + r"\test_gen" + ".gwl"

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
                a_line = f"A;{LabSource[sample]};;;{SourceWell[sample]};;{Volume*3};;;;\n" # 3x volume to save time
                d_line_1 = f"D;{LabDest[0]};;;{DestWell[0]};;{Volume};;;;\n"
                d_line_2 = f"D;{LabDest[0]};;;{DestWell[1]};;{Volume};;;;\n"
                d_line_3 = f"D;{LabDest[0]};;;{DestWell[2]};;{Volume};;;;\n"
                w_line = "W;\n" if change_tip else "F;\n" # use F to flush tip remaining contents, W to change tips instead of changing tip
                
                # Append the lines to the output lines list
                output_lines.append(a_line)
                output_lines.append(d_line_1)
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

        self.count_starting_lw_pos()

        self.calculate_deep_well_positions()
        print("Calculated 384 well positions:", self.sample_dest_positions)

        self.generate_gwl_file()
        print("Generated GWL file.")

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
        self.n_samples = external.nDSF_n_samples.get() # amount of samples for the sample transfer
        self.sample_volume_per_well = external.nDSF_volume.get() # volume (uL) to transfer to each well
        self.sample_lw_origin = external.nDSF_lw_origin.get() # origin labware of samples
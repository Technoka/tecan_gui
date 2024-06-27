
# -----------------------
# General dilution class #
# -----------------------

import pandas as pd
import numpy as np
import utils # file with helper methods


class GeneralDilution():
    """
    Produces CSV files with all the steps to carry out a general dilution in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.csv_files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\5. General Dilution' # network path where all the CSV files will be saved in.
        self.last_eppendorf_pos = -1 # position of the last Eppendorf tube used. Useful so that methods don't use same tube twice.
        self.last_deep_well_pos = -1 # position of the last Deep well position used. Useful so that methods don't use same well twice.
        self.used_labware_pos = {lw: 0 for lw in utils.LabwareNames} # initialize labware positions 

        # CSV file names
        self.sample_dilutions_csv_name = r"\1. Sample dilutions - "

        # dictionaries to store all dilution values
        self.sample_dilution_data = {}

        self.final_dilutions_in_eppendorf = True # if True, will make final dilutions of everything in eppendorf tubes, so that it is much easier for the technician to take them out for the next steps

        # Sample dilution parameters
        self.n_samples = 0 # amount of samples for the sample dilution
        self.n_sample_dilution_steps = 0 # number of sample dilution steps to achieve final concentration
        self.sample_lw_origin = "" # where to perform main sample dilutions (deep welleppendorf)
        self.sample_lw_dest = "" # 
        self.sample_int_dil_destination = "DeepWell" # All intermediate dilutions will be made in Deep Wells, and then final results will be transfered to Eppendorf tubes
        self.samples_initial_volume_transfer = 300 # At the beginning, transfer once this amount of volume (uL) of the samples to the wells, so that for later steps, all the volumes of the samples can be taken from here with smaller tips rather than changing tip all the time.
        self.sample_dest_positions = 0 # positions of Eppendorf tubes where the diluted samples end up

        # Labware names
        self.blocking_buffer_lw_name = "def_blocking" # Blocking Buffer labware

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
            if labware_name in utils.LabwareNames:
                    if (self.used_labware_pos[labware_name] + 1 <= utils.AvailableLabware[labware_name]): # if max pos has not been reached
                        self.used_labware_pos[labware_name] = self.used_labware_pos[labware_name] + 1
                        return self.used_labware_pos[labware_name] # return current one before adding an unit
            else:
                return -1
        except Exception as e:
            return -1


    def next_eppendorf_pos(self):
        """
        Deprecated.


        Adds one to the Eppendorf position used and returns that number.
        If no Eppendorf tubes are available, returns -1.
        """

        if (self.last_eppendorf_pos + 1 <= utils.AvailableLabware.Eppendorf): # if max pos has not been reached
            self.last_eppendorf_pos = self.last_eppendorf_pos + 1
            return self.last_eppendorf_pos - 1 # return current one before adding an unit
        else:
            return -1


    def next_deep_well_pos(self):
        """
        Deprecated.

        Adds one to the Deep Well position used and returns that number.
        If no Deep Well tubes are available, returns -1.
        """

        if (self.last_deep_well_pos + 1 <= self.utils.AvailableLabware.DeepWell): # if max pos has not been reached
            self.last_deep_well_pos = self.last_deep_well_pos + 1
            return self.last_deep_well_pos - 1 # return current one before adding an unit
        else:
            return -1


    def pos_2_str(self, name: str, pos: int):
        """
        Converts name and position number to string format with brackets.

        Parameters
        ----------
        name : str
            Labware name as in TECAN Fluent worktable.
        pos : int
            Position number to be converted.

        Returns
        -------
        new_name : str
            Concatenation of Labware name and its position.
        
        Example
        --------
        >>> pos_2_str("Eppendorf", 3)
        "Eppendorf[003]"

        >>> pos_2_str("Eppendorf", 13)
        "Eppendorf[013]"
        """

        if isinstance(pos, list):
            pos = pos[0]

        if pos < 10:
            new_name = name + "[00"+str(pos)+"]"
        else:
            new_name = name + "[0"+str(pos)+"]"

        return new_name
        

    def dilution_position_def(self, labware_name: str, initial_pos: int, nsamples: int):
        """
        Creates two arrays, for the source labware name and position.

        Parameters
        ----------
        labware_name : str
            Labware name as in TECAN Fluent worktable.
        initial_pos : int
            Labware position/well of the initial sample.
        n_samples : int
            Number of samples used, same as returned array length.

        Returns
        ----------
        Label: array
            Array of the labware names, including square brackets.
        Pos: array
            Array of the list of positions for the labware.
        """


        Label = np.array([])
        Pos = np.array([])
 
        if labware_name in utils.LabwarePlates:
            for i in range(0,nsamples):
                # Label = np.append(Label,['96 Deep Well 2ml[001]']) # labware name is fixed for eppendorf
                Label = np.append(Label,[utils.LabwareNames[labware_name]]) # labware name is fixed for eppendorf
                Pos = np.append(Pos, int(initial_pos+i))

        else:
            for i in range(0,nsamples):
                name = self.pos_2_str(labware_name,initial_pos+i) # the labware name gets updated for eppendorf
                Label = np.append(Label,[name])
                Pos = np.append(Pos, int(1)) # this type of labware only has one position, so it is fixed to 1.

        return Label, Pos.astype(int)
        

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
    

    def count_starting_lw_pos(self):
        """
        Counts the positions of the sample origin labware, so that
        if the destination labware is the same, new tubes are used.
        """

        if self.sample_lw_origin in utils.LabwareNames:

            # if self.sample_lw_origin == "Eppendorf":
            #     for i in range(0, self.n_samples):
            #         self.next_labware_pos(utils.LabwareNames["Eppendorf"])
            # elif self.sample_lw_origin == "Deep well":
            #     for i in range(0, self.n_samples):
            #         self.next_labware_pos(utils.LabwareNames["DeepWell"])

            for i in range(0, self.n_samples):
                self.next_labware_pos(utils.LabwareNames[self.sample_lw_origin])
  
    
    def general_dilution(self):
        """
        Class main method.
        ----------

        Calls other methods to perform the dilution correctly and generates CSV files for them.
        """

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


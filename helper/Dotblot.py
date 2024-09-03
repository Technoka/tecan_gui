
# -----------------------
# Dot Blot method class #
# -----------------------

import pandas as pd
import numpy as np
from helper.utils import * # file with helper methods


class DotblotMethod():
    """
    Produces CSV files with all the steps to carry out the Dot Blot method in the TECAN.
    """

    def __init__(self, debug=False):
        # General parameters
        self.DEBUG = debug

        self.csv_files_path = r"C:\Users\DPerez36\OneDrive - JNJ\Documents\git repos\method outputs\dotblot" if self.DEBUG else r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\3. DotBlot' # network path where all the CSV files will be saved in.

        self.used_labware_pos = {lw: 0 for lw in LabwareNames} # initialize labware positions 

        self.has_2_coatings = False # if method has 2 coating proteins, then all dilutions are doubled (1 for each) and process is more difficult

        # CSV file names
        self.pos_control_csv_name = r"\1. Positive control - "
        self.neg_control_csv_name = r"\2. Negative control - "
        self.sample_dilutions_csv_name = r"\3. Sample dilutions - "
        self.pump_steps_csv_name = r"\4. Pump steps - "
        self.config_file_name = r"\config.txt"

        # dictionaries to store all dilution values
        self.sample_dilution_data = [{}]
        self.coating_protein_dilution_data = [{}]
        self.pos_control_dilution_data = [{}]
        self.neg_control_dilution_data = [{}]

        self.custom_holder_name = "Custom_vial_holder[001]" # name of the 3D printed custom holder in the TECAN software.

        self.final_dilutions_in_eppendorf = True # if True, will make final dilutions of everything in eppendorf tubes, so that it is much easier for the technician to take them out for the next steps

        # Sample dilution parameters
        self.n_samples_main_dilution = 0 # amount of samples for the sample dilution
        self.n_sample_dilution_steps = 0 # number of sample dilution steps to achieve final concentration
        self.main_sample_labware_type = "" # where to perform main sample dilutions (deep well or eppendorf)
        self.main_sample_dil_destination = "DeepWell" # All intermediate dilutions will be made in Deep Wells, and then final results will be transfered to Eppendorf tubes
        self.samples_initial_volume_transfer = 300 # At the beginning, transfer once this amount of volume (uL) of the samples to the wells, so that for later steps, all the volumes of the samples can be taken from here with smaller tips rather than changing tip all the time.
        self.sample_eppendorf_positions = 0 # positions of Eppendorf tubes where the diluted samples end up

        # Coating protein parameters
        self.n_samples_coating_protein = 0 # amount of samples
        self.n_coating_protein_steps = 0 # number of positive control dilution steps to achieve final concentration
        self.coating_protein_vial_type = 0 # type of vial used (1-7)
        self.coating_protein_buffer = "" # name of pos control buffer
                
        # Positive control parameters
        # self.n_samples_pos_control = 0 # amount of samples for the positive control dilution
        self.n_pos_control_steps = 0 # number of positive control dilution steps to achieve final concentration
        # self.pos_control_vial_type = 0 # type of vial used (1-7)
        self.pos_control_vial_posY = "" # A,B,C,D,E position of pos contorl vial inside of custom holder
        self.pos_control_vial_posX = "" # 1,2,3,4,5,6 position of pos contorl vial inside of custom holder
        self.pos_control_buffer = "AssayBuffer" # name of pos control buffer (assay or DPBS)
        self.pos_control_eppendorf_positions = []

        # Negative control parameters
        self.n_neg_control_steps = 0 # number of positive control dilution steps to achieve final concentration
        self.neg_control_vial_posY = "" # A,B,C,D,E position of neg contorl vial inside of custom holder
        self.neg_control_vial_posX = "" # 1,2,3,4,5,6 position of neg contorl vial inside of custom holder
        self.neg_control_buffer = "AssayBuffer" # name of neg control buffer (assay or DPBS)
        self.neg_control_eppendorf_positions = []

        # Labware names
        self.coat_prot_lw_name = "def_coat_prot" # Coating protein labware
        self.blocking_buffer_lw_name = "def_blocking" # Blocking Buffer labware
        self.pos_ctr_diluted_lw_name = "def_pos_ctr" # Positive control labware
        self.neg_ctr_diluted_lw_name = "def_neg_ctr" # Negative control labware
        self.conjugate_lw_name = "def_conjugate" # Conjugate labware
        self.dpbs_lw_name = "def_dpbs" # DPBS labware
        self.pump_lw_name = "dotblot_appr_standalone" # Pump vacuum labware

        # Pump steps
        self.pump_steps_data = {}
        self.n_wells_pump_labware = 96 # number of wells in labware inside pump vacuum area
        self.pump_lw_well_pos = {} # pump labware well positions of different ctr and samples

        # Total volumes needed for the method
        self.total_volumes = {}

        self.dye_volume_per_well = 100 # in uL


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
                logger.error(f"labware_name {labware_name} not found.")
                return -1
        except Exception as e:
            logger.error(f"Exception in next_labware_pos: {e}")
            return -1
        

    def count_starting_lw_pos(self):
        """
        Counts the positions of the sample origin labware, so that
        if the destination labware is the same, new tubes are used.
        """

        if self.main_sample_labware_type in LabwareNames:
            for i in range(0, self.n_samples_main_dilution):
                self.next_labware_pos(LabwareNames[self.main_sample_labware_type])
        

    def positive_control_dilutions(self):
        """
        Performs the dilutions to get the positive control final concentration.

        Parameters
        ----------
        ``mix`` : bool
            If True, a mixing step will be added after each dilution step.

        Outputs
        ----------
            CSV files containing instructions for the Tecan.
        """
        
        initial_pos = 1 # position of the first vial of the pos control
        buffer_labware_name = LabwareNames[self.pos_control_buffer] # Name of Labware in TECAN for the Assay buffer
        eppendorf_positions = [] # to store final eppendorf positions

        # Define custom vial holder labware position depending on the vial position
        if self.pos_control_vial_posX == "A":
            initial_pos = 1
        elif self.pos_control_vial_posX == "B":
            initial_pos = 2
        elif self.pos_control_vial_posX == "C":
            initial_pos = 3
        elif self.pos_control_vial_posX == "D":
            initial_pos = 4
        elif self.pos_control_vial_posX == "E":
            initial_pos = 5

        initial_pos = initial_pos + (int(self.pos_control_vial_posY) - 1) * 5 # add X position
        
        for k in range(len(self.pos_control_dilution_data)): # 1 or 2 times, depending on the coating protein necesities

            csv_number = 1 # to name generated files sequentially
            sample_lab_source = pos_2_str(LabwareNames["Pos_Ctr_Vial"], initial_pos) # initial source of pos control sample
            sample_lab_well = 1 # labware only has 1 well

            # for i in range(self.n_pos_control_steps):
            for i in range(len(self.pos_control_dilution_data[k]["Assay buffer volume"])):
                csv_data_sample = [] # list to store CSV data
                csv_data_buffer = [] # list to store CSV data

                if i + 1 == len(self.pos_control_dilution_data[k]["Assay buffer volume"]): # if this is the final dilution step
                    eppendorf_positions.append(self.used_labware_pos["Eppendorf"])
                    
                    LabDest, DestWell = dilution_position_def("Eppendorf", self.next_labware_pos("Eppendorf"), 1) # define destination labware as eppendorf
                    
                else:
                    LabDest, DestWell = dilution_position_def("DeepWell", self.next_labware_pos("DeepWell"), 1) # define destination labware as deep well

                csv_data_sample.append( # move pos control to dest well
                {
                    'LabSource': sample_lab_source,
                    'SourceWell': sample_lab_well,
                    'LabDest': LabDest[0],
                    'DestWell': DestWell[0],
                    'Volume': float(self.pos_control_dilution_data[k]["Sample volume"][i])
                })

                csv_data_buffer.append( # move buffer to destination well
                {
                    'LabSource': buffer_labware_name,
                    'SourceWell': int(1), # buffer only has 1 big well
                    'LabDest': LabDest[0],
                    'DestWell': DestWell[0],
                    'Volume': float(self.pos_control_dilution_data[k]["Assay buffer volume"][i])
                })
            

                sample_lab_source, sample_lab_well = LabDest[0], DestWell[0] # source of next step is destination of previous one

                # generate CSV files (we separate them so that in the buffer one we can use liquid class for mixing)
                path = self.csv_files_path + self.pos_control_csv_name + f"{k+1} - " + str(csv_number) + ".csv" # path for sample
                pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False) # create dataframe and then CSV file
                path = self.csv_files_path + self.pos_control_csv_name + f"{k+1} - " + str(csv_number + 1) + ".csv" # path for buffer
                pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False) # create dataframe and then CSV file
                csv_number = csv_number + 2

            # if less than 3 dilutions steps are needed, blank out the remaining CSV files so that the Tecan ignores them basically
            for i in range(csv_number, 6 + 1):
                path = self.csv_files_path + self.pos_control_csv_name + f"{k+1} - " + str(csv_number) + ".csv"
                pd.DataFrame(list()).to_csv(path, index=False, header=False) # create empty dataframe and save it into an empty CSV
                csv_number = csv_number + 1
        
        # divide "eppendorf_positions" into sublists of 1 item
        return [eppendorf_positions[i:i + 1] for i in range(0, len(eppendorf_positions), 1)]
    

    def negative_control_dilutions(self):
        """
        Performs the dilutions to get the negative control final concentration.

        Outputs
        ----------
            CSV files containing instructions for the Tecan.
        """
        
        # initial_pos = 1 # position of the first vial of the pos control
        buffer_labware_name = LabwareNames[self.neg_control_buffer] # Name of Labware in TECAN for the Assay buffer
        eppendorf_positions = [] # to store final eppendorf positions

        for k in range(len(self.neg_control_dilution_data)): # 1 or 2 times, depending on the coating protein necesities

            csv_number = 1 # to name generated files sequentially
            sample_lab_source = pos_2_str(LabwareNames["8R_Vial neg_ctr"], 1) # initial source of neg control sample, pos fixed to 1 (left upper-most position)
            sample_lab_well = 1 # hard coded for now, so ALWAYS place negative control vial in first position (top left) of 8R holder

            for i in range(len(self.neg_control_dilution_data[k]["Assay buffer volume"])):
                csv_data_sample = [] # list to store CSV data
                csv_data_buffer = [] # list to store CSV data

                if i + 1 == len(self.neg_control_dilution_data[k]["Assay buffer volume"]): # if this is the final dilution step
                    eppendorf_positions.append(self.used_labware_pos["Eppendorf"])
                    LabDest, DestWell = dilution_position_def("Eppendorf", self.next_labware_pos("Eppendorf"), 1) # define destination labware as eppendorf
                    
                else:
                    LabDest, DestWell = dilution_position_def("DeepWell", self.next_labware_pos("DeepWell"), 1) # define destination labware as deep well

                csv_data_sample.append( # move pos control to dest well
                {
                    'LabSource': sample_lab_source,
                    'SourceWell': sample_lab_well,
                    'LabDest': LabDest[0],
                    'DestWell': DestWell[0],
                    'Volume': float(self.neg_control_dilution_data[k]["Sample volume"][i])
                })

                csv_data_buffer.append( # move buffer to destination well
                {
                    'LabSource': buffer_labware_name,
                    'SourceWell': int(1), # buffer only has 1 big well
                    'LabDest': LabDest[0],
                    'DestWell': DestWell[0],
                    'Volume': float(self.neg_control_dilution_data[k]["Assay buffer volume"][i])
                })
            
                sample_lab_source, sample_lab_well = LabDest[0], DestWell[0] # source of next step is destination of previous one

                # generate CSV files (we separate them so that in the buffer one we can use liquid class for mixing)
                path = self.csv_files_path + self.neg_control_csv_name + f"{k+1} - " + str(csv_number) + ".csv" # path for sample 
                pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False) # create dataframe and then CSV file
                path = self.csv_files_path + self.neg_control_csv_name + f"{k+1} - " + str(csv_number + 1) + ".csv" # path for buffer
                pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False) # create dataframe and then CSV file
                csv_number = csv_number + 2

            # if less than 3 dilutions steps are needed, blank out the remaining CSV files so that the Tecan ignores them basically
            for i in range(csv_number, 6 + 1):
                path = self.csv_files_path + self.neg_control_csv_name + f"{k+1} - " + str(csv_number) + ".csv"
                pd.DataFrame(list()).to_csv(path, index=False, header=False) # create empty dataframe and save it into an empty CSV
                csv_number = csv_number + 1
        
        # divide "eppendorf_positions" into sublists of 1 item
        return [eppendorf_positions[i:i + 1] for i in range(0, len(eppendorf_positions), 1)]
    

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

        eppendorf_positions = [] # list to store positions of eppendorf positions used for the final dilution

        # calculate initial sample epp. positions because it is the same for both dilution groups
        initial_sample_positions = []
        for i in range(1, self.n_samples_main_dilution + 1):
            if self.main_sample_labware_type == "Eppendorf":
                initial_sample_positions.append(self.next_labware_pos("Eppendorf"))                
        
        for k in range(len(self.sample_dilution_data)): # 1 or 2 times, depending on the coating protein necesities
            csv_number = 0 # to name generated files sequentially
            csv_data_init = []

            LabDest, DestWell = dilution_position_def(self.main_sample_dil_destination, self.used_labware_pos["DeepWell"], self.n_samples_main_dilution)

            # Initial transfer of sample to deep wells, so that smaller tips can reach
            for j in range(1, self.n_samples_main_dilution + 1):
                if self.main_sample_labware_type == "Eppendorf":
                    LabSource = pos_2_str(self.main_sample_labware_type, initial_sample_positions[j-1])

                else:
                    LabSource = pos_2_str(self.main_sample_labware_type, j) # sample always comes in a labware with 1 hole (falcon, fakeFalcon, eppendorf, ...) if not we would use dilution_pos_def instead of pos2str

                csv_data_init.append(
                {
                    'LabSource': LabSource,
                    'SourceWell': int(1), # sample always comes in a labware with 1 hole (falcon, fakeFalcon, eppendorf, ...)
                    'LabDest': LabDest[j-1],
                    'DestWell': DestWell[j-1],
                    'Volume': float(self.samples_initial_volume_transfer)
                }
                )
                self.next_labware_pos("DeepWell") # to keep the position updated
                
            path = self.csv_files_path + self.sample_dilutions_csv_name + f"{k+1} - " + str(csv_number) + ".csv"
            pd.DataFrame(csv_data_init).to_csv(path, index=False, header=False)
            csv_number = csv_number + 1

            for i in range(len(self.sample_dilution_data[k]["Assay buffer volume"])):
                csv_data_sample = []
                csv_data_buffer = []

                LabSource, SourceWell = LabDest, DestWell # source of next step is destination of previous one

                if i + 1 == len(self.sample_dilution_data[k]["Assay buffer volume"]): # if this is the final dilution step
                    LabDest, DestWell = dilution_position_def("Eppendorf", self.used_labware_pos["Eppendorf"], (self.n_samples_main_dilution * (i+1) + 1))
                else:
                    LabDest, DestWell = dilution_position_def("DeepWell", self.used_labware_pos["DeepWell"], (self.n_samples_main_dilution * (i+1) + 1))

                for j in range(self.n_samples_main_dilution):
                    csv_data_sample.append(
                    {
                        'LabSource': LabSource[j],
                        'SourceWell': SourceWell[j],
                        'LabDest': LabDest[j],
                        'DestWell': DestWell[j],
                        'Volume': float(self.sample_dilution_data[k]["Sample volume"][i])
                    }
                    )
                    
                    csv_data_buffer.append(
                    {
                        'LabSource': LabwareNames["AssayBuffer"],
                        'SourceWell': int(1),
                        'LabDest': LabDest[j],
                        'DestWell':  DestWell[j],
                        'Volume': float(self.sample_dilution_data[k]["Assay buffer volume"][i])
                    }
                    )
                    if i + 1 == len(self.sample_dilution_data[k]["Assay buffer volume"]): # if this is the last dilution step
                        eppendorf_positions.append(self.used_labware_pos["Eppendorf"])
                        self.next_labware_pos("Eppendorf")

                    else:
                        self.next_labware_pos("DeepWell")

                path = self.csv_files_path + self.sample_dilutions_csv_name + f"{k+1} - " + str(csv_number) + ".csv"
                pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False)
                path = self.csv_files_path + self.sample_dilutions_csv_name + f"{k+1} - " + str(csv_number + 1) + ".csv"
                pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False)
                csv_number = csv_number + 2

            # if less than 3 dilutions steps are needed, blank out the remaining CSV files so that the Tecan ignores them basically
            for i in range(csv_number, 6 + 1):
                path = self.csv_files_path + self.sample_dilutions_csv_name + f"{k+1} - " + str(csv_number) + ".csv"
                pd.DataFrame(list()).to_csv(path, index=False, header=False) # create empty dataframe and save it into an empty CSV
                csv_number = csv_number + 1

        # divide "eppendorf_positions" into sublists every n_samples, to handle it better in later steps
        return [eppendorf_positions[i:i + self.n_samples_main_dilution] for i in range(0, len(eppendorf_positions), self.n_samples_main_dilution)]
    

    def calculate_pump_labware_positions(self):
        """
        Calculate well positions of pos/neg control and samples for the pump labware.

        Returns
        --------
        Dictionary containing well positions of pos and neg control, and samples.

        Example
        --------
        >>> self.sample_eppendorf_positions = [3,4,5,6]
            calculate_pump_labware_positions()
        {'pos_ctr_pos': [1, 9, 17],
        'neg_ctr_pos': [2, 10, 18],
        'sample_pos': [[3, 11, 19], [4, 12, 20], [5, 13, 21], [6, 14, 22]]}

        """

        pos_ctr_pos = []
        neg_ctr_pos = []
        
        if len(self.pos_control_dilution_data) == 1:
            pos_ctr_pos.append(get_deep_well_pos(1)) # always in first place
            neg_ctr_pos.append(get_deep_well_pos(2)) # always in second place
            sample_pos = [[]]

        elif len(self.pos_control_dilution_data) == 2:
            pos_ctr_pos.append(get_deep_well_pos(1)) # always in first place
            pos_ctr_pos.append(get_deep_well_pos(9)) # always in first place,   second row
            neg_ctr_pos.append(get_deep_well_pos(2)) # always in second place
            neg_ctr_pos.append(get_deep_well_pos(10)) # always in second place, second row
            sample_pos = [[], []]

        else:
            logger.error(f"Positive control data must be of length 1 or 2, not {len(self.pos_control_dilution_data)}")
            raise ValueError(f"Positive control data must be of length 1 or 2, not {len(self.pos_control_dilution_data)}")


        # First coating protein side
        samples_per_block = 8 # fixed. number of triplicate vertical spaces in a 96 well plate.

        for k, sample_group in enumerate(self.sample_eppendorf_positions):
            for i, sample in enumerate(sample_group):
                if i < 6: # if in first triplicate block
                    sample_pos[k].append(get_deep_well_pos(i + 3 + k*samples_per_block)) # i starts at 0. We add 2 positions because 1 is pos.ctr and 2 is neg.ctr
                else:
                    # if 2 coatings are present, it changes, if only 1 coating is present it is the same as above statement always
                    sample_pos[k].append(get_deep_well_pos(i + 3 + (k+int(self.has_2_coatings))*samples_per_block))

        final_pos = {"pos_ctr_pos": pos_ctr_pos,
                     "neg_ctr_pos": neg_ctr_pos,
                     "samples_pos": sample_pos}

        self.pump_lw_well_pos =  final_pos

        logger.debug(f"Pos. ctr. wells: {pos_ctr_pos}")
        logger.debug(f"Neg. ctr. wells: {neg_ctr_pos}")
        logger.debug(f"Sample wells: {sample_pos}")

        return final_pos


    def generate_pump_step_instruction_files(self):
        """
        Generate CSV files regarding pump step instructions.

        One config CSV containing the name of each step per row is generated first.
        Then, another CSV for each step type.

        Outputs
        ----------
            CSV file containing instructions list for the pump steps.

        Example
        --------
        ``step_type.csv:``
        >>> transfer;
            vacuum;
            timer;
            transfer;
            end;

        ``timer.csv:``
        >>> wait_timer;
            10.0;
            5.0;

        ``transfer.csv:``
        >>> volume_amount;liquid_type;
            100;DPBS;
            100;Coating protein;
            200;Blocking buffer;
        """

        step_types = [] # temp list to store step names
        transfer_step_data = pd.DataFrame([], columns=["volume_amount", "liquid_type"])
        timer_step_data = pd.DataFrame([], columns=["wait_timer"])
        csv_number = 1

        self.calculate_pump_labware_positions()
        print("calculated pump labware positions")


        for i, step in enumerate(self.pump_steps_data):
            if step["step_type"] == "Transfer volume to wells":
                step_types.append("transfer")
                transfer_step_data.loc[i] = (list(step.values())[1:]) # select only values from dict, ignoring first entry (step type)

                self.transfer_volume_to_wells(step["liquid_type"], self.pump_lw_name, step["volume_amount"], csv_number)
                csv_number = csv_number + 1

            elif step["step_type"] == "Vacuum":
                step_types.append("vacuum")
            elif step["step_type"] == "Wait timer":
                step_types.append("timer")
                timer_step_data.loc[i] = (list(step.values())[1:]) # select only values from dict, ignoring first entry (step type)

        # multiply by 60 because in Tecan the timer is in seconds and here the value is in minutes
        timer_step_data["wait_timer"] = timer_step_data["wait_timer"] * 60

        step_types.append("end") # add this as last line, because Tecan uses it to recognize that last instruction has been reached

        pd.DataFrame(step_types).to_csv(self.csv_files_path + "\config - step_types.csv", header=["step_type"], index=False, lineterminator=";\n") # generate CSV file

        path = self.csv_files_path + self.pump_steps_csv_name + "Transfer.csv"
        pd.DataFrame(transfer_step_data).to_csv(path, header="step_type", index=False, sep=";", lineterminator=";\n") # generate CSV file
        path = self.csv_files_path + self.pump_steps_csv_name + "Timer.csv"
        pd.DataFrame(timer_step_data).to_csv(path, index=False, sep=";", lineterminator=";\n") # generate CSV file


    def transfer_volume_to_wells(self, source_labware: str, dest_labware: str, volume: float, csv_number: int):
        """
        Generates a CSV file to transfer volume from a labware to the pump vacuum one.

        Parameters
        ----------
        ``source_labware``: str
            Source labware name.

        ``dest_labware``: str
            Destination labware name.

        ``volume``: float
            Volume (uL) to transfer.

        ``csv_number``: int
            Code to add to end of CSV file name. If file with that name already exists, it will be sustituted.

        Outputs
        ----------
            GWL file containing instructions list for the pump transfer step.
        """

        csv_data = []
        LabSource, SourceWell = "undefined_labware", 1 # default values

        _type = "All wells" # to decide where to transfer the volume to.

        # Define labware source name as in Tecan worktable
        if source_labware == "DPBS": # DPBS
            LabSource = LabwareNames["DPBS"]
            # _type = "reagent_distribution" # to skip the CSV and generate the GWL directly with the reagent distribution command
        elif source_labware == "Coating protein":
            # LabSource = self.coat_prot_lw_name
            LabSource = LabwareNames["CoatingProtein"]
        elif source_labware == "Coating protein 2":
            # LabSource = self.coat_prot_lw_name
            LabSource = LabwareNames["CoatingProtein_2"]
        elif source_labware == "Blocking buffer":
            # LabSource = self.blocking_buffer_lw_name
            LabSource = LabwareNames["BlockingBuffer"]
        elif source_labware == "Pos/Neg control":
            # special case
            _type = "pos/neg"
        elif source_labware == "Samples":
            # special case
            _type = "Only samples"
        elif source_labware == "Conjugate":
            # LabSource = self.conjugate_lw_name
            LabSource = LabwareNames["Conjugate"]


        sample_wells = np.ndarray.flatten(np.array(self.pump_lw_well_pos["samples_pos"])).tolist()
        min_sample_well = np.min(sample_wells)
        max_sample_well = np.max(sample_wells)
        max_neg_ctr_well = np.max(self.pump_lw_well_pos["neg_ctr_pos"])

        all_wells = flatten(self.pump_lw_well_pos["pos_ctr_pos"]) + flatten(self.pump_lw_well_pos["neg_ctr_pos"]) + sample_wells # position of all wells to be used
        
        if _type == "All wells": # transfer to all wells
            if self.has_2_coatings == True and source_labware == "Coating protein":

                coating_1_wells = self.pump_lw_well_pos["pos_ctr_pos"][0] + self.pump_lw_well_pos["neg_ctr_pos"][0] + flatten(self.pump_lw_well_pos["samples_pos"][0])
                logger.debug(f"coating 1 wells: {coating_1_wells}")
                
                for well in coating_1_wells:
                    csv_data.append(
                    {
                        'LabSource': LabwareNames["CoatingProtein"],
                        'SourceWell': SourceWell,
                        'LabDest': dest_labware,
                        'DestWell': well,
                        'Volume': volume
                    })

                # make reagent distribution command, with all wells excluding the unused ones
                # generate the GWL directly
                path = self.csv_files_path + self.pump_steps_csv_name + "Transfer " + str(csv_number) + ".gwl"
                max_coating_1_well = np.max(coating_1_wells)
                
                complete_well_list = np.arange(1, max_coating_1_well + 1) # list with all wells from 1 to the max sample pos
                excluded_pos = list(set(complete_well_list) - set(coating_1_wells)) # positions to exclude from pipetting in the reag. distrib. command
                n_diti_reuses = 12
                n_multi_dispense = 12

                generate_reagent_distribution_gwl(path, LabwareNames["CoatingProtein"], dest_labware, 1, 1, 1, max_coating_1_well, volume, n_diti_reuses, n_multi_dispense, excluded_positions=excluded_pos)
                
                return

            elif self.has_2_coatings == True and source_labware == "Coating protein 2":
                coating_2_wells = self.pump_lw_well_pos["pos_ctr_pos"][1] + self.pump_lw_well_pos["neg_ctr_pos"][1] + flatten(self.pump_lw_well_pos["samples_pos"][1])
                logger.debug(f"coating 2 wells: {coating_2_wells}")

                for well in coating_2_wells:
                    csv_data.append(
                    {
                        'LabSource': LabwareNames["CoatingProtein_2"],
                        'SourceWell': SourceWell,
                        'LabDest': dest_labware,
                        'DestWell': well,
                        'Volume': volume
                    })

                # make reagent distribution command, with all wells excluding the unused ones
                # generate the GWL directly
                path = self.csv_files_path + self.pump_steps_csv_name + "Transfer " + str(csv_number) + ".gwl"
                max_coating_2_well = np.max(coating_2_wells)
                
                complete_well_list = np.arange(1, max_coating_2_well + 1) # list with all wells from 1 to the max sample pos
                excluded_pos = list(set(complete_well_list) - set(coating_2_wells)) # positions to exclude from pipetting in the reag. distrib. command
                n_diti_reuses = 12
                n_multi_dispense = 12

                generate_reagent_distribution_gwl(path, LabwareNames["CoatingProtein_2"], dest_labware, 1, 1, 1, max_coating_2_well, volume, n_diti_reuses, n_multi_dispense, excluded_positions=excluded_pos)
                
                return


            else: # if it has only 1 coating or step is not coating protein
                path = self.csv_files_path + self.pump_steps_csv_name + "Transfer " + str(csv_number) + ".gwl"
                
                complete_well_list = np.arange(1, max_sample_well + 1) # list with all wells from 1 to the max sample pos
                excluded_pos = list(set(complete_well_list) - set(all_wells)) # positions to exclude from pipetting in the reag. distrib. command
                n_diti_reuses = 12
                n_multi_dispense = 12

                generate_reagent_distribution_gwl(path, LabSource, dest_labware, 1, 1, 1, max_sample_well, volume, n_diti_reuses, n_multi_dispense, excluded_positions=excluded_pos)
                
                return



        elif _type == "Only samples": # transfer samples from Eppendorf to wells
            
            for j, sample_group in enumerate(self.sample_eppendorf_positions):
                LabSource, SourceWell = dilution_position_def("Eppendorf", sample_group[0], len(sample_group))

                for i, sample in enumerate(sample_group):
                    for well in self.pump_lw_well_pos["samples_pos"][j][i]:
                        csv_data.append(
                        {
                            'LabSource': LabSource[i],
                            'SourceWell': SourceWell[i],
                            'LabDest': dest_labware,
                            'DestWell': well,
                            'Volume': 100
                        })

            # make reagent distribution command, with all wells excluding the unused ones
            # generate the GWL directly
            path = self.csv_files_path + self.pump_steps_csv_name + "Transfer " + str(csv_number) + ".gwl"
            # path = "SampleTransferTestRUN.gwl"
            
            complete_well_list = np.arange(1, max_sample_well + 1) # list with all wells from 1 to the max sample pos
            excluded_pos = list(set(complete_well_list) - set(sample_wells)) # positions to exclude from pipetting in the reag. distrib. command
            n_diti_reuses = 1 # no reuse
            n_multi_dispense = 3
            sample_direction = 1 # top to down
            replicate_direction = 0 # left to right
            LabSource = "1x24 Eppendorf Tube Runner no Tubes"
            sample_eppendorf_pos = np.array(self.sample_eppendorf_positions).flatten()
            print("sample eppendorf pos:", sample_eppendorf_pos)

            # all samples fit in the first eppendorf rack
            if sample_eppendorf_pos.max() <= 24:
                generate_sample_transfer_gwl(path, "w", pos_2_str(LabSource, 1), dest_labware, self.sample_eppendorf_positions[0][0], self.sample_eppendorf_positions[-1][-1], min_sample_well, max_sample_well, volume, n_diti_reuses, n_multi_dispense, self.n_samples_main_dilution * (1 + int(self.has_2_coatings)), 3, sample_direction, replicate_direction, excluded_positions=excluded_pos)
            
            # if all samples are in the second rack
            elif sample_eppendorf_pos.min() > 24 and sample_eppendorf_pos.max() <= 48:
                generate_sample_transfer_gwl(path, "w", pos_2_str(LabSource, 2), dest_labware, self.sample_eppendorf_positions[0][0] - 24, self.sample_eppendorf_positions[-1][-1] - 24, min_sample_well, max_sample_well, volume, n_diti_reuses, n_multi_dispense, self.n_samples_main_dilution * (1 + int(self.has_2_coatings)), 3, sample_direction, replicate_direction, excluded_positions=excluded_pos)
            
            # some samples are in the second eppendorf rack (sample number is high), so the sample transfer has to be divided in 2 commands actually
            else:
                # np.where works because the array is sorted from smaller to bigger by definition
                n_samples_first_eppendorf_rack = np.where(sample_eppendorf_pos == 24)[0][0] + 1 # we add 1 because the result is an index and we want the number itself
                triplet_sample_wells = np.array(self.pump_lw_well_pos["samples_pos"]).reshape(-1, 3) # reshape to be a list of triplets

                # Sample transfer command for first rack
                # max_sample_well_1 = np.max(triplet_sample_wells[n_samples_first_eppendorf_rack - 1])
                sample_wells_1 = triplet_sample_wells[:n_samples_first_eppendorf_rack].flatten()
                complete_well_list = np.arange(1, sample_wells_1.max() + 1) # list with all wells from 1 to the max sample pos
                excluded_pos = list(set(complete_well_list) - set(sample_wells_1)) # positions to exclude from pipetting in the reag. distrib. command

                if n_samples_first_eppendorf_rack <= self.n_samples_main_dilution:
                    generate_sample_transfer_gwl(path, "w", pos_2_str(LabSource, 1), dest_labware, sample_eppendorf_pos[0], sample_eppendorf_pos[n_samples_first_eppendorf_rack - 1], sample_wells_1.min(), sample_wells_1.max(), volume, n_diti_reuses, n_multi_dispense, n_samples_first_eppendorf_rack, 3, sample_direction, replicate_direction, excluded_positions=excluded_pos)

                else: # we have to divide in 2 commands, because there are samples from both groups (diluted 1 and diluted 2)
                    # if only has 1 coating, I think we dont have to do this separation, samples will be in order anyway, but let's test it later
                    sample_wells_1_1 = triplet_sample_wells[:self.n_samples_main_dilution].flatten()
                    complete_well_list = np.arange(1, sample_wells_1_1.max() + 1) # list with all wells from 1 to the max sample pos
                    excluded_pos_1_1 = list(set(complete_well_list) - set(sample_wells_1_1)) # positions to exclude from pipetting in the reag. distrib. command

                    generate_sample_transfer_gwl(path, "w", pos_2_str(LabSource, 1), dest_labware, sample_eppendorf_pos[0], sample_eppendorf_pos[self.n_samples_main_dilution - 1], sample_wells_1_1.min(), sample_wells_1_1.max(), volume, n_diti_reuses, n_multi_dispense, self.n_samples_main_dilution, 3, sample_direction, replicate_direction, excluded_positions=excluded_pos_1_1)

                    sample_wells_1_2 = triplet_sample_wells[self.n_samples_main_dilution:n_samples_first_eppendorf_rack].flatten()
                    excluded_pos_1_2 = list(set(complete_well_list) - set(sample_wells_1_2)) # positions to exclude from pipetting in the reag. distrib. command
                    generate_sample_transfer_gwl(path, "a", pos_2_str(LabSource, 1), dest_labware, sample_eppendorf_pos[self.n_samples_main_dilution], sample_eppendorf_pos[n_samples_first_eppendorf_rack - 1], sample_wells_1_2.min(), sample_wells_1_2.max(), volume, n_diti_reuses, n_multi_dispense, n_samples_first_eppendorf_rack - self.n_samples_main_dilution, 3, sample_direction, replicate_direction, excluded_positions=excluded_pos_1_2)



                # Sample transfer command for second rack
                max_sample_well_2 = np.max(triplet_sample_wells)
                complete_well_list = np.arange(1, max_sample_well_2 + 1) # list with all wells from 1 to the max sample pos
                sample_wells_2 = triplet_sample_wells[n_samples_first_eppendorf_rack:].flatten()
                excluded_pos_2 = list(set(complete_well_list) - set(sample_wells_2)) # positions to exclude from pipetting in the reag. distrib. command

                generate_sample_transfer_gwl(path, "a", pos_2_str(LabSource, 2), dest_labware, sample_eppendorf_pos[n_samples_first_eppendorf_rack] - 24, sample_eppendorf_pos[-1] - 24, sample_wells_2.min(), sample_wells_2.max(), volume, n_diti_reuses, n_multi_dispense, len(sample_eppendorf_pos) - n_samples_first_eppendorf_rack, 3, sample_direction, replicate_direction, excluded_positions=excluded_pos_2)

            return
        
        elif _type == "pos/neg":
            for j, sample_group in enumerate(self.pos_control_eppendorf_positions):
                LabSource, SourceWell = dilution_position_def("Eppendorf", sample_group[0], len(sample_group))

                for well in self.pump_lw_well_pos["pos_ctr_pos"][j]: # Positive control
                    csv_data.append(
                    {
                        'LabSource': self.pos_ctr_diluted_lw_name[j],
                        # 'LabSource': LabwareNames["PosControl"],
                        'SourceWell': 1,
                        'LabDest': dest_labware,
                        'DestWell': well,
                        'Volume': volume
                    })

                for well in self.pump_lw_well_pos["neg_ctr_pos"][j]: # Negative control
                    csv_data.append(
                    {
                        'LabSource': self.neg_ctr_diluted_lw_name[j],
                        # 'LabSource': LabwareNames["NegControl"],
                        'SourceWell': 1,
                        'LabDest': dest_labware,
                        'DestWell': well,
                        'Volume': volume
                    })

            # command for pos/neg control transfer to dotblot_apparatus
            # this should be the fixed generated command, since positions are fixed independent of all other parameters (for 2 coatings)
            # "T;1x24 Eppendorf Tube Runner no Tubes[001];;;1;4;dotblot_appr_standalone;;;1;42;100;;1;3;4;3;0;0;3;4;5;6;7;8;11;12;13;14;15;16;19;20;21;22;23;24;27;28;29;30;31;32;35;36;37;38;39;40;"

            # make reagent distribution command, with all wells excluding the unused ones
            # generate the GWL directly
            path = self.csv_files_path + self.pump_steps_csv_name + "Transfer " + str(csv_number) + ".gwl"
            
            complete_ctr_well_list = np.array(self.pump_lw_well_pos["neg_ctr_pos"] + self.pump_lw_well_pos["pos_ctr_pos"]).flatten() # list with all wells from 1 to the max sample pos
            min_ctr_well = complete_ctr_well_list.min()
            max_ctr_well = complete_ctr_well_list.max()
            excluded_pos = list(set(np.arange(1, max_ctr_well + 1)) - set(complete_ctr_well_list)) # positions to exclude from pipetting in the reag. distrib. command
            
            n_diti_reuses = 1 # no reuse
            n_multi_dispense = 3
            sample_direction = 0 # left to right
            replicate_direction = 0 # left to right
            n_ctr_samples = 2 * (1 + int(self.has_2_coatings))
            LabSource = "1x24 Eppendorf Tube Runner no Tubes"
            sample_eppendorf_pos = np.array(self.sample_eppendorf_positions).flatten()

            # all samples fit in the first eppendorf rack
            if sample_eppendorf_pos.max() <= 24:
                generate_sample_transfer_gwl(path, "w", pos_2_str(LabSource, 1), dest_labware, self.pos_control_eppendorf_positions[0][0], self.neg_control_eppendorf_positions[-1][-1], min_ctr_well, max_ctr_well, volume, n_diti_reuses, n_multi_dispense, n_ctr_samples, 3, sample_direction, replicate_direction, excluded_positions=excluded_pos)

            return

        elif _type == "reagent_distribution": # right now only DPBS uses this
            # generate the GWL directly
            path = self.csv_files_path + self.pump_steps_csv_name + "Transfer " + str(csv_number) + ".gwl"
            n_diti_reuses = 12
            n_multi_dispense = 12

            generate_reagent_distribution_gwl(path, LabSource, dest_labware, 1, 1, 1, max_sample_well, volume, n_diti_reuses, n_multi_dispense)
            print("transfer volume instruction ", csv_number, "done")

            return
        
        # Generate CSV file
        path = self.csv_files_path + self.pump_steps_csv_name + "Transfer " + str(csv_number) + ".csv"
        pd.DataFrame(csv_data).to_csv(path, index=False, header=False)

        # Convert the file from CSV to GWL
        output_path = f"{path.replace('.csv', '.gwl')}"

        if _type in ["pos/neg", "Only samples"]:
            convert_csv_to_gwl(path, output_path, reuse_tips=False)
        else:
            convert_csv_to_gwl(path, output_path, reuse_tips=True)


        print("transfer volume instruction ", csv_number, "done")


    def calculate_total_volumes(self):
        """
        Calculates the total volume needed for each reagent.
        
        Returns
        ----------
            Dictionary with the calculated volumes.
        """

        # empty dictionary that will contain keys for total
        total_volume = {}
        ctr_wells = 2 * 3 * (1 + int(self.has_2_coatings)) # total number of wells for positive and negative controls
        n_sample_wells = self.n_samples_main_dilution * 3 * (1 + int(self.has_2_coatings)) # total number of wells used for samples


        for step in self.pump_steps_data:
            if step["step_type"] == "Transfer volume to wells":
                if step["liquid_type"] not in total_volume:
                    total_volume[step["liquid_type"]] = 0 # create key
                
                total_volume[step["liquid_type"]] += float(step["volume_amount"])/1000 # because volume amount is in uL and we want it in mL

        # remove this key because it is not needed
        total_volume.pop("Samples")
        total_volume.pop("Pos/Neg control")

        # multiply by number of samples
        for key in total_volume:
            total_volume[key] *= n_sample_wells
            total_volume[key] = total_volume[key]

        assay_buffer_vol = 0
        for k, sample_group in enumerate(self.sample_dilution_data):
            assay_buffer_vol += sum(self.pos_control_dilution_data[k]["Assay buffer volume"]) + sum(self.neg_control_dilution_data[k]["Assay buffer volume"]) + sum(self.sample_dilution_data[k]["Assay buffer volume"] * self.n_samples_main_dilution)

        buffer_type = "Assay buffer" # pos/neg ctr are diluted always with assay buffer
        total_volume[buffer_type] = assay_buffer_vol/1000

        # double the volume if 2 coatings are needed (samples are doubled)
        if self.has_2_coatings:
            for key in total_volume:
                if key in ["Coating protein", "Coating protein 2"]:
                    total_volume[key] /= 2

        total_volume["Dye"] = (96 * self.dye_volume_per_well) / 1000 # full 96 wells used, DYE is used only once in whole method

        # calculate DPBS total volume
        total_volume["DPBS"] = 0

        for step in self.pump_steps_data:
            if step["step_type"] == "Transfer volume to wells":
                if step["liquid_type"] == "DPBS":
                    total_volume["DPBS"]+= (ctr_wells + n_sample_wells) * int(step["volume_amount"]) / 1000

        # round values
        total_volume = {key: round(value, 1) for key, value in total_volume.items()}

        self.total_volumes = total_volume


    def generate_dye_and_wash_files(self):
        """
        Generates the dye and wash csv and gwl files.
        """

        # generate GWL files
        dye_path = self.csv_files_path + self.pump_steps_csv_name + "Transfer dye.gwl"
        wash_path = self.csv_files_path + self.pump_steps_csv_name + "Transfer wash.gwl"
        n_diti_reuses = 12
        n_multi_dispense = 12

        # Dye
        generate_reagent_distribution_gwl(dye_path, LabwareNames["Dye"], self.pump_lw_name, 1, 1, 1, 96, self.dye_volume_per_well, n_diti_reuses, n_multi_dispense)
        
        # Wash
        generate_reagent_distribution_gwl(wash_path, LabwareNames["DPBS"], self.pump_lw_name, 1, 1, 1, 96, 200, n_diti_reuses, n_multi_dispense)
        
        logger.info("Generated Dye and Wash GWL files.")


    def generate_config_file(self):
        """
        Generates the config file for the current run.
        """

        # If there are repeated keys in the dictionary, the last one and its value is the dominant one !!!

        config_parameters = {"has_2_coatings": str(True),
                            "DPBS": LabwareNames["DPBS"],
                            "Coating protein": LabwareNames["CoatingProtein"],
                            "Blocking buffer": LabwareNames["BlockingBuffer"],
                            "Assay buffer": LabwareNames["AssayBuffer"],
                            "Pos. control": str(self.pos_control_vial_posX) + ", " + str(self.pos_control_vial_posY),
                            "Neg. control": "A, 1",
                            "Samples": self.main_sample_labware_type,
                            "Conjugate": LabwareNames["Conjugate"],
                            "Coating protein 2": LabwareNames["CoatingProtein_2"],
                            "Dye": LabwareNames["Dye"]
                     }

        with open(self.csv_files_path + self.config_file_name, 'w') as file:
            # Write the keys
            keys = "; ".join(config_parameters.keys())
            file.write(keys + ";\n")
            
            # Write the values
            values = "; ".join(map(str, config_parameters.values()))
            file.write(values + ";\n")


    def dotblot(self):
        """
        Class main method.
        ----------

        Executes all stages of the Dot Blot method step by step and generates CSV files for them.
        """

        logger.info(f"has_2_coatings: {str(self.has_2_coatings)}")
        logger.info("-------------------------------------")
        logger.info(f"N. of samples: {self.n_samples_main_dilution}")
        logger.info(f"Samples initial labware: {self.main_sample_labware_type}")
        logger.info(f"Pos. ctr. vial position: {self.pos_control_vial_posX}, {self.pos_control_vial_posY}")
        logger.info("-------------------------------------")


        logger.info("Starting Dotblot method calculations")
        self.generate_config_file()
        logger.info("Config file generated.")
        
        self.next_labware_pos("Eppendorf") # we call this once at the start because the dict begins at 0, and the coded positions assume the number is 1
        self.next_labware_pos("DeepWell") # we call this once at the start because the dict begins at 0, and the coded positions assume the number is 1

        self.calculate_total_volumes()
        logger.debug(f"Total volumes: {self.total_volumes}")

        # make sure that if run has 2 coatings, it is present as a transfer step in the pump data (extracted from assays.json)
        if self.has_2_coatings:
            pump_data_coating_2 = [True if step["step_type"] == "Transfer volume to wells" and step["liquid_type"] == "Coating protein 2" else False for step in self.pump_steps_data]
            assert True in pump_data_coating_2, "This Dotblot run has 2 coatings, so a transfer option in 'assays.json' with 'Coating protein 2' as liquid_type has to be present."

        self.pos_control_eppendorf_positions = self.positive_control_dilutions()
        self.pos_ctr_diluted_lw_name = [pos_2_str("Eppendorf", self.pos_control_eppendorf_positions[i]) for i in range(len(self.pos_control_eppendorf_positions))] # set position of positive ctr diluted sample
        print(f"pos dilutions done: {self.pos_control_eppendorf_positions}")
        logger.info(f"Positive control dilutions done. Positions: {self.pos_control_eppendorf_positions}")
        
        self.neg_control_eppendorf_positions = self.negative_control_dilutions()
        self.neg_ctr_diluted_lw_name = [pos_2_str("Eppendorf", self.neg_control_eppendorf_positions[i]) for i in range(len(self.neg_control_eppendorf_positions))] # set position of positive ctr diluted sample
        print(f"negative ctr eppendorf pos: {self.neg_control_eppendorf_positions}")
        logger.info(f"Negative control dilutions done. Positions: {self.neg_control_eppendorf_positions}")

        self.sample_eppendorf_positions = self.sample_dilutions()
        print("sample eppendorf pos:", self.sample_eppendorf_positions)
        logger.info(f"Sample dilutions done. Positions: {self.sample_eppendorf_positions}")

        self.generate_pump_step_instruction_files()
        logger.info("Pump instruction files generated.")

        self.generate_dye_and_wash_files()
        logger.info("Dye and wash files generated.")

        print("generated all GWL files")
        logger.info("All GWL files generated.")

        
        logger.info("Dotblot method finished successfully.")
        return self.pos_control_eppendorf_positions, self.neg_control_eppendorf_positions, self.sample_eppendorf_positions

        
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
        self.sample_dilution_data = external.sample_dilution_data
        self.coating_protein_dilution_data = external.coating_protein_dilution_data
        self.n_sample_dilution_steps = len(self.sample_dilution_data[0]["Assay buffer volume"])

        # Sample
        self.main_sample_labware_type = external.optionmenu_1.get()
        self.n_samples_main_dilution = int(external.entry_slider2.get())
        # self.samples_initial_volume_transfer = external.entry_slider3.get()
        # self.samples_initial_volume_transfer = self.sample_dilution_data["Sample volume"][0] * 10 # value normally between 10uL, so transfer around 100uL, which is more than
        self.samples_initial_volume_transfer = 30 # hard coded for nicolas's test on thu. 4/7

        # Positive control
        self.pos_control_dilution_data = external.pos_control_dilution_data
        self.n_pos_control_steps = len(self.pos_control_dilution_data[0]["Assay buffer volume"])
        self.pos_control_vial_posX = external.pos_ctr_X_pos.get()
        self.pos_control_vial_posY = external.pos_ctr_Y_pos.get()
        
        # Negative control
        self.neg_control_dilution_data = external.neg_control_dilution_data
        self.n_neg_control_steps = len(self.neg_control_dilution_data[0]["Assay buffer volume"])

        # Pump steps
        self.pump_steps_data = external.pump_steps_data


# -----------------------
# Dot Blot method class #
# -----------------------

import pandas as pd
import numpy as np
from utils import * # file with helper methods


class DotblotMethod():
    """
    Produces CSV files with all the steps to carry out the Dot Blot method in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.csv_files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\3. DotBlot' # network path where all the CSV files will be saved in.
        self.last_eppendorf_pos = 1 # position of the last Eppendorf tube used. Useful so that methods don't use same tube twice.
        self.last_deep_well_pos = 1 # position of the last Deep well position used. Useful so that methods don't use same well twice.

        # CSV file names
        self.pos_control_csv_name = r"\1. Positive control - "
        self.neg_control_csv_name = r"\1. Negative control - "
        self.sample_dilutions_csv_name = r"\2. Sample dilutions - "
        self.pump_steps_csv_name = r"\3. Pump steps - "

        # dictionaries to store all dilution values
        self.sample_dilution_data = {}
        self.coating_protein_dilution_data = {}
        self.pos_control_dilution_data = {}
        self.neg_control_dilution_data = {}

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
        self.pos_control_buffer = "" # name of pos control buffer (assay or DPBS)

        # Negative control parameters
        self.n_neg_control_steps = 0 # number of positive control dilution steps to achieve final concentration
        self.neg_control_vial_posY = "" # A,B,C,D,E position of neg contorl vial inside of custom holder
        self.neg_control_vial_posX = "" # 1,2,3,4,5,6 position of neg contorl vial inside of custom holder
        self.neg_control_buffer = "" # name of neg control buffer (assay or DPBS)

        # Labware names
        self.coat_prot_lw_name = "def_coat_prot" # Coating protein labware
        self.blocking_buffer_lw_name = "def_blocking" # Blocking Buffer labware
        self.pos_ctr_lw_name = "def_pos_ctr" # Positive control labware
        self.neg_ctr_lw_name = "def_neg_ctr" # Negative control labware
        self.conjugate_lw_name = "def_conjugate" # Conjugate labware
        self.dpbs_lw_name = "def_dpbs" # DPBS labware
        self.pump_lw_name = "dotblot_appr_standalone" # Pump vacuum labware

        # Pump steps
        self.pump_steps_data = {}
        self.n_wells_pump_labware = 96 # number of wells in labware inside pump vacuum area
        self.pump_lw_well_pos = {} # pump labware well positions of different ctr and samples


    def next_eppendorf_pos(self):
        """
        Adds one to the Eppendorf position used and returns that number.
        If no Eppendorf tubes are available, returns -1.
        """

        if (self.last_eppendorf_pos + 1 <= AvailableLabware["Eppendorf"]): # if max pos has not been reached
            self.last_eppendorf_pos = self.last_eppendorf_pos + 1
            return self.last_eppendorf_pos - 1 # return current one before adding an unit
        else:
            return -1


    def next_deep_well_pos(self):
        """
        Adds one to the Deep Well position used and returns that number.
        If no Deep Well tubes are available, returns -1.
        """
        
        if (self.last_deep_well_pos + 1 <= AvailableLabware["DeepWell"]): # if max pos has not been reached
            self.last_deep_well_pos = self.last_deep_well_pos + 1
            return self.last_deep_well_pos - 1 # return current one before adding an unit
        else:
            return -1
        

    def positive_control_dilutions(self, mix: bool = True):
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
        
        csv_number = 1 # to name generated files sequentially
        initial_pos = 1 # position of the first vial of the pos control
        buffer_labware_name = "100ml_1" # Name of Labware in TECAN for the Assay buffer
        eppendorf_positions = [] # to store final eppendorf positions

        if self.pos_control_buffer == "DPBS":
            buffer_labware_name = "100ml_2" # Name of Labware in TECAN containing the DPBS buffer

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
        
        # sample_lab_source = self.custom_holder_name # initial source of pos control sample
        sample_lab_source = LabwareNames["CustomVialHolder"] # initial source of pos control sample
        sample_lab_well = initial_pos

        for i in range(self.n_pos_control_steps):
            csv_data_sample = [] # list to store CSV data
            csv_data_buffer = [] # list to store CSV data

            if i + 1 == self.n_pos_control_steps: # if this is the final dilution step
                eppendorf_positions.append(self.last_eppendorf_pos)
                # LabDest, DestWell = self.dilution_position_def("Eppendorf", self.next_eppendorf_pos(), 1) # define destination labware as eppendorf
                LabDest, DestWell = dilution_position_def("Eppendorf", self.next_eppendorf_pos(), 1) # define destination labware as eppendorf
            else:
                # LabDest, DestWell = self.dilution_position_def("Deep Well", self.next_deep_well_pos(), 1) # define destination labware as deep well
                LabDest, DestWell = dilution_position_def("DeepWell", self.next_deep_well_pos(), 1) # define destination labware as deep well

            csv_data_sample.append( # move pos control to dest well
            {
                'LabSource': sample_lab_source,
                'SourceWell': sample_lab_well,
                'LabDest': LabDest[0],
                'DestWell': DestWell[0],
                'Volume': float(self.pos_control_dilution_data["Sample volume"][i])
            })

            csv_data_buffer.append( # move buffer to destination well
            {
                'LabSource': buffer_labware_name,
                'SourceWell': int(1), # buffer only has 1 big well
                'LabDest': LabDest[0],
                'DestWell': DestWell[0],
                'Volume': float(self.pos_control_dilution_data["Assay buffer volume"][i])
            })
        

            sample_lab_source, sample_lab_well = LabDest[0], DestWell[0] # source of next step is destination of previous one

            # generate CSV files (we separate them so that in the buffer one we can use liquid class for mixing)
            path = self.csv_files_path + self.pos_control_csv_name + str(csv_number) + ".csv" # path for sample 
            pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False) # create dataframe and then CSV file
            path = self.csv_files_path + self.pos_control_csv_name + str(csv_number + 1) + ".csv" # path for buffer
            pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False) # create dataframe and then CSV file
            csv_number = csv_number + 2

        # if less than 3 dilutions steps are needed, blank out the remaining CSV files so that the Tecan ignores them basically
        for i in range(csv_number, 6 + 1):
            path = self.csv_files_path + self.pos_control_csv_name + str(csv_number) + ".csv"
            pd.DataFrame(list()).to_csv(path, index=False, header=False) # create empty dataframe and save it into an empty CSV
            csv_number = csv_number + 1
        
        return eppendorf_positions


    def negative_control_dilutions(self):
        """
        Performs the dilutions to get the negative control final concentration.

        Outputs
        ----------
            CSV files containing instructions for the Tecan.
        """
        
        csv_number = 1 # to name generated files sequentially
        initial_pos = 1 # position of the first vial of the pos control
        buffer_labware_name = "100ml_1" # Name of Labware in TECAN for the Assay buffer
        eppendorf_positions = [] # to store final eppendorf positions

        if self.neg_control_buffer == "DPBS":
            buffer_labware_name = "100ml_2" # Name of Labware in TECAN containing the DPBS buffer

        # Define custom vial holder labware position depending on the vial position
        if self.neg_control_vial_posX == "A":
            initial_pos = 1
        elif self.neg_control_vial_posX == "B":
            initial_pos = 2
        elif self.neg_control_vial_posX == "C":
            initial_pos = 3
        elif self.neg_control_vial_posX == "D":
            initial_pos = 4
        elif self.neg_control_vial_posX == "E":
            initial_pos = 5

        initial_pos = initial_pos + (int(self.neg_control_vial_posY) - 1) * 5 # add X position
        
        # sample_lab_source = self.custom_holder_name # initial source of pos control sample
        sample_lab_source = LabwareNames["CustomVialHolder"] # initial source of pos control sample
        sample_lab_well = initial_pos

        for i in range(self.n_neg_control_steps):
            csv_data_sample = [] # list to store CSV data
            csv_data_buffer = [] # list to store CSV data

            if i + 1 == self.n_neg_control_steps: # if this is the final dilution step
                eppendorf_positions.append(self.last_eppendorf_pos)
                # LabDest, DestWell = self.dilution_position_def("Eppendorf", self.next_eppendorf_pos(), 1) # define destination labware as eppendorf
                LabDest, DestWell = dilution_position_def("Eppendorf", self.next_eppendorf_pos(), 1) # define destination labware as eppendorf
            else:
                # LabDest, DestWell = self.dilution_position_def("Deep Well", self.next_deep_well_pos(), 1) # define destination labware as deep well
                LabDest, DestWell = dilution_position_def("DeepWell", self.next_deep_well_pos(), 1) # define destination labware as deep well

            csv_data_sample.append( # move pos control to dest well
            {
                'LabSource': sample_lab_source,
                'SourceWell': sample_lab_well,
                'LabDest': LabDest[0],
                'DestWell': DestWell[0],
                'Volume': float(self.neg_control_dilution_data["Sample volume"][i])
            })

            csv_data_buffer.append( # move buffer to destination well
            {
                'LabSource': buffer_labware_name,
                'SourceWell': int(1), # buffer only has 1 big well
                'LabDest': LabDest[0],
                'DestWell': DestWell[0],
                'Volume': float(self.neg_control_dilution_data["Assay buffer volume"][i])
            })
        

            sample_lab_source, sample_lab_well = LabDest[0], DestWell[0] # source of next step is destination of previous one

            # generate CSV files (we separate them so that in the buffer one we can use liquid class for mixing)
            path = self.csv_files_path + self.neg_control_csv_name + str(csv_number) + ".csv" # path for sample 
            pd.DataFrame(csv_data_sample).to_csv(path, index=False, header=False) # create dataframe and then CSV file
            path = self.csv_files_path + self.neg_control_csv_name + str(csv_number + 1) + ".csv" # path for buffer
            pd.DataFrame(csv_data_buffer).to_csv(path, index=False, header=False) # create dataframe and then CSV file
            csv_number = csv_number + 2

        # if less than 3 dilutions steps are needed, blank out the remaining CSV files so that the Tecan ignores them basically
        for i in range(csv_number, 6 + 1):
            path = self.csv_files_path + self.pos_control_csv_name + str(csv_number) + ".csv"
            pd.DataFrame(list()).to_csv(path, index=False, header=False) # create empty dataframe and save it into an empty CSV
            csv_number = csv_number + 1
        
        return eppendorf_positions    

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
        eppendorf_positions = [] # list to store positions of eppendorf positions used for the final dilution
        
        LabDest, DestWell = dilution_position_def(self.main_sample_dil_destination, self.last_deep_well_pos, self.n_samples_main_dilution)

        # Initial transfer of sample to deep wells, so that 
        # print("before initial")
        # print("self.main_sample_labware_type:", self.main_sample_labware_type)
        print("labdest:", LabDest)
        print("destwell:", DestWell)
        for j in range(1, self.n_samples_main_dilution + 1):

            LabSource = pos_2_str(self.main_sample_labware_type, j)
            csv_data_init.append(
            {
                'LabSource': LabSource,
                'SourceWell': int(1),
                'LabDest': LabDest[j-1],
                'DestWell': DestWell[j-1],
                'Volume': float(self.samples_initial_volume_transfer)
            }
            )
            self.next_deep_well_pos() # to keep the position updated
            
        path = self.csv_files_path + self.sample_dilutions_csv_name + str(csv_number) + ".csv"
        pd.DataFrame(csv_data_init).to_csv(path, index=False, header=False)
        csv_number = csv_number + 1

        print("before long csv")
        for i in range(self.n_sample_dilution_steps):
            csv_data_sample = []
            csv_data_buffer = []

            LabSource, SourceWell = LabDest, DestWell # source of next step is destination of previous one

            if i + 1 == self.n_sample_dilution_steps: # if this is the final dilution step
                LabDest, DestWell = dilution_position_def("Eppendorf", self.last_eppendorf_pos, (self.n_samples_main_dilution * (i+1) + 1))
            else:
                LabDest, DestWell = dilution_position_def("DeepWell", self.last_deep_well_pos, (self.n_samples_main_dilution * (i+1) + 1))

            for j in range(self.n_samples_main_dilution):
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
                    'LabSource': '100ml_1',
                    'SourceWell': int(1),
                    'LabDest': LabDest[j],
                    'DestWell':  DestWell[j],
                    'Volume': float(self.sample_dilution_data["Assay buffer volume"][i])
                }
                )
                if i + 1 == self.n_sample_dilution_steps: # if this is the last dilution step
                    eppendorf_positions.append(self.last_eppendorf_pos)
                    self.next_eppendorf_pos()
                else:
                    self.next_deep_well_pos()

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


        return eppendorf_positions
    

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
        
        pos_ctr_pos = get_deep_well_pos(1) # always in first place
        neg_ctr_pos = get_deep_well_pos(2) # always in second place
        sample_pos = []

        # self.sample_eppendorf_positions = [5,6,11,12,15,16,17,18,21,22,27,28,31,32] # setup manually by force
        # diff = 3 - self.sample_eppendorf_positions[0] # diference between first sample pos and number 3, because pos 1 is for positive_control, and pos 2 for negative control, so samples start in pos 3
        # print("diff is ", diff)
        print("sample eppendorf pos:", self.sample_eppendorf_positions)

        # for i in range(1, self.n_samples_main_dilution + 1):
        #     sample_pos.append(get_deep_well_pos(i + diff))

        for sample in self.sample_eppendorf_positions:
            sample_pos.append(get_deep_well_pos(sample))

        final_pos = {"pos_ctr_pos": pos_ctr_pos,
                     "neg_ctr_pos": neg_ctr_pos,
                     "samples_pos": sample_pos}

        self.pump_lw_well_pos =  final_pos


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
        # vacuum_step_data = pd.DataFrame([], columns=[""])
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
                # vacuum_step_data.loc[i] = (list(step.values())[1:]) # select only values from dict, ignoring first entry (step type)
            elif step["step_type"] == "Wait timer":
                step_types.append("timer")
                timer_step_data.loc[i] = (list(step.values())[1:]) # select only values from dict, ignoring first entry (step type)

        # multiply by 60 because in Tecan the timer is in seconds and here the value is in minutes
        timer_step_data["wait_timer"] = timer_step_data["wait_timer"] * 60

        step_types.append("end") # add this as last line, because Tecan uses it to recognize that last instruction has been reached

        pd.DataFrame(step_types).to_csv(self.csv_files_path + "\config - step_types.csv", header=["step_type"], index=False, lineterminator=";\n") # generate CSV file

        path = self.csv_files_path + self.pump_steps_csv_name + "Transfer.csv"
        pd.DataFrame(transfer_step_data).to_csv(path, header="step_type", index=False, sep=";", lineterminator=";\n") # generate CSV file
        # path = self.csv_files_path + self.pump_steps_csv_name + "Vacuum.csv"
        # pd.DataFrame(vacuum_step_data).to_csv(path, header=False, index=False, sep=";", lineterminator=";\n") # generate CSV file
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
            CSV file containing instructions list for the pump transfer step.
        """

        csv_data = []
        LabSource, SourceWell = "undefined_labware", 1 # default values

        _type = "All wells" # to decide where to transfer the volume to.

        # Define labware source name as in Tecan worktable
        if source_labware == "DPBS": #  pos neg conjugate
            LabSource = LabwareNames["DPBS"]
        elif source_labware == "Coating protein":
            # LabSource = self.coat_prot_lw_name
            LabSource = LabwareNames["CoatingProtein"]
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


        sample_wells = flatten(self.pump_lw_well_pos["samples_pos"]) # flatten sample well pos
        print("sample wells:", sample_wells)
        all_wells = self.pump_lw_well_pos["pos_ctr_pos"] + self.pump_lw_well_pos["neg_ctr_pos"] + sample_wells # position of all wells to be used
        
        print("pos_ctr_pos:", self.pump_lw_well_pos["pos_ctr_pos"])
        print("neg_ctr_pos:", self.pump_lw_well_pos["neg_ctr_pos"])

        if _type == "All wells": # transfer to all wells
            for well in all_wells:
                csv_data.append(
                {
                    'LabSource': LabSource,
                    'SourceWell': SourceWell,
                    'LabDest': dest_labware,
                    'DestWell': well,
                    'Volume': volume
                })        
        elif _type == "Only samples": # transfer samples from Eppendorf to wells
            
            # reset positions where samples are, in this case forced to be there ones
            # self.sample_eppendorf_positions = [1,2,1,2,1,2,2,1,2,1,2,1,2,1] # pos 1 is positive ctr, pos 2 is neg ctr

            LabSource, SourceWell = dilution_position_def("Eppendorf", self.sample_eppendorf_positions[0], len(self.sample_eppendorf_positions))

            for i, sample_eppendorf_pos in enumerate(self.sample_eppendorf_positions):
                for well in self.pump_lw_well_pos["samples_pos"][i]:
                    csv_data.append(
                    {
                        'LabSource': LabSource[i],
                        'SourceWell': SourceWell[i],
                        'LabDest': dest_labware,
                        'DestWell': well,
                        'Volume': 100
                    })

        elif _type == "pos/neg":
            for well in self.pump_lw_well_pos["pos_ctr_pos"]: # Positive control
                csv_data.append(
                {
                    # 'LabSource': self.pos_ctr_lw_name,
                    'LabSource': LabwareNames["PosControl"],
                    'SourceWell': 1,
                    'LabDest': dest_labware,
                    'DestWell': well,
                    'Volume': volume
                })

            for well in self.pump_lw_well_pos["neg_ctr_pos"]: # Negative control
                csv_data.append(
                {
                    # 'LabSource': self.neg_ctr_lw_name,
                    'LabSource': LabwareNames["NegControl"],
                    'SourceWell': 1,
                    'LabDest': dest_labware,
                    'DestWell': well,
                    'Volume': volume
                })

        print("before csv generating")
        # Generate CSV file
        path = self.csv_files_path + self.pump_steps_csv_name + "Transfer " + str(csv_number) + ".csv"
        pd.DataFrame(csv_data).to_csv(path, index=False, header=False)


    def dotblot(self):
        """
        Class main method.
        ----------

        Executes all stages of the Dot Blot method step by step and generates CSV files for them.
        """

        pos_control_eppendorf_positions = self.positive_control_dilutions()
        self.pos_ctr_lw_name = pos_2_str("Eppendorf", pos_control_eppendorf_positions) # set position of positive ctr diluted sample
        print("pos dilutions done")
        
        neg_control_eppendorf_positions = self.negative_control_dilutions()
        print(f"negative ctr eppendorf pos: {neg_control_eppendorf_positions}")
        self.neg_ctr_lw_name = pos_2_str("Eppendorf", neg_control_eppendorf_positions) # set position of negative ctr diluted sample
        print("neg dilutions done")

        self.sample_eppendorf_positions = self.sample_dilutions()
        print("sample dilutions done")

        self.generate_pump_step_instruction_files()

        # self.generate_gwl_files() # to reuse tip

        # Call method in utils file
        pattern = r"3\. Pump steps - Transfer (\d+)\.csv"
        convert_all_csv_files_in_directory(self.csv_files_path, pattern)
        print("generated all GWL files")

        return pos_control_eppendorf_positions, neg_control_eppendorf_positions, self.sample_eppendorf_positions

        
    def set_all_parameters(self, external):
        """
        Sets all parameters from self class to be able to generate all CSV files.
        
        Parameters
        ----------
        external : class obj
            Reference to external class object where all parameters will be get from.
        """

        # Reset parameters
        self.last_eppendorf_pos = 1
        self.last_deep_well_pos = 1

        # General
        self.sample_dilution_data = external.sample_dilution_data
        self.coating_protein_dilution_data = external.coating_protein_dilution_data
        self.n_sample_dilution_steps = len(self.sample_dilution_data["Assay buffer volume"])
        self.n_coating_protein_steps = len(self.coating_protein_dilution_data["Assay buffer volume"])

        # Sample
        self.main_sample_labware_type = external.optionmenu_1.get()
        self.n_samples_main_dilution = int(external.entry_slider2.get())
        self.samples_initial_volume_transfer = external.entry_slider3.get()

        # Positive control
        self.pos_control_dilution_data = external.pos_control_dilution_data
        self.n_pos_control_steps = len(self.pos_control_dilution_data["Assay buffer volume"])
        self.pos_control_vial_posX = external.pos_ctr_X_pos.get()
        self.pos_control_vial_posY = external.pos_ctr_Y_pos.get()
        self.pos_control_buffer = external.pos_ctr_buffer.get()
        print("after posc torntol asignation")
        
        self.neg_control_dilution_data = external.neg_control_dilution_data
        self.n_neg_control_steps = len(self.neg_control_dilution_data["Assay buffer volume"])
        self.neg_control_vial_posX = external.neg_ctr_X_pos.get()
        self.neg_control_vial_posY = external.neg_ctr_Y_pos.get()
        self.neg_control_buffer = external.neg_ctr_buffer.get()
        print("AFTER neg external assingnations")

        # Pump steps
        self.pump_steps_data = external.pump_steps_data

        # Labware of reagents
        self.coat_prot_lw_name = "def_coat_prot" # Coating protein labware
        self.blocking_buffer_lw_name = "def_blocking" # Blocking Buffer labware
        self.pos_ctr_lw_name = "def_pos_ctr" # Positive control labware
        self.neg_ctr_lw_name = "def_neg_ctr" # Negative control labware
        self.conjugate_lw_name = "def_conjugate" # Conjugate labware
        self.dpbs_lw_name = "def_dpbs" # DPBS labware

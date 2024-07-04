
# -----------------------
# nano DSF method class #
# -----------------------

import pandas as pd
import numpy as np
from utils import * # file with helper methods


class nanoDSFMethod():
    """
    Produces CSV files with all the steps to carry out the Dot Blot method in the TECAN.
    """

    def __init__(self):
        # General parameters
        self.csv_files_path = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\3. DotBlot' # network path where all the CSV files will be saved in.
        self.last_eppendorf_pos = 1 # position of the last Eppendorf tube used. Useful so that methods don't use same tube twice.
        self.last_deep_well_pos = 1 # position of the last Deep well position used. Useful so that methods don't use same well twice.

        # dictionaries to store all dilution values
        self.sample_dilution_data = {}

        # Sample dilution parameters
        self.n_samples_main_dilution = 0 # amount of samples for the sample dilution
        self.n_sample_dilution_steps = 0 # number of sample dilution steps to achieve final concentration
        self.main_sample_labware_type = "" # where to perform main sample dilutions (deep well or eppendorf)
        self.main_sample_dil_destination = "DeepWell" # All intermediate dilutions will be made in Deep Wells, and then final results will be transfered to Eppendorf tubes
        self.samples_initial_volume_transfer = 300 # At the beginning, transfer once this amount of volume (uL) of the samples to the wells, so that for later steps, all the volumes of the samples can be taken from here with smaller tips rather than changing tip all the time.
        self.sample_eppendorf_positions = 0 # positions of Eppendorf tubes where the diluted samples end up

        self.sample_volume_per_well = 20 # volume (uL) to transfer to each well

        # Labware names
        self.coat_prot_lw_name = "def_coat_prot" # Coating protein labware
        self.blocking_buffer_lw_name = "def_blocking" # Blocking Buffer labware
        self.pos_ctr_lw_name = "def_pos_ctr" # Positive control labware
        self.neg_ctr_lw_name = "def_neg_ctr" # Negative control labware
        self.conjugate_lw_name = "def_conjugate" # Conjugate labware
        self.dpbs_lw_name = "def_dpbs" # DPBS labware
        self.pump_lw_name = "dotblot_appr_standalone" # Pump vacuum labware


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
        print("las eppendorf pos: ", self.last_eppendorf_pos)

        csv_data_init = []
        csv_number = 0 # # to name generated files sequentially
        eppendorf_positions = [] # list to store positions of eppendorf positions used for the final dilution
        
        LabDest, DestWell = dilution_position_def(self.main_sample_dil_destination, self.last_deep_well_pos, self.n_samples_main_dilution)

        # Initial transfer of sample to deep wells, so that smaller tips can reach bottom
        for j in range(1, self.n_samples_main_dilution + 1):
            if self.main_sample_labware_type == "Eppendorf":
                LabSource = pos_2_str(self.main_sample_labware_type, self.last_eppendorf_pos)
                self.next_eppendorf_pos()
            else:
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

        # print("before long csv")
        for i in range(self.n_sample_dilution_steps):
            csv_data_sample = []
            csv_data_buffer = []

            LabSource, SourceWell = LabDest, DestWell # source of next step is destination of previous one

            if i + 1 == self.n_sample_dilution_steps: # if this is the final dilution step
                print("sample last eppensorf pos: ", self.last_eppendorf_pos)
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
                    'LabSource': LabwareNames["AssayBuffer"],
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
        # print("sample wells:", sample_wells)
        all_wells = self.pump_lw_well_pos["pos_ctr_pos"] + self.pump_lw_well_pos["neg_ctr_pos"] + sample_wells # position of all wells to be used
        
        # print("pos_ctr_pos:", self.pump_lw_well_pos["pos_ctr_pos"])
        # print("neg_ctr_pos:", self.pump_lw_well_pos["neg_ctr_pos"])

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
                    'LabSource': self.pos_ctr_lw_name,
                    # 'LabSource': LabwareNames["PosControl"],
                    'SourceWell': 1,
                    'LabDest': dest_labware,
                    'DestWell': well,
                    'Volume': volume
                })

            for well in self.pump_lw_well_pos["neg_ctr_pos"]: # Negative control
                csv_data.append(
                {
                    'LabSource': self.neg_ctr_lw_name,
                    # 'LabSource': LabwareNames["NegControl"],
                    'SourceWell': 1,
                    'LabDest': dest_labware,
                    'DestWell': well,
                    'Volume': volume
                })

        # print("before csv generating")
        # Generate CSV file
        path = self.csv_files_path + self.pump_steps_csv_name + "Transfer " + str(csv_number) + ".csv"
        pd.DataFrame(csv_data).to_csv(path, index=False, header=False)

        print("transfer volume instruction ", csv_number, "done")

  

    def nanoDSF(self):
        """
        Class main method.
        ----------

        Executes all stages of the nanoDSF method step by step and generates CSV files for them.
        """

        self.sample_eppendorf_positions = self.sample_dilutions()
        print("sample dilutions done")

        self.generate_pump_step_instruction_files()

        # Call method in utils file
        pattern = r"3\. Pump steps - Transfer (\d+)\.csv"
        convert_all_csv_files_in_directory(self.csv_files_path, pattern) # to reuse tips
        print("generated all GWL files")

        return self.sample_eppendorf_positions

        
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
        self.n_sample_dilution_steps = len(self.sample_dilution_data["Assay buffer volume"])

        # Sample
        self.main_sample_labware_type = external.optionmenu_1.get()
        self.n_samples_main_dilution = int(external.entry_slider2.get())
        self.samples_initial_volume_transfer = 50 # hard coded for nicolas's test on thu. 4/7

        # Labware of reagents
        self.coat_prot_lw_name = "def_coat_prot" # Coating protein labware
        self.blocking_buffer_lw_name = "def_blocking" # Blocking Buffer labware
        self.pos_ctr_lw_name = "def_pos_ctr" # Positive control labware
        self.neg_ctr_lw_name = "def_neg_ctr" # Negative control labware
        self.conjugate_lw_name = "def_conjugate" # Conjugate labware
        self.dpbs_lw_name = "def_dpbs" # DPBS labware

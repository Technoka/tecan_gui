# from tkinter import filedialog
import pandas as pd
import numpy as np
import re
import os
import json
import logging
from datetime import datetime



# Set up logging configuration
logger = logging.getLogger("assay_logger")
logger.setLevel(logging.DEBUG)


def new_log_file():
    """
    Creates a new log file handler for a method to log into it.
    """

    # Remove all handlers, so that each new call only writes to the new log file
    while logger.handlers:
        handler = logger.handlers[0]
        logger.removeHandler(handler)
        handler.close()

    # name for new log file
    current_time = datetime.now().strftime('%d-%m-%Y_%H-%M')

    logs_folder_name = "logs"

    # Check if the folder exists
    if not os.path.exists(logs_folder_name):
        # Create the folder if it doesn't exist
        os.makedirs(logs_folder_name)

    log_filename = f"{logs_folder_name}/{current_time}.log"
    logger_file_handler = logging.FileHandler(log_filename, encoding="utf-8")  # Log to a file
    logger_file_handler.setLevel(logging.DEBUG)
    logger_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    logger.addHandler(logger_file_handler)

    logger.debug(f"USER: {os.getlogin()}")



# Labware names as defined in Tecan worktable
LabwareNames = {
    "Falcon15": "Falcon15",
    "Falcon50": "Falcon50",
    "Eppendorf": "Eppendorf", # Eppendorf 1.5mL
    "Eppendorf 1.5mL": "Eppendorf", # Eppendorf 1.5mL
    "Eppendorf 2mL": "Eppendorf 2mL", # Eppendorf 2mL
    "FakeFalcon15": "FakeFalcon15",
    "DeepWell": "96 Deep Well 2ml[001]",
    "384_Well": "384 Well[001]",
    "384_Well_Tall": "384 Well Tall[001]",
    "2R Vial": "2R Vial holder[001]",
    "8R Vial": "8R_Vial",
    "8R_Vial neg_ctr": "8R_Vial_neg_ctr", # dotblot negative control vial
    # "CustomVialHolder": "30 Custom_vial_holder[001]",
    "Pos_Ctr_Vial": "Pos_Ctr_Vial", # dotblot small positive control vial with orange cap
    "Orange cap small vial": "Pos_Ctr_Vial", # another name for the vial defined right before this one
    "BlockingBuffer": "100ml_1",
    "DPBS": "100ml_2",
    "AssayBuffer": "100ml_3",
    # "AssayBuffer": "Falcon15[002]",
    "Conjugate": "100ml_4",
    "CoatingProtein": "Falcon15[001]",
    "CoatingProtein_2": "Falcon15[002]",
    "Dye": "100ml_7",
    # "PosControl": "Falcon15[001]",
    # "NegControl": "Falcon15[002]",
    "100mL reservoir": "100ml_1", # the [00x] needs to be added later
    "soloVPE cuvettes": "48 Pos 2R Vial Rack[001]",
    "GeneralBuffer": "100ml_1", # for every method that uses a buffer of any kind, this will be the position
    "BSA tube": "Brown_screw_cap_2ml",
    "16 weird tube runner": "1x16 16mm Tube Runner No Tubes",
    "16 falcon15 tube runner": "1x16 15ml Falcon Tube Runner no Tubes",
    "Mobile Phase": "100ml_1",
    "2mL Vial": "2mL_Vial",
    "UV Cuvette holder": "UV Cuvette holder[001]",
    "UV Cuvette holder 2": "UV Cuvette holder[002]",
    "UV Cuvette": "UV_Cuvette"

}

# IMPORTANT!!! ------ Keys in 'LabwareNames' and in 'AvailableLabware' should match exactly

# Available tubes/wells per labware type as defined in Tecan worktable physically.
AvailableLabware = {
    "Falcon15": 48,
    "Falcon50": 20,
    "Eppendorf": 48,
    "FakeFalcon15": 16,
    "DeepWell": 96,
    "2R Vial": 24, # 4 x 6
    "8R Vial": 12, # 3 x 4
    "CustomVialHolder": 30, # 5 x 6
    "2mL Vial": 40,
    "UV Cuvette": 80,
    "UV Cuvette holder": 40,
    "UV Cuvette holder 2": 40

}

# Collection of labwares that are plates/wells
LabwarePlates = ["DeepWell", 
                 "384_Well", 
                 "2R Vial", 
                 "soloVPE cuvettes",
                 "UV Cuvette holder"]


 # fill the rest and actually do the calculations............................ measure myself with tecan for all tips, place biggest value obtained, most likely for the smaller tips
# labware name: dead_volume, max_volume (in mL)
LABWARE_VOLUMES = {
# #             dead vol, max_vol
    "Eppendorf": [0.05, 1.5],
    "Falcon15": [0.6, 15],
    # "Falcon50": [5, 50],
    # "2R Vial": [0.1, 2],
    # "8R Vial": [0.3, 8],
    "100mL_reservoir": [3, 100]
}


# Dead volume of labware, info in https://confluence.jnj.com/display/VBHI/Dead+volume+of+labware+in+Tecan

# Define the values for each category
# dead volume values in uL, max volume value in mL
data = {
    "Eppendorf": [np.nan, 25, 50, 1.5], # 10uL, 200uL, 1000uL, labware_max_volume
    "Falcon15": [np.nan, 600, 35, 15],
    "100mL_reservoir": [np.nan, np.nan, 2000, 100]
}

LABWARE_DEAD_VOLUMES = pd.DataFrame(data, index=["10uL", "200uL", "1000uL", "max_volume"], columns=data.keys())


def import_excel_dotblot(file_path: str):
    """
    Parses Excel file containing dilution data for Dotblot.

    Parameters
    ----------
    ``file_path``: str
        Path of excel file to parse.

    Returns
    ----------
    Tuple (sample, coating_protein, pos_ctr, neg_ctr) data,
    or ``None`` if error occurs when importing file.
    """
    # file_path = r"L:/Departements/BTDS_AD/002_AFFS/Lab Automation/09. Tecan/06. DotBlot_automation_DPP/DotBlot automation dilution data.xlsx"

    sample_dilution_data = {}
    coating_protein_dilution_data = {}
    pos_control_dilution_data = {}
    neg_control_dilution_data = {}

    # file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])

    # if file_path:
    data = pd.read_excel(file_path, header=5) # read excel file and ignore 5 first rows
    # check if read excel file is the correct one by checking hidden message in specific cell
    if data.columns[0] != "spain is awesome":
        return None

    data = data.iloc[:, 1:9] # ignore first column and all after 8
    data = data.drop(data.columns[4], axis=1) # remove column (because it is empty, just used for excel visual formatting)

    data.loc[len(data)] = [np.nan] * len(data.columns) # add extra row at the end with NaN values, so that subsequent for loops can end correctly

    # remove the units (inside parenthesis) from the column names
    for column in data.columns:
        index = column.find('(') # find the index of the first "(" symbol
        if index != -1: # if a "(" symbol is found
            # rename the column by removing all text after the "(" symbol
            new_column_name = column[:index].strip()
            data.rename(columns={column: new_column_name}, inplace=True)

    # sample dilution - ignore rows with no dilution data
    for index, row in data.iterrows():
        if pd.isna(row["Withdrawn volume"]): # if a NaN value is found
            sample_dilution_data = data.iloc[:index, :] # remove all rows after the first NaN is found in "Initial Concentration" column
            break
    
    # coating protein dilution data is in row 10 after initial read
    for index, row in data.iloc[10:14,:].iterrows():
        if pd.isna(row["Withdrawn volume"]): # if a NaN value is found
            coating_protein_dilution_data = data.iloc[10:index,:] # remove all rows after the first NaN is found in "Initial Concentration" column
            break

    # positive control dilution data is in row 15 after initial read
    for index, row in data.iloc[17:21,:].iterrows():
        if pd.isna(row["Withdrawn volume"]): # if a NaN value is found
            pos_control_dilution_data = data.iloc[17:index,:] # remove all rows after the first NaN is found in "Initial Concentration" column
            break    
    # else:
    #     return -1  

    # negative control dilution data is in row 24 after initial read
    for index, row in data.iloc[24:28,:].iterrows():
        if pd.isna(row["Withdrawn volume"]): # if a NaN value is found
            neg_control_dilution_data = data.iloc[24:index,:] # remove all rows after the first NaN is found in "Initial Concentration" column
            break

    return [sample_dilution_data], [coating_protein_dilution_data], [pos_control_dilution_data], [neg_control_dilution_data]


def import_excel_dotblot_2_coating(file_path: str):
    """
    Parses Excel file containing dilution data (with 2 coating proteins) for Dotblot.

    Parameters
    ----------
    ``file_path``: str
        Path of excel file to parse.

    Returns
    ----------
    Tuple (sample, coating_protein, pos_ctr, neg_ctr) data,
    or ``None`` if error occurs when importing file.
    """
    # file_path = r"L:/Departements/BTDS_AD/002_AFFS/Lab Automation/09. Tecan/06. DotBlot_automation_DPP/DotBlot automation dilution data - 2 coating.xlsx"

    sample_dilution_data = [{}, {}]
    coating_protein_dilution_data = [{}, {}]
    pos_control_dilution_data = [{}, {}]
    neg_control_dilution_data = [{}, {}]

    # file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])

    # if file_path:
    data = pd.read_excel(file_path, header=5) # read excel file and ignore 5 first rows
    # check if read excel file is the correct one by checking hidden message in specific cell
    if data.columns[0] != "spain eurocup winner 2024":
        return None

    data = data.iloc[:, 1:9] # ignore first column and all after 8
    data = data.drop(data.columns[4], axis=1) # remove column (because it is empty, just used for excel visual formatting)

    data.loc[len(data)] = [np.nan] * len(data.columns) # add extra row at the end with NaN values, so that subsequent for loops can end correctly

    # remove the units (inside parenthesis) from the column names
    for column in data.columns:
        index = column.find('(') # find the index of the first "(" symbol
        if index != -1: # if a "(" symbol is found
            # rename the column by removing all text after the "(" symbol
            new_column_name = column[:index].strip()
            data.rename(columns={column: new_column_name}, inplace=True)

    # sample dilution 1 - ignore rows with no dilution data
    for index, row in data.iterrows():
        if pd.isna(row["Withdrawn volume"]): # if a NaN value is found
            sample_dilution_data[0] = data.iloc[:index, :] # remove all rows after the first NaN is found in "Initial Concentration" column
            break

     # sample dilution 2 data is in row 10 after initial read
    for index, row in data.iloc[10:17,:].iterrows():
        if pd.isna(row["Withdrawn volume"]): # if a NaN value is found
            sample_dilution_data[1] = data.iloc[10:index,:] # remove all rows after the first NaN is found in "Initial Concentration" column
            break

    # positive control dilution 1 data is in row 15 after initial read
    for index, row in data.iloc[20:24,:].iterrows():
        if pd.isna(row["Withdrawn volume"]): # if a NaN value is found
            pos_control_dilution_data[0] = data.iloc[20:index,:] # remove all rows after the first NaN is found in "Initial Concentration" column
            break

    # positive control dilution 2 data is in row 15 after initial read
    for index, row in data.iloc[27:31,:].iterrows():
        if pd.isna(row["Withdrawn volume"]): # if a NaN value is found
            pos_control_dilution_data[1] = data.iloc[27:index,:] # remove all rows after the first NaN is found in "Initial Concentration" column
            break

    # negative control dilution data is in row 24 after initial read
    for index, row in data.iloc[34:38,:].iterrows():
        if pd.isna(row["Withdrawn volume"]): # if a NaN value is found
            neg_control_dilution_data[0] = data.iloc[34:index,:] # remove all rows after the first NaN is found in "Initial Concentration" column
            break

    # negative control dilution data is in row 24 after initial read
    for index, row in data.iloc[41:45,:].iterrows():
        if pd.isna(row["Withdrawn volume"]): # if a NaN value is found
            neg_control_dilution_data[1] = data.iloc[41:index,:] # remove all rows after the first NaN is found in "Initial Concentration" column
            break

    return sample_dilution_data, coating_protein_dilution_data, pos_control_dilution_data, neg_control_dilution_data


def import_excel_general_dilution(file_path):
    """
    Parses Excel file containing dilution data for a general dilution.

    Parameters
    ----------
    ``file_path``: str
        Path of excel file to parse.

    Returns
    ----------
    Dictionary with dilution data,
    or ``None`` if error occurs when importing file.
    """

    # file_path = r"L:/Departements/BTDS_AD/002_AFFS/Lab Automation/09. Tecan/06. DotBlot_automation_DPP/DotBlot_automation_dilution_template_final.xlsx"

    sample_dilution_data = {}

    # file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])

    # if file_path:
    data = pd.read_excel(file_path, header=5) # read excel file and ignore 5 first rows
    # check if read excel file is the correct one by checking hidden message in specific cell
    if data.columns[0] != "almeria is awesome":
        return None

    data = data.iloc[:, 1:9] # ignore first column and all after 8
    data = data.drop(data.columns[4], axis=1) # remove column (because it is empty, just used for excel formatting)

    # remove the units (inside parenthesis) from the column names
    for column in data.columns:
        index = column.find('(') # find the index of the first "(" symbol
        if index != -1: # if a "(" symbol is found
            # rename the column by removing all text after the "(" symbol
            new_column_name = column[:index].strip()
            data.rename(columns={column: new_column_name}, inplace=True)

    # ignore rows with no dilution data
    for index, row in data.iterrows():
        if pd.isna(row["Withdrawn volume"]): # if a NaN value is found
            sample_dilution_data = data.iloc[:index, :] # remove all rows after the first NaN is found in "Initial Concentration" column
            break

    return sample_dilution_data


def pos_2_str(name: str, pos):
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

    if not isinstance(pos, int):
        # print(f"pos2str is not an int: found {pos} with type {type(pos)}")
        if len(pos) == 1:
            pos = pos[0]

    if pos < 10:
        new_name = name + "[00"+str(pos)+"]"
    else:
        new_name = name + "[0"+str(pos)+"]"
    
    return new_name


def dilution_position_def(labware_name: str, initial_pos: int, nsamples: int):
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

    if labware_name in LabwarePlates:
        for i in range(0,nsamples):
            Label = np.append(Label,LabwareNames[labware_name]) # labware name is fixed for eppendorf
            Pos = np.append(Pos, int(initial_pos+i))

    else:
        for i in range(0,nsamples):
            name = pos_2_str(labware_name,initial_pos+i) # the labware name gets updated for eppendorf
            Label = np.append(Label,[name])
            Pos = np.append(Pos, int(1)) # this type of labware only has one position, so it is fixed to 1.

    return Label, Pos.astype(int)


def get_deep_well_pos(pos: int, plate_type:int = 96, sample_direction: str = "vertical", sample_transfer:str = "triplicate"):
    """
    Receives a position for a well-plate sample and returns the triplet well positions associated with it.

    Parameters
    ----------
    ``pos``: int
        Position for the whole sample triplet.
    ``plate_type``: int
        Type of plate (96 or 384). Defaults to 96.
    ``sample_direction``: str
        Direction of the sample (either 'vertical' or 'horizontal'). Defaults to 'vertical'.
    ``sample_transfer``: str
        Number of the sample transfers (either 'single' or 'triplicate'). Defaults to 'triplicate'.

    Returns
    ----------
    List containing the well positions of the triplet.

    Examples
    ----------
    >>> get_deep_well_pos(1)
    [1, 9, 17]
    >>> get_deep_well_pos(3, 96)
    [3, 11, 19]
    >>> get_deep_well_pos(9)
    [25, 33, 41]
    >>> get_deep_well_pos(1, 384)
    [1, 17, 33]
    >>> get_deep_well_pos(3, 384)
    [3, 19, 35]
    >>> get_deep_well_pos(3, 384, 'horizontal')
    [97, 113, 129]
    
    """

    if plate_type not in [96, 384]:
        raise ValueError("Invalid plate type. Must be either 96 or 384.")
    
    if sample_direction not in ['vertical', 'horizontal']:
        raise ValueError("Invalid direction. Must be either 'vertical' or 'horizontal'.")
    
    if sample_transfer not in ['single', 'triplicate']:
        raise ValueError("Invalid transfer type. Must be either 'single' or 'triplicate'.")

    if plate_type == 96:
        if pos < 1 or pos > 96:
            return ValueError("Invalid position. Must be between [1-96].")
        
        wells_per_block = 24
        wells_per_col = 8
        wells_per_row = 12

    elif plate_type == 384:
        if pos < 1 or pos > 384:
            return ValueError(f"Invalid position {pos}. Must be between [1-384].")
        wells_per_block = 48
        wells_per_col = 16
        wells_per_row = 24

    # each block has 24 wells, and therefore fits 8 samples in vertical order
    if sample_direction == "vertical":
        if sample_transfer == "triplicate":
            block = int((pos-1) / wells_per_col) # floor operation
            row = pos % wells_per_col
            if row == 0:
                row = wells_per_col

            init_pos = int( block * wells_per_block + row )
        
        else: # sample transfer = "single"
            return pos

    else: # sample direction = "horizontal"
        if sample_transfer == "triplicate":
            row = int((pos-1) / (wells_per_row/3)) + 1
            block = (pos % (wells_per_row/3))
            if block == 0:
                block = wells_per_row/3

            init_pos = int( (block-1) * wells_per_block + row )

        else: # sample transfer = "single"
            row = int(pos / wells_per_row)
            col = pos % wells_per_row
            if col == 0:
                col = 24

            init_pos = row + (col-1) * wells_per_col + 1

            if init_pos == 385:
                init_pos = 384

            return init_pos

    return [init_pos,
            init_pos + wells_per_col,
            init_pos + 2 * wells_per_col]
    

def flatten(matrix):
    """
    Flattens an iterable object.

    Example
    --------
    >>> flatten([[1,2,3], [4,5,6], [7,8,9]])
    [1,2,3,4,5,6,7,8,9]

    """
    
    flat_list = []
    try:
        for row in matrix:
            flat_list += row
        return flat_list
    except TypeError: # if object is not iterable return it as is
        return matrix


def convert_csv_to_gwl(input_file_path:str, output_file_path:str, reuse_tips:bool = True, onetime_tip_change=False):
    """
    Converts all CSV files in the ``path`` directory to GWL.

    Parameters
    ----------
    ``input_file_path``: str
        Path to the input file.

    ``output_file_path``: str
        Path to the output file.
        
    ``reuse_tips``: bool
        Decide if tips can be reused or are changed after each use.

    ``onetime_tip_change``: bool
        If True, the extra ``W`` commands will be removed so that only 8 are left, to ensure that all tips are used only once and then reused throughout the script.

    Example
    --------
    Input: ``3. Pump steps - Transfer 4.csv:``
    >>> Falcon15[001],1,dotblot_appr_standalone,1,100
        Falcon15[001],1,dotblot_appr_standalone,9,100
        Falcon15[001],1,dotblot_appr_standalone,17,100
        Falcon15[002],1,dotblot_appr_standalone,2,100
        Falcon15[002],1,dotblot_appr_standalone,10,100
        Falcon15[002],1,dotblot_appr_standalone,18,100

    Output: ``3. Pump steps - Transfer 4.gwl:``
    >>> A;Falcon15[001];;;1;;100;;;;
        D;dotblot_appr_standalone;;;1;;100;;;;
        F;
        A;Falcon15[001];;;1;;100;;;;
        D;dotblot_appr_standalone;;;9;;100;;;;
        F;
        A;Falcon15[001];;;1;;100;;;;
        D;dotblot_appr_standalone;;;17;;100;;;;
        F;
        A;Falcon15[002];;;1;;100;;;;
        D;dotblot_appr_standalone;;;2;;100;;;;
        F;
        A;Falcon15[002];;;1;;100;;;;
        D;dotblot_appr_standalone;;;10;;100;;;;
        F;
        A;Falcon15[002];;;1;;100;;;;
        D;dotblot_appr_standalone;;;18;;100;;;;
        W;
    """
    
    NUMBER_OF_PARTS = 5 # number of parts per instruction line in the csv file

    # Open the input file in read mode and output file in write mode
    with open(input_file_path, 'r') as input_file, open(output_file_path, 'w') as output_file:
        # Read all lines from the input file
        lines = input_file.readlines()

        output_lines = []
        
        # Process each line in the input file
        for line in lines:
            # Strip any leading/trailing whitespace
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            
            # Split the line by commas
            parts = line.split(',')
            if len(parts) != NUMBER_OF_PARTS:
                continue  # Skip lines that don't have exactly 6 parts
            
            # Extract the values
            first_part = parts[0]
            second_part = parts[1]
            third_part = parts[2]
            fourth_part = parts[3]
            fifth_part = parts[4]
            
            # Create the three lines for the output
            a_line = f"A;{first_part};;;{second_part};;{fifth_part};;;;\n"
            d_line = f"D;{third_part};;;{fourth_part};;{fifth_part};;;;\n"
            w_line = "W;\n" # use F to flush tip remaining contents instead of changing tip, which is actually better for each round
            
            # Append the lines to the output lines list
            output_lines.append(a_line)
            output_lines.append(d_line)
            output_lines.append(w_line)
        
        # If True, the W/F commands will be removed so that only 8 are left, to ensure that all tips are used and all are reused throughout the script,
        # eliminating the unneeded W/F commands and leaving then as evenly distributed as possible.
        if onetime_tip_change:
            # Count the number of "W;" lines
            w_lines_count = sum(1 for line in output_lines if line == "W;\n")
            
            if w_lines_count > 8:
                # Calculate the indices where the "W;" lines should be kept
                total_lines = len(output_lines)
                indices_to_keep = [int(i * (w_lines_count - 1) / 7) for i in range(8)]
                
                # Collect the indices of all "W;" lines
                w_indices = [i for i, line in enumerate(output_lines) if line == "W;\n"]
                
                # Determine which "W;" lines to keep based on calculated indices
                keep_w_indices = [w_indices[i] for i in indices_to_keep]
                
                # Remove "W;" lines that are not in the keep_w_indices
                new_output_lines = [line for i, line in enumerate(output_lines) if line != "W;\n" or i in keep_w_indices]
            else:
                new_output_lines = output_lines
        
        else:
            new_output_lines = output_lines

        # Replace all "W;" with "F;"
        if reuse_tips == True:
            w_indices = [i for i, line in enumerate(new_output_lines) if line == "W;\n"]
            for i in w_indices:  # Exclude the last "W;"
                new_output_lines[i] = "F;\n"

        # Write the lines to the output file
        output_file.writelines(new_output_lines)


def generate_reagent_distribution_gwl(output_file_path:str, open_mode:str, source_lw:str, dest_lw:str, source_pos_start:int, source_pos_end:int, dest_pos_start:int, dest_pos_end:int, volume:int, n_diti_reuses:int, n_multi_dispenses:int, excluded_positions:list[int]=[]):
    """
    Generates a GWL file with a reagent distribution command with the specified parameters.

    Parameters
    ----------
    ``output_file_path``: str
        Path to the output file.
        
    ``open_mode``: str
        Mode to open the output file. Can be 'a' or 'w'.

    ``source_lw``: str
        Labware source name as in Tecan worktable.

    ``dest_lw``: str
        Labware destination name as in Tecan worktable.

    ``source_pos_start``: int
        Start well position of source labware.

    ``source_pos_end``: int
        Start well position of source labware.

    ``dest_pos_start``: int
        Start well position of destination labware.

    ``dest_pos_end``: int
        End well position of destination labware.

    ``volume``: int
        Volume to transfer to destination wells. Same for all wells.

    ``n_diti_reuses``: int
        Maximum number of DiTi reuses allowed (1 for no reuse).

    ``n_multi_dispenses``: int
        Mmaximum number of dispenses in a multi-dispense sequence (1 for no multi-dispense).

    ``excluded_positions``: list[int]
        Optional list of wells in destination labware to be excluded from pipetting.
        
    Example
    --------
    generate_reagent_distribution_gwl("test.gwl", "100ml_1", "dotblot_apparatus", 1, 1, 1, 24, 100, 12, 12)

    >>> Output: ``R;100ml_1;;;1;1;dotblot_apparatus;;;1;24;100;;12;12;0;``
    """
    
    assert(open_mode in ["a", "w"])

    # Open the input file in read mode and output file in write mode
    with open(output_file_path, open_mode) as output_file:
        
        # Create the line for the output
        r_command = f"R;{source_lw};;;{source_pos_start};{source_pos_end};{dest_lw};;;{dest_pos_start};{dest_pos_end};{volume};;{n_diti_reuses};{n_multi_dispenses};0;"

        # If there are some excluded positions, add them at the end
        if isinstance(excluded_positions, list):
            if len(excluded_positions) > 0:
                for excluded_pos in sorted(excluded_positions):
                    r_command = r_command + f"{excluded_pos};"
        
        r_command = r_command + "\n"

        # Write the lines to the output file
        output_file.writelines(r_command)


def generate_sample_transfer_gwl(output_file_path:str, open_mode:str, source_lw:str, dest_lw:str, source_pos_start:int, source_pos_end:int, dest_pos_start:int, dest_pos_end:int, volume:int, n_diti_reuses:int, n_multi_dispenses:int, sample_count:int, replication_count:int, sample_direction:int, replicate_direction:int, excluded_positions:list[int]=[]):
    """
    Generates a GWL file with a reagent distribution command with the specified parameters.

    Parameters
    ----------
    ``output_file_path``: str
        Path to the output file.

    ``open_mode``: str
        Mode to open the output file. Can be 'a' or 'w'.

    ``source_lw``: str
        Labware source name as in Tecan worktable.

    ``dest_lw``: str
        Labware destination name as in Tecan worktable.

    ``source_pos_start``: int
        Start well position of source labware.

    ``source_pos_end``: int
        Start well position of source labware.

    ``dest_pos_start``: int
        Start well position of destination labware.

    ``dest_pos_end``: int
        End well position of destination labware.

    ``volume``: int
        Volume to transfer to destination wells. Same for all wells.

    ``n_diti_reuses``: int
        Maximum number of DiTi reuses allowed (1 for no reuse).

    ``n_multi_dispenses``: int
        Maximum number of dispenses in a multi-dispense sequence (1 for no multi-dispense).

    ``sample_count``: int
        Number of samples.

    ``replication_count``: int
        Number of replicates per sample.

    ``sample_direction``: int
        Direction of samples (0 for vertical, 1 for horizontal).

    ``replicate_direction``: int
        Direction of replicates (0 for vertical, 1 for horizontal).

    ``excluded_positions``: list[int]
        Optional list of wells in destination labware to be excluded from pipetting.
        
    Example
    --------
    generate_sample_transfer_gwl("test.gwl", "100ml_1", "dotblot_apparatus", 1, 1, 1, 24, 100, 12, 12)

    >>> Output: ``R;100ml_1;;;1;1;dotblot_apparatus;;;1;24;100;;12;12;0;``
    """

    assert(open_mode in ["a", "w"])


    # Open the input file in read mode and output file in write mode
    with open(output_file_path, open_mode) as output_file:
        
        # Create the line for the output
        s_command = f"T;{source_lw};;;{source_pos_start};{source_pos_end};{dest_lw};;;{dest_pos_start};{dest_pos_end};{volume};;{n_diti_reuses};{n_multi_dispenses};{sample_count};{replication_count};{sample_direction};{replicate_direction};"

        # If there are some excluded positions, add them at the end
        if isinstance(excluded_positions, list):
            if len(excluded_positions) > 0:
                for excluded_pos in sorted(excluded_positions):
                    s_command = s_command + f"{excluded_pos};"
        
        s_command = s_command + "\n"

        # Write the lines to the output file
        output_file.writelines(s_command)


def convert_all_csv_files_in_directory(path: str, pattern: str):
    """
    Converts all CSV files in the ``path`` directory to GWL.

    Parameters
    ----------
    ``path``: str
        Path where all input files are. It is also where the output files will be saved.

    ``pattern``: str
        Regular expression. Only the files in the directory that match this pattern will be converted.
    """

    # Define the input file pattern
    # file_pattern = re.compile(r'3\. Pump steps - Transfer (\d+)\.csv')
    file_pattern = re.compile(pattern)
    
    # Iterate over all files in the directory
    for filename in os.listdir(path):

        # Check if the filename matches the pattern
        match = file_pattern.match(filename)
        if match:
            # Generate the input and output file paths
            input_file_path = os.path.join(path, filename)
            output_file_path = os.path.join(path, f"{filename.replace('.csv', '.gwl')}")
            
            # Convert the file
            convert_csv_to_gwl(input_file_path, output_file_path)


def generate_methods_and_products(json_path: str):
    """
    Generate list of methods and products found in the JSON file.

    Parameters
    ----------
    ``json_path``: strl
        Path to the JSON file to read.
            
    Returns
    ----------
    ``(METHODS_LIST, PRODUCTS_DICT)``: Tuple
        Tuple with a list of methods as first item, and a dict of products with second item.
    
    Example result:
    ---------------

    METHODS_LIST = ["Dotblot", "FIPA", "DLS", "nDSF"]
    PRODUCTS_DICT = {
        "Dotblot": ["PD1", "Product1_B"],
        "FIPA": ["Product2_A", "Product2_B"],
        "DLS": ["Product3_A", "Product3_B"],
        "nDSF": ["Product3_A", "Product3_B"],
    }
    """
    # read json file
    with open(json_path, "r") as f:
        RAW_ASSAYS_DATA = json.load(f)["assays"]

    METHODS_LIST = []
    PRODUCTS_DICT = {}

    for assay in RAW_ASSAYS_DATA:
        if assay["method"] not in METHODS_LIST:
            METHODS_LIST.append(assay["method"])
        
        if assay["method"] not in PRODUCTS_DICT:
            PRODUCTS_DICT[assay["method"]] = [] # create empty list
            
        PRODUCTS_DICT[assay["method"]].append(assay["product"]) # add product to list

    return (RAW_ASSAYS_DATA, METHODS_LIST, PRODUCTS_DICT)
    

def get_assay_indices(raw_data: list, method: str, product: str) -> list:
    """
    Returns all indexes in ``raw_data`` that match the specified method and product type. 

    Parameters
    ----------
    ``raw_data``: list
        List containing all assay data.
    
    ``method``: str
        Name of the method to search for.

    ``product``: str
        Name of the product to search for.

    Returns
    --------
        List of the indices that match the method and product type.

    """
        
    # Find indexes of matching assays
    matching_indexes = [
        index for index, assay in enumerate(raw_data)
        if assay.get('method').lower() == method.lower() and assay.get('product').lower() == product.lower()
    ]

    return matching_indexes


def divide_string_into_lines(input_string: str, X: int):
    """
    Receives a string and returns the same one but divided into several lines every X characters
    """

    # Initialize an empty result string
    result = ""
    line = ""

    # Iterate over each word in the input string
    for word in input_string.split():
        # Check if adding the next word exceeds the limit X
        if len(line) + len(word) + 1 > X:
            # If it exceeds, add the current line to the result and start a new line
            result += line.strip() + '\n'
            line = word + ' '
        else:
            # Otherwise, add the word to the current line
            line += word + ' '
    
    # Add the last line to the result
    result += line.strip()

    return result


def find_best_container(reagents: dict | float | int):
    """
    Assigns the best labware type for each reagent considering the volume needed.

    """


    if isinstance(reagents, (float | int)):
        volume_needed = reagents
        best_container = None
        best_sum = float('inf')

        for labware, (dead_vol, max_vol) in LABWARE_VOLUMES.items():
            if volume_needed <= max_vol - dead_vol:
                current_sum = max_vol - dead_vol
                if current_sum < best_sum:
                    best_sum = current_sum
                    best_container = labware

        if best_container:
            return best_container
        else:
            return "VOLUME TOO BIG"

    if isinstance(reagents, dict):
        result = {}
        
        for item, volume_needed in reagents.items():
            best_container = None
            best_sum = float('inf')
            
            for labware, (dead_vol, max_vol) in LABWARE_VOLUMES.items():
                if volume_needed <= max_vol - dead_vol:
                    current_sum = max_vol - dead_vol
                    if current_sum < best_sum:
                        best_sum = current_sum
                        best_container = labware
            
            if best_container:
                result[item] = best_container
            else:
                result[item] = "VOLUME TOO BIG"
        
        return result


def calculate_dilution_parameter(init_conc: float, final_conc: float, sample_vol: float = None, total_vol: float = None) -> float:
    """
    Calculates the buffer volume needed for the desired dilution parameters.

    Parameters
    ----------
    ``init_conc``: float
        Sample initial concentration (mg/mL).
    
    ``final_conc``: float
        Sample final concentration (mg/mL).

    ``sample_vol``: float
        Sample withdrawn volume (uL).

    Returns
    --------
        float: Buffer volume needed to get desired dilution parameters (uL).
    """

    assert total_vol is None or sample_vol is None, "Either 'sample_vol' or 'total_vol' have to be 'None'."

    # This is the parameter to calculate
    if total_vol is None:
        total_vol = init_conc * sample_vol / final_conc
        assert total_vol - sample_vol > 0, f"Calculated buffer volume was less than 0: {total_vol - sample_vol}"
        return total_vol - sample_vol
    
    elif sample_vol is None:
        sample_vol = total_vol * final_conc / init_conc
        buffer_vol = total_vol - sample_vol
        assert sample_vol >= 0, f"Calculated sample volume was less than 0: {sample_vol}"
        assert buffer_vol >= 0, f"Calculated buffer volume was less than 0: {buffer_vol}"
        return (sample_vol, buffer_vol)

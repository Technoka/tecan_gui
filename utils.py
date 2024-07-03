# from tkinter import filedialog
import pandas as pd
import numpy as np
import re
import os
import json


# Labware names as defined in Tecan worktable
LabwareNames = {
    "Falcon15": "Falcon15",
    "Falcon50": "Falcon50",
    "Eppendorf": "Eppendorf",
    "DeepWell": "96 Deep Well 2ml[001]",
    "2R Vial": "2R Vial holder[001]",
    "8R Vial": "8R Vial holder[001]",
    "CustomVialHolder": "Custom_vial_holder[001]",
    "AssayBuffer": "100ml_3",
    "DPBS": "100ml_2",
    "BlockingBuffer": "100ml_1",
    "Conjugate": "100ml_4",
    "CoatingProtein": "100ml_5",
    # "PosControl": "Falcon15[001]",
    # "NegControl": "Falcon15[002]",
    "100mL reservoir": "100ml" # the [00x] needs to be added later

}

# IMPORTANT!!! ------ Keys in 'LabwareNames' and in 'AvailableLabware' should match exactly

# Available tubes/wells per labware type as defined in Tecan worktable physically.
AvailableLabware = {
    "Falcon15": 48,
    "Falcon50": 20,
    "Eppendorf": 48,
    "DeepWell": 96,
    "2R Vial": 24, # 4 x 6
    "8R Vial": 12, # 3 x 4
    "CustomVialHolder": 30 # 5 x 6

}

# Collection of labwares that are plates/wells
LabwarePlates = ["DeepWell", "2R Vial", "8R Vial"]


 # fill the rest and actually do the calculations............................ measure myself with tecan for all tips, place biggest value obtained, most likely for the smaller tips
# labware name: dead_volume, max_volume (in mL)
LABWARE_INFO = {
    "Eppendorf": [0.2, 1.5],
    "Falcon15": [0.8, 15],
    # "Falcon50": [5, 50],
    # "2R Vial": [0.1, 2],
    # "8R Vial": [0.3, 8],
    "100mL_reservoir": [2, 100]
}


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
    # file_path = r"L:/Departements/BTDS_AD/002_AFFS/Lab Automation/09. Tecan/06. DotBlot_automation_DPP/DotBlot_automation_dilution_template_final.xlsx"

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
        if pd.isna(row["Initial concentration"]): # if a NaN value is found
            sample_dilution_data = data.iloc[:index, :] # remove all rows after the first NaN is found in "Initial Concentration" column
            break
    
    # coating protein dilution data is in row 10 after initial read
    for index, row in data.iloc[10:14,:].iterrows():
        if pd.isna(row["Initial concentration"]): # if a NaN value is found
            coating_protein_dilution_data = data.iloc[10:index,:] # remove all rows after the first NaN is found in "Initial Concentration" column
            break

    # positive control dilution data is in row 15 after initial read
    for index, row in data.iloc[17:21,:].iterrows():
        if pd.isna(row["Initial concentration"]): # if a NaN value is found
            pos_control_dilution_data = data.iloc[17:index,:] # remove all rows after the first NaN is found in "Initial Concentration" column
            break    
    # else:
    #     return -1  

    # negative control dilution data is in row 24 after initial read
    for index, row in data.iloc[24:28,:].iterrows():
        if pd.isna(row["Initial concentration"]): # if a NaN value is found
            neg_control_dilution_data = data.iloc[24:index,:] # remove all rows after the first NaN is found in "Initial Concentration" column
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
        if pd.isna(row["Initial concentration"]): # if a NaN value is found
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



def get_deep_well_pos(pos: int):
    """
    Receives a position for a Deep Well sample and returns the triplet well positions associated with it.

    Parameters
    ----------
    ``pos``: int
        Position for the whole sample triplet.

    Returns
    ----------
    List containing the well positions of the triplet.

    Examples
    ----------
    >>> get_deep_well_pos(1)
    [1, 9, 17]
    >>> get_deep_well_pos(3)
    [3, 11, 19]
    >>> get_deep_well_pos(9)
    [25, 33, 41]
    
    """

    # each block has 24 wells, and therefore fits 8 samples in vertical order
    block = int((pos-1) / 8) # floor operation
    row = pos % 8
    if row == 0:
        row = 8

    init_pos = block * 24 + row

    return [init_pos, init_pos+8, init_pos+16]


def flatten(matrix):
    """
    Flattens an iterable object.

    Example
    --------
    >>> flatten([[1,2,3], [4,5,6], [7,8,9]])
    [1,2,3,4,5,6,7,8,9]

    """
    
    flat_list = []
    for row in matrix:
        flat_list += row
    return flat_list


def convert_csv_to_gwl(input_file_path, output_file_path, onetime_tip_change=False):
    """
    Converts all CSV files in the ``path`` directory to GWL.

    Parameters
    ----------
    ``input_file_path``: str
        Path to the input file.

    ``output_file_path``: str
        Path to the output file.

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

        # Replace all "W;" with "F;" except the last "W;"
        w_indices = [i for i, line in enumerate(new_output_lines) if line == "W;\n"]
        for i in w_indices[:-1]:  # Exclude the last "W;"
            new_output_lines[i] = "F;\n"

        # Write the lines to the output file
        output_file.writelines(new_output_lines)


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

        for labware, (dead_vol, max_vol) in LABWARE_INFO.items():
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
            
            for labware, (dead_vol, max_vol) in LABWARE_INFO.items():
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

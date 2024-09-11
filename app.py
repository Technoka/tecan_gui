# %% [markdown]
# #### Imports and initial setup

# %%
import os

from tkinter import messagebox
from tkinter import filedialog
import tkinter as tk
from tkinter import ttk
# from PIL import Image, ImageTk
import customtkinter as ctk

import helper.utils as utils # file with helper methods
import helper.Dotblot as Dotblot
import helper.nanoDSF as nanoDSF
import helper.A280 as A280
import helper.SEC_HPLC as SEC_HPLC
import helper.GeneralDilution as GeneralDilution
import helper.VolumeTransfer as VolumeTransfer

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


paths = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\DotBlot Sample Prep' + "\\" +str(1) +'.csv'

dotblot_dilution_excel_path = 'L:/Departements/BTDS_AD/002_AFFS/Lab Automation/09. Tecan/06. DotBlot_automation_DPP/DotBlot automation dilution data.xlsx'
general_dilution_excel_path = 'L:/Departements/BTDS_AD/002_AFFS/Lab Automation/09. Tecan/06. DotBlot_automation_DPP/General_dilution_template.xlsx'

dotblot_method = Dotblot.DotblotMethod()
nDSF_method = nanoDSF.nanoDSFMethod()
a280_method = A280.A280Method()
sec_hplc_method = SEC_HPLC.sec_HPLCMethod()
general_dilution = GeneralDilution.GeneralDilution()
vol_tr = VolumeTransfer.VolumeTransfer()


# %% [markdown]
# ### GUI Classes
# 

# %%
# read JSON assay file and generate methods and products lists
RAW_ASSAYS_DATA, METHODS_LIST, PRODUCTS_DICT = utils.generate_methods_and_products("helper/assays.json")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("Tecan Interface")
        self.geometry(f"{1100}x{580}")
        # self.iconbitmap("gui_icon.ico")

        self.DEBUG = False # debug flag

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 2), weight=0)
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)

        # dictionaries to store all dilution values
        self.sample_dilution_data = {}
        self.coating_protein_dilution_data = {}
        self.pos_control_dilution_data = {}

        # flag to know if an excel file has been imported
        self.is_excel_imported = False

        # create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Method Starter", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.export_csv_button = ctk.CTkButton(self.sidebar_frame, command=self.generate_csv_button_event)
        self.export_csv_button.grid(row=1, column=0, padx=20, pady=10)
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.scaling_label = ctk.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"], command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Tecan Interface v0.4.6\nGenerated 10/09/2024", anchor="w", font=ctk.CTkFont(size=8))
        self.appearance_mode_label.grid(row=9, column=0, padx=20, pady=(10, 0))


        # create middle frame (used for extra information depending on the selected method)
        self.middle_frame = ctk.CTkScrollableFrame(self, width=680)
        self.middle_frame.grid(row=0, column=1, rowspan=3, padx=(10, 0), pady=(10, 0), sticky="nsew")
        # add default label to middle frame
        self.middle_frame_default_label = ctk.CTkLabel(self.middle_frame, text="Import an Excel dilutions file, \nselect the correct options \nand press Generate CSV files.\nAs easy as that.", font=ctk.CTkFont(size=16, weight="bold"))
        self.middle_frame_default_label.pack()

        # create warning and errors frame at bottom
        self.warning_frame = ctk.CTkScrollableFrame(self, width=680)
        self.warning_frame.grid(row=3, column=1, padx=(10, 0), pady=(10, 0), sticky="sew")
        # dictionary to store warning/error messages
        self.warning_labels = {}

        self.logo_label = ctk.CTkLabel(self.warning_frame, text="Information/Warnings/Errors", font=ctk.CTkFont(size=14, weight="bold"))
        self.logo_label.pack()

        # create tabview
        self.right_scrollable_frame = ctk.CTkScrollableFrame(self, width=280)
        self.right_scrollable_frame.grid(row=0, column=2, padx=(0, 0), pady=(0, 0), rowspan=4, sticky="nsew")


        self.tabview = ctk.CTkTabview(self.right_scrollable_frame, width=280, command=self.tab_changed)
        self.tabview.grid(row=1, column=0, padx=(10, 0), pady=(10, 0), rowspan=4, sticky="nsew")
        self.tabview.add("Assay")
        self.tabview.add("General dilution")
        self.tabview.add("Vol. transfer")
        self.tabview.tab("Assay").grid_columnconfigure(0, weight=2)  # configure grid of individual tabs
        self.tabview.tab("General dilution").grid_columnconfigure(0, weight=2)
        self.tabview.tab("Vol. transfer").grid_columnconfigure(0, weight=2)


        # Variables ==============================================================================
        self.var_assay_tmd = tk.StringVar(value="---")
        self.chosen_method = tk.StringVar(value="---")
        self.chosen_product = tk.StringVar(value="---")
        self.chosen_tmd = tk.StringVar(value="---")
        self.chosen_title = tk.StringVar(value="---")

        self.confirm_check_assay = tk.BooleanVar(value=False)

        self.n_samples = tk.IntVar()
        # self.labware_text = tk.StringVar(value="Import an Excel dilution file\nto see the labware needed\nfor each reagent.\n")

        # Pos/Neg control
        self.pos_ctr_X_pos = tk.StringVar(value="A")
        self.pos_ctr_Y_pos = tk.IntVar(value=1) # if we don't specify an initial value it gets 0 by default, which is not allowed in this case, so we initialize to 1 to avoid errors
        self.neg_ctr_X_pos = tk.StringVar()
        self.neg_ctr_Y_pos = tk.IntVar(value=1)
        self.pos_ctr_buffer = tk.StringVar()
        self.neg_ctr_buffer = tk.StringVar()

        # Reagents volumes
        # self.text_samples_vol = tk.StringVar(value="?, ? mL needed\n")
        # self.vol_samples = tk.DoubleVar()
        self.text_conjugate_vol = tk.StringVar(value="?, ? mL needed\n")
        self.vol_conjugate = tk.DoubleVar()
        self.text_coating_protein_vol = tk.StringVar(value="?, ? mL needed\n")
        self.vol_coating_protein = tk.DoubleVar()
        self.text_dpbs_vol = tk.StringVar(value="?, ? mL needed\n")
        self.vol_dpbs = tk.DoubleVar()
        self.text_assay_buffer_vol = tk.StringVar(value="?, ? mL needed\n")
        self.vol_assay_buffer = tk.DoubleVar()
        self.text_blocking_buffer_vol = tk.StringVar(value="?, ? mL needed\n")
        self.vol_blocking_buffer = tk.DoubleVar()

        # self.check_dotblot = tk.BooleanVar(value=False)

        self.REAGENTS_LABWARE_LIST = ["Falcon15", "Falcon50", "2R Vial", "8R Vial", "Eppendorf", "100mL reservoir"] # list with labware names where reagents can be placed
        self.SAMPLES_LABWARE_LIST = ["Falcon15", "Falcon50", "2R Vial", "8R Vial", "Eppendorf", "FakeFalcon15"] # list with labware names where samples can be placed

        # general dilution
        self.check_gd = tk.BooleanVar(value=False)

        # volume transfer
        self.check_vt = tk.BooleanVar(value=False)


        # nanoDSF
        self.nDSF_n_samples = tk.IntVar(value=1)
        self.nDSF_lw_origin = tk.StringVar(value="---")
        self.nDSF_volume = tk.StringVar(value="20")
        self.nDSF_sample_triplicates = tk.StringVar(value="Single transfer")
        self.nDSF_add_BSA = tk.BooleanVar(value="False") # if it is allowed, decide if you want to add BSA to first column of each row
        # self.check_nDSF = tk.BooleanVar(value=False)
        
        # A280
        self.a280_n_samples = tk.IntVar(value=1)
        self.a280_lw_origin = tk.StringVar(value="---")
        self.a280_concentration = tk.StringVar(value="100")
        # self.check_a280 = tk.BooleanVar(value=False)
        
        # SEC-HPLC
        self.sec_HPLC_n_samples = tk.IntVar(value=1)
        self.sec_HPLC_lw_origin = tk.StringVar(value="---")
        self.sec_HPLC_initial_concentration = tk.StringVar(value="100")
        self.sec_HPLC_lw_dest = tk.StringVar(value="---")
        # self.check_sec_HPLC = tk.BooleanVar(value=False)


# ========================================================================================================================000

        # Assay
        self.title_assay = ctk.CTkLabel(self.tabview.tab("Assay"), text="Assay", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_assay.pack(pady=(1, 6))
        self.label_1d = ctk.CTkLabel(self.tabview.tab("Assay"), text="Choose method:", width=120, height=25, corner_radius=8)
        self.label_1d.pack(padx=20, pady=(5, 1))
        self.optionmenu_method = ctk.CTkOptionMenu(self.tabview.tab("Assay"), dynamic_resizing=False, values=METHODS_LIST, variable=self.chosen_method, command=self.update_method)
        self.optionmenu_method.pack(padx=20, pady=(1, 5))
        self.label_1d = ctk.CTkLabel(self.tabview.tab("Assay"), text="Choose product type:", width=120, height=25, corner_radius=8)
        self.label_1d.pack(padx=20, pady=(5, 1))
        self.optionmenu_product = ctk.CTkOptionMenu(self.tabview.tab("Assay"), width=180, dynamic_resizing=False, values=[], variable=self.chosen_product, command=self.update_assay_info)
        self.optionmenu_product.pack(padx=20, pady=(1, 5))
        self.label_1d = ctk.CTkLabel(self.tabview.tab("Assay"), text="Assay information:", width=120, height=25, corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"))
        self.label_1d.pack(padx=20, pady=(5, 1))
        self.label_assay_code = ctk.CTkLabel(self.tabview.tab("Assay"), text="Assay code: ---", width=120, height=25,corner_radius=8)
        self.label_assay_code.pack(padx=20, pady=(1, 1))
        self.label_assay_title = ctk.CTkLabel(self.tabview.tab("Assay"), text="Assay title: ---", width=120, height=25,corner_radius=8)
        self.label_assay_title.pack(padx=20, pady=(1, 1))
        self.separator = ttk.Separator(self.tabview.tab("Assay"), orient='horizontal')
        self.separator.pack(fill='x', pady=(10, 10))

        
        self.assay_method_frame = ctk.CTkFrame(self.tabview.tab("Assay"), width=280)
        self.assay_method_frame.pack(padx=(0, 0), pady=(10, 0))


        # GENERAL DILUTION ===============================================================================
        self.separator = ttk.Separator(self.tabview.tab("General dilution"), orient='horizontal')
        self.separator.pack(fill='x')
        self.title_gd = ctk.CTkLabel(self.tabview.tab("General dilution"), text="Dilutions file", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_gd.pack(pady=(1, 6))
        self.open_csv_dilution = ctk.CTkButton(self.tabview.tab("General dilution"), text="Open and edit Excel", state="normal", command=lambda: os.startfile(general_dilution_excel_path), fg_color="#2ca39b", hover_color="#1bb5ab")
        self.open_csv_dilution.pack(padx=2, pady=(5, 5))
        self.import_csv_button = ctk.CTkButton(self.tabview.tab("General dilution"), text="Import Excel", state="normal", command=self.import_excel_gen_dil, fg_color="#288230", hover_color="#235e28")
        self.import_csv_button.pack(padx=2, pady=(5, 20))
        self.separator = ttk.Separator(self.tabview.tab("General dilution"), orient='horizontal')
        self.separator.pack(fill='x')

        # Samples
        self.title_sample = ctk.CTkLabel(self.tabview.tab("General dilution"), text="Samples", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_sample.pack(pady=(1, 6))
        self.label_1d = ctk.CTkLabel(self.tabview.tab("General dilution"), text="Sample origin:", width=120, height=25, corner_radius=8)
        self.label_1d.pack(padx=20, pady=(5, 1))
        self.optionmenu_1_gd = ctk.CTkOptionMenu(self.tabview.tab("General dilution"), dynamic_resizing=False, values=["Falcon15", "Falcon50", "2R Vial", "8R Vial", "Eppendorf"])
        self.optionmenu_1_gd.pack(padx=20, pady=(1, 10))
        self.label_slider2_gd = ctk.CTkLabel(self.tabview.tab("General dilution"), text="Number of samples: 1", width=120, height=25,corner_radius=8)
        self.label_slider2_gd.pack(padx=20, pady=(1, 1))
        self.entry_slider2_gd = ctk.CTkSlider(self.tabview.tab("General dilution"), from_=1, to=25, number_of_steps=24, command=self.gd_slider)
        self.entry_slider2_gd.set(1) # set initial value
        self.entry_slider2_gd.pack(padx=20, pady=(1, 5))
        self.title_buffer = ctk.CTkLabel(self.tabview.tab("General dilution"), text="Buffer:", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_buffer.pack(pady=(1, 6))
        self.optionmenu_buffer1_gd = ctk.CTkOptionMenu(self.tabview.tab("General dilution"), values=["DPBS", "Blocking buffer"])
        self.optionmenu_buffer1_gd.pack()
        self.separator = ttk.Separator(self.tabview.tab("General dilution"), orient='horizontal')
        self.separator.pack(fill='x', pady=(10, 10))
        self.label_1d = ctk.CTkLabel(self.tabview.tab("General dilution"), text="Dilution destination:", width=120, height=25, corner_radius=8)
        self.label_1d.pack(padx=20, pady=(5, 1))
        self.gd_dil_dest = ctk.CTkOptionMenu(self.tabview.tab("General dilution"), dynamic_resizing=False, values=["Falcon15", "Falcon50", "2R Vial", "8R Vial", "Eppendorf"])
        self.gd_dil_dest.pack(padx=20, pady=(1, 10))
        self._check_gd = ctk.CTkCheckBox(self.tabview.tab("General dilution"), text="Confirm", variable=self.confirm_check_assay)
        self._check_gd.pack(padx=0, pady=(20, 10))


        # VOLUME TRANSFER ===============================================================================

        # Samples
        self.separator = ttk.Separator(self.tabview.tab("Vol. transfer"), orient='horizontal')
        self.separator.pack(fill='x')
        self.title_sample = ctk.CTkLabel(self.tabview.tab("Vol. transfer"), text="Configuration parameters", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_sample.pack(pady=(1, 6))
        self.label_1d = ctk.CTkLabel(self.tabview.tab("Vol. transfer"), text="Sample origin:", width=120, height=25, corner_radius=8)
        self.label_1d.pack(pady=(5, 1))
        self.optionmenu_1_vt = ctk.CTkOptionMenu(self.tabview.tab("Vol. transfer"), dynamic_resizing=False, values=["Falcon15", "Falcon50", "2R Vial", "8R Vial", "Eppendorf"])
        self.optionmenu_1_vt.pack(pady=(1, 10))
        self.label_slider2_vt = ctk.CTkLabel(self.tabview.tab("Vol. transfer"), text="Number of samples: 1", width=120, height=25,corner_radius=8)
        self.label_slider2_vt.pack(pady=(1, 1))
        self.entry_slider2_vt = ctk.CTkSlider(self.tabview.tab("Vol. transfer"), from_=1, to=25, number_of_steps=24, command=self.vt_sample_slider)
        self.entry_slider2_vt.set(1) # set initial value
        self.entry_slider2_vt.pack(pady=(1, 5))
        self.label_1d = ctk.CTkLabel(self.tabview.tab("Vol. transfer"), text="Volume (uL):", width=120, height=25, corner_radius=8)
        self.label_1d.pack(padx=20, pady=(5, 1))
        self.vt_volume = ctk.CTkEntry(self.tabview.tab("Vol. transfer"),placeholder_text="1", validate="all", validatecommand=(self.register(self.validate_input), "%P"))
        self.vt_volume.pack(pady=(1, 10))
        self.label_slider3_vt = ctk.CTkLabel(self.tabview.tab("Vol. transfer"), text="Repetitions at destination: 1", width=120, height=25,corner_radius=8)
        self.label_slider3_vt.pack(pady=(1, 1))
        self.entry_slider3_vt = ctk.CTkSlider(self.tabview.tab("Vol. transfer"), from_=1, to=5, number_of_steps=4, command=self.vt_repetition_slider)
        self.entry_slider3_vt.set(1) # set initial value
        self.entry_slider3_vt.pack(pady=(1, 5)) 
        self.label_1d = ctk.CTkLabel(self.tabview.tab("Vol. transfer"), text="Sample destination:", width=120, height=25, corner_radius=8)
        self.label_1d.pack(pady=(5, 1))
        self.vt_dest = ctk.CTkOptionMenu(self.tabview.tab("Vol. transfer"), dynamic_resizing=False, values=["Falcon15", "Falcon50", "2R Vial", "8R Vial", "Eppendorf"])
        self.vt_dest.pack(pady=(1, 10))
        self._check_vt = ctk.CTkCheckBox(self.tabview.tab("Vol. transfer"), text="Confirm", variable=self.confirm_check_assay)
        self._check_vt.pack(padx=0, pady=(20, 10))


        # set default values
        self.export_csv_button.configure(state="normal", text="Generate CSV files", fg_color="#25702b", hover_color="#235e28")
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")
        self.toplevel_window = None



    def update_side_panel_options(self):
        
            # Forget the widget from its geometry manager
        for widget in self.assay_method_frame.winfo_children():
            widget.pack_forget()


        if self.chosen_method.get() == "Dotblot":

            # DOT BLOT ===============================================================================
            self.separator = ttk.Separator(self.assay_method_frame, orient='horizontal')
            self.separator.pack(fill='x')
            self.title_pos_control = ctk.CTkLabel(self.assay_method_frame, text="Dilutions file", font=ctk.CTkFont(size=16, weight="bold"))
            self.title_pos_control.pack(pady=(1, 6))
            self.open_csv_dilution = ctk.CTkButton(self.assay_method_frame, text="Open and edit Excel", state="normal", command=self.open_dotblot_excel_file, fg_color="#2ca39b", hover_color="#1bb5ab")
            self.open_csv_dilution.pack(padx=2, pady=(5, 5))
            self.import_csv_button = ctk.CTkButton(self.assay_method_frame, text="Import Excel", state="normal", command=self.import_excel_dotblot, fg_color="#288230", hover_color="#235e28")
            self.import_csv_button.pack(padx=2, pady=(5, 20))
            self.separator = ttk.Separator(self.assay_method_frame, orient='horizontal')
            self.separator.pack(fill='x')

            # Samples
            self.title_sample = ctk.CTkLabel(self.assay_method_frame, text="Samples", font=ctk.CTkFont(size=16, weight="bold"))
            self.title_sample.pack(pady=(1, 6))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Sample type:", width=120, height=25, corner_radius=8)
            self.label_1d.pack(padx=20, pady=(5, 1))
            self.optionmenu_1 = ctk.CTkOptionMenu(self.assay_method_frame, dynamic_resizing=False, values=["Eppendorf", "Falcon15", "FakeFalcon15"])
            self.optionmenu_1.pack(padx=20, pady=(1, 10))
            self.label_slider2 = ctk.CTkLabel(self.assay_method_frame, text="Number of samples: 1", width=120, height=25,corner_radius=8)
            self.label_slider2.pack(padx=20, pady=(1, 1))
            self.entry_slider2 = ctk.CTkSlider(self.assay_method_frame, from_=1, to=25, number_of_steps=24, variable=self.n_samples, command=self.samples_slider)
            self.entry_slider2.set(1) # set initial value
            self.entry_slider2.pack(padx=20, pady=(1, 5))
            self.separator = ttk.Separator(self.assay_method_frame, orient='horizontal')
            self.separator.pack(fill='x', pady=(10, 10))

            # Positive control
            self.title_pos_control = ctk.CTkLabel(self.assay_method_frame, text="Positive control", font=ctk.CTkFont(size=16, weight="bold"))
            self.title_pos_control.pack(pady=(1, 6))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Vial position:", width=120, height=25, corner_radius=8)
            self.label_1d.pack(padx=20, pady=(5, 1))
            self.vial_pos_frame1 = ctk.CTkFrame(self.assay_method_frame, width=280)
            self.vial_pos_frame1.pack(pady=(5, 6))
            self.optionmenu_vials1 = ctk.CTkOptionMenu(self.vial_pos_frame1, width=60, values=["A", "B", "C", "D", "E"], variable=self.pos_ctr_X_pos)
            self.optionmenu_vials1.pack(side=tk.LEFT, padx=10)
            self.optionmenu_vials1a = ctk.CTkOptionMenu(self.vial_pos_frame1, width=60, values=["1", "2", "3", "4", "5", "6"], variable=self.pos_ctr_Y_pos)
            self.optionmenu_vials1a.pack(side=tk.LEFT, padx=10)
            self.separator = ttk.Separator(self.assay_method_frame, orient='horizontal')
            self.separator.pack(fill='x', pady=(10, 10))

            # Labware of reagents
            self.title_pos_control = ctk.CTkLabel(self.assay_method_frame, text="Labware of reagents", font=ctk.CTkFont(size=16, weight="bold"))
            self.title_pos_control.pack(pady=(1, 6))
            self.title_pump_steps = ctk.CTkLabel(self.assay_method_frame, text="Automatic calculation of\nlabware and volumes needed\n")
            self.title_pump_steps.pack(pady=(1, 3))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Conjugate:", width=120, height=25, corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#b85d33")
            self.label_1d.pack(padx=20, pady=(5, 1))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, textvariable=self.text_conjugate_vol, width=120, height=25, corner_radius=8)
            self.label_1d.pack(padx=20, pady=(5, 10))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Coating protein(s)", width=120, height=25, corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#a2b833")
            self.label_1d.pack(padx=20, pady=(5, 1))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, textvariable=self.text_coating_protein_vol, width=120, height=25, corner_radius=8)
            self.label_1d.pack(padx=20, pady=(5, 10))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="DPBS", width=120, height=25, corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#33b87e")
            self.label_1d.pack(padx=20, pady=(5, 1))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, textvariable=self.text_dpbs_vol, width=120, height=25, corner_radius=8)
            self.label_1d.pack(padx=20, pady=(5, 10))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Assay buffer", width=120, height=25, corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#3350b8")
            self.label_1d.pack(padx=20, pady=(5, 1))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, textvariable=self.text_assay_buffer_vol, width=120, height=25, corner_radius=8)
            self.label_1d.pack(padx=20, pady=(5, 10))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Blocking buffer", width=120, height=25, corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#9033b8")
            self.label_1d.pack(padx=20, pady=(5, 1))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, textvariable=self.text_blocking_buffer_vol, width=120, height=25, corner_radius=8)
            self.label_1d.pack(padx=20, pady=(5, 10))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Dye", width=120, height=25, corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#b8337e")
            self.label_1d.pack(padx=20, pady=(5, 1))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="100mL_reservoir, 15mL needed", width=120, height=25, corner_radius=8)
            self.label_1d.pack(padx=20, pady=(5, 10))
            self.separator = ttk.Separator(self.assay_method_frame, orient='horizontal')
            self.separator.pack(fill='x', pady=(10, 10))


            # Confirm button
            self.separator = ttk.Separator(self.assay_method_frame, orient='horizontal')
            self.separator.pack(fill='x', pady=(10, 10))
            self._check_dotblot = ctk.CTkCheckBox(self.assay_method_frame, text="Confirm", variable=self.confirm_check_assay)
            self._check_dotblot.pack(padx=0, pady=(20, 10))


        elif self.chosen_method.get() == "nDSF":

            self.title_sample = ctk.CTkLabel(self.assay_method_frame, text="Configuration parameters", font=ctk.CTkFont(size=16, weight="bold"))
            self.title_sample.pack(pady=(1, 6))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Sample origin:", width=120, height=25, corner_radius=8)
            self.label_1d.pack(pady=(5, 1))
            self.optionmenu_1 = ctk.CTkOptionMenu(self.assay_method_frame, dynamic_resizing=False, variable=self.nDSF_lw_origin, values=["FakeFalcon15", "Falcon15", "Eppendorf"])
            self.optionmenu_1.pack(pady=(1, 10))
            self.optionmenu_1.set("FakeFalcon15")
            self.label_slider_nDSF = ctk.CTkLabel(self.assay_method_frame, text="Number of samples: " + str(self.nDSF_n_samples.get()), width=120, height=25,corner_radius=8)
            self.label_slider_nDSF.pack(pady=(1, 1))
            self.entry_slider2 = ctk.CTkSlider(self.assay_method_frame, from_=1, to=25, number_of_steps=24, command=self.nDSF_sample_slider, variable=self.nDSF_n_samples)
            self.entry_slider2.set(1) # set initial value
            self.entry_slider2.pack(pady=(1, 5))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Volume (uL):", width=120, height=25, corner_radius=8)
            self.label_1d.pack(padx=20, pady=(5, 1))
            self.volume = ctk.CTkEntry(self.assay_method_frame,placeholder_text=self.nDSF_volume.get(), validate="all", validatecommand=(self.register(self.validate_input), "%P"), textvariable=self.nDSF_volume)
            self.volume.pack(pady=(1, 10))
            self._check_triplicates = ctk.CTkSwitch(self.assay_method_frame, textvariable=self.nDSF_sample_triplicates, variable=self.nDSF_sample_triplicates, onvalue="Triplicate transfer", offvalue="Single Transfer", command=self.nDSF_sample_transfer)
            self._check_triplicates.pack(padx=0, pady=(10, 5))
            self._check_add_BSA = ctk.CTkCheckBox(self.assay_method_frame, text="Add BSA to first column", variable=self.nDSF_add_BSA)
            self._check_add_BSA.pack(padx=0, pady=(5, 10))

            # Confirm button
            self.separator = ttk.Separator(self.assay_method_frame, orient='horizontal')
            self.separator.pack(fill='x', pady=(10, 10))
            self._check_nDSF = ctk.CTkCheckBox(self.assay_method_frame, text="Confirm", variable=self.confirm_check_assay)
            self._check_nDSF.pack(padx=0, pady=(20, 10))


        elif self.chosen_method.get() == "A280 (soloVPE)":

            self.title_sample = ctk.CTkLabel(self.assay_method_frame, text="Configuration parameters", font=ctk.CTkFont(size=16, weight="bold"))
            self.title_sample.pack(pady=(1, 6))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Sample origin:", width=120, height=25, corner_radius=8)
            self.label_1d.pack(pady=(5, 1))
            self.optionmenu_1 = ctk.CTkOptionMenu(self.assay_method_frame, dynamic_resizing=False, variable=self.a280_lw_origin, values=["Falcon15", "FakeFalcon15", "Eppendorf"])
            self.optionmenu_1.pack(pady=(1, 10))
            self.label_slider_a280 = ctk.CTkLabel(self.assay_method_frame, text="Number of samples: " + str(self.a280_n_samples.get()), width=120, height=25,corner_radius=8)
            self.label_slider_a280.pack(pady=(1, 1))
            self.entry_slider2 = ctk.CTkSlider(self.assay_method_frame, from_=1, to=25, number_of_steps=24, command=self.a280_sample_slider, variable=self.a280_n_samples)
            self.entry_slider2.set(1) # set initial value
            self.entry_slider2.pack(pady=(1, 5))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Sample concentration (mg/mL):", width=120, height=25, corner_radius=8)
            self.label_1d.pack(padx=20, pady=(5, 1))
            self.volume = ctk.CTkEntry(self.assay_method_frame,placeholder_text="100", validate="all", validatecommand=(self.register(self.validate_input), "%P"), textvariable=self.a280_concentration)
            self.volume.pack(pady=(1, 10))

            # Confirm button
            self.separator = ttk.Separator(self.assay_method_frame, orient='horizontal')
            self.separator.pack(fill='x', pady=(10, 10))
            self._check_a280 = ctk.CTkCheckBox(self.assay_method_frame, text="Confirm", variable=self.confirm_check_assay)
            self._check_a280.pack(padx=0, pady=(20, 10))
    
        elif self.chosen_method.get() == "SEC-HPLC":

            self.title_sample = ctk.CTkLabel(self.assay_method_frame, text="Configuration parameters", font=ctk.CTkFont(size=16, weight="bold"))
            self.title_sample.pack(pady=(1, 6))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Sample origin:", width=120, height=25, corner_radius=8)
            self.label_1d.pack(pady=(5, 1))
            self.optionmenu_1 = ctk.CTkOptionMenu(self.assay_method_frame, dynamic_resizing=False, variable=self.sec_HPLC_lw_origin, values=["Falcon15", "FakeFalcon15", "Eppendorf"])
            self.optionmenu_1.pack(pady=(1, 10))
            self.label_slider_sec_HPLC = ctk.CTkLabel(self.assay_method_frame, text="Number of samples: " + str(self.a280_n_samples.get()), width=120, height=25,corner_radius=8)
            self.label_slider_sec_HPLC.pack(pady=(1, 1))
            self.entry_slider2 = ctk.CTkSlider(self.assay_method_frame, from_=1, to=25, number_of_steps=24, command=self.sec_HPLC_sample_slider, variable=self.sec_HPLC_n_samples)
            self.entry_slider2.set(1) # set initial value
            self.entry_slider2.pack(pady=(1, 5))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Sample concentration (mg/mL):", width=120, height=25, corner_radius=8)
            self.label_1d.pack(padx=20, pady=(5, 1))
            self.volume = ctk.CTkEntry(self.assay_method_frame,placeholder_text="100", validate="all", validatecommand=(self.register(self.validate_input), "%P"), textvariable=self.sec_HPLC_initial_concentration)
            self.volume.pack(pady=(1, 10))
            self.label_1d = ctk.CTkLabel(self.assay_method_frame, text="Sample destination:", width=120, height=25, corner_radius=8)
            self.label_1d.pack(pady=(5, 1))
            self.optionmenu_1 = ctk.CTkOptionMenu(self.assay_method_frame, dynamic_resizing=False, variable=self.sec_HPLC_lw_dest, values=["Falcon15", "FakeFalcon15", "Eppendorf"])
            self.optionmenu_1.pack(pady=(1, 10))

            # Confirm button
            self.separator = ttk.Separator(self.assay_method_frame, orient='horizontal')
            self.separator.pack(fill='x', pady=(10, 10))
            self._check_a280 = ctk.CTkCheckBox(self.assay_method_frame, text="Confirm", variable=self.confirm_check_assay)
            self._check_a280.pack(padx=0, pady=(20, 10))
    


# ------------------------------------------------------------------------------------------------------------------------------------------------------- #

    def test(self):
        # print("sample truplicate value variable:", self.sample_triplicates.get())
        pass

# ------------------------------------------------------------------------------------------------------------------------------------------------------- #

    def reset_reagent_volumes(self):
        self.text_conjugate_vol.set("?, ? mL needed\n")
        self.text_coating_protein_vol.set(value="?, ? mL needed\n")
        self.text_dpbs_vol.set(value="?, ? mL needed\n")
        self.text_assay_buffer_vol.set(value="?, ? mL needed\n")
        self.text_blocking_buffer_vol.set(value="?, ? mL needed\n")

    def open_dotblot_excel_file(self):
        
        initial_dir = r"L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\06. DotBlot_automation_DPP"
        
        method_index = utils.get_assay_indices(RAW_ASSAYS_DATA,self.chosen_method.get(), self.chosen_product.get())[0]

        # read correct excel depending if the method has 1 coating protein or 2
        try:
            if RAW_ASSAYS_DATA[method_index]["has_2_coating_proteins"] == "True":
                file_path = initial_dir + r"\DotBlot automation dilution data - 2 coating.xlsx"
        except:
            file_path = initial_dir + r"\DotBlot automation dilution data.xlsx"

        os.startfile(file_path)
        

    def update_method(self, chosen_method):
        # Update the product options based on the selected method
        products = PRODUCTS_DICT.get(chosen_method, [])
        self.optionmenu_product.configure(values=products)
        if products:
            self.chosen_product.set(products[0])  # Set default selection to the first product
        self.update_assay_info()


        # update side panel with correct options
        self.update_side_panel_options()


    def update_assay_info(self, event=None):
        indices = utils.get_assay_indices(RAW_ASSAYS_DATA, self.chosen_method.get(), self.chosen_product.get())
        self.chosen_tmd.set(RAW_ASSAYS_DATA[indices[0]]["tmd"])
        self.chosen_title.set(RAW_ASSAYS_DATA[indices[0]]["title"])
        title_text = utils.divide_string_into_lines(self.chosen_title.get(), 35)

        self.label_assay_code.configure(text="Assay code: " + self.chosen_tmd.get())
        self.label_assay_title.configure(text=title_text)

        self.confirm_check_assay.set(False) # uncheck confirm button
        
        # reset read excel data if present
        if self.is_excel_imported:
            self.tab_changed() # this method resets the middle frame
        
        self.reset_reagent_volumes()

    
    def assay_changed(self, event): # DEPRECATED

        # get index of TMD inside JSON file
        index = 0
        for _index, tmd in enumerate(RAW_ASSAYS_DATA["assays"]):
            print("before raw asssay data")
            if self.var_assay_tmd.get() == list(tmd.keys())[0]:
                index = _index
                break
        print("after raw das")

        self.label_assay.configure(text="Assay code: " + self.var_assay_tmd.get())
        self.label_assay_type.configure(text="Assay type: " + RAW_ASSAYS_DATA["assays"][index][self.var_assay_tmd.get()]["type"])

        self.reset_reagent_volumes()


    def nDSF_sample_transfer(self):
        if self.nDSF_sample_triplicates.get() == "Single Transfer":
            self._check_add_BSA.configure(state=tk.NORMAL)
        else:
            self._check_add_BSA.configure(state=tk.DISABLED)
            self._check_add_BSA.deselect()

    def sample_initial_volume_slider(self, event):
        self.label_slider3.configure(text="Initial volume transfer: " + str(int(self.entry_slider3.get())) + " uL")

    def samples_slider(self, event):
        self.label_slider2.configure(text="Number of samples: " + str(int(self.entry_slider2.get())))

        # update labware reagents calculations
        if self.is_excel_imported == False:
            return

        self.calculate_volumes_dotblot()

    def sec_HPLC_sample_slider(self, event):
        self.label_slider_sec_HPLC.configure(text="Number of samples: " + str(self.sec_HPLC_n_samples.get()))

    def a280_sample_slider(self, event):
        self.label_slider_a280.configure(text="Number of samples: " + str(self.a280_n_samples.get()))

    def nDSF_sample_slider(self, event):
        self.label_slider_nDSF.configure(text="Number of samples: " + str(self.nDSF_n_samples.get()))

    def gd_slider(self, event):
        self.label_slider2_gd.configure(text="Number of samples: " + str(int(self.entry_slider2_gd.get())))

    def vt_sample_slider(self, event):
        self.label_slider2_vt.configure(text="Number of samples: " + str(int(self.entry_slider2_vt.get())))

    def vt_repetition_slider(self, event):
        self.label_slider3_vt.configure(text="Repetitions at destination: " + str(int(self.entry_slider3_vt.get())))

    def open_input_dialog_event(self):
        dialog = ctk.CTkInputDialog(text="Type in a number:", title="Choose Simple")
        print("Choose Simple:", dialog.get_input())

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
        
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- #
      

    # Add label to warnings frame     
    def add_label(self, code: int, type: str, custom_message=None):
        # dictionary to store text messages depending on a warning/error code
        message_description = {0: "The number of samples is okey",
                               1: "CSV file cannot be generated.\nPlease check the 'CONFIRM' checkbox at the bottom of the right side pane --->",
                               2: "The imported excel file is not supported or is incorrect.",
                               3: "CSV files could not be generated.\nCheck that all the options in the right column are correct.",
                               4: "Please import an EXCEL file before generating CSV files...",
                               5: "Excel file imported correctly.",
                               6: "Choose a method before importing Excel.",}
        # list of message codes that should disappear automatically after some seconds
        auto_disappear = [1, 2, 3, 4, 5, 6]

        # if message is specified use that as text
        if custom_message is not None:
            new_label = ctk.CTkLabel(self.warning_frame, text=custom_message) # ignores code parameter
        else:
            new_label = ctk.CTkLabel(self.warning_frame, text=message_description[code])

        if type == "warning":
            new_label.configure(text_color="orange")
        elif type == "error":
            new_label.configure(text_color="red")
        elif type == "info":
            new_label.configure(text_color="green")

        new_label.pack(pady=2)
        # add label with corresponding code
        self.warning_labels[new_label] = code

        # if label is one of these codes, make the message disappear automatically after 8 seconds
        if code in auto_disappear:
            self.after(8000, new_label.destroy)


    # remove label to warnings frame depending on the code that it has
    def remove_label(self, code: int):
        if self.warning_labels:
            # get positions with the specified code
            positions = [key for key, val in self.warning_labels.items() if val == code]
            # remove messages
            for label in positions:
                self.warning_labels.pop(label)
                label.destroy()


    # validate input from Entry widgets
    def validate_input(self, text, _min = 1, _max = 1000):
        if str(text) == "":
            return True
        if str.isdigit(text):
            if int(text) >= _min and int(text) <= _max:
                return True
            else:
                return False
        else:
            return False


    # show relevant information depending on selected tab
    def tab_changed(self):
        self.confirm_check_assay.set(False)

        # reset read excel data if present
        for widget in self.middle_frame.winfo_children(): # destroy all widgets present in frame
            widget.destroy()

        self.is_excel_imported = False
        self.reset_reagent_volumes()

        # add default label to middle frame
        self.middle_frame_default_label = ctk.CTkLabel(self.middle_frame, text="Import an Excel dilutions file, \nselect the correct options \nand press Generate CSV files.\nAs easy as that.", font=ctk.CTkFont(size=16, weight="bold"))
        self.middle_frame_default_label.pack()

        if self.tabview.get() == "Assay":
            # self.middle_frame.grid(row=0, column=1, padx=(10, 0), pady=(10, 0), sticky="nsew")
            pass
        else:
            # self.middle_frame.grid_forget()
            pass

    
    def calculate_volume_text(self, volume:float, container:str):
        """
            Calculates the text string for the labware and volume needed for the reagent data passed.
            
            Parameters
            ----------
            ``volume``: float
                Volume for the reagent.
                
            ``container``: str
                Container for the reagent.

            Returns
            ---------
            ``result_text``: str
                Formatted string with the information summary.

        """

        if container == "VOLUME TOO BIG": # if container is this, don't try to sum the dead volume of the container because it will give of an error
            result_text = container + ", " + str(round(volume, 1)) + " mL needed\n"

        else:
            result_text = container + ", " + str(round(volume + utils.LABWARE_VOLUMES[container][0], 1)) + " mL needed\n"

        return result_text



    def calculate_volumes_dotblot(self):
        """
        Calculates the volumes for the DotBlot method needed based on the excel dilution files.

        """

        dotblot_method.set_all_parameters(self)

        dotblot_method.calculate_total_volumes()
        containers = utils.find_best_container(dotblot_method.total_volumes)
        
        self.vol_conjugate.set(dotblot_method.total_volumes["Conjugate"])
        self.vol_coating_protein.set(dotblot_method.total_volumes["Coating protein"])
        self.vol_dpbs.set(dotblot_method.total_volumes["DPBS"])
        self.vol_assay_buffer.set(dotblot_method.total_volumes["Assay buffer"])
        self.vol_blocking_buffer.set(dotblot_method.total_volumes["Blocking buffer"])

        self.text_conjugate_vol.set(self.calculate_volume_text(self.vol_conjugate.get(), containers["Conjugate"])) # conjugate
        self.text_coating_protein_vol.set(self.calculate_volume_text(self.vol_coating_protein.get(), containers["Coating protein"])) # coating protein
        self.text_dpbs_vol.set(self.calculate_volume_text(self.vol_dpbs.get(), containers["DPBS"])) # dpbs
        self.text_assay_buffer_vol.set(self.calculate_volume_text(self.vol_assay_buffer.get(), containers["Assay buffer"])) # assay buffer
        self.text_blocking_buffer_vol.set(self.calculate_volume_text(self.vol_blocking_buffer.get(), containers["Blocking buffer"])) # blocking buffer


    # select excel file from computer
    def import_excel_dotblot(self):
        self.is_excel_imported = False
        
        if self.chosen_method.get() == "---": # default value, no None is chosen
            self.add_label(6, "warning")
            return None

        # Open a file dialog to select the Excel file
        initial_dir = r"L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\06. DotBlot_automation_DPP"
        method_index = utils.get_assay_indices(RAW_ASSAYS_DATA,self.chosen_method.get(), self.chosen_product.get())[0]
        self.pump_steps_data = RAW_ASSAYS_DATA[method_index]["step_types"] # get pump steps from JSON file


        # read correct excel depending if the method has 1 coating protein or 2
        try:
            if RAW_ASSAYS_DATA[method_index]["has_2_coating_proteins"] == "True":
                print("importing 2 coating excel") if self.DEBUG else 0
                file_path = initial_dir + r"\DotBlot automation dilution data - 2 coating.xlsx"
                data = utils.import_excel_dotblot_2_coating(file_path)
                dotblot_method.has_2_coatings = True

            else:
                print("importing excel 1 coating")
                file_path = initial_dir + r"\DotBlot automation dilution data.xlsx"
                data = utils.import_excel_dotblot(file_path)
                dotblot_method.has_2_coatings = False

        except:
            print("importing excel 1 coating")
            file_path = initial_dir + r"\DotBlot automation dilution data.xlsx"
            data = utils.import_excel_dotblot(file_path)
            dotblot_method.has_2_coatings = False

        # initial_file = r"DotBlot automation dilution data.xlsx"
        # file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")], initialdir=initial_dir, initialfile=initial_file)


        # if file_path: 

        if data == None: # Excel file selected was not correct one
            self.add_label(2, "error")
            self.is_excel_imported = False
            self.middle_frame_default_label.pack()
            return None
        
        else: # reading file was successful
            sample_dilution_data = data[0]
            coating_protein_dilution_data = data[1]
            pos_control_dilution_data = data[2]
            neg_control_dilution_data = data[3]
            
            # print("Sample data", sample_dilution_data) if self.DEBUG else 0
            # print("Pos ctr data", pos_control_dilution_data) if self.DEBUG else 0
            # print("Neg ctr data", neg_control_dilution_data) if self.DEBUG else 0

        self.middle_frame_default_label.destroy() # before using grid

        self.sample_dilution_data = [sample_dilution_data[i].to_dict(orient="list") for i in range(len(sample_dilution_data))]
        # self.coating_protein_dilution_data = [coating_protein_dilution_data[i].to_dict(orient="list") for i in range(len(coating_protein_dilution_data))]
        self.pos_control_dilution_data = [pos_control_dilution_data[i].to_dict(orient="list") for i in range(len(pos_control_dilution_data))]
        self.neg_control_dilution_data = [neg_control_dilution_data[i].to_dict(orient="list") for i in range(len(neg_control_dilution_data))]

        # calculate number of sample dilutions needed
        number_of_sample_dilutions = len(sample_dilution_data[0]["Assay buffer volume"])

        # to keep track of row number to display in middle frame widget
        row_number = 0

        # destroy all widgets in middle frame
        for widget in self.middle_frame.winfo_children(): # destroy all widgets present in frame
            widget.destroy()

        # add title to middle frame
        self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text="Dotblot Dilution data", font=ctk.CTkFont(size=20, weight="bold"))
        self.middle_frame_description_label.grid(row=row_number, column=0, columnspan=7, padx=10, pady=10, sticky="ew")
        row_number = row_number + 1

        # add imported file name to second row
        # self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text="Imported file: " + file_path.rsplit("/", 1)[-1])
        self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text="Imported file: " + utils.divide_string_into_lines(file_path, 60))
        self.middle_frame_description_label.grid(row=row_number, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
        row_number = row_number + 1

        # display read data into middle frame ------------------------------------------

        # display data from dictionary in the middle frame
        dilution_keys = list(self.sample_dilution_data[0].keys()) # we use first value of list because the keys are the same for all
        sample_dilution_values = [self.sample_dilution_data[i].values() for i in range(len(self.sample_dilution_data))]
        # coating_protein_dilution_values = [self.coating_protein_dilution_data[i].values() for i in range(len(self.coating_protein_dilution_data))]
        pos_control_dilution_values = [self.pos_control_dilution_data[i].values() for i in range(len(self.pos_control_dilution_data))]
        neg_control_dilution_values = [self.neg_control_dilution_data[i].values() for i in range(len(self.neg_control_dilution_data))]

        # create labels for column titles and respective units
        column_units = ["", "(mg/mL)", "(uL)", "(mg/mL)", "(uL)", "(uL)", "(uL)"]
        for col, key in enumerate(dilution_keys):
            column_name = ctk.CTkLabel(self.middle_frame, text=key.replace(" ", "\n") + "\n" + column_units[col], corner_radius=8, fg_color="green")
            column_name.grid(row=row_number, column=col, padx=5, pady=5, sticky="ew")
        row_number = row_number + 1


        # create labels for values in subsequent rows
        for i, sample_dilution in enumerate(sample_dilution_values):
            # add Sample dilution data title
            title_text = "Sample dilution data" if i == 0 else "Sample dilution data 2"
            self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text=title_text, font=ctk.CTkFont(weight="bold"), corner_radius=8, fg_color="#239172")
            self.middle_frame_description_label.grid(row=row_number, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
            row_number = row_number + 1
            for row, value_list in enumerate(sample_dilution):
                for col, value in enumerate(value_list):
                    label = ctk.CTkLabel(self.middle_frame, text=round(float(value), 4))
                    label.grid(row=col+row_number, column=row, sticky="ew")
            row_number = row_number + len(self.sample_dilution_data[0])

        # add coating protein data title
        # self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text="Coating protein data", font=ctk.CTkFont(weight="bold"), corner_radius=8, fg_color="#23918e")
        # self.middle_frame_description_label.grid(row=row_number, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
        # row_number = row_number + 1

        # # create labels for values in subsequent rows
        # for dilution_group in coating_protein_dilution_values:
        #     for row, value_list in enumerate(dilution_group):
        #         for col, value in enumerate(value_list):
        #             label = ctk.CTkLabel(self.middle_frame, text=round(float(value), 2))
        #             label.grid(row=col+row_number, column=row, sticky="ew")
        #     row_number = row_number + len(self.coating_protein_dilution_data)


        # create labels for values in subsequent rows
        for i, dilution_group in enumerate(pos_control_dilution_values):
        # add positive control data title
            title_text = "Positive control data" if i == 0 else "Positive control data 2"
            self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text=title_text, font=ctk.CTkFont(weight="bold"), corner_radius=8, fg_color="#236791")
            self.middle_frame_description_label.grid(row=row_number, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
            row_number = row_number + 1

            for row, value_list in enumerate(dilution_group):
                for col, value in enumerate(value_list):
                    label = ctk.CTkLabel(self.middle_frame, text=round(float(value), 4))
                    label.grid(row=col+row_number, column=row, sticky="ew")
            row_number = row_number + len(self.pos_control_dilution_data[0])
        

        # create labels for values in subsequent rows
        for i, dilution_group in enumerate(neg_control_dilution_values):
            # add negative control data title
            title_text = "Negative control data" if i == 0 else "Negative control data 2"
            self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text=title_text, font=ctk.CTkFont(weight="bold"), corner_radius=8, fg_color="#234491")
            self.middle_frame_description_label.grid(row=row_number, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
            row_number = row_number + 1

            for row, value_list in enumerate(dilution_group):
                for col, value in enumerate(value_list):
                    label = ctk.CTkLabel(self.middle_frame, text=round(float(value), 4))
                    label.grid(row=col+row_number, column=row, sticky="ew")
            row_number = row_number + len(self.neg_control_dilution_data[0])

        self.is_excel_imported = True
        self.add_label(5, "info")

        # self.labware_text = "" # remove inplace text
        self.calculate_volumes_dotblot()


    # select excel file from computer
    def import_excel_gen_dil(self):
        self.is_excel_imported = False

        # Open a file dialog to select the Excel file
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])

        if file_path:

            data = utils.import_excel_general_dilution(file_path)

            # if data == None: # Excel file selected was not correct one
            # if type(data) != type(DataFrame([32])):
            if data is None: # no data extracted
                self.add_label(2, "error")
                self.is_excel_imported = False
                self.middle_frame_default_label.pack()
                return None
            
            else: # reading file was successful
                sample_dilution_data = data

            self.middle_frame_default_label.destroy() # before using grid

            self.sample_dilution_data = {col: sample_dilution_data[col].values.astype(float).tolist() for col in sample_dilution_data.columns}
            
            # calculate number of sample dilutions needed
            number_of_sample_dilutions = len(sample_dilution_data["Assay buffer volume"])

            # to keep track of row number to display in middle frame widget
            row_number = 0

            # add title to middle frame
            self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text="General Dilution data", font=ctk.CTkFont(size=20, weight="bold"))
            self.middle_frame_description_label.grid(row=row_number, column=0, columnspan=7, padx=10, pady=10, sticky="ew")
            row_number = row_number + 1

            # add imported file name to second row
            self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text="Imported file: " + file_path.rsplit("/", 1)[-1])
            self.middle_frame_description_label.grid(row=row_number, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
            row_number = row_number + 1

            # display read data into middle frame ------------------------------------------

            # display data from dictionary in the middle frame
            dilution_keys = list(self.sample_dilution_data.keys())
            sample_dilution_values = list(self.sample_dilution_data.values())
            # print("smple dilution values\n", sample_dilution_values)


            # create labels for column titles and respective units
            column_units = ["", "(mg/mL)", "(uL)", "(mg/mL)", "(uL)", "(uL)", "(uL)"]
            for col, key in enumerate(dilution_keys):
                column_name = ctk.CTkLabel(self.middle_frame, text=key.replace(" ", "\n") + "\n" + column_units[col], corner_radius=8, fg_color="green")
                column_name.grid(row=row_number, column=col, padx=5, pady=5, sticky="ew")
            row_number = row_number + 1

            # add Sample dilution data title
            self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text="Sample dilution data", font=ctk.CTkFont(weight="bold"), corner_radius=8, fg_color="#239172")
            self.middle_frame_description_label.grid(row=row_number, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
            row_number = row_number + 1

            # create labels for values in subsequent rows
            for row, value_list in enumerate(sample_dilution_values):
                for col, value in enumerate(value_list):
                    label = ctk.CTkLabel(self.middle_frame, text=round(float(value), 2))
                    label.grid(row=col+row_number, column=row, sticky="ew")
            row_number = row_number + number_of_sample_dilutions

            self.is_excel_imported = True
            self.add_label(5, "info")


    def generate_csv_button_event(self):
        try:
            if self.confirm_check_assay.get() == False:
                self.add_label(1, "info")
                return
            
            utils.new_log_file() # pass current time as a string to create the log file with that name
            utils.logger.info(f"METHOD: {self.chosen_method.get()}")
            utils.logger.info(f"PRODUCT: {self.chosen_product.get()}")


            if self.tabview.get() == "Assay":
                if self.chosen_method.get() == "Dotblot": # if DOTBLOT confirm check is pressed
                    if not self.is_excel_imported:
                        self.add_label(4, "info")
                        return
                    
                    # self.set_pump_steps_parameters()
                    print("starting dotblot calculations...") if self.DEBUG else 0

                    # not needed now, as they are imported when importing the excel file, saving computing time
                    # indices = utils.get_assay_indices(RAW_ASSAYS_DATA, self.chosen_method.get(), self.chosen_product.get())
                    # self.pump_steps_data = RAW_ASSAYS_DATA[indices[0]]["step_types"] # get pump steps from JSON file
                    print(self.pump_steps_data) if self.DEBUG else 0

                    dotblot_method.set_all_parameters(self)
                    print("parameters set") if self.DEBUG else 0
                    pos_control_eppendorf_positions, neg_control_eppendorf_positions, sample_eppendorf_positions = dotblot_method.dotblot()
                    
                    messagebox.showinfo("Information", "CSV files generated correctly!\n\n\
    Final Eppendorf positions:\n\
    Positive control: " + str(pos_control_eppendorf_positions) + "\n\
    Negative control: " + str(neg_control_eppendorf_positions) + "\n\
    Samples: " + str(sample_eppendorf_positions) + "\n")
                

                if self.chosen_method.get() == "nDSF": # nanoDSF
                    # execute nDSF method

                    nDSF_method.set_all_parameters(self)
                    nDSF_method.nanoDSF()
                    messagebox.showinfo("Information", "nanoDSF files generated correctly!") # A280


                if self.chosen_method.get() == "A280 (soloVPE)":
                    # execute a280 method

                    a280_method.set_all_parameters(self)
                    a280_method.a280()
                    messagebox.showinfo("Information", "A280 files generated correctly!")
                    

                if self.chosen_method.get() == "SEC-HPLC":
                    # execute a280 method

                    sec_hplc_method.set_all_parameters(self)
                    sec_hplc_method.sec_HPLC()
                    messagebox.showinfo("Information", "SEC-HPLC files generated correctly!")


            elif self.tabview.get() == "General dilution": # if GENRAL DILUTION confirm check is pressed
                if not self.is_excel_imported:
                    self.add_label(4, "info")

                general_dilution.set_all_parameters(self)
                # print("parameters set")
                # print(self.sample_dilution_data)
                sample_dest_positions = general_dilution.general_dilution()
                
                messagebox.showinfo("Information", "CSV files generated correctly!\n\n\
    Final positions in " + str(self.gd_dil_dest.get()) + ":\n\
    " + str(sample_dest_positions) + "\n")
                

            elif self.tabview.get() == "Vol. transfer": # if VOLUME TRANSFER confirm check is pressed
                
                vol_tr.set_all_parameters(self)
                vt_dest_positions = vol_tr.volume_transfer()
                # sample_dest_positions = "[debug test]"
                
                messagebox.showinfo("Information", "CSV files generated correctly!\n\n\
    Final positions in " + str(self.vt_dest.get()) + ":\n\
    " + str(vt_dest_positions) + "\n")
            else:
                self.add_label(1, "info")

        except Exception as e:
            # print(f"e is {e}, and the type is: {str(e)}")
            if len(str(e)) == 0: # if exception has no message attached, show general error message
                self.add_label(3, "error")
            else:
                self.add_label(1, "error",  custom_message= utils.divide_string_into_lines(str(e), 80))
            print(e)
            utils.logger.error("Method failed.", exc_info=True)
            

# Run main loop
if __name__ == "__main__":
    app = App()

    app.DEBUG = True

    app.mainloop()





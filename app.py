# %% [markdown]
# #### Imports and initial setup

# %%
import os
# import pandas as pd
# from pandas import read_excel
from pandas import DataFrame
# from pandas import isna
import numpy as np

from tkinter import messagebox
from tkinter import filedialog
# from CTkToolTip import *
import tkinter as tk
from tkinter import ttk
# from PIL import Image, ImageTk
import customtkinter as ctk

import utils # file with helper methods
import Dotblot
import GeneralDilution
import VolumeTransfer

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


paths = r'L:\Departements\BTDS_AD\002_AFFS\Lab Automation\09. Tecan\01. Methods\DotBlot Sample Prep' + "\\" +str(1) +'.csv'

dotblot_dilution_excel_path = 'L:/Departements/BTDS_AD/002_AFFS/Lab Automation/09. Tecan/06. DotBlot_automation_DPP/DotBlot_automation_dilution_template_final.xlsx'
general_dilution_excel_path = 'L:/Departements/BTDS_AD/002_AFFS/Lab Automation/09. Tecan/06. DotBlot_automation_DPP/General_dilution_template.xlsx'

dotblot_method = Dotblot.DotblotMethod()
general_dilution = GeneralDilution.GeneralDilution()
vol_tr = VolumeTransfer.VolumeTransfer()

# %% [markdown]
# ### GUI Classes
# 

# %%

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("Tecan Interface")
        self.geometry(f"{1100}x{580}")
        # self.iconbitmap("gui_icon.ico")

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
        self.export_csv_button = ctk.CTkButton(self.sidebar_frame, command=self.sidebar_button_event)
        self.export_csv_button.grid(row=1, column=0, padx=20, pady=10)
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.scaling_label = ctk.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"], command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Tecan Interface v0.3.4b", anchor="w", font=ctk.CTkFont(size=8))
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

        
        # self.tabview_new = ctk.CTkOptionMenu(self.right_scrollable_frame, values=["Dotblot", "General dilution", "Volume transfer", "HPLC", "FIPA"])
        # self.tabview_new.grid(row=0, column=0, padx=(10, 0), pady=(10, 0), sticky="nsew")

        self.tabview = ctk.CTkTabview(self.right_scrollable_frame, width=280, command=self.tab_changed)
        self.tabview.grid(row=1, column=0, padx=(10, 0), pady=(10, 0), rowspan=4, sticky="nsew")
        self.tabview.add("DotBlot")
        # self.tabview.add("DLS")
        self.tabview.add("General dilution")
        self.tabview.add("Vol. transfer")
        # self.tabview.add("HPLC")
        # self.tabview.add("FIPA")
        self.tabview.tab("DotBlot").grid_columnconfigure(0, weight=2)  # configure grid of individual tabs
        # self.tabview.tab("DLS").grid_columnconfigure(0, weight=2)
        self.tabview.tab("General dilution").grid_columnconfigure(0, weight=2)
        self.tabview.tab("Vol. transfer").grid_columnconfigure(0, weight=2)
        # self.tabview.tab("HPLC").grid_columnconfigure(0, weight=2)
        # self.tabview.tab("FIPA").grid_columnconfigure(0, weight=2)



        # DOT BLOT ===============================================================================
        self.separator = ttk.Separator(self.tabview.tab("DotBlot"), orient='horizontal')
        self.separator.pack(fill='x')
        self.title_pos_control = ctk.CTkLabel(self.tabview.tab("DotBlot"), text="Dilutions file", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_pos_control.pack(pady=(1, 6))
        self.open_csv_dilution = ctk.CTkButton(self.tabview.tab("DotBlot"), text="Open and edit Excel", state="normal", command=lambda: os.startfile(dotblot_dilution_excel_path), fg_color="#2ca39b", hover_color="#1bb5ab")
        self.open_csv_dilution.pack(padx=2, pady=(5, 5))
        self.import_csv_button = ctk.CTkButton(self.tabview.tab("DotBlot"), text="Import Excel", state="normal", command=self.import_excel_dotblot, fg_color="#288230", hover_color="#235e28")
        self.import_csv_button.pack(padx=2, pady=(5, 20))
        self.separator = ttk.Separator(self.tabview.tab("DotBlot"), orient='horizontal')
        self.separator.pack(fill='x')

        # Samples
        self.title_sample = ctk.CTkLabel(self.tabview.tab("DotBlot"), text="Samples", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_sample.pack(pady=(1, 6))
        self.label_1d = ctk.CTkLabel(self.tabview.tab("DotBlot"), text="Sample type:", width=120, height=25, corner_radius=8)
        self.label_1d.pack(padx=20, pady=(5, 1))
        self.optionmenu_1 = ctk.CTkOptionMenu(self.tabview.tab("DotBlot"), dynamic_resizing=False, values=["Falcon15", "2R Vial", "8R Vial", "Eppendorf"])
        self.optionmenu_1.pack(padx=20, pady=(1, 10))
        self.label_slider2 = ctk.CTkLabel(self.tabview.tab("DotBlot"), text="Number of samples: 1", width=120, height=25,corner_radius=8)
        self.label_slider2.pack(padx=20, pady=(1, 1))
        self.entry_slider2 = ctk.CTkSlider(self.tabview.tab("DotBlot"), from_=1, to=25, number_of_steps=24, command=self.samples_slider)
        self.entry_slider2.set(1) # set initial value
        self.entry_slider2.pack(padx=20, pady=(1, 5))
        self.label_slider3 = ctk.CTkLabel(self.tabview.tab("DotBlot"), text="Initial volume transfer: 300 uL", width=120, height=25,corner_radius=8)
        self.label_slider3.pack(padx=20, pady=(1, 1))
        self.entry_slider3 = ctk.CTkSlider(self.tabview.tab("DotBlot"), from_=50, to=300, number_of_steps=5, command=self.sample_initial_volume_slider)
        self.entry_slider3.set(300) # set initial value
        self.entry_slider3.pack(padx=20, pady=(1, 5))
        self.separator = ttk.Separator(self.tabview.tab("DotBlot"), orient='horizontal')
        self.separator.pack(fill='x', pady=(10, 10))

        # self.img1 = ImageTk.PhotoImage(Image.open(r"./vial_types/glass_vials_types.png").resize((500, 180)), master=self)

        # Positive control
        self.title_pos_control = ctk.CTkLabel(self.tabview.tab("DotBlot"), text="Positive control", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_pos_control.pack(pady=(1, 6))
        self.label_1d = ctk.CTkLabel(self.tabview.tab("DotBlot"), text="Vial position:", width=120, height=25, corner_radius=8)
        self.label_1d.pack(padx=20, pady=(5, 1))
        self.vial_pos_frame1 = ctk.CTkFrame(self.tabview.tab("DotBlot"), width=280)
        self.vial_pos_frame1.pack(pady=(5, 6))

        self.optionmenu_vials1 = ctk.CTkOptionMenu(self.vial_pos_frame1, width=60, values=["A", "B", "C", "D", "E"])
        self.optionmenu_vials1.pack(side=tk.LEFT, padx=10)
        self.optionmenu_vials1a = ctk.CTkOptionMenu(self.vial_pos_frame1, width=60, values=["1", "2", "3", "4", "5", "6"])
        self.optionmenu_vials1a.pack(side=tk.LEFT, padx=10)
        self.label_1d = ctk.CTkLabel(self.tabview.tab("DotBlot"), text="Buffer used:", width=120, height=25, corner_radius=8)
        self.label_1d.pack(padx=20, pady=(5, 1))
        self.optionmenu_3 = ctk.CTkOptionMenu(self.tabview.tab("DotBlot"), dynamic_resizing=False, values=["Assay buffer", "DPBS"])
        self.optionmenu_3.pack(padx=20, pady=(1, 5))

        # Pump system steps
        self.pump_system_frames = [] # list to store references to the different created frames for the steps needed
        self.n_pump_system_frames = len(self.pump_system_frames)

        self.separator = ttk.Separator(self.tabview.tab("DotBlot"), orient='horizontal')
        self.separator.pack(fill='x', pady=(10, 10))
        self.title_pump_steps = ctk.CTkLabel(self.tabview.tab("DotBlot"), text="Pump system steps", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_pump_steps.pack(pady=(1, 6))
        self.title_pump_steps = ctk.CTkLabel(self.tabview.tab("DotBlot"), text="Just visual, not \n implemented in Tecan yet.")
        self.title_pump_steps.pack(pady=(1, 3))

        self.main_pump_system_frame = ctk.CTkFrame(self.tabview.tab("DotBlot"), width=280)
        self.main_pump_system_frame.pack(pady=(5, 5))
        # self.pump_system_frames.append(self.pump_system_frame) # add first step by default

        self.add_step_pump_btn = ctk.CTkButton(self.main_pump_system_frame, text="+", state="normal", width=60, command=self.add_step_pump, font=ctk.CTkFont(size=22, weight="bold"), fg_color="#b8a52c", hover_color="#baa414")
        self.add_step_pump_btn.pack(padx=20, pady=(10, 20))


        # Confirm button
        self.separator = ttk.Separator(self.tabview.tab("DotBlot"), orient='horizontal')
        self.separator.pack(fill='x', pady=(10, 10))
        # self.test2 = ctk.CTkButton(self.tabview.tab("DotBlot"), text="print pump step data", state="normal",command=self.set_pump_steps_parameters, fg_color="#b8a52c", hover_color="#baa414")
        # self.test2.pack(padx=20, pady=(5, 5))
        self.check_dotblot = ctk.CTkCheckBox(self.tabview.tab("DotBlot"), text="Confirm")
        self.check_dotblot.pack(padx=0, pady=(20, 10))


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
        self.check_gd = ctk.CTkCheckBox(self.tabview.tab("General dilution"), text="Confirm")
        self.check_gd.pack(padx=0, pady=(20, 10))


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
        self.check_vt = ctk.CTkCheckBox(self.tabview.tab("Vol. transfer"), text="Confirm")
        self.check_vt.pack(padx=0, pady=(20, 10))


        # set default values
        self.export_csv_button.configure(state="normal", text="Generate CSV files", fg_color="#25702b", hover_color="#235e28")
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")
        self.toplevel_window = None


        # Create the tooltip window (hidden by default) - reused for all tooltips in the app
        # self.tooltip = tk.Toplevel(self)
        # self.tooltip.withdraw()
        # # self.tooltip_label = tk.Label(self.tooltip, text="", background="darkgrey", relief="solid", borderwidth=1, image=self.img1, compound="bottom")
        # self.tooltip_label = tk.Label(self.tooltip, text="", background="darkgrey", relief="solid", borderwidth=1, compound="bottom")
        # self.tooltip_label.pack()

# ?========================================================================================

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- #
    # pump_system_frame
    MAX_PUMP_STEPS = 20
    pump_steps_data = []

    def step_type_changed(self, frame_n):
        # print("frame number (step type changed):", frame_n)
        # for widget in self.inside_option_frame.winfo_children(): # clean up frame
        for i, widget in enumerate(self.pump_system_frames[int(frame_n)].winfo_children()): # clean up frame
            if i > 1: # ignore first 2 objects because they are the label and optionmenu
                # print("widget", widget)
                widget.destroy()
            else:
                if "optionmenu" in widget.winfo_name(): # we got our step type optionmenu
                    step_type_optionmenu = widget
        # self.inside_option_frame

        if step_type_optionmenu.get() == "Wait timer":
            self.label_wait_timer = ctk.CTkLabel(self.pump_system_frames[int(frame_n)], text="Wait 10 minutes", width=120, height=25,corner_radius=8)
            self.label_wait_timer.pack(padx=1, pady=(1, 1))
            self.slider_wait_timer = ctk.CTkSlider(self.pump_system_frames[int(frame_n)], from_=1, to=20, number_of_steps=19, command=lambda frame_number=frame_n: self.pump_timer_slider(int(frame_n)))
            self.slider_wait_timer.set(10) # set initial value
            self.slider_wait_timer.pack()
        elif step_type_optionmenu.get() == "Transfer volume to wells":
            self.label_transfer_vol = ctk.CTkLabel(self.pump_system_frames[int(frame_n)], text="Volume amount (uL):", width=120, height=25,corner_radius=8)
            self.label_transfer_vol.pack(padx=1, pady=(1, 1))
            self.entry_transfer_vol = ctk.CTkEntry(self.pump_system_frames[int(frame_n)],placeholder_text="1", validate="all", validatecommand= (self.register(self.validate_input), "%P"))
            # self.entry_transfer_vol = ctk.CTkEntry(self.pump_system_frames[int(frame_n)],placeholder_text="1")               validatecommand= (self.register(self.validate_input), "%P")
            self.entry_transfer_vol.pack(padx=20, pady=(1, 5))
            self.label_transfer_vol2 = ctk.CTkLabel(self.pump_system_frames[int(frame_n)], text="Liquid type:", width=120, height=25,corner_radius=8)
            self.label_transfer_vol2.pack(padx=1, pady=(1, 1))
            self.substance_type = ctk.CTkOptionMenu(self.pump_system_frames[int(frame_n)], values=["DPBS", "Coating protein", "Blocking buffer", "Pos/Neg control", "Samples", "Conjugate"])
            self.substance_type.pack(pady=(1, 5))
            # self.seg_button1 = ctk.CTkSegmentedButton(self.pump_system_frames[int(frame_n)], values=["All wells", "Only samples"])
            # self.seg_button1.set("All wells") # default selection
            # self.seg_button1.pack(pady=(1, 1))
        elif step_type_optionmenu.get() == "Vacuum":
            # self.label_transfer_vol = ctk.CTkLabel(self.pump_system_frames[int(frame_n)], text="Vacuum pressure:", width=120, height=25,corner_radius=8)
            # self.label_transfer_vol.pack(padx=1, pady=(1, 1))
            pass
            
        self.separator = ttk.Separator(self.pump_system_frames[int(frame_n)], orient='horizontal')
        self.separator.pack(fill='x', pady=(5, 5))

        self.del_step_pump_btn = ctk.CTkButton(self.pump_system_frames[int(frame_n)], text="Delete step", state="normal", command= lambda frame_n=frame_n: self.del_step_pump(frame_n), font=ctk.CTkFont(size=10), width=40, fg_color="#ba2514", hover_color="#b81907")
        self.del_step_pump_btn.pack(padx=2, pady=(5, 5))

        # print("number of pump frames: ", len(self.pump_system_frames))

    def add_step_pump(self):
        self.add_step_pump_btn.pack_forget() # remove from screen
        frame_number = len(self.pump_system_frames)
        # print("frame number (add step pump):", frame_number)

        # self.debug_info(frame_number)

        self.pump_system_frame = ctk.CTkFrame(self.main_pump_system_frame, width=280, fg_color="#7a7764")
        self.pump_system_frame.pack(pady=(5, 5))
        # self.label_step_name = ctk.CTkLabel(self.pump_system_frame, text= "Step " + str(frame_number+1) + ":", width=120, height=25, corner_radius=8, font=ctk.CTkFont(weight="bold"))
        self.label_step_name = ctk.CTkLabel(self.pump_system_frame, text= "Step type:", width=120, height=25, corner_radius=8, font=ctk.CTkFont(weight="bold"))
        self.label_step_name.pack(padx=2, pady=(5, 1))
        self.step_type1 = ctk.CTkOptionMenu(self.pump_system_frame, values=["Transfer volume to wells", "Vacuum", "Wait timer"], command=lambda frame_n=frame_number: self.step_type_changed(frame_number))
        self.step_type1.set("Wait timer")
        self.step_type1.pack(padx=1, pady=(1, 5))
        self.inside_option_frame = ctk.CTkFrame(self.pump_system_frame, width=280, height=3, fg_color="#47484d")
        self.inside_option_frame.pack(pady=(5, 5))
        
        self.pump_system_frames.append(self.pump_system_frame) # add step by default
        self.n_pump_system_frames = len(self.pump_system_frames) # add step
        self.step_type_changed(frame_number) # call function to display correct widgets already

        real_length = len(self.pump_system_frames) - self.pump_system_frames.count("no_widget") # actual length MINUS number of empty values
        # print("real lenth:", real_length)
        # print("count of no_widget:", self.pump_system_frames.count("no_widget"))
        if real_length < self.MAX_PUMP_STEPS: # if not reached MAX LIMIT of pump steps
            self.add_step_pump_btn.pack() # add ADD(+) button to screen at end



    def del_step_pump(self, frame_n):
        # for widget in self.pump_system_frames[int(frame_n)].winfo_children(): # clean up frame
        #     # print("widget", widget)
        #     widget.destroy()
        self.pump_system_frames[int(frame_n)].destroy() # remove widget from screen

        # we cannot remove the element from the list directly, because then all references to list positions is incorrect and editing of the frames does not work
        # so, instead, we change that element with a specific string, while all other remain the widgets themselves
        self.pump_system_frames[frame_n] = "no_widget"
        
        real_length = len(self.pump_system_frames) - self.pump_system_frames.count("no_widget") # actual length MINUS number of empty values
        if real_length < self.MAX_PUMP_STEPS:
            self.add_step_pump_btn.pack() # add to screen at end

    # update slider values
    def pump_timer_slider(self, frame_number):
        if type(frame_number) != type(int) or frame_number > 5:
            # print("frame number (pump slider): ", frame_number)
            pass

        for i, widget in enumerate(self.pump_system_frames[int(frame_number)].winfo_children()): # cycle through widgets in frame
            # print("i: ", i, "widget name: ", widget.winfo_name())
            if "slider" in widget.winfo_name(): # we got our timer slider
                slider = widget
            elif "label" in widget.winfo_name(): # slider label
                label = widget

        label.configure(text="Wait " + str(int(slider.get())) + " minutes")
            
    
    def set_pump_steps_parameters(self): # takes data from pump frames list and updates dict
        self.pump_steps_data = []
        step_data = {}
        curr_widget = 0

        for step in self.pump_system_frames: # loop over each widget frame
            if step == "no_widget":
                continue
            else:
                n_childs = len(step.winfo_children())
                # print("PUMP STEP DATA:    n_childs. ", n_childs)
                if n_childs == 8: # we are in transfer volume
                    # step_data["step_type"] = step.winfo_children()[1].cget("variable") # step type
                    step_data["step_type"] = step.winfo_children()[1].get() # step type
                    step_data["volume_amount"] = step.winfo_children()[3].get() # volume amount
                    step_data["liquid_type"] = step.winfo_children()[5].get() # liquid type
                    # step_data["wells_type"] = step.winfo_children()[6].get() # wells type
                    self.pump_steps_data.append(step_data) # add step
                    step_data = {} # reset for next step

                elif n_childs == 4: # vacuum step
                    step_data["step_type"] = step.winfo_children()[1].get() # step type
                    self.pump_steps_data.append(step_data) # add step
                    step_data = {} # reset for next step

                elif n_childs == 6: # wait timer
                    step_data["step_type"] = step.winfo_children()[1].get() # step type
                    # step_data["volume_amount"] = step.winfo_children()[3].cget("variable") # slider
                    step_data["wait_timer"] = step.winfo_children()[3].get() # slider
                    self.pump_steps_data.append(step_data) # add step
                    step_data = {} # reset for next step

        print(self.pump_steps_data)
        # self.debug_info_label.configure(text=str(self.pump_steps_data))

# ------------------------------------------------------------------------------------------------------------------------------------------------------- #

    def sample_initial_volume_slider(self, event):
        self.label_slider3.configure(text="Initial volume transfer: " + str(int(self.entry_slider3.get())) + " uL")

    def samples_slider(self, event):
        self.label_slider2.configure(text="Number of samples: " + str(int(self.entry_slider2.get())))

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
                               1: "CSV file cannot be generated. Please check the 'CONFIRM' checkbox at the bottom of the right side pane --->",
                               2: "The imported excel file is not supported or is incorrect.",
                               3: "CSV files could not be generated.Check that all the options in the right column are correct.",
                               4: "Please import an EXCEL file before generating CSV files...",
                               5: "Excel file imported correctly."}
        # list of message codes that should disappear automatically after some seconds
        auto_disappear = [1, 2, 3, 4, 5]

        # if message is specified use that as text
        if custom_message is not None:
            new_label = ctk.CTkLabel(self.warning_frame, text=custom_message)
        else:
            new_label = ctk.CTkLabel(self.warning_frame, text=message_description[code])

        if type == "warning":
            new_label.configure(text_color="orange")
        elif type == "error":
            new_label.configure(text_color="red")
        elif type == "info":
            new_label.configure(text_color="blue")

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
        # reset read excel data if present
        for widget in self.middle_frame.winfo_children(): # destroy all widgets present in frame
            widget.destroy()

        self.is_excel_imported = False

        # add default label to middle frame
        self.middle_frame_default_label = ctk.CTkLabel(self.middle_frame, text="Import an Excel dilutions file, \nselect the correct options \nand press Generate CSV files.\nAs easy as that.", font=ctk.CTkFont(size=16, weight="bold"))
        self.middle_frame_default_label.pack()

        if self.tabview.get() == "DotBlot":
            # self.middle_frame.grid(row=0, column=1, padx=(10, 0), pady=(10, 0), sticky="nsew")
            pass
        else:
            # self.middle_frame.grid_forget()
            pass


    # select excel file from computer
    def import_excel_dotblot(self):
        self.is_excel_imported = False

        # Open a file dialog to select the Excel file
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])

        if file_path:

            data = utils.import_excel_dotblot(file_path)

            if data == None: # Excel file selected was not correct one
                self.add_label(2, "error")
                self.is_excel_imported = False
                self.middle_frame_default_label.pack()
                return None
            
            else: # reading file was successful
                sample_dilution_data = data[0]
                coating_protein_dilution_data = data[1]
                pos_control_dilution_data = data[2]

            self.middle_frame_default_label.destroy() # before using grid

            self.sample_dilution_data = {col: sample_dilution_data[col].values.astype(float).tolist() for col in sample_dilution_data.columns}
            self.coating_protein_dilution_data = {col: coating_protein_dilution_data[col].values.astype(float).tolist() for col in coating_protein_dilution_data.columns}
            self.pos_control_dilution_data = {col: pos_control_dilution_data[col].values.astype(float).tolist() for col in pos_control_dilution_data.columns}

            # calculate number of sample dilutions needed
            number_of_sample_dilutions = len(sample_dilution_data["Assay buffer volume"])

            # to keep track of row number to display in middle frame widget
            row_number = 0

            # add title to middle frame
            self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text="Dotblot Dilution data", font=ctk.CTkFont(size=20, weight="bold"))
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
            coating_protein_dilution_values = list(self.coating_protein_dilution_data.values())
            pos_control_dilution_values = list(self.pos_control_dilution_data.values())


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

            # add coating protein data title
            self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text="Coating protein data", font=ctk.CTkFont(weight="bold"), corner_radius=8, fg_color="#23918e")
            self.middle_frame_description_label.grid(row=row_number, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
            row_number = row_number + 1

            # create labels for values in subsequent rows
            for row, value_list in enumerate(coating_protein_dilution_values):
                for col, value in enumerate(value_list):
                    label = ctk.CTkLabel(self.middle_frame, text=round(float(value), 2))
                    label.grid(row=col+row_number, column=row, sticky="ew")
            row_number = row_number + len(self.coating_protein_dilution_data)

            # add positive control data title
            self.middle_frame_description_label = ctk.CTkLabel(self.middle_frame, text="Positive control data", font=ctk.CTkFont(weight="bold"), corner_radius=8, fg_color="#236791")
            self.middle_frame_description_label.grid(row=row_number, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
            row_number = row_number + 1

            # create labels for values in subsequent rows
            for row, value_list in enumerate(pos_control_dilution_values):
                for col, value in enumerate(value_list):
                    label = ctk.CTkLabel(self.middle_frame, text=round(float(value), 2))
                    label.grid(row=col+row_number, column=row, sticky="ew")
            row_number = row_number + len(self.pos_control_dilution_data)

            self.is_excel_imported = True
            self.add_label(5, "info")

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


    def sidebar_button_event(self):
        if self.tabview.get() == "DotBlot" and self.check_dotblot.get() == 1: # if DOTBLOT confirm check is pressed
            if not self.is_excel_imported:
                self.add_label(4, "info")

            try:
                self.set_pump_steps_parameters()
                dotblot_method.set_all_parameters(self)
                # print("parameters set")
                pos_control_eppendorf_positions, sample_eppendorf_positions = dotblot_method.dotblot()
                
                messagebox.showinfo("Information", "CSV files generated correctly!\n\n\
Final Eppendorf positions:\n\
Positive control: " + str(pos_control_eppendorf_positions) + "\n\
Samples: " + str(sample_eppendorf_positions) + "\n")
            except Exception as e:
                self.add_label(3, "error")
                print(e)
        # else:
            # self.add_label(1, "info")

        elif self.tabview.get() == "General dilution" and self.check_gd.get() == 1: # if GENRAL DILUTION confirm check is pressed
            if not self.is_excel_imported:
                self.add_label(4, "info")

            try:
                general_dilution.set_all_parameters(self)
                # print("parameters set")
                # print(self.sample_dilution_data)
                sample_dest_positions = general_dilution.general_dilution()
                # sample_dest_positions = "[debug test]"
                
                messagebox.showinfo("Information", "CSV files generated correctly!\n\n\
Final positions in " + str(self.gd_dil_dest.get()) + ":\n\
" + str(sample_dest_positions) + "\n")
            except Exception as e:
                self.add_label(3, "error")
                print(e)
        # else:
        #     self.add_label(1, "info")

        elif self.tabview.get() == "Vol. transfer" and self.check_vt.get() == 1: # if VOLUME TRANSFER confirm check is pressed
            try:
                vol_tr.set_all_parameters(self)
                vt_dest_positions = vol_tr.volume_transfer()
                # sample_dest_positions = "[debug test]"
                
                messagebox.showinfo("Information", "CSV files generated correctly!\n\n\
Final positions in " + str(self.vt_dest.get()) + ":\n\
" + str(vt_dest_positions) + "\n")
            except Exception as e:
                self.add_label(3, "error")
                print(e)
        else:
            self.add_label(1, "info")
            

# Run main loop
if __name__ == "__main__":
    app = App()
    app.mainloop()


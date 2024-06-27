import cx_Freeze, sys

base = None

if sys.platform == 'win32':
    base = "Win32GUI"

executables = [cx_Freeze.Executable("app.py", base=base)]

cx_Freeze.setup(
    name="tecan interface test",
    options={"build_exe": {"packages": ["customtkinter"]}},
    version="0.2.x",
    description="Tecan Interface",
    executables=executables
)

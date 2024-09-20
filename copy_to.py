import easygui, shutil

source = easygui.fileopenbox("Source File", default="d:\GIT\EMC Tools\emc_tools.py", filetypes= "*.py", multiple=True)
destination = easygui.diropenbox("Destination Folder", default=r"d:\MEGA\Blender Configs\4.2\scripts\addons")

for file in source:
    shutil.copy2(file, destination)

print(str(source))
print(str(destination))
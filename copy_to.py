import easygui, shutil

source = easygui.fileopenbox("Source File", default="d:\GIT\EMC Tools\emc_tools.py", filetypes= "*.py")
destination = easygui.diropenbox("Destination Folder", default=r"d:\MEGA\Blender Configs\2.80\scripts\addons")

shutil.copy2(source, destination)

print(str(source))
print(str(destination))
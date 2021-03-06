# EMC Tools
## NOTE: you ONLY need to download emc_tools.py. Don't download as ZIP!

![thumbnail](https://static-2.gumroad.com/res/gumroad/3574851046664/asset_previews/942a27720490e880a2d9d86b1e4e9d02/retina/thumbnail.png)

*Works on versions 2.83 all the way up to 2.91.*

[Documentation](https://www.artstation.com/artwork/4816nl)

This addon was created to speed up the modeling workflow in blender, as well as expand its toolset a little bit. Some modifiers can be added interactively via a modal operation, and some operations combine and automate multiple steps into one.

You might've noticed that some of these menus resemble the maya marking menus. I initially created those for myself so I can learn and get used to the maya menus, as I'm familiar with blender's workflow but haven't expanded my horizons much past the basics of other applications. I figured it could be useful for other people as well who are migrating from maya, or maybe just following maya tutorials.
I didn't include some options obviously, because they simply don't make sense in blender, or wouldn't work the same.

As it is by default, this menu will not work well out of the box. The selection menu and context menus will not activate due to the way all of blender's default keymaps are setup. I highly encourage you to edit the default shortcuts of either the addon or the default keymap. By default, the menus have the same shortcuts as their maya counterparts.

If this is your first time using blender, coming from maya, I suggest you download and install the keymap I have included as well. It's an edited version of the Industry Standard keymap that's included with blender, which I've setup to work with my addon out of the box, and it should work very similarly to maya!

If you'd like to support me, please consider buying the addon on [Gumroad](https://gum.co/emctools) 

**UPDATES:**


***VERSION 1.2.2:***

- Added support to Blender 2.91's new boolean modifiers. From 2.91 on, this addon's booleans will be using collections instead of objects.

- Fixed/adjusted a few minor things


***VERSION 1.2.0:***

- Added support to Blender 2.90 (2.83 support was not dropped)

- Smooth Faces operator was partially rewritten. It now subdivides exactly like the Subdivision Surface modifier no matter the topology, albeit the smoothing is still not the same

- Controls for all parametric primitives were moved to the Side Panel -> View tab -> Properties

- Added a build corner operator (experimental)

- Refresh Weighted Normals can now adapt to the mode of the initial Weighted Normals modifier. It now also defaults to Face Area with Angle

- Random fixes



***VERSION 1.1.0:***

- Replaced the Bevel % operator with the EMC Patch operator because it's more useful and I never used the old one

- All primitives are now parametric primitives

- Added the modifiers menu which includes modal modifier creation for some modifiers

- Removed the need for the booltool addon, because I re-created the functionality from scratch. I also added compatibility with the Bool XR Addon for setting up the multibool operator automatically

- Added check boxes to the addon preferences panel to show which addons need to be enabled (clicking them doesn't do anything though)

- Added a reset button for the top bar and tools in object and edit modes

- Added the ability to create face maps from materials and UV islands

- Added a shortcut to toggle all available Subdivision Surface modifiers on all selected objects

- Added more options for sharpening edges

- Added a UV selection menu

- Added a delete keyframes option for the curve editor that doesn't show a popup

- Fixed some things

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "EMC Tools",
    "author": "Ehab Charek",
    "version": (1, 2, 3),
    "blender": (2, 83, 3),
    "location": "View3D",
    "category": "Pie Menu",
    "description": "EMC's custom shortcuts and menus. Partially Maya Marking Menu Replicas tho",
    "doc_url": "https://gum.co/emctools",
    "warning": "WIP"
}

import bpy, bmesh, math, mathutils, addon_utils
from bpy.types import Menu, Operator
from rna_prop_ui import rna_idprop_ui_prop_get


version = bpy.app.version
int_version = int(str(version[0])+str(version[1]))

def bmesh_vert_active(bm):
    if bm.select_history:
        elem = bm.select_history[-1]
        if isinstance(elem, bmesh.types.BMVert):
            return elem
    return None

def move_to_col(ob_name, col_name, scene, check):
    does_it_exist = True if bpy.data.collections.get(col_name) else False

    if does_it_exist and check:
        pass
    else:
        bpy.data.collections.new(col_name)
        if col_name == "EMC Extras" and int_version > 290:
            bpy.data.collections['EMC Extras'].color_tag = 'COLOR_08'
        if scene:
            bpy.context.scene.collection.children.link(bpy.data.collections[col_name])
        else:
            bpy.context.collection.children.link(bpy.data.collections[col_name])

    try:
        bpy.data.collections[col_name].objects.link(ob_name)
    except:
        pass
        
    for i in ob_name.users_collection:
        if i == bpy.data.collections[col_name]:
            pass
        else:
            i.objects.unlink(ob_name)

def delete_drivers():
    driver = bpy.context.active_object.animation_data.drivers
    for fc in driver:
        driver.remove(driver[0])

def create_prop(name, value, desc, use_min, use_max, use_lims, use_soft_min, use_soft_max, min, max, soft_min, soft_max):
    bpy.context.active_object[name] = value
    prop_ui = rna_idprop_ui_prop_get(bpy.context.active_object, name)
    prop_ui["default"] = value
    if use_min:
        prop_ui["min"] = min
    if use_max:
        prop_ui["max"] = max
    prop_ui["is_overridable_library"] = True
    prop_ui["use_soft_limits"] = use_lims
    if use_soft_min:
        prop_ui["soft_min"] = soft_min
    if use_soft_max:
        prop_ui["soft_max"] = soft_max
    prop_ui["description"] = desc

def create_driver(mod_name, mod_var, expression, path):
    dr = bpy.context.object.modifiers[mod_name].driver_add(mod_var)
    dr.driver.type='SCRIPTED'
    dr.driver.expression = expression
    var = dr.driver.variables.new()
    var.type = 'SINGLE_PROP'
    var.targets[0].id = bpy.context.object
    var.targets[0].data_path = path


#-------------------------------------------------------------------
#Pie Menus e

class VIEW3D_MT_customMenu(Menu):
    bl_label = "EMC Tools Menu"
    bl_idname = "Mesh.EMC_MT_ToolsMenu"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        pie.operator("emc.repeat", icon='SCRIPTPLUGINS') #CON_TRANSLIKE

        if bpy.context.object.mode == 'EDIT':
            pie.operator("emc.hole", icon='CLIPUV_DEHLT')
            pie.operator("emc.checkerloop", icon='SNAP_EDGE')
            pie.operator("emc.patchfill", icon='MESH_GRID')
            pie.operator("emc.buildcorner", icon='OUTLINER_DATA_EMPTY')
            pie.operator("emc.panellines", icon='MOD_MULTIRES')

        elif bpy.context.object.mode == 'OBJECT':
            pie.operator("emc.cage", icon='FILE_3D')
            pie.operator("emc.purge", icon='CANCEL')
        
class VIEW3D_MT_EmcModifiers(Menu):
    bl_label = "EMC Modifiers Menu"
    bl_idname = "Mesh.EMC_MT_Modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        pie.operator("emc.arraymod", icon='MOD_ARRAY')
        pie.operator("emc.bevelmod", icon='MOD_BEVEL')
        pie.operator("emc.screwmod", icon='MOD_SCREW')
        pie.operator("emc.solidifymod", icon='MOD_SOLIDIFY')
        pie.operator("emc.weightmod", icon='MOD_NORMALEDIT')
        pie.operator("object.modifier_add", text='Add Weld Modifier', icon = "AUTOMERGE_OFF").type='WELD'
        pie.operator("emc.deformmod", icon='MOD_SIMPLEDEFORM')
        pie.operator("emc.displacemod", icon='MOD_DISPLACE')

        pie.separator()
        pie.separator()
        other = pie.column()
        gap = other.column()
        gap.separator()
        gap.scale_y = 7
        other_menu = other.column()

        other_menu.operator("emc.mirror", icon = "MOD_MIRROR").existing = False
        other_menu.operator("object.modifier_add", text='SubD Surface', icon = "MOD_SUBSURF").type='SUBSURF'
        other_menu.operator('wm.call_menu_pie', text='EMC Boolean', icon='MOD_BOOLEAN').name="emc.boolmenu"
        other_menu.operator("emc.addmod", text = "Decimate", icon = "MOD_DECIM").modifier = 'DECIMATE'
        other_menu.operator("emc.addmod", text = "Data Transfer", icon = "MOD_DATA_TRANSFER").modifier = 'DATA_TRANSFER'
        other_menu.operator("emc.addmod", text = "Shrinkwrap", icon = "MOD_SHRINKWRAP").modifier = 'SHRINKWRAP'
        other_menu.operator("emc.addmod", text = "Mesh Deform", icon = "MOD_MESHDEFORM").modifier = 'MESH_DEFORM'
        other_menu.operator("emc.addmod", text = "Triangulate", icon = "MOD_TRIANGULATE").modifier = 'TRIANGULATE'
        other_menu.operator("emc.addmod", text = "Vertex Weight Edit", icon = "MOD_VERTEX_WEIGHT").modifier = 'VERTEX_WEIGHT_EDIT'
        other_menu.operator("object.modifier_add", text='Remesh', icon = "MOD_REMESH").type='REMESH'
        other_menu.operator("emc.addmod", text = "Cast", icon = "MOD_CAST").modifier = 'CAST'

class VIEW3D_MT_Extras(Menu):
    bl_label = "EMC Extras"
    bl_idname = "Mesh.EMC_MT_Extras"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        if bpy.context.scene.transform_orientation_slots[0].type == 'GLOBAL':
            pie.operator("emc.global", depress=True, icon='ORIENTATION_GLOBAL')
        else:
            pie.operator("emc.global", depress=False, icon='ORIENTATION_GLOBAL')

        if bpy.context.scene.transform_orientation_slots[0].type == 'GIMBAL':
            pie.operator("emc.gimbal", depress=True, icon='ORIENTATION_GIMBAL')
        else:
            pie.operator("emc.gimbal", depress=False, icon='ORIENTATION_GIMBAL')

        pie = pie.row()
        pie.label(text='')
        pie = layout.menu_pie()

        if bpy.context.object.mode == 'EDIT':
            pie.operator('wm.call_menu_pie', text='Symmetry', icon='MOD_MIRROR').name="emc.symmetry"
        else:
            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

        if bpy.context.scene.transform_orientation_slots[0].type == 'LOCAL':
            pie.operator("emc.local", depress=True, icon='ORIENTATION_LOCAL')
        else:
            pie.operator("emc.local", depress=False, icon='ORIENTATION_LOCAL')

        if bpy.context.scene.transform_orientation_slots[0].type == 'NORMAL':
            pie.operator("emc.normal", depress=True, icon='ORIENTATION_NORMAL')
        else:
            pie.operator("emc.normal", depress=False, icon='ORIENTATION_NORMAL')

class VIEW3D_MT_selectMode(Menu):
    bl_label = "EMC Selection Mode"
    bl_idname = "Mesh.EMC_MT_SelectMode"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        if bpy.context.tool_settings.mesh_select_mode[0] == True and bpy.context.object.mode == 'EDIT':
            pie.operator("emc.vertex", depress=True, icon='VERTEXSEL')
        else:
            pie.operator("emc.vertex", depress=False, icon='VERTEXSEL')
        pie.operator("emc.uv", icon='UV')
        if bpy.context.tool_settings.mesh_select_mode[2] == True and bpy.context.object.mode == 'EDIT':
            pie.operator("emc.face", depress=True, icon='FACESEL')
        else:
            pie.operator("emc.face", depress=False, icon='FACESEL')
        if bpy.context.tool_settings.mesh_select_mode[1] == True and bpy.context.object.mode == 'EDIT':
            pie.operator("emc.edge", depress=True, icon='EDGESEL')
        else:
            pie.operator("emc.edge", depress=False, icon='EDGESEL')
        pie.operator("emc.reset", icon='FILE_REFRESH')
        if bpy.context.object.mode == 'OBJECT':
            pie.operator("object.mode_set", text='Object Mode', depress=True, icon='OBJECT_DATA').mode='OBJECT'
        else:
            pie.operator("object.mode_set", text='Object Mode', depress=False, icon='OBJECT_DATA').mode='OBJECT'
        pie.operator("emc.vertface", icon='SNAP_FACE_CENTER')
        pie.operator("emc.multi", icon='EDITMODE_HLT')

        pie.separator()
        pie.separator()
        other = pie.column()
        gap = other.column()
        gap.separator()
        gap.scale_y = 7
        other_menu = other.column()

        if bpy.context.object.mode == 'EDIT':
            other_menu.operator("mesh.select_all", text = "Select All", icon = "RESTRICT_SELECT_OFF").action='SELECT'
        elif bpy.context.object.mode == 'OBJECT':
            other_menu.operator("object.select_all", text = "Select All", icon = "RESTRICT_SELECT_OFF").action='SELECT'
        if bpy.context.object.mode == 'EDIT':
            other_menu.operator("mesh.select_all", text = "Deselect All", icon = "RESTRICT_SELECT_ON").action='DESELECT'
        elif bpy.context.object.mode == 'OBJECT':
            other_menu.operator("object.select_all", text = "Deselect All", icon = "RESTRICT_SELECT_ON").action='DESELECT'
        other_menu.operator("emc.selheir", icon = "CON_CHILDOF")
        if bpy.context.object.mode == 'EDIT':
            other_menu.operator("mesh.select_all", text = "Invert Selection", icon = "ARROW_LEFTRIGHT").action='INVERT'
        elif bpy.context.object.mode == 'OBJECT':
            other_menu.operator("object.select_all", text = "Invert Selection", icon = "ARROW_LEFTRIGHT").action='INVERT'
        other_menu.operator("emc.selsim", icon = "FACE_MAPS")
        if 'materials_utils' in bpy.context.preferences.addons.keys():
            other_menu.operator("wm.call_menu", text="Material Utilities", icon = "MATERIAL").name="VIEW3D_MT_materialutilities_main"
        else:
            other_menu.operator("emc.null", text='Material Utilities addon not enabled', icon='ERROR')
        other_menu.separator()

        other_menu.operator("emc.facemapmaterial", icon='FACE_MAPS')
        other_menu.operator("emc.islandmaps", icon = "UV_DATA")

class VIEW3D_MT_Context(Menu):
    bl_label = "EMC Context Menu"
    bl_idname = "Mesh.EMC_MT_Add"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        if bpy.context.selected_objects == []:
            # ADD MENU

            pie.operator("emc.cylinder", icon='MESH_CYLINDER')
            pie.operator("emc.sphere", icon='MESH_UVSPHERE')
            pie.operator("emc.cube", icon='MESH_CUBE')
            if 'add_mesh_extra_objects' in bpy.context.preferences.addons.keys():
                pie.operator("mesh.primitive_emptyvert_add", icon='DECORATE')
            else:
                pie.operator("emc.null", text='Extra Objects addon not enabled', icon='ERROR')  
            pie.operator("emc.plane", icon='MESH_PLANE')
            pie.operator("emc.circle", icon='MESH_CIRCLE')
            pie.operator("emc.cone", icon='MESH_CONE')
            pie.operator("emc.torus", icon='MESH_TORUS')

            pie.separator()
            pie.separator()
            other = pie.column()
            gap = other.column()
            gap.separator()
            gap.scale_y = 7
            other_menu = other.column()

            if 'add_mesh_extra_objects' in bpy.context.preferences.addons.keys():
                other_menu.operator("mesh.primitive_solid_add", icon = "SEQ_CHROMA_SCOPE")
            else:
                other_menu.operator("emc.null", text='Extra Objects addon not enabled', icon='ERROR')                  
            other_menu.operator("emc.prism", icon='OUTLINER_OB_MESH')
            other_menu.operator("emc.pipe", icon='META_CAPSULE')
            other_menu.operator("emc.helix", icon='MOD_SCREW')
            if 'add_mesh_extra_objects' in bpy.context.preferences.addons.keys():
                other_menu.operator('wm.call_menu_pie', text='Gears', icon='SETTINGS').name="emc.gears"
            else:
                other_menu.operator("emc.null", text='Extra Objects addon not enabled', icon='ERROR')  
            other_menu.operator("mesh.primitive_ico_sphere_add", icon = "MESH_ICOSPHERE") 
            other_menu.operator("emc.mobius", icon = "HAND") 

            other_menu.separator()

            other_menu.operator("object.text_add", icon='OUTLINER_OB_FONT')
            other_menu.operator("import_curve.svg", icon='IMAGE_PLANE')
            other_menu.operator("emc.polydraw", text='Retopo Setup', icon='MESH_GRID')
        else:
            # TOOLS MENU

            if bpy.context.active_object.type == 'MESH':
                pie = layout.menu_pie()

                pie.operator("emc.knife", icon='MOD_SIMPLIFY')

                pie = pie.row()
                pie.label(text='')
                pie = layout.menu_pie()

                pie.operator("emc.extrude", icon='MOD_SOLIDIFY')
                pie.operator("emc.weld", icon='TRANSFORM_ORIGINS')
                pie.operator("object.mode_set", text='Sculpt Mode', icon='SCULPTMODE_HLT').mode='SCULPT'
                pie.operator("emc.fillholes", icon='SELECT_SET')
                pie.operator("emc.loopcut", icon='MOD_MULTIRES')
                pie.operator('wm.call_menu_pie', text='Smoothing', icon='MATSHADERBALL').name="emc.smoothing"

                pie.separator()
                pie.separator()
                other = pie.column()
                gap = other.column()
                gap.separator()
                gap.scale_y = 7
                other_menu = other.column()

                other_menu.operator("emc.offsetedge", text='Offset Edge Loop', icon = "ARROW_LEFTRIGHT")
                if "Subdivision" in bpy.context.object.modifiers:
                    other_menu.operator("object.subdivision_set", text='Add SubD Modifier', depress=True, icon = "MOD_SUBSURF").level=2
                else:
                    other_menu.operator("object.subdivision_set", text='Add SubD Modifier', depress=False, icon = "MOD_SUBSURF").level=2
                
                other_menu.separator()

                other_menu.operator("emc.projcurve", text='Project Curve', icon = "CURVE_NCURVE")
                other_menu.operator("emc.knifeproject", text='Knife Project', icon = "FCURVE")
                other_menu.operator("object.convert", text='Convert Menu', icon = "FILE_REFRESH")

                other_menu.separator()

                if "EMC Mirror" in bpy.context.object.modifiers:
                    other_menu.operator("emc.mirror", depress=True, icon = "MOD_MIRROR").existing = True
                else:
                    other_menu.operator("emc.mirror", depress=False, icon = "MOD_MIRROR").existing = True
                other_menu.operator("object.modifier_add", text='Add Triangulate Modifier', icon = "MOD_TRIANGULATE").type='TRIANGULATE'
                other_menu.operator("emc.tristoquads", icon = "UV_ISLANDSEL")
                other_menu.operator("object.modifier_add", text='Add Decimate Modifier', icon = "MOD_DECIM").type='DECIMATE'
                other_menu.operator("object.modifier_add", text='Add Remesh Modifier', icon = "MOD_REMESH").type='REMESH'

                other_menu.separator()

                other_menu.operator("emc.separate", icon = "MOD_EXPLODE")
                other_menu.operator("object.join", icon = "SELECT_EXTEND")
                other_menu.operator('wm.call_menu_pie', text='EMC Boolean', icon='MOD_BOOLEAN').name="emc.boolmenu"
                other_menu.operator("emc.polydraw", text='Retopo Setup', icon='MESH_GRID')
            else:
                pie = pie.row()
                pie.label(text='')
                pie = layout.menu_pie()

                pie = pie.row()
                pie.label(text='')
                pie = layout.menu_pie()

                pie = pie.row()
                pie.label(text='')
                pie = layout.menu_pie()

                pie.operator("emc.null", text='Non-MESH objects currently not supported', icon='ERROR')
        
class VIEW3D_MT_EditContext(Menu):
    bl_label = "EMC Edit Mode Context Menu"
    bl_idname = "Mesh.EMC_MT_Edit"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (True, False, False):
            # Vertex Select Menu

            pie = layout.menu_pie()

            if bpy.context.workspace.tools.from_space_view3d_mode("EDIT_MESH", create=False).idname == 'builtin.knife':
                pie.operator("emc.knife", depress=True, icon='MOD_SIMPLIFY')
            else:
                pie.operator("emc.knife", depress=False, icon='MOD_SIMPLIFY')
            
            if int_version > 283:
                pie.operator("mesh.bevel", icon='MOD_BEVEL').affect='VERTICES'
            else:
                pie.operator("mesh.bevel", icon='MOD_BEVEL').vertex_only=True

            pie.operator("emc.extrudevert", icon='MOD_WARP')
            pie.operator('wm.call_menu_pie', text='Merge', icon='FULLSCREEN_EXIT').name="Mesh.EMC_MT_Merge"
            pie.operator("wm.toolbar_fallback_pie", text='Selection Type', icon='RESTRICT_SELECT_OFF')
            if 'mesh_tools' in bpy.context.preferences.addons.keys():
                pie.operator("mesh.relax", icon='MOD_FLUIDSIM')
            else:
                pie.operator("emc.null", text='Edit Mesh Tools addon not enabled', icon='ERROR')  
            pie.operator("mesh.dissolve_verts", icon='CANCEL')
            pie.operator('wm.call_menu_pie', text='Vertex Normals', icon='NORMALS_VERTEX').name="emc.vertnorm"

            pie.separator()
            pie.separator()
            other = pie.column()
            gap = other.column()
            gap.separator()
            gap.scale_y = 7
            other_menu = other.column()

            other_menu.operator("transform.edge_crease", text='Crease', icon = "SNAP_VOLUME")
            other_menu.operator("mesh.vert_connect_path", text='Connect Path', icon='CON_FOLLOWTRACK')
            other_menu.operator("mesh.rip_move", icon='LIBRARY_DATA_BROKEN')

            if 'mesh_looptools' in bpy.context.preferences.addons.keys():
                other_menu.operator("mesh.looptools_circle", text='Circularize', icon='MESH_CIRCLE')
            else:
                other_menu.operator("emc.null", text='Loop Tools addon not enabled', icon='ERROR')   

            other_menu.separator()

            other_menu.operator("object.mode_set", text='Vertex Paint Mode', icon='VPAINT_HLT').mode='VERTEX_PAINT'

        elif tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, True, False):
            # Edge Select Menu

            pie = layout.menu_pie()

            if bpy.context.workspace.tools.from_space_view3d_mode("EDIT_MESH", create=False).idname == 'builtin.knife':
                pie.operator("emc.knife", depress=True, icon='MOD_SIMPLIFY')
            else:
                pie.operator("emc.knife", depress=False, icon='MOD_SIMPLIFY')

            if int_version > 283:
                pie.operator("mesh.bevel", icon='MOD_BEVEL').affect='EDGES'
            else:
                pie.operator("mesh.bevel", icon='MOD_BEVEL').vertex_only=False

            if bpy.context.workspace.tools.from_space_view3d_mode("EDIT_MESH", create=False).idname == 'builtin.extrude_region':
                pie.operator("emc.extrude", depress=True, icon='EDGESEL')
            else:
                pie.operator("emc.extrude", depress=False, icon='EDGESEL')
            pie.operator('wm.call_menu_pie', text='Merge', icon='FULLSCREEN_EXIT').name="Mesh.EMC_MT_Merge"
            pie.operator("wm.toolbar_fallback_pie", text='Selection Type', icon='RESTRICT_SELECT_OFF')
            pie.operator('wm.call_menu_pie', text='Rotate Edge', icon='CON_ROTLIKE').name="emc.rotedge"
            pie.operator("mesh.dissolve_edges", icon='CANCEL')
            pie.operator('wm.call_menu_pie', text='Smoothing', icon='MATSHADERBALL').name="emc.smoothing"

            pie.separator()
            pie.separator()
            other = pie.column()
            gap = other.column()
            gap.separator()
            gap.scale_y = 7
            other_menu = other.column()

            other_menu.operator("transform.edge_crease", text='Crease', icon = "SNAP_VOLUME")
            if bpy.context.workspace.tools.from_space_view3d_mode("EDIT_MESH", create=False).idname == 'builtin.offset_edge_loop_cut':
                other_menu.operator("emc.offsetedge", text='Offset Edge Loop', depress=True, icon = "ARROW_LEFTRIGHT")
            else:
                other_menu.operator("emc.offsetedge", text='Offset Edge Loop', depress=False, icon = "ARROW_LEFTRIGHT")
            if bpy.context.workspace.tools.from_space_view3d_mode("EDIT_MESH", create=False).idname == 'builtin.loop_cut':
                other_menu.operator("emc.loopcut", text='Loop Cut', depress=True, icon = "MOD_MULTIRES")
            else:
                other_menu.operator("emc.loopcut", text='Loop Cut', depress=False, icon = "MOD_MULTIRES")
            if bpy.context.workspace.tools.from_space_view3d_mode("EDIT_MESH", create=False).idname == 'builtin.edge_slide':
                other_menu.operator("emc.edgeslide", text='Edge Slide', depress=True, icon = "OPTIONS")
            else:
                other_menu.operator("emc.edgeslide", text='Edge Slide', depress=False, icon = "OPTIONS")
            if 'mesh_looptools' in bpy.context.preferences.addons.keys():
                other_menu.operator("mesh.looptools_circle", text='Circularize', icon='MESH_CIRCLE')
            else:
                other_menu.operator("emc.null", text='Loop Tools addon not enabled', icon='ERROR')  

            other_menu.separator()

            other_menu.operator("mesh.subdivide", text='Subdivide/Connect',  icon = "SNAP_MIDPOINT").quadcorner='STRAIGHT_CUT'
            other_menu.operator("mesh.bridge_edge_loops", icon = "OUTLINER_OB_LATTICE")
            if 'mesh_f2' in bpy.context.preferences.addons.keys():
                other_menu.operator("mesh.f2", icon = "CLIPUV_DEHLT")
            else:
                other_menu.operator("emc.null", text='F2 addon not enabled', icon='ERROR')  
            other_menu.operator("mesh.rip_move", icon='LIBRARY_DATA_BROKEN')
        else:
            # Any other selection mode menu

            pie = layout.menu_pie()

            if bpy.context.workspace.tools.from_space_view3d_mode("EDIT_MESH", create=False).idname == 'builtin.knife':
                pie.operator("emc.knife", depress=True, icon='MOD_SIMPLIFY')
            else:
                pie.operator("emc.knife", depress=False, icon='MOD_SIMPLIFY')

            if int_version > 283:
                pie.operator("mesh.bevel", icon='MOD_BEVEL').affect='EDGES'
            else:
                pie.operator("mesh.bevel", icon='MOD_BEVEL').vertex_only=False

            if bpy.context.workspace.tools.from_space_view3d_mode("EDIT_MESH", create=False).idname == 'builtin.extrude_region':
                pie.operator("emc.extrude", depress=True, icon='EDGESEL')
            else:
                pie.operator("emc.extrude", depress=False, icon='EDGESEL')
            pie.operator('wm.call_menu_pie', text='Merge', icon='FULLSCREEN_EXIT').name="Mesh.EMC_MT_Merge"
            pie.operator("wm.toolbar_fallback_pie", text='Selection Type', icon='RESTRICT_SELECT_OFF')
            pie.operator('mesh.poke', icon='X')
            if bpy.context.workspace.tools.from_space_view3d_mode("EDIT_MESH", create=False).idname == 'builtin.spin':
                pie.operator("emc.spin", text='Spin Tool', depress=True, icon='DECORATE_OVERRIDE')
            else:
                pie.operator("emc.spin", text='Spin Tool', depress=False, icon='DECORATE_OVERRIDE')
            pie.operator('wm.call_menu_pie', text='Face Normals', icon='NORMALS_FACE').name="emc.vertnorm"

            pie.separator()
            pie.separator()
            other = pie.column()
            gap = other.column()
            gap.separator()
            gap.scale_y = 7
            other_menu = other.column()

            other_menu.operator("emc.smoothfaces", icon = "MOD_SMOOTH")
            if 'mesh_looptools' in bpy.context.preferences.addons.keys():
                other_menu.operator("mesh.looptools_circle", text='Circularize', icon='MESH_CIRCLE')
            else:
                other_menu.operator("emc.null", text='Loop Tools addon not enabled', icon='ERROR')  
            other_menu.operator("emc.split", icon = "LIBRARY_DATA_BROKEN")
            other_menu.operator("mesh.quads_convert_to_tris", icon = "MOD_TRIANGULATE")
            other_menu.operator("mesh.tris_convert_to_quads", icon = "UV_ISLANDSEL")
            other_menu.operator("mesh.bridge_edge_loops", icon = "OUTLINER_OB_LATTICE")

            other_menu.separator()

            if "EMC Mirror" in bpy.context.object.modifiers:
                other_menu.operator("emc.mirror", depress=True, icon = "MOD_MIRROR").existing = True
            else:
                other_menu.operator("emc.mirror", depress=False, icon = "MOD_MIRROR").existing = True
            other_menu.operator("mesh.separate", icon = "MOD_EDGESPLIT")
            other_menu.operator("emc.weld", icon='TRANSFORM_ORIGINS')

class VIEW3D_MT_uvMenu(Menu):
    bl_label = "EMC Select UV"
    bl_idname = "Mesh.EMC_MT_SelectUV"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        if bpy.context.scene.tool_settings.use_uv_select_sync == True:

            pie.operator("emc.vertex", depress=bpy.context.tool_settings.mesh_select_mode[0], icon='VERTEXSEL')
            pie.operator("wm.call_menu", text='UV Menu', icon='UV').name="VIEW3D_MT_uv_map"
            pie.operator("emc.face", depress=bpy.context.tool_settings.mesh_select_mode[2], icon='FACESEL')
            pie.operator("emc.edge", depress=bpy.context.tool_settings.mesh_select_mode[1], icon='EDGESEL')

            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie.operator("emc.uvselectmode", text='UV Sync Selection', depress=True, icon='UV_SYNC_SELECT').mode = 'SYNC'

        else:

            if bpy.context.scene.tool_settings.uv_select_mode == 'VERTEX':
                pie.operator("emc.uvselectmode", text='Vertex', depress=True, icon='UV_VERTEXSEL').mode = 'VERTEX'
            else:
                pie.operator("emc.uvselectmode", text='Vertex', depress=False, icon='UV_VERTEXSEL').mode = 'VERTEX'

            pie.operator("wm.call_menu", text='UV Menu', icon='UV').name="VIEW3D_MT_uv_map"

            if bpy.context.scene.tool_settings.uv_select_mode == 'FACE':
                pie.operator("emc.uvselectmode", text='Face', depress=True, icon='UV_FACESEL').mode = 'FACE'
            else:
                pie.operator("emc.uvselectmode", text='Face', depress=False, icon='UV_FACESEL').mode = 'FACE'

            if bpy.context.scene.tool_settings.uv_select_mode == 'EDGE':
                pie.operator("emc.uvselectmode", text='Edge', depress=True, icon='UV_EDGESEL').mode = 'EDGE'
            else:
                pie.operator("emc.uvselectmode", text='Edge', depress=False, icon='UV_EDGESEL').mode = 'EDGE'

            if bpy.context.scene.tool_settings.uv_select_mode == 'ISLAND':
                pie.operator("emc.uvselectmode", text='Island', depress=True, icon='UV_ISLANDSEL').mode = 'ISLAND'
            else:
                pie.operator("emc.uvselectmode", text='Island', depress=False, icon='UV_ISLANDSEL').mode = 'ISLAND'

            pie.operator("emc.uvselectmode", text='UV Sync Selection', depress=False, icon='UV_SYNC_SELECT').mode = 'SYNC'

        pie.operator("uv.mark_seam", text='Clear Seam', icon='META_CUBE').clear = True
        pie.operator("uv.mark_seam", text='Mark Seam', icon='SNAP_VOLUME').clear = False

        pie.separator()
        pie.separator()
        other = pie.column()
        gap = other.column()
        gap.separator()
        gap.scale_y = 7
        other_menu = other.column()

        other_menu.operator("emc.moveislands", icon = "GROUP_UVS")


#-------------------------------------------------------------------
#Custom Operators
          
class Helix(bpy.types.Operator):
    bl_label = "Helix"
    bl_idname = "emc.helix"
    bl_description = "Create a Helix Primitive"
    bl_options = {'REGISTER', 'UNDO'}

    width: bpy.props.FloatProperty(
        name = "Width", 
        description = "Width of the Spring", 
        default = 2.0,
        min = 0.5
    )

    springiness: bpy.props.FloatProperty(
        name = "Springiness",
        description = "Separation of the Spring Segments",
        default = 1,
        min = 0.1
    )

    thicc: bpy.props.FloatProperty(
        name = "THICC",
        description = "The Chonkiness of the boi",
        default = 0.5,
        min = 0.01
        )

    res: bpy.props.IntProperty(
        name = "Spring Subdivisions",
        description = "Number of Segments Along the Body of the Spring",
        default = 16,
        min = 3
    )

    segments: bpy.props.IntProperty(
        name = "Cross-Segments",
        description = "Number of Segments of the Pipe Profile",
        default = 16,
        min = 3
    )

    iterations: bpy.props.IntProperty(
        name = "Iterations",
        description = "Number of Iterations the Spring Body is Arrayed",
        default = 4,
        min = 1
    )

    apply: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Create Primitive Non-Destructively if Disabled",
        default = False,
    )
      
    def execute(self, context):
        bpy.ops.mesh.primitive_vert_add()
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers["Displace"].strength = self.thicc
        bpy.context.object.modifiers["Displace"].direction = 'Z'
        bpy.context.object.modifiers["Displace"].show_in_editmode = True
        bpy.context.object.modifiers["Displace"].show_on_cage = True

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers["Screw"].axis = 'X'
        bpy.context.object.modifiers["Screw"].steps = self.segments

        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers["Displace.001"].direction = 'Y'
        bpy.context.object.modifiers["Displace.001"].strength = self.width
        bpy.context.object.modifiers["Displace.001"].show_in_editmode = True

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers["Screw.001"].screw_offset = self.springiness
        bpy.context.object.modifiers["Screw.001"].iterations = self.iterations
        bpy.context.object.modifiers["Screw.001"].steps = self.res
        bpy.context.object.modifiers["Screw.001"].use_merge_vertices = True

        # --------------

        create_prop("THICC", self.thicc, 'The Chonkiness of the boi', True, False, True, True, True, 0.01, 100.0, 0.01, 100.0)
        create_driver('Displace', 'strength', 'var', '["THICC"]')
        
        create_prop("Cross-Segments", self.segments, 'Number of Segments of the Pipe Profile', True, True, True, True, True, 3, 96*2, 3, 96)
        create_driver('Screw', 'steps', 'var', '["Cross-Segments"]')
        create_driver('Screw', 'render_steps', 'var', 'modifiers["Screw"].steps')

        create_prop("Width", self.width, 'Width of the Spring', True, True, True, True, True, 0.5, 96*2, 0.5, 96)
        create_driver('Displace.001', 'strength', 'var', '["Width"]')

        create_prop("Springiness", self.springiness, 'Separation of the Spring Segments', True, False, True, True, True, 0.1, 100.0, 0.1, 100.0)
        create_driver('Screw.001', 'screw_offset', 'var', '["Springiness"]')

        create_prop("Iterations", self.iterations, 'Number of Iterations the Spring Body is Arrayed', True, False, True, True, True, 0, 1, 0, 10)
        create_driver('Screw.001', 'iterations', 'var', '["Iterations"]')

        create_prop("Spring Subdivisions", self.res, 'Number of Segments Along the Body of the Spring', True, True, True, True, True, 3, 96*2, 3, 96)
        create_driver('Screw.001', 'steps', 'var', '["Spring Subdivisions"]')
        create_driver('Screw.001', 'render_steps', 'var', 'modifiers["Screw.001"].steps')

        # --------------

        for i in bpy.context.active_object.modifiers:
            i.show_expanded = False

        if self.apply:
            bpy.ops.object.convert(target='MESH')

            del bpy.context.active_object['THICC']
            del bpy.context.active_object['Cross-Segments']
            del bpy.context.active_object['Width']
            del bpy.context.active_object['Springiness']
            del bpy.context.active_object['Iterations']
            del bpy.context.active_object['Spring Subdivisions']
            delete_drivers()

        bpy.context.object.name = "EMC Helix"
        bpy.context.object.data.name = "EMC Helix"
        return{'FINISHED'}

class Pipe(bpy.types.Operator):
    bl_label = "Pipe"
    bl_idname = "emc.pipe"
    bl_description = "Create a Pipe Primitive"
    bl_options = {'REGISTER', 'UNDO'}
      
    width: bpy.props.FloatProperty(
        name = "Width", 
        description = "Width of the Pipe", 
        default = 1.0,
        min = 0.1
    )

    height: bpy.props.FloatProperty(
        name = "Height",
        description = "Height",
        default = 1,
        min = 0.1
    )

    thicc: bpy.props.FloatProperty(
        name = "THICC",
        description = "The Chonkiness of the boi",
        default = 0.25,
        min = 0.01
        )

    subdivisions: bpy.props.IntProperty(
        name = "Vertical Subdivisions",
        description = "Number of Cuts Applied Vertically",
        default = 1,
        min = 1
    )

    segments: bpy.props.IntProperty(
        name = "Segments",
        description = "Number of Segments, or Sides",
        default = 16,
        min = 3
    )

    apply: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Create Primitive Non-Destructively if Disabled",
        default = False,
    )

    def execute(self, context):
        bpy.ops.mesh.primitive_vert_add()
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers["Displace"].direction = 'X'
        bpy.context.object.modifiers["Displace"].strength = self.width
        bpy.context.object.modifiers["Displace"].show_in_editmode = True
        bpy.context.object.modifiers["Displace"].show_on_cage = True

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers["Screw"].steps = self.segments
        bpy.context.object.modifiers["Screw"].use_merge_vertices = True     

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers["Screw.001"].angle = 0
        bpy.context.object.modifiers["Screw.001"].screw_offset = 1
        bpy.context.object.modifiers["Screw.001"].steps = self.subdivisions
        bpy.context.object.modifiers["Screw.001"].screw_offset = self.height
        bpy.context.object.modifiers["Screw.001"].use_merge_vertices = True 

        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers["Solidify"].offset = 0
        bpy.context.object.modifiers["Solidify"].thickness = self.thicc

        # --------------

        create_prop("Width", self.width, 'Width of the Pipe', True, False, True, True, True, 0.1, 100.0, 0.1, 100.0)
        create_driver('Displace', 'strength', 'var', '["Width"]')
        
        create_prop("Segments", self.segments, 'Number of Segments, or Sides', True, True, True, True, True, 3, 96*2, 3, 96)
        create_driver('Screw', 'steps', 'var', '["Segments"]')
        create_driver('Screw', 'render_steps', 'var', 'modifiers["Screw"].steps')

        create_prop("THICC", self.thicc, 'The Chonkiness of the boi', True, False, True, True, True, 0.1, 100.0, 0.1, 100.0)
        create_driver('Solidify', 'thickness', 'var', '["THICC"]')

        create_prop("Vertical Subdivisions", self.subdivisions, 'Number of Cuts Applied Vertically', True, True, True, True, True, 1, 96*2, 1, 96)
        create_driver('Screw.001', 'steps', 'var', '["Vertical Subdivisions"]')
        create_driver('Screw.001', 'render_steps', 'var', 'modifiers["Screw.001"].steps')

        create_prop("Height", self.height, 'Height', True, False, True, True, True, 0.1, 100.0, 0.1, 100.0)
        create_driver('Screw.001', 'screw_offset', 'var', '["Height"]')

        # --------------

        bpy.context.object.data.use_auto_smooth = True

        for i in bpy.context.active_object.modifiers:
            i.show_expanded = False

        if self.apply:
            bpy.ops.object.convert(target='MESH')

            del bpy.context.active_object['Width']
            del bpy.context.active_object['Segments']
            del bpy.context.active_object['THICC']
            del bpy.context.active_object['Vertical Subdivisions']
            del bpy.context.active_object['Height']
            delete_drivers()

        bpy.context.object.name = "EMC Pipe"
        bpy.context.object.data.name = "EMC Pipe"
        return{'FINISHED'}

class Prism(bpy.types.Operator):
    bl_label = "Prism"
    bl_idname = "emc.prism"
    bl_description = "Create a Prism Primitive"
    bl_options = {'REGISTER', 'UNDO'}

    width: bpy.props.FloatProperty(
        name = "Width", 
        description = "The Width of the Prism", 
        default = 1.0,
        min = 0.1
    )

    sides: bpy.props.IntProperty(
        name = "Sides",
        description = "The Number of Sides",
        default = 3,
        min = 3
    )

    thicc: bpy.props.FloatProperty(
        name = "THICC",
        description = "The The Chonkiness of the boi",
        default = 2.0,
        min = 0.01
        )

    top: bpy.props.BoolProperty(
        name = "Ngon Cap",
        description = "The Style of the Caps",
        default = True,
    )

    topSub: bpy.props.IntProperty(
        name = "Cap Subdivision",
        description = "The Subdivision Level of the triangle Fan of the Caps",
        default = 2,
        min = 1
    )

    apply: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Create Primitive Non-Destructively if Disabled",
        default = False,
    )
      
    def execute(self, context):
        bpy.ops.mesh.primitive_vert_add()
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers["Screw"].angle = 0
        bpy.context.object.modifiers["Screw"].screw_offset = self.width
        bpy.context.object.modifiers["Screw"].axis = 'X'
        bpy.context.object.modifiers["Screw"].steps = self.topSub

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers["Screw.001"].use_merge_vertices = True
        bpy.context.object.modifiers["Screw.001"].steps = self.sides

        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers["Solidify"].offset = 0
        bpy.context.object.modifiers["Solidify"].thickness = self.thicc

        if self.top == True:
            bpy.ops.object.modifier_add(type='DECIMATE')
            bpy.context.object.modifiers["Decimate"].decimate_type = 'DISSOLVE'

            create_prop("Ngon Cap", self.top, 'The Style of the Caps', True, True, True, True, True, 0, 1, 0, 1)
            create_driver('Decimate', 'show_viewport', 'var', '["Ngon Cap"]')
            create_driver('Decimate', 'show_render', 'var', 'modifiers["Decimate"].show_viewport')

        else:
            pass

        # --------------

        create_prop("Width", self.width, 'The Width of the Prism', True, False, True, True, True, 0.1, 100.0, 0.1, 100.0)
        create_driver('Screw', 'screw_offset', 'var', '["Width"]')
        
        create_prop("Cap Subdivision", self.topSub, 'The Subdivision Level of the triangle Fan of the Caps', True, True, True, True, True, 1, 96*2, 1, 96)
        create_driver('Screw', 'steps', 'var', '["Cap Subdivision"]')
        create_driver('Screw', 'render_steps', 'var', 'modifiers["Screw"].steps')

        create_prop("Sides", self.sides, 'The Number of Sides', True, True, True, True, True, 3, 96*2, 3, 96)
        create_driver('Screw.001', 'steps', 'var', '["Sides"]')
        create_driver('Screw.001', 'render_steps', 'var', 'modifiers["Screw.001"].steps')

        create_prop("THICC", self.thicc, 'The The Chonkiness of the boi', True, False, True, True, True, 0.01, 100.0, 0.01, 100.0)
        create_driver('Solidify', 'thickness', 'var', '["THICC"]')

        # --------------

        bpy.context.object.data.use_auto_smooth = True

        for i in bpy.context.active_object.modifiers:
            i.show_expanded = False

        if self.apply:
            bpy.ops.object.convert(target='MESH')

            del bpy.context.active_object['Width']
            del bpy.context.active_object['Cap Subdivision']
            del bpy.context.active_object['Sides']
            del bpy.context.active_object['THICC']
            try:
                del bpy.context.active_object['Ngon Cap']
            except:
                pass
            delete_drivers()

        bpy.context.object.name = "EMC Prism"
        bpy.context.object.data.name = "EMC Prism"
        return{'FINISHED'}

class Mobius(bpy.types.Operator):
    bl_label = "Mobius Strip"
    bl_idname = "emc.mobius"
    bl_description = "Create a Mobius Strip"
    bl_options = {'REGISTER', 'UNDO'}

    width: bpy.props.FloatProperty(
        name = "Width", 
        description = "Width of the Strip", 
        default = 10,
        min = 1,
    )

    height: bpy.props.FloatProperty(
        name = "Height",
        description = "Height of the Strip",
        default = 0.33,
        min = 0.05,
    )

    thicc: bpy.props.FloatProperty(
        name = "THICC",
        description = "The Chonkiness of the boi",
        default = 0.1,
        min = 0.01, max = 1,
        )

    z_seg: bpy.props.IntProperty(
        name = "Vertical Segments",
        description = "Number of Segments Along the Vertical Surface of the Strip [(x*2)-1]",
        default = 2,
        min = 1, soft_max = 20
    )

    x_seg: bpy.props.IntProperty(
        name = "Horizantal Segments",
        description = "Number of Segments Along the Body of the Strip",
        default = 96,
        min = 3, soft_max = 1000
    )

    iterations: bpy.props.IntProperty(
        name = "Iterations",
        description = "Number of Iterations of the Strip Rotation",
        default = 1,
        min = 1, max = 50,
    )

    merge: bpy.props.FloatProperty(
        name = "Merge Distance",
        description = "Distance of Merging the Generated Seam",
        default = 0.05,
        min = 0.001,
        )
      
    def execute(self, context):
        bpy.ops.mesh.primitive_vert_add()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers["Screw"].screw_offset = self.height
        bpy.context.object.modifiers["Screw"].angle = 0
        bpy.context.object.modifiers["Screw"].steps = self.z_seg
        bpy.context.object.modifiers["Screw"].use_merge_vertices = True
        bpy.ops.object.modifier_add(type='MIRROR')
        bpy.context.object.modifiers["Mirror"].use_axis[2] = True
        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers["Screw.001"].axis = 'X'
        bpy.context.object.modifiers["Screw.001"].screw_offset = self.width
        bpy.context.object.modifiers["Screw.001"].angle = 0
        bpy.context.object.modifiers["Screw.001"].steps = self.x_seg
        bpy.context.object.modifiers["Screw.001"].use_normal_calculate = True
        bpy.context.object.modifiers["Screw.001"].use_normal_flip = True
        bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
        bpy.context.object.modifiers["SimpleDeform"].angle = 3.14159 * self.iterations
        bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
        bpy.context.object.modifiers["SimpleDeform.001"].deform_method = 'BEND'
        bpy.context.object.modifiers["SimpleDeform.001"].angle = 6.28319
        bpy.context.object.modifiers["SimpleDeform.001"].deform_axis = 'Z'
        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers["Solidify"].thickness = self.thicc
        bpy.context.object.modifiers["Solidify"].offset = 0
        bpy.ops.object.modifier_add(type='WELD')
        bpy.context.object.modifiers["Weld"].merge_threshold = self.merge

        y_dimension = bpy.context.active_object.dimensions[1]
        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers["Displace"].direction = 'Y'
        bpy.context.object.modifiers["Displace"].strength = -(y_dimension-0.5)

        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_non_manifold()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.data.use_auto_smooth = True

        bpy.context.object.name = "EMC Mobius Strip"
        bpy.context.object.data.name = "EMC Mobius Strip"
        return{'FINISHED'}

class PolyDraw(bpy.types.Operator):
    bl_label = "Polyquilt"
    bl_idname = "emc.polydraw"
    bl_description = "Enter Edit Mode and Select Poly Build Tool. If an Object is Selected, Origin and Rotation Will Match. Otherwise the Retopo Mesh Will be Aligned to the World"
      
    def execute(self, context):
        orig_cur_loc = mathutils.Vector.copy(bpy.context.scene.cursor.location)
        orig_cur_rot = mathutils.Euler.copy(bpy.context.scene.cursor.rotation_euler)

        try:
            bpy.ops.view3d.snap_cursor_to_selected()
            bpy.context.scene.cursor.rotation_euler = bpy.context.object.rotation_euler 
        except:
            bpy.ops.view3d.snap_cursor_to_center()
        bpy.ops.mesh.primitive_emptyvert_add() 

        bpy.context.scene.cursor.location = orig_cur_loc
        bpy.context.scene.cursor.rotation_euler = orig_cur_rot 

        bpy.ops.wm.tool_set_by_id(name="builtin.poly_build")
        bpy.ops.wm.tool_set_by_id(name="mesh_tool.poly_quilt")
        if bpy.context.workspace.tools.from_space_view3d_mode("EDIT_MESH", create=False).idname == 'mesh_tool.poly_quilt':
            self.report({"INFO"}, "PolyQuilt is installed! using it instead of Poly Build")
            print("PolyQuilt is installed! using it instead of Poly Build")
            bpy.context.object.data.use_mirror_x = True
        else:
            self.report({"INFO"}, "PolyQuilt is not installed. using Poly Build")
            print("PolyQuilt is not installed. using Poly Build")
            bpy.ops.object.modifier_add(type='MIRROR')
            bpy.context.object.modifiers["Mirror"].use_clip = True
        bpy.context.scene.tool_settings.use_mesh_automerge = True
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        bpy.context.scene.tool_settings.use_snap_backface_culling = True
        bpy.context.scene.tool_settings.use_snap_self = True
        bpy.context.scene.tool_settings.use_snap_project = True
        bpy.context.object.show_in_front = True
        bpy.context.space_data.shading.color_type = 'OBJECT'
        bpy.context.object.color = (0.270008, 1, 0.47917, 1 )
        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers["Displace"].show_in_editmode = True
        bpy.context.object.modifiers["Displace"].show_on_cage = True
        bpy.context.object.modifiers["Displace"].strength = 0.0005
        bpy.context.space_data.shading.show_backface_culling = True
        bpy.context.object.name = "Retopology Mesh"
        bpy.context.object.data.name = "Retopology Mesh"
        return{'FINISHED'}

class Knife(bpy.types.Operator):
    """Enter Edit Mode With the Knife Tool Enabled"""
    bl_label = "Knife"
    bl_idname = "emc.knife"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name="builtin.knife")
        return{'FINISHED'}

class OffsetEdge(bpy.types.Operator):
    """Enter Edit Mode With the Offset Edge Loop Tool Enabled"""
    bl_label = "Offset Edge Loop"
    bl_idname = "emc.offsetedge"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name="builtin.offset_edge_loop_cut")
        return{'FINISHED'}

class Extrude(bpy.types.Operator):
    """Enter Edit Mode With the Extrude Tool Enabled"""
    bl_label = "Extrude"
    bl_idname = "emc.extrude"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name="builtin.extrude_region")
        return{'FINISHED'}

class Spin(bpy.types.Operator):
    """Enter Edit Mode With the Spin Tool Enabled"""
    bl_label = "Spin"
    bl_idname = "emc.spin"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name="builtin.spin")
        return{'FINISHED'}

class EdgeSlide(bpy.types.Operator):
    """Enter Edit Mode With the Edge Slide Tool Enabled"""
    bl_label = "Edge Slide"
    bl_idname = "emc.edgeslide"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name="builtin.edge_slide")
        return{'FINISHED'}

class LoopCut(bpy.types.Operator):
    """Enter Edit Mode With the Loop Cut Tool Enabled"""
    bl_label = "Loop Cut"
    bl_idname = "emc.loopcut"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name="builtin.loop_cut")
        return{'FINISHED'}

class KnifeProject(bpy.types.Operator):
    """Enter Edit Mode and Cut the Active Object using the Selected Curve"""
    bl_label = "Knife Project"
    bl_idname = "emc.knifeproject"
    bl_options = {'REGISTER', 'UNDO'}

    through: bpy.props.BoolProperty(
        name = "Cut Through", 
        description = "Cut through all faces, not just visible ones", 
        default = True,
    )
    
    def execute(self, context):
        try:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.knife_project(cut_through=self.through)
        except:
            self.report({"ERROR"}, "Select a Cut Object (Selection) Then the Surface Object (Active)")
        return{'FINISHED'}

class Weld(bpy.types.Operator):
    """Enter Edit Mode and Create a Vertex Weld Setup"""
    bl_label = "Weld"
    bl_idname = "emc.weld"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.scene.tool_settings.use_mesh_automerge = True
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'VERTEX'}
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
        bpy.ops.wm.tool_set_by_id(name="builtin.select", as_fallback=True, space_type='VIEW_3D')
        return{'FINISHED'}

class VertexM(bpy.types.Operator):
    """Switch to Edit Mode with Vertex Selection"""
    bl_label = "Vertex"
    bl_idname = "emc.vertex"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.object.mode_set_with_submode(mode='EDIT', mesh_select_mode={"VERT"})
        return{'FINISHED'}

class EdgeM(bpy.types.Operator):
    """Switch to Edit Mode with Edge Selection"""
    bl_label = "Edge"
    bl_idname = "emc.edge"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.object.mode_set_with_submode(mode='EDIT', mesh_select_mode={"EDGE"})
        return{'FINISHED'}

class FaceM(bpy.types.Operator):
    """Switch to Edit Mode with Face Selection"""
    bl_label = "Face"
    bl_idname = "emc.face"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.object.mode_set_with_submode(mode='EDIT', mesh_select_mode={"FACE"})
        return{'FINISHED'}

class MultiM(bpy.types.Operator):
    """Switch to Edit Mode with ALL Slection Modes Active"""
    bl_label = "Multi"
    bl_idname = "emc.multi"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (True, True, True)
        return{'FINISHED'}

class VertFaceM(bpy.types.Operator):
    """Switch to Edit Mode with Vertex and Face Modes Active"""
    bl_label = "Vertex Face"
    bl_idname = "emc.vertface"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (True, False, True)
        return{'FINISHED'}

class FillHoles(bpy.types.Operator):
    """Fill Holes in the Model"""
    bl_label = "Fill Holes"
    bl_idname = "emc.fillholes"
    bl_options = {'REGISTER', 'UNDO'}

    sides: bpy.props.IntProperty(
        name = "Sides", 
        description = "Number of sides in hole required to fill (zero fills all holes)", 
        default = 0,
        min = 0
    )
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.fill_holes(sides=self.sides)
        bpy.ops.mesh.select_all(action='DESELECT')
        return{'FINISHED'}

class Autosmooth(bpy.types.Operator):
    """Set Smoothing Based on Angle"""
    bl_label = "Auto Smooth Shading"
    bl_idname = "emc.autosmooth"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objs = bpy.context.selected_objects
        
        bpy.ops.object.shade_smooth()
        for e in objs:
            if e.type == 'MESH':
                e.data.use_auto_smooth = not e.data.use_auto_smooth
        return{'FINISHED'}

class MarkSharp(bpy.types.Operator):
    """Mark Sharp Edges by Angle"""
    bl_label = "Mark Sharp by Angle"
    bl_idname = "emc.anglesharp"
    bl_options = {'REGISTER', 'UNDO'}

    angle: bpy.props.FloatProperty(
        name = "Angle", 
        description = "Maximum angle between face normals that will be considered as smooth (unused if custom split normals data are available))", 
        default = 30,
        min = 0, max = 180,
        subtype = 'FACTOR',
    )

    smooth: bpy.props.BoolProperty(
        name = "Setup Autosmooth", 
        description = "Set Autosmooth Angle to 180d", 
        default = False,
    )

    seams: bpy.props.BoolProperty(
        name = "Mark Seams", 
        description = "Mark the Generated Sharp Edges as Seams", 
        default = False,
    )

    def execute(self, context):
        og_angle = bpy.context.object.data.auto_smooth_angle
        bpy.ops.object.vertex_group_add()
        bpy.context.scene.tool_settings.vertex_group_weight = 1
        bpy.ops.object.vertex_group_assign()

        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.ops.mesh.edges_select_sharp(sharpness=(self.angle * (math.pi/180)))
        bpy.ops.mesh.mark_sharp()

        if self.seams:
            bpy.ops.mesh.mark_seam(clear=False)
        else:
            pass

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.faces_shade_smooth()
        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)

        bpy.context.object.data.auto_smooth_angle = math.pi if self.smooth == True else og_angle
            
        bpy.context.object.data.use_auto_smooth = self.smooth

        # bpy.ops.object.mode_set(mode='OBJECT')
        # bpy.ops.object.shade_smooth()
        # bpy.ops.object.mode_set(mode='EDIT')
        return{'FINISHED'}

class FaceMapSharp(bpy.types.Operator):
    """Mark Sharp Edges on All Face Map Boarders"""
    bl_label = "Mark Sharp by Face Maps"
    bl_idname = "emc.facemapsharp"
    bl_options = {'REGISTER', 'UNDO'}

    smooth: bpy.props.BoolProperty(
        name = "Setup Autosmooth", 
        description = "Set Autosmooth Angle to 180d", 
        default = False,
    )

    seams: bpy.props.BoolProperty(
        name = "Mark Seams", 
        description = "Mark the Generated Sharp Edges as Seams", 
        default = False,
    )

    clear: bpy.props.BoolProperty(
        name = "Clear Previous", 
        description = "Clears the Previously Marked Sharp Edges", 
        default = False,
    )

    def execute(self, context):
        bpy.ops.object.vertex_group_add()
        bpy.context.scene.tool_settings.vertex_group_weight = 1
        bpy.ops.object.vertex_group_assign()

        if self.clear:
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.mark_sharp(clear=True)
        else:
            pass

        bpy.ops.mesh.select_all(action='DESELECT')

        for i in range(0, len(bpy.context.object.face_maps)):
            bpy.context.object.face_maps.active_index = i
            bpy.ops.object.face_map_select()
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.mark_sharp(clear=False)

            if self.seams:
                bpy.ops.mesh.mark_seam(clear=False)
            else:
                pass

        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)

        if self.smooth:
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.faces_shade_smooth()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.context.object.data.auto_smooth_angle = math.pi
            bpy.context.object.data.use_auto_smooth = True
        else:
            pass
        return{'FINISHED'}

class SmoothAngle(bpy.types.Operator):
    """Set Angle of Smoothing (Default = 30d)"""
    bl_label = "Auto Smooth Angle"
    bl_idname = "emc.smoothangle"
    bl_options = {'REGISTER', 'UNDO'}

    angle: bpy.props.FloatProperty(
        name = "Angle", 
        description = "Maximum angle between face normals that will be considered as smooth (unused if custom split normals data are available))", 
        default = 30,
        min = 0, max = 180,
        subtype = 'FACTOR',
    )

    def invoke(self, context, event):
        if len(bpy.context.selected_objects) == 1:
            if bpy.context.selected_objects[0].type == 'MESH':
                self.angle = 180/math.pi * bpy.context.object.data.auto_smooth_angle # rad to deg
        return {'FINISHED'}
    
    def execute(self, context):
        for e in bpy.context.selected_objects:
            if e.type == 'MESH':
                e.data.auto_smooth_angle = (self.angle * (math.pi/180)) #deg to ang
        return{'FINISHED'}

class Smooth(bpy.types.Operator):
    """Set Shading to Smooth"""
    bl_label = "Smooth Shading"
    bl_idname = "emc.smooth"
    
    def execute(self, context):
        if bpy.context.object.mode == 'EDIT':
            bpy.ops.mesh.mark_sharp(clear=True)
        else:
            objs = bpy.context.selected_objects
            for e in objs:
                if e.type == 'MESH':
                    e.data.use_auto_smooth = False
                bpy.ops.object.shade_smooth()
        return{'FINISHED'}     

class Flat(bpy.types.Operator):
    """Set Shading to Flat"""
    bl_label = "Flat Shading"
    bl_idname = "emc.flat"
    
    def execute(self, context):
        if bpy.context.object.mode == 'EDIT':
            bpy.ops.mesh.mark_sharp()
        else:
            bpy.ops.object.shade_flat()

            objs = bpy.context.selected_objects
            for e in objs:
                if e.type == 'MESH':
                    e.data.use_auto_smooth = False
        return{'FINISHED'}      

class EmcUV(bpy.types.Operator):
    """Enter Edit Mode and Activate the UV Menu"""
    bl_label = "UV Unwrapping"
    bl_idname = "emc.uv"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.call_menu(name="VIEW3D_MT_uv_map")
        # bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        # bpy.context.area.ui_type = 'UV'
        return{'FINISHED'}    

class SelHier(bpy.types.Operator):
    """Select all of the childern of the active object"""
    bl_label = "Select Hierarchy"
    bl_idname = "emc.selheir"
    
    def execute(self, context):
        myObj = bpy.context.active_object
        bpy.ops.object.select_grouped(type='CHILDREN_RECURSIVE')
        myObj.select_set(True)
        return{'FINISHED'} 

class SelSim(bpy.types.Operator):
    """Select Similar Types"""
    bl_label = "Select Similar"
    bl_idname = "emc.selsim"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.call_menu(name="VIEW3D_MT_edit_mesh_select_similar")
        return{'FINISHED'} 

class ExtrudeVert(bpy.types.Operator):
    """Extrude Vertex"""
    bl_label = "Extrude Vertex"
    bl_idname = "emc.extrudevert"
    bl_options = {'REGISTER', 'UNDO'}

    offset: bpy.props.FloatProperty(
        name = "Offset", 
        description = "Offset", 
        default = 0.5,
        min = 0, soft_max = 1
    )

    depth: bpy.props.FloatProperty(
        name = "Depth", 
        description = "Depth", 
        default = 0.5,
        min = 0
    )
    
    def execute(self, context):
        ob = bpy.context.object
        my_mesh = ob.data
        bm = bmesh.from_edit_mesh(my_mesh)

        bpy.ops.object.vertex_group_add()
        bpy.context.scene.tool_settings.vertex_group_weight = 1
        bpy.ops.object.vertex_group_assign()

        selected_verts = [vertex for vertex in bm.verts if vertex.select]
        
        for i in selected_verts:
            bpy.ops.mesh.select_all(action='DESELECT')
            i.select = True
            bpy.ops.mesh.bevel(offset_type='OFFSET', offset=self.offset, offset_pct=100, vertex_only=True, clamp_overlap=True, loop_slide=True)
            bpy.ops.mesh.inset(thickness=0.25, depth=self.depth)
            bpy.ops.mesh.merge(type='COLLAPSE')

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        return{'FINISHED'}

class PropReverse(bpy.types.Operator):
    """Flip Normals of all of the linked polygons of the selection"""
    bl_label = "Propagate Flip"
    bl_idname = "emc.propreverse"
    
    def execute(self, context):
        bpy.ops.mesh.select_linked()
        bpy.ops.mesh.flip_normals()
        return{'FINISHED'}

class SmoothFaces(bpy.types.Operator):
    """Subdivide and Smooth Selected Faces"""
    bl_label = "Smooth Faces"
    bl_idname = "emc.smoothfaces"
    bl_options = {'REGISTER', 'UNDO'}

    Cuts: bpy.props.IntProperty(
        name = "Cuts", 
        description = "Number of Cuts", 
        default = 2,
        min = 1, soft_max = 6
    )

    outer: bpy.props.BoolProperty(
        name = "Smooth Outer Edges", 
        description = "Include Non-Manifold Outer Edges in the Smoothing Process", 
        default = False,
    )

    customSmoothing: bpy.props.BoolProperty(
        name = "Custom Smoothing", 
        description = "Use the Smoothing Options Below", 
        default = False,
    )

    smoothing: bpy.props.FloatProperty(
        name = "Smoothing", 
        description = "Smoothing factor", 
        default = 0.5,
        soft_min = 0, soft_max = 1,
    )

    repeat: bpy.props.IntProperty(
        name = "Repeat", 
        description = "Number of times to smooth the mesh", 
        default = 10,
        min = 1, max = 100
    )

    cleanup: bpy.props.BoolProperty(
        name = "Cleanup", 
        description = "Cleanup Neighboring Faces. In Some Cases, Having this Option Enabled Will Delete Some Details", 
        default = True,
    )

    slow: bpy.props.BoolProperty(
        name = "Match Modifier (Slow)", 
        description = "Subdivisions match the modifier subdivisions, but this option is much slower", 
        default = False,
    )

    def execute(self, context):
        ob = bpy.context.object
        my_mesh = ob.data

        bm = bmesh.from_edit_mesh(my_mesh)

        bpy.context.tool_settings.mesh_select_mode = (False, False, True)

        bpy.ops.object.vertex_group_add()
        bpy.context.scene.tool_settings.vertex_group_weight = 1
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.face_map_add()
        bpy.ops.object.face_map_assign()

        selected_edges = [edge for edge in bm.edges if edge.select]
        init_verts = [vertex for vertex in bm.verts if vertex.select]
        poke_verts = []

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bmesh.ops.subdivide_edges(bm, edges=selected_edges, cuts=1, use_grid_fill=False)
        bmesh.update_edit_mesh(my_mesh)

        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.object.vertex_group_remove_from()

        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_add()
        bpy.ops.object.vertex_group_assign()
        for i in bm.verts:
            if i not in init_verts:
                poke_verts.append(i)
        bpy.ops.mesh.poke()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.object.vertex_groups.active_index = len(bpy.context.object.vertex_groups)-2
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bpy.context.tool_settings.mesh_select_mode = (False, True, False)
        bpy.ops.mesh.dissolve_mode(use_verts=False, use_face_split=False, use_boundary_tear=False)
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        bpy.context.object.vertex_groups.active_index = len(bpy.context.object.vertex_groups)-1
        bpy.ops.object.vertex_group_select()

        if self.Cuts == 1:
            pass
        else:
            if self.slow:
                for i in range(1, self.Cuts):
                    bpy.ops.mesh.subdivide(number_cuts=1)
            else:
                bpy.ops.mesh.subdivide(number_cuts=self.Cuts-1)

        if self.cleanup:
            try:
                # bpy.ops.mesh.select_similar(type='COPLANAR', threshold=0.01)
                bpy.ops.object.face_map_deselect()
                bpy.ops.mesh.dissolve_mode(use_verts=False, use_face_split=False, use_boundary_tear=True)
            except:
                pass
        
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.face_map_select()

        if self.outer:
            bpy.ops.mesh.select_less()
        else:
            bpy.ops.mesh.region_to_loop()
            bpy.ops.object.vertex_group_remove_from()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_select()
            
        try:
            bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        except:
            pass
        
        if self.customSmoothing:
            bpy.ops.mesh.vertices_smooth(factor=self.smoothing, repeat=self.repeat, wait_for_input=False)
        else:
            if self.Cuts == 1:
                bpy.ops.mesh.vertices_smooth(factor=1, repeat=1, wait_for_input=False)
            elif self.Cuts > 1:
                if self.slow:
                    bpy.ops.mesh.vertices_smooth(factor=1, repeat=(5 ** (self.Cuts-1)), wait_for_input=False)
                else:
                    bpy.ops.mesh.vertices_smooth(factor=1, repeat=((self.Cuts*self.Cuts)*1.25), wait_for_input=False)

        bpy.ops.object.vertex_group_select()

        if not self.outer:
            bpy.ops.mesh.select_more()
            if self.Cuts == 1:
                bpy.ops.object.face_map_select()

        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        bpy.ops.object.face_map_remove()
        return{'FINISHED'}

class EmcMirror(bpy.types.Operator):
    """Add a Mirror Modifier with Bisect Enabled"""
    bl_label = "Add Mirror Modifier"
    bl_idname = "emc.mirror"

    existing: bpy.props.BoolProperty(
        default = True
    )

    def add_mirror(self, name):
        bpy.ops.object.modifier_add(type='MIRROR')
        if self.existing:
            id_name = name
        else:
            id_name = bpy.context.object.modifiers[-1].name
        bpy.context.object.modifiers[len(bpy.context.object.modifiers)-1].name = id_name
        bpy.context.object.modifiers[id_name].use_bisect_axis[0] = True
        bpy.context.object.modifiers[id_name].use_bisect_axis[1] = True
        bpy.context.object.modifiers[id_name].use_bisect_axis[2] = True
        bpy.context.object.modifiers[id_name].use_clip = True

    def execute(self, context):
        name = "EMC Mirror"
        objs = bpy.context.selected_objects
        active = bpy.context.active_object

        if self.existing:
            if name not in bpy.context.object.modifiers:
                EmcMirror.add_mirror(self, name)
        else:
            EmcMirror.add_mirror(self, "None")
        
        self.report({"INFO"}, "Selected object can be used as origin")

        if len(bpy.context.selected_objects) == 2:
            objs.remove(active)
            if self.existing:
                bpy.context.object.modifiers[name].mirror_object = objs[0]
            else:
                bpy.context.object.modifiers[-1].mirror_object = objs[0]
            self.report({"INFO"}, "Selected object was set as origin")
        elif len(bpy.context.selected_objects) > 2:
            self.report({"WARNING"}, "Must Select 1 or 2 objects, depending on the intended usecase")
        return{'FINISHED'}

class ProjectCurve(bpy.types.Operator):
    """Project Curve on mesh and create a new Edge (Mesh) from the projection"""
    bl_label = "Project Curve"
    bl_idname = "emc.projcurve"

    def execute(self, context):
        selection_names = bpy.context.selected_objects
        og = bpy.context.active_object

        try:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_add()
            bpy.context.scene.tool_settings.vertex_group_weight = 1
            bpy.ops.object.vertex_group_assign()
            bpy.ops.mesh.knife_project(cut_through=True)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.loop_multi_select(ring=False)
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.loop_multi_select(ring=False)
            bpy.ops.mesh.dissolve_edges()
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            for obj in selection_names:
                obj.select_set(False)
        except:
            self.report({"ERROR"}, "Select Curve Object (Selection) Then the Surface Object (Active)")
            bpy.ops.ed.undo()

        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.convert(target='CURVE')
        bpy.context.object.name = og.name + ".Projected Curve"
        return{'FINISHED'}

class Separate(bpy.types.Operator):
    """Separate Loose Parts"""
    bl_label = "Separate"
    bl_idname = "emc.separate"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.separate(type='LOOSE')
        bpy.ops.object.mode_set(mode='OBJECT')
        return{'FINISHED'}

class EmcTris(bpy.types.Operator):
    """Tries to Convert Triangles to 4-Sided Polygons"""
    bl_label = "Tris to Quads"
    bl_idname = "emc.tristoquads"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.tris_convert_to_quads(face_threshold=3.14159, shape_threshold=3.14159)
        bpy.ops.object.mode_set(mode='OBJECT')
        return{'FINISHED'}

class EmcCage(bpy.types.Operator):
    """Create a Cage Object for Baking"""
    bl_label = "Baking Cage"
    bl_idname = "emc.cage"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        color = (0.0982859, 0.952395, 1, 0.75)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        name = bpy.context.object.name
        bpy.ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked":True, "mode":'TRANSLATION'})
        bpy.context.object.name = name + ".CAGE"
        bpy.ops.object.vertex_group_add()
        bpy.ops.object.editmode_toggle()
        bpy.context.object.vertex_groups[-1].name = 'Cage THICC-ness'
        bpy.context.scene.tool_settings.vertex_group_weight = 0.5
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers["Displace"].vertex_group = bpy.context.object.vertex_groups[-1].name
        bpy.context.object.modifiers["Displace"].show_in_editmode = True
        bpy.context.object.modifiers["Displace"].show_on_cage = True
        bpy.ops.object.editmode_toggle()
        bpy.context.object.color = color
        bpy.context.object.show_wire = True
        bpy.context.space_data.shading.color_type = 'OBJECT'
        bpy.context.space_data.overlay.weight_paint_mode_opacity = 0.25
        return{'FINISHED'}

class EmcHoleLoop(bpy.types.Operator):
    """Create a Hole and a Support Loop Around a Selection"""
    bl_label = "Hole Edge Loop"
    bl_idname = "emc.hole"
    bl_options = {'REGISTER', 'UNDO'}

    slide: bpy.props.FloatProperty(
        name = "Slide", 
        description = "Slide Generated Loop", 
        default = 0.1,
        min = 0.001
    )

    loopslide: bpy.props.BoolProperty(
        name = "Loop Slide", 
        description = "Loop Slide", 
        default = False,
    )

    clamp: bpy.props.BoolProperty(
        name = "Clamp", 
        description = "Clamp", 
        default = True,
    )

    def execute(self, context):
        try:
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.ops.mesh.edge_face_add()
            bpy.ops.mesh.bevel(offset=self.slide, offset_pct=self.slide, segments=2, profile=1, vertex_only=False, loop_slide=self.loopslide, clamp_overlap=self.clamp)
            bpy.context.tool_settings.mesh_select_mode = (False, False, True)
            bpy.ops.mesh.select_less(use_face_step=False)
            bpy.ops.mesh.delete(type='FACE')
        except:
            self.report({"ERROR"}, "Invalid Selection")
        return{'FINISHED'}

class LocalOr(bpy.types.Operator):
    """Enable Local Oreontation"""
    bl_label = "Local"
    bl_idname = "emc.local"

    def execute(self, context):
        bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
        return{'FINISHED'}

class GlobalOr(bpy.types.Operator):
    """Enable Global Oreontation"""
    bl_label = "Global"
    bl_idname = "emc.global"

    def execute(self, context):
        bpy.context.scene.transform_orientation_slots[0].type = 'GLOBAL'
        return{'FINISHED'}

class NormalOr(bpy.types.Operator):
    """Enable Normal Oreontation"""
    bl_label = "Normal"
    bl_idname = "emc.normal"

    def execute(self, context):
        bpy.context.scene.transform_orientation_slots[0].type = 'NORMAL'
        return{'FINISHED'}

class GimbalOr(bpy.types.Operator):
    """Enable Gimbal Oreontation"""
    bl_label = "Gimbal"
    bl_idname = "emc.gimbal"

    def execute(self, context):
        bpy.context.scene.transform_orientation_slots[0].type = 'GIMBAL'
        return{'FINISHED'}

class CheckerLoop(bpy.types.Operator):
    """Select Every n-th Edge loop of the Selected Edge"""
    bl_label = "Checker Loop"
    bl_idname = "emc.checkerloop"
    bl_options = {'REGISTER', 'UNDO'}

    deselected: bpy.props.IntProperty(
        name = "Deselected", 
        description = "Number of Deselected Loops in the Sequence", 
        default = 1,
        min = 1,
    )

    selected: bpy.props.IntProperty(
        name = "Selected", 
        description = "Number of Selected Loops in the Sequence", 
        default = 1,
        min = 1,
    )

    offset: bpy.props.IntProperty(
        name = "Offset", 
        description = "Offset From the Starting Point", 
        default = 1,
        min = 0,
    )

    def execute(self, context):
        bpy.ops.mesh.loop_multi_select(ring=True)
        bpy.ops.mesh.select_nth(skip=self.deselected, nth=self.selected, offset=self.offset)
        bpy.ops.mesh.loop_multi_select(ring=False)
        return{'FINISHED'}

class EMCpatch(bpy.types.Operator):
    """Patch a hole with an even number of vertices (ORIGINAL EDGES MUST HAVE FACES)"""
    bl_label = "Patch Fill"
    bl_idname = "emc.patchfill"
    bl_options = {'REGISTER', 'UNDO', 'UNDO_GROUPED'}

    flip: bpy.props.BoolProperty(
        name = "Flip Normals", 
        description = "Flip Normals if Inverted", 
        default = True,
    )

    rotate: bpy.props.IntProperty(
        name = "Rotate", 
        description = "Rotate Pattern", 
        default = 0,
    )

    relax: bpy.props.FloatProperty(
        name = "Relax", 
        description = "Relax vertices patch", 
        default = 1,
        min = 0, max = 1,
        subtype = 'FACTOR',
    )

    snap: bpy.props.FloatProperty(
        name = "Snap to", 
        description = "Snap to generated patch or original edges", 
        default = 0,
        min = 0, max = 1,
        subtype = 'FACTOR',
    )

    priority: bpy.props.EnumProperty(
        name="Priority Order",
        items=(("3 4 5", "Diamond, Grid, Star", "Priority Order"),
               ("4 3 5", "Grid, Diamond, Star", "Priority Order"),
               ("5 3 4", "Star, Diamond, Grid", "Priority Order"),
               ("3 5 4", "Diamond, Star, Grid", "Priority Order"),
               ("4 5 3", "Grid, Star, Diamond", "Priority Order"),
               ("5 4 3", "Star, Grid, Diamond", "Priority Order")),
        description="Determines which pattern takes priority when the patch is created",
        default='4 3 5'
        )

    def execute(self, context):
        ob = bpy.context.object
        my_mesh = ob.data
        bm = bmesh.from_edit_mesh(my_mesh)

        og_merge = bpy.context.scene.tool_settings.use_mesh_automerge

        bpy.context.scene.tool_settings.use_mesh_automerge = False

        selected_verts = [vertex for vertex in bm.verts if vertex.select]

        a_list = str(self.priority).split()
        map_object = map(int, a_list)

        pri_order = list(map_object)

        if(len(selected_verts)%pri_order[0]==0):
            if len(selected_verts) == pri_order[0]:
                bpy.ops.mesh.edge_face_add()
                return{'FINISHED'}
            else:
                sides = pri_order[0]
        elif(len(selected_verts)%pri_order[1]==0):
            if len(selected_verts) == pri_order[1]:
                bpy.ops.mesh.edge_face_add()
                return{'FINISHED'}
            else:
                sides = pri_order[1]
        elif(len(selected_verts)%pri_order[2]==0):
            if len(selected_verts) == pri_order[2]:
                bpy.ops.mesh.edge_face_add()
                return{'FINISHED'}
            else:
                sides = pri_order[2]
        else:
            self.report({"ERROR"}, "Selected vertex count must not be a prime number, or a double of one")
            if(len(selected_verts)%2==0):
                self.report({"WARNING"}, "Try Grid Fill instead")
            return{'CANCELLED'}

        try:
            bpy.ops.object.vertex_group_add()
            bpy.context.scene.tool_settings.vertex_group_weight = 1
            bpy.context.object.vertex_groups[len(bpy.context.object.vertex_groups)-1].name = "TEMP1"
            bpy.ops.object.vertex_group_assign()

            bpy.ops.mesh.split()
            bpy.ops.object.vertex_group_remove_from()
            

            bpy.ops.object.vertex_group_add()
            bpy.context.object.vertex_groups[len(bpy.context.object.vertex_groups)-1].name = "TEMP2"
            bpy.ops.object.vertex_group_assign()

            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_nth(nth=((len(selected_verts)-sides)/sides))
            bpy.ops.mesh.dissolve_verts()
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.edge_face_add()
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            if self.flip:
                bpy.ops.mesh.flip_normals()
            bpy.ops.transform.rotate(value=(360/len(selected_verts))*(math.pi/180)*self.rotate, orient_axis='Z', orient_type='NORMAL')

            bpy.ops.emc.smoothfaces(Cuts=1, customSmoothing=True, smoothing=0, repeat=1, cleanup=False, slow=False)
            bpy.ops.mesh.ext_deselect_boundary()

            if len(selected_verts) == sides*2:
                pass
            else:
                if int_version > 283:
                    bpy.ops.mesh.bevel(offset_type='WIDTH', offset=1, offset_pct=0, segments=((len(selected_verts)-sides)/sides)-1, affect='EDGES', clamp_overlap=True, loop_slide=True)
                else:
                    bpy.ops.mesh.bevel(offset_type='WIDTH', offset=1, offset_pct=0, segments=((len(selected_verts)-sides)/sides)-1, vertex_only=False, clamp_overlap=True, loop_slide=True)

            bpy.ops.mesh.select_linked(delimit=set())
            
            bpy.ops.mesh.region_to_loop()
            bpy.context.object.vertex_groups.active_index = len(bpy.context.object.vertex_groups)-2
            bpy.ops.object.vertex_group_select()

            bpy.ops.mesh.bridge_edge_loops(use_merge=True, merge_factor=self.snap)

            bpy.ops.object.vertex_group_select()
            bpy.context.object.vertex_groups.active_index = len(bpy.context.object.vertex_groups)-1
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.vertices_smooth(factor=self.relax, repeat=100)
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.mesh.select_more()
            bpy.context.scene.tool_settings.use_mesh_automerge = og_merge
        except:
            self.report({"WARNING"}, "Something went wrong :(")
            bpy.ops.ed.undo()
        return{'FINISHED'}

class EmcRepeat(bpy.types.Operator):
    """Repeat Scripted Operation n Amount of Times"""
    bl_label = "Repeat"
    bl_idname = "emc.repeat"
    bl_options = {'REGISTER', 'UNDO'}

    repeat: bpy.props.IntProperty(
        name = "Repeat", 
        description = "Number of Repetitions", 
        default = 1,
        min = 0, soft_max = 100,
    )

    operation: bpy.props.StringProperty(
        name = "Operation", 
        description = "Repeat this Operation", 
        # default = "bpy.ops.screen.repeat_last()"
    )

    script: bpy.props.BoolProperty(
        name = "Script", 
        description = "Run a Script Instead of an Operation", 
        default = False
    )

    def execute(self, context):
        try:
            if self.script == True:
                script = bpy.data.texts[self.operation]
                for i in range(0, self.repeat):
                    exec(script.as_string())
            else:
                for i in range(0, self.repeat):
                    exec(self.operation)
        except:
            self.report({"WARNING"}, "Invalid Code")
        return{'FINISHED'}

class Reset(bpy.types.Operator):
    """Reset Snapping and Tools to Factory Default"""
    bl_label = "Reset"
    bl_idname = "emc.reset"
    bl_options = {'REGISTER', 'UNDO'}

    selection: bpy.props.BoolProperty(
        name = "Box Selection", 
        description = "Toggle Between Box Selection and Tweak", 
        default = True,
    )

    def execute(self, context):
        try:
            bpy.context.scene.tool_settings.workspace_tool_type = 'DEFAULT'
        except:
            pass
        bpy.context.scene.tool_settings.snap_elements = {'INCREMENT'}
        bpy.context.scene.tool_settings.use_snap = False
        bpy.context.scene.tool_settings.use_snap_rotate = False
        bpy.context.scene.tool_settings.use_snap_scale = False
        bpy.context.scene.tool_settings.use_snap_grid_absolute = False
        if self.selection:
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        else:
            bpy.ops.wm.tool_set_by_id(name="builtin.select")
        bpy.context.scene.tool_settings.use_mesh_automerge = True
        bpy.context.scene.transform_orientation_slots[0].type = 'GLOBAL'
        bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
        bpy.context.object.data.use_mirror_x = False
        bpy.context.object.data.use_mirror_y = False
        bpy.context.object.data.use_mirror_z = False
        bpy.context.object.data.use_mirror_topology = False
        bpy.context.scene.tool_settings.use_mesh_automerge_and_split = False
        bpy.context.scene.tool_settings.double_threshold = 0.001
        bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'
        bpy.context.scene.tool_settings.use_proportional_projected = False
        bpy.context.scene.tool_settings.use_proportional_connected = False
        return{'FINISHED'}

class FaceMapsMaterial(bpy.types.Operator):
    """Creates Face Maps of Each Material and Assigns the Respective Faces to the Face Maps"""
    bl_label = "Face Maps from Materials"
    bl_idname = "emc.facemapmaterial"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        orig_mode = bpy.context.object.mode
        orig_len = len(bpy.context.object.face_maps)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

        bpy.ops.object.vertex_group_add()
        bpy.context.scene.tool_settings.vertex_group_weight = 1
        bpy.ops.object.vertex_group_assign()

        bpy.ops.mesh.select_all(action='DESELECT')

        for i in range(0, len(bpy.context.object.material_slots)):
            bpy.ops.object.face_map_add()
            bpy.context.object.active_material_index = i
            bpy.ops.object.material_slot_select()
            bpy.ops.object.face_map_assign()
            bpy.context.object.face_maps[i+orig_len].name = bpy.context.object.active_material.name
            bpy.ops.mesh.select_all(action='DESELECT')
            
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            
        bpy.ops.object.mode_set(mode=orig_mode)
        return{'FINISHED'}

class EMCsplit(bpy.types.Operator):
    """Split Faces"""
    bl_label = "Split"
    bl_idname = "emc.split"
    bl_options = {'REGISTER', 'UNDO'}

    methods: bpy.props.EnumProperty(
        name="Method",
        items=(("sel", "Selection", "Split off selected geometry from connected unselected geometry"),
               ("edge", "Faces by Edges", "Split selected edges so that each neighbor face gets its own copy"),
               ("vert", "Faces & Edges by Vertices", "Split selected edges so that each neighbor face gets its own copy")),
        description="Method used to split faces",
        default='sel'
        )
 
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "methods")

    def execute(self, context):
        if self.methods == "sel":
            bpy.ops.mesh.split()
        elif self.methods == "vert":
            bpy.ops.mesh.edge_split(type='VERT')
        else:
            bpy.ops.mesh.edge_split(type='EDGE')
        return{'FINISHED'}

class EMCbool(bpy.types.Operator):
    """Boolean Operations"""
    bl_label = "Boolean"
    bl_idname = "emc.bool"
    bl_options = {'REGISTER', 'UNDO'}

    operation: bpy.props.EnumProperty(
        name="Method",
        items=(("diff", "Difference", "Erase geometry"),
               ("uni", "Union", "Add geometry"),
               ("inter", "Intersection", "Only keep geometry inside of the intersection"),
               ("slice", "Slice", "Cut across the Boolean Object")),
        description="Operation Used",
        default='diff'
        )

    old: bpy.props.BoolProperty(
        name = "Individual Objects", 
        description = "Use the old, original method of using one modifier per object", 
        default = False
    )
    
    apply: bpy.props.BoolProperty(
        default = False
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "operation")
        if int_version > 290:
            row = layout.row(align=True)
            row.prop(self, "old")
        row = layout.row(align=True)
        row.prop(self, "apply")

    def execute(self, context):

        selected = bpy.context.selected_objects
        active = bpy.context.view_layer.objects.active
        try:
            selected.remove(active)
        except:
            pass

        if len(selected) <= 0:
            self.report({"WARNING"}, "Select at least 2 objects")
            return{'CANCELLED'}

        if int_version > 284 and self.operation != "slice" and self.old == False:
            check_col_viz = False

            bpy.ops.object.select_all(action='DESELECT')
            active.select_set(True)
            bpy.context.view_layer.objects.active = active
            bpy.ops.object.modifier_add(type='BOOLEAN')
            bpy.context.object.modifiers[-1].operand_type = 'COLLECTION'
            bpy.context.object.modifiers[-1].show_expanded = False

            for i in selected:
                move_to_col(i, "EMC Extras", True, True)
                
            current_col = bpy.context.view_layer.active_layer_collection
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['EMC Extras']

            if bpy.context.layer_collection.exclude == True:
                bpy.context.layer_collection.exclude = False
                check_col_viz = True

            bpy.data.collections.new('EMC Bool')

            colnameget = ''
            for i in bpy.data.collections:
                if i.name.split('.')[0] == 'EMC Bool':
                    colnameget = i.name

            bpy.context.collection.children.link(bpy.data.collections[colnameget])

            for i in selected:
                i.users_collection[0].objects.unlink(i)
                bpy.data.collections[colnameget].objects.link(i)

                i.display_type = 'BOUNDS'
                i.parent = active
                i.matrix_parent_inverse = active.matrix_world.inverted()

            bpy.context.object.modifiers[-1].collection = bpy.data.collections[colnameget]

            if self.operation == "diff":
                bpy.context.object.modifiers[-1].operation = 'DIFFERENCE'
                bpy.data.collections[colnameget].color_tag = 'COLOR_01'
            elif self.operation == "uni":
                bpy.context.object.modifiers[-1].operation = 'UNION'
                bpy.data.collections[colnameget].color_tag = 'COLOR_04'
            else:
                bpy.context.object.modifiers[-1].operation = 'INTERSECT'
                bpy.data.collections[colnameget].color_tag = 'COLOR_05'

            if check_col_viz:
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['EMC Extras']
                bpy.context.layer_collection.exclude = True
            
            bpy.context.view_layer.active_layer_collection = current_col

        else:
            for i in selected:
                bpy.ops.object.select_all(action='DESELECT')
                active.select_set(True)
                bpy.context.view_layer.objects.active = active
                bpy.ops.object.modifier_add(type='BOOLEAN')
                bpy.context.object.modifiers[-1].show_expanded = False
                bpy.context.object.modifiers[-1].object = i
                i.display_type = 'BOUNDS'
                i.parent = active
                i.matrix_parent_inverse = active.matrix_world.inverted()
                try:
                    i.Multi_Bool_Object = active
                except:
                    pass

                if self.operation == "diff":
                    bpy.context.object.modifiers[-1].operation = 'DIFFERENCE'
                elif self.operation == "uni":
                    bpy.context.object.modifiers[-1].operation = 'UNION'
                elif self.operation == "inter":
                    bpy.context.object.modifiers[-1].operation = 'INTERSECT'
                else:
                    bpy.context.object.modifiers[-1].operation = 'DIFFERENCE'
                    bpy.ops.object.duplicate_move_linked()
                    bpy.context.object.modifiers[-1].operation = 'INTERSECT'
                    
                    bpy.context.active_object.parent = active
                    bpy.ops.object.location_clear(clear_delta=False)
                    bpy.ops.object.rotation_clear(clear_delta=False)
                    bpy.ops.object.scale_clear(clear_delta=False)

                    if self.apply:
                        if int_version > 283:
                            bpy.ops.object.modifier_apply(modifier=bpy.context.object.modifiers[-1].name)
                        else:
                            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=bpy.context.object.modifiers[-1].name)
                
                active.select_set(True)
                i.select_set(True)
                bpy.context.view_layer.objects.active = active
                move_to_col(i, "EMC Extras", True, True)

        if self.apply:
            if int_version > 283:
                bpy.ops.object.modifier_apply(modifier=bpy.context.object.modifiers[-1].name)
            else:
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier=bpy.context.object.modifiers[-1].name)
        return{'FINISHED'}

class addCylinder(bpy.types.Operator):
    bl_label = "Add Cylinder"
    bl_idname = "emc.cylinder"
    bl_description = "Create a Cylinder Modifier Parametric Primitive"
    bl_options = {'REGISTER', 'UNDO'}

    vertices: bpy.props.IntProperty(
        name = "Vertices",
        description = "Vertices",
        default = 32,
        min = 3
    )

    radius: bpy.props.FloatProperty(
        name = "Radius", 
        description = "Radius", 
        default = 1.0,
        min = 0.001
    )

    depth: bpy.props.FloatProperty(
        name = "Depth",
        description = "Depth",
        default = 2.0,
        min = 0.001
        )

    top: bpy.props.BoolProperty(
        name = "Ngon Cap",
        description = "The Style of the Caps",
        default = True,
    )

    topSub: bpy.props.IntProperty(
        name = "Cap Subdivision",
        description = "The Subdivision Level of the triangle Fan of the Caps",
        default = 1,
        min = 1
    )

    smooth: bpy.props.BoolProperty(
        name = "Smooth Shading",
        description = "Use Smooth Shading",
        default = True,
    )

    apply: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Create Primitive Non-Destructively if Disabled",
        default = False,
    )
      
    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=True)
        bpy.ops.mesh.merge(type='CENTER')
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers[0].name = "Radius | Cap Subdiv"
        bpy.context.object.modifiers["Radius | Cap Subdiv"].axis = 'X'
        bpy.context.object.modifiers["Radius | Cap Subdiv"].angle = 0
        bpy.context.object.modifiers["Radius | Cap Subdiv"].screw_offset = self.radius
        bpy.context.object.modifiers["Radius | Cap Subdiv"].steps = self.topSub
        bpy.context.object.modifiers["Radius | Cap Subdiv"].render_steps = self.topSub

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers[1].name = "Vertices"
        bpy.context.object.modifiers["Vertices"].use_normal_calculate = True
        bpy.context.object.modifiers["Vertices"].use_merge_vertices = True
        bpy.context.object.modifiers["Vertices"].render_steps = self.vertices
        bpy.context.object.modifiers["Vertices"].steps = self.vertices
        bpy.context.object.modifiers["Vertices"].use_smooth_shade = self.smooth

        bpy.ops.emc.autosmooth()
        bpy.context.object.data.auto_smooth_angle = 1.309

        if self.top:
            bpy.ops.object.modifier_add(type='DECIMATE')
            bpy.context.object.modifiers[2].name = "Ngon Cap"
            bpy.context.object.modifiers["Ngon Cap"].decimate_type = 'DISSOLVE'
            bpy.context.object.modifiers["Ngon Cap"].angle_limit = 0.0174533

            create_prop("Ngon Cap", self.top, 'Ngon Cap', True, True, True, True, True, 0, 1, 0, 1)
            create_driver('Ngon Cap', 'show_viewport', 'var', '["Ngon Cap"]')
            create_driver('Ngon Cap', 'show_render', 'var', 'modifiers["Ngon Cap"].show_viewport')

        else:
            pass
        
        bpy.ops.object.modifier_add(type='SOLIDIFY')
        if self.top:
            bpy.context.object.modifiers[3].name = "Depth"
        else:
            bpy.context.object.modifiers[2].name = "Depth"
        bpy.context.object.modifiers["Depth"].offset = 0
        bpy.context.object.modifiers["Depth"].thickness = self.depth

        # --------------

        create_prop("Vertices", self.vertices, 'Vertices', True, False, True, True, True, 3, 96*2, 3, 96*2)
        create_driver('Vertices', 'steps', 'var', '["Vertices"]')
        create_driver('Vertices', 'render_steps', 'var', 'modifiers["Vertices"].steps')

        # --------------

        create_prop("Radius", self.radius, 'Radius', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('Radius | Cap Subdiv', 'screw_offset', 'var', '["Radius"]')

        # --------------

        create_prop("Depth", self.depth, 'Depth', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('Depth', 'thickness', 'var', '["Depth"]')

        # --------------

        create_prop("Cap Subdivisions", self.topSub, 'Number of rings on the caps', True, False, True, True, True, 1, 64, 1, 64)
        create_driver('Radius | Cap Subdiv', 'steps', 'var', '["Cap Subdivisions"]')
        create_driver('Radius | Cap Subdiv', 'render_steps', 'var', 'modifiers["Radius | Cap Subdiv"].steps')

        # --------------

        create_prop("Smooth Shading", self.smooth, 'Smooth Shading', True, True, True, True, True, 0, 1, 0, 1)
        create_driver('Vertices', 'use_smooth_shade', 'var', '["Smooth Shading"]')

        # --------------

        for i in bpy.context.active_object.modifiers:
            i.show_expanded = False

        if self.apply:
            og = bpy.context.selected_objects[0]

            bpy.ops.mesh.primitive_cylinder_add(vertices=self.vertices, radius=self.radius, depth=self.depth, end_fill_type='TRIFAN')
            bpy.ops.object.editmode_toggle()
            og_mode = bpy.context.tool_settings.mesh_select_mode[:]
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_face_by_sides(number=4, type='EQUAL')
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.subdivide(number_cuts=self.vertices-1)
            bpy.ops.object.editmode_toggle()
            new = bpy.context.selected_objects[0]

            bpy.ops.object.select_all(action='DESELECT')
            og.select_set(True)
            bpy.context.view_layer.objects.active = og

            bpy.ops.object.modifier_add(type='DATA_TRANSFER')
            bpy.context.object.modifiers["DataTransfer"].object = new
            bpy.context.object.modifiers["DataTransfer"].use_loop_data = True
            bpy.context.object.modifiers["DataTransfer"].data_types_loops = {'UV'}

            bpy.ops.object.convert(target='MESH')

            bpy.ops.object.select_all(action='DESELECT')
            new.select_set(True)
            bpy.ops.object.delete()

            og.select_set(True)
            bpy.context.view_layer.objects.active = og

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.edges_select_sharp(sharpness=1.309)
            bpy.ops.transform.edge_crease(value=1)
            bpy.ops.transform.edge_bevelweight(value=1)
            bpy.ops.uv.seams_from_islands()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.context.tool_settings.mesh_select_mode = og_mode
            bpy.ops.object.editmode_toggle()

            del bpy.context.active_object['Depth']
            del bpy.context.active_object['Cap Subdivisions']
            del bpy.context.active_object['Vertices']
            del bpy.context.active_object['Radius']
            del bpy.context.active_object['Smooth Shading']
            try:
                del bpy.context.active_object['Ngon Cap']
            except:
                pass
            delete_drivers()

        bpy.context.object.name = "EMC Cylinder"
        bpy.context.object.data.name = "EMC Cylinder"
        return{'FINISHED'}

class addPlane(bpy.types.Operator):
    bl_label = "Add Plane"
    bl_idname = "emc.plane"
    bl_description = "Create a Plane Modifier Parametric Primitive"
    bl_options = {'REGISTER', 'UNDO'}

    x_size: bpy.props.FloatProperty(
        name = "X Scale", 
        description = "X Axis Scale", 
        default = 2.0,
        min = 0.001
    )

    y_size: bpy.props.FloatProperty(
        name = "Y Scale", 
        description = "Y Axis Scale", 
        default = 2.0,
        min = 0.001
    )

    x_subdiv: bpy.props.IntProperty(
        name = "X Subdivision",
        description = "The Subdivision Level on X",
        default = 1,
        min = 1
    )

    y_subdiv: bpy.props.IntProperty(
        name = "Y Subdivision",
        description = "The Subdivision Level on Y",
        default = 1,
        min = 1
    )

    apply: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Create Primitive Non-Destructively if Disabled",
        default = False,
    )
      
    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=True)
        bpy.ops.mesh.merge(type='CENTER')
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers[0].name = "X Scale | Subdivision"
        bpy.context.object.modifiers["X Scale | Subdivision"].axis = 'X'
        bpy.context.object.modifiers["X Scale | Subdivision"].angle = 0
        bpy.context.object.modifiers["X Scale | Subdivision"].screw_offset = self.x_size
        bpy.context.object.modifiers["X Scale | Subdivision"].steps = self.x_subdiv
        bpy.context.object.modifiers["X Scale | Subdivision"].render_steps = self.x_subdiv

        create_prop("X Scale", self.x_size, 'X axis scale', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('X Scale | Subdivision', 'screw_offset', 'var', '["X Scale"]')

        create_prop("X Subdivisions", self.x_subdiv, 'The Subdivision Level on X', True, True, True, True, True, 1, 96*2, 1, 96)
        create_driver('X Scale | Subdivision', 'steps', 'var', '["X Subdivisions"]')
        create_driver('X Scale | Subdivision', 'render_steps', 'var', 'modifiers["X Scale | Subdivision"].steps')

        # --------------
        
        bpy.ops.object.modifier_copy(modifier="X Scale | Subdivision")
        bpy.context.object.modifiers[1].name = "Y Scale | Subdivision"
        bpy.context.object.modifiers["Y Scale | Subdivision"].axis = 'Y'
        bpy.context.object.modifiers["Y Scale | Subdivision"].screw_offset = self.y_size
        bpy.context.object.modifiers["Y Scale | Subdivision"].steps = self.y_subdiv
        bpy.context.object.modifiers["Y Scale | Subdivision"].render_steps = self.y_subdiv
        bpy.context.object.modifiers["Y Scale | Subdivision"].use_normal_calculate = True

        create_prop("Y Scale", self.y_size, 'Y axis scale', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('Y Scale | Subdivision', 'screw_offset', 'var', '["Y Scale"]')

        create_prop("Y Subdivisions", self.y_subdiv, 'The Subdivision Level on Y', True, True, True, True, True, 1, 96*2, 1, 96)
        create_driver('Y Scale | Subdivision', 'steps', 'var', '["Y Subdivisions"]')
        create_driver('Y Scale | Subdivision', 'render_steps', 'var', 'modifiers["Y Scale | Subdivision"].steps')

        # --------------
        
        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers[2].name = "X Loc Correction"
        bpy.context.object.modifiers["X Loc Correction"].direction = 'X'
        bpy.context.object.modifiers["X Loc Correction"].show_in_editmode = True
        
        create_driver('X Loc Correction', 'strength', '-var', 'modifiers["X Scale | Subdivision"].screw_offset')

        # --------------

        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers[3].name = "Y Loc Correction"
        bpy.context.object.modifiers["Y Loc Correction"].show_in_editmode = True
        bpy.context.object.modifiers["Y Loc Correction"].direction = 'Y'

        create_driver('Y Loc Correction', 'strength', '-var', 'modifiers["Y Scale | Subdivision"].screw_offset')

        bpy.ops.emc.autosmooth()
        bpy.context.object.data.auto_smooth_angle = 1.0472

        for i in bpy.context.active_object.modifiers:
            i.show_expanded = False

        if self.apply:
            bpy.ops.object.convert(target='MESH')

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project()
            bpy.ops.object.editmode_toggle()

            del bpy.context.active_object['X Scale']
            del bpy.context.active_object['Y Scale']
            del bpy.context.active_object['X Subdivisions']
            del bpy.context.active_object['Y Subdivisions']
            delete_drivers()

        bpy.context.object.name = "EMC Plane"
        bpy.context.object.data.name = "EMC Plane"
        return{'FINISHED'}

class addCube(bpy.types.Operator):
    bl_label = "Add Cube"
    bl_idname = "emc.cube"
    bl_description = "Create a Cube Modifier Parametric Primitive"
    bl_options = {'REGISTER', 'UNDO'}

    x_size: bpy.props.FloatProperty(
        name = "X Scale", 
        description = "X Axis Scale", 
        default = 2.0,
        min = 0.001
    )

    y_size: bpy.props.FloatProperty(
        name = "Y Scale", 
        description = "Y Axis Scale", 
        default = 2.0,
        min = 0.001
    )

    z_size: bpy.props.FloatProperty(
        name = "Z Scale", 
        description = "Z Axis Scale", 
        default = 2.0,
        min = 0.001
    )

    subdiv: bpy.props.IntProperty(
        name = "Subdivision",
        description = "The Subdivision Level",
        default = 0,
        min = 0, max = 6
    )

    smooth: bpy.props.BoolProperty(
        name = "Catmull Clark Subdivision",
        description = "Catmull Clark Subdivision",
        default = False,
    )

    spherize: bpy.props.FloatProperty(
        name = "Spherize",
        description = "Spherize",
        default = 0,
        min = 0, soft_max = 1,
        subtype = 'FACTOR',
    )

    apply: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Create Primitive Non-Destructively if Disabled",
        default = False,
        )
      
    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=True)
        bpy.ops.mesh.merge(type='CENTER')
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers[0].name = "X Scale"
        bpy.context.object.modifiers["X Scale"].axis = 'X'
        bpy.context.object.modifiers["X Scale"].angle = 0
        bpy.context.object.modifiers["X Scale"].screw_offset = self.x_size
        bpy.context.object.modifiers["X Scale"].steps = 1
        bpy.context.object.modifiers["X Scale"].render_steps = 1

        create_prop("X Scale", self.x_size, 'X axis scale', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('X Scale', 'screw_offset', 'var', '["X Scale"]')

        # --------------
        
        bpy.ops.object.modifier_copy(modifier="X Scale")
        bpy.context.object.modifiers[1].name = "Y Scale"
        bpy.context.object.modifiers["Y Scale"].axis = 'Y'
        bpy.context.object.modifiers["Y Scale"].screw_offset = self.y_size
        bpy.context.object.modifiers["Y Scale"].steps = 1
        bpy.context.object.modifiers["Y Scale"].render_steps = 1
        bpy.context.object.modifiers["Y Scale"].use_normal_calculate = True

        create_prop("Y Scale", self.y_size, 'Y axis scale', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('Y Scale', 'screw_offset', 'var', '["Y Scale"]')

        # --------------

        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers[2].name = "Z Scale"
        bpy.context.object.modifiers["Z Scale"].offset = 0
        bpy.context.object.modifiers["Z Scale"].thickness = self.z_size

        create_prop("Z Scale", self.z_size, 'Z axis scale', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('Z Scale', 'thickness', 'var', '["Z Scale"]')

        # --------------

        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers[3].name = "X Loc Correction"
        bpy.context.object.modifiers["X Loc Correction"].direction = 'X'
        bpy.context.object.modifiers["X Loc Correction"].show_in_editmode = True

        create_driver('X Loc Correction', 'strength', '-var', 'modifiers["X Scale"].screw_offset')

        # --------------

        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers[4].name = "Y Loc Correction"
        bpy.context.object.modifiers["Y Loc Correction"].show_in_editmode = True
        bpy.context.object.modifiers["Y Loc Correction"].direction = 'Y'

        create_driver('Y Loc Correction', 'strength', '-var', 'modifiers["Y Scale"].screw_offset')

        if self.subdiv > 0:
            bpy.ops.object.modifier_add(type='SUBSURF')
            bpy.context.object.modifiers["Subdivision"].subdivision_type = 'CATMULL_CLARK' if self.smooth else 'SIMPLE'
            bpy.context.object.modifiers["Subdivision"].show_only_control_edges = False
            bpy.context.object.modifiers["Subdivision"].levels = self.subdiv

        if self.spherize > 0 and self.subdiv > 0:
            bpy.ops.object.modifier_add(type='CAST')
            bpy.context.object.modifiers[6 if self.subdiv > 0 else 5].name = "Spherize"
            bpy.context.object.modifiers["Spherize"].factor = self.spherize

            create_prop("Spherize", self.spherize, 'Spherize', True, True, True, True, True, 0.0, 1.0, 0.0, 1.0)
            create_driver('Spherize', 'factor', 'var', '["Spherize"]')

        bpy.ops.emc.autosmooth()
        bpy.context.object.data.auto_smooth_angle = 1.0472

        for i in bpy.context.active_object.modifiers:
            i.show_expanded = False

        if self.apply:
            og = bpy.context.selected_objects[0]

            bpy.ops.mesh.primitive_cube_add(enter_editmode=False)
            bpy.context.object.scale[0] = self.x_size/2
            bpy.context.object.scale[1] = self.y_size/2
            bpy.context.object.scale[2] = self.z_size/2
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            bpy.ops.object.editmode_toggle()
            for i in range(0, self.subdiv+1):
                bpy.ops.mesh.subdivide(number_cuts=1)
            bpy.ops.object.editmode_toggle()
            new = bpy.context.selected_objects[0]

            bpy.ops.object.select_all(action='DESELECT')
            og.select_set(True)
            bpy.context.view_layer.objects.active = og

            bpy.ops.object.modifier_add(type='DATA_TRANSFER')
            bpy.context.object.modifiers["DataTransfer"].object = new
            bpy.context.object.modifiers["DataTransfer"].use_loop_data = True
            bpy.context.object.modifiers["DataTransfer"].data_types_loops = {'UV'}

            bpy.ops.object.convert(target='MESH')

            bpy.ops.object.select_all(action='DESELECT')
            new.select_set(True)
            bpy.ops.object.delete()

            og.select_set(True)
            bpy.context.view_layer.objects.active = og

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.seams_from_islands()
            bpy.ops.object.editmode_toggle()

            del bpy.context.active_object['X Scale']
            del bpy.context.active_object['Y Scale']
            del bpy.context.active_object['Z Scale']
            try:
                del bpy.context.active_object['Spherize']
            except:
                pass
            delete_drivers()

        bpy.context.object.name = "EMC Cube"
        bpy.context.object.data.name = "EMC Cube"
        return{'FINISHED'}

class addCircle(bpy.types.Operator):
    bl_label = "Add Circle"
    bl_idname = "emc.circle"
    bl_description = "Create a Circle Modifier Parametric Primitive"
    bl_options = {'REGISTER', 'UNDO'}

    vertices: bpy.props.IntProperty(
        name = "Vertices",
        description = "Vertices",
        default = 32,
        min = 3
    )

    radius: bpy.props.FloatProperty(
        name = "Radius", 
        description = "Radius", 
        default = 1.0,
        min = 0.001
    )

    edges: bpy.props.BoolProperty(
        name = "Only Edges",
        description = "Only Create Edges",
        default = True,
    )

    top: bpy.props.BoolProperty(
        name = "Ngon Fill",
        description = "The Style of the Caps",
        default = True,
    )

    subdiv: bpy.props.IntProperty(
        name = "Fill Subdivision",
        description = "The Subdivision Level of the triangle Fan of the Caps",
        default = 1,
        min = 1
    )

    apply: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Create Primitive Non-Destructively if Disabled",
        default = False,
    )
      
    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=True)
        bpy.ops.mesh.merge(type='CENTER')
        bpy.ops.object.editmode_toggle()

        if self.edges == True:
            bpy.ops.object.modifier_add(type='DISPLACE')
            bpy.context.object.modifiers[0].name = "Radius"
            bpy.context.object.modifiers["Radius"].direction = 'X'
            bpy.context.object.modifiers["Radius"].mid_level = 0
            bpy.context.object.modifiers["Radius"].strength = self.radius

            create_prop("Radius", self.radius, 'Radius', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
            create_driver('Radius', 'strength', 'var', '["Radius"]')

            bpy.ops.object.modifier_add(type='SCREW')
            bpy.context.object.modifiers[1].name = "Vertices"
            bpy.context.object.modifiers["Vertices"].use_merge_vertices = True
            bpy.context.object.modifiers["Vertices"].steps = self.vertices
            bpy.context.object.modifiers["Vertices"].render_steps = self.vertices
            bpy.context.object.modifiers["Vertices"].use_normal_calculate = True
            
        else:
            bpy.ops.object.modifier_add(type='SCREW')
            bpy.context.object.modifiers[0].name = "Radius | Subdivisions"
            bpy.context.object.modifiers["Radius | Subdivisions"].axis = 'X'
            bpy.context.object.modifiers["Radius | Subdivisions"].angle = 0
            bpy.context.object.modifiers["Radius | Subdivisions"].screw_offset = self.radius
            bpy.context.object.modifiers["Radius | Subdivisions"].steps = self.subdiv
            bpy.context.object.modifiers["Radius | Subdivisions"].render_steps = self.subdiv

            create_prop("Radius", self.radius, 'Radius', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
            create_driver('Radius | Subdivisions', 'screw_offset', 'var', '["Radius"]')

            # --------------

            create_prop("Subdivisions", self.subdiv, 'Subdivisions', True, False, True, True, True, 0, 96, 0, 96)
            create_driver('Radius | Subdivisions', 'steps', 'var', '["Subdivisions"]')
            create_driver('Radius | Subdivisions', 'render_steps', 'var', 'modifiers["Radius | Subdivisions"].steps')

            bpy.ops.object.modifier_add(type='SCREW')
            bpy.context.object.modifiers[1].name = "Vertices"
            bpy.context.object.modifiers["Vertices"].use_normal_calculate = True
            bpy.context.object.modifiers["Vertices"].use_merge_vertices = True
            bpy.context.object.modifiers["Vertices"].steps = self.vertices
            bpy.context.object.modifiers["Vertices"].render_steps = self.vertices

            if self.top:
                bpy.ops.object.modifier_add(type='DECIMATE')
                bpy.context.object.modifiers[2].name = "Ngon Fill"
                bpy.context.object.modifiers["Ngon Fill"].decimate_type = 'DISSOLVE'
                bpy.context.object.modifiers["Ngon Fill"].show_expanded = False

                create_prop("Ngon Fill", self.top, 'Ngon Fill', True, True, True, True, True, 0, 1, 0, 1)
                create_driver('Ngon Fill', 'show_viewport', 'var', '["Ngon Fill"]')
                create_driver('Ngon Fill', 'show_render', 'var', 'modifiers["Ngon Fill"].show_viewport')

        create_prop("Vertices", self.vertices, 'Vertices', True, False, True, True, True, 3, 96*2, 3, 96*2)
        create_driver('Vertices', 'steps', 'var', '["Vertices"]')
        create_driver('Vertices', 'render_steps', 'var', 'modifiers["Vertices"].steps')

        for i in bpy.context.active_object.modifiers:
            i.show_expanded = False

        if self.apply:
            bpy.ops.object.convert(target='MESH')
            if not self.edges:
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.05)
                bpy.ops.object.editmode_toggle()

                del bpy.context.active_object['Subdivisions']
                try:
                    del bpy.context.active_object['Ngon Fill']
                except:
                    pass

            del bpy.context.active_object['Vertices']
            del bpy.context.active_object['Radius']
            delete_drivers()

        bpy.context.object.name = "EMC Circle"
        bpy.context.object.data.name = "EMC Circle"
        return{'FINISHED'}

class addCone(bpy.types.Operator):
    bl_label = "Add Cone"
    bl_idname = "emc.cone"
    bl_description = "Create a Cone Modifier Parametric Primitive"
    bl_options = {'REGISTER', 'UNDO'}

    vertices: bpy.props.IntProperty(
        name = "Vertices",
        description = "Vertices",
        default = 32,
        min = 4
    )

    radius1: bpy.props.FloatProperty(
        name = "Base Radius", 
        description = "Base Radius", 
        default = 1.0,
        min = 0.001, max = 100.0
    )

    radius2: bpy.props.FloatProperty(
        name = "Tip Radius", 
        description = "Tip Radius", 
        default = 0,
        min = 0, max = 100
    )

    depth: bpy.props.FloatProperty(
        name = "Depth",
        description = "Depth",
        default = 2.0,
        min = 0.001
        )

    top: bpy.props.BoolProperty(
        name = "Ngon Cap",
        description = "The Style of the Caps",
        default = True,
    )

    topSub: bpy.props.IntProperty(
        name = "Cap Subdivision",
        description = "The Subdivision Level of the triangle Fan of the Caps",
        default = 1,
        min = 1
    )

    smooth: bpy.props.BoolProperty(
        name = "Smooth Shading",
        description = "Use Smooth Shading",
        default = True,
    )

    apply: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Create Primitive Non-Destructively if Disabled",
        default = False,
    )
      
    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=True)
        bpy.ops.mesh.merge(type='CENTER')
        bpy.ops.object.editmode_toggle()
        og = bpy.context.selected_objects[0]

        bpy.ops.object.empty_add(type='PLAIN_AXES')
        # bpy.ops.transform.translate(value=(0, 0, -(self.depth/2)), orient_type='LOCAL')
        bpy.context.object.name = "Cone Taper Origin"
        t_origin = bpy.context.selected_objects[0]
        t_origin.parent = og
        move_to_col(t_origin, 'EMC Extras', True, True)
        bpy.ops.object.select_all(action='DESELECT')
        og.select_set(True)
        bpy.context.view_layer.objects.active = og

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers[0].name = "Radius | Cap Subdiv"
        bpy.context.object.modifiers["Radius | Cap Subdiv"].axis = 'Y'
        bpy.context.object.modifiers["Radius | Cap Subdiv"].angle = 0
        bpy.context.object.modifiers["Radius | Cap Subdiv"].screw_offset = self.radius1
        bpy.context.object.modifiers["Radius | Cap Subdiv"].steps = self.topSub
        bpy.context.object.modifiers["Radius | Cap Subdiv"].render_steps = self.topSub

        create_prop("Base Radius", self.radius1, 'Base Radius', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('Radius | Cap Subdiv', 'screw_offset', 'var', '["Base Radius"]')

        create_prop("Cap Subdivision", self.topSub, 'The Subdivision Level of the triangle Fan of the Caps', True, True, True, True, True, 1, 96*2, 1, 96)
        create_driver('Radius | Cap Subdiv', 'steps', 'var', '["Cap Subdivision"]')
        create_driver('Radius | Cap Subdiv', 'render_steps', 'var', 'modifiers["Radius | Cap Subdiv"].steps')

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers[1].name = "Vertices"
        bpy.context.object.modifiers["Vertices"].use_normal_calculate = True
        bpy.context.object.modifiers["Vertices"].use_merge_vertices = True
        bpy.context.object.modifiers["Vertices"].render_steps = self.vertices
        bpy.context.object.modifiers["Vertices"].steps = self.vertices
        bpy.context.object.modifiers["Vertices"].use_smooth_shade = self.smooth

        create_prop("Vertices", self.vertices, 'Vertices', True, False, True, True, True, 4, 96*2, 4, 96)
        create_driver('Vertices', 'steps', 'var', '["Vertices"]')
        create_driver('Vertices', 'render_steps', 'var', 'modifiers["Vertices"].steps')

        create_prop("Smooth Shading", self.smooth, 'Smooth Shading', True, True, True, True, True, 0, 1, 0, 1)
        create_driver('Vertices', 'use_smooth_shade', 'var', '["Smooth Shading"]')

        bpy.ops.emc.autosmooth()
        bpy.context.object.data.auto_smooth_angle = 1.309

        if self.top:
            bpy.ops.object.modifier_add(type='DECIMATE')
            bpy.context.object.modifiers[2].name = "Ngon Cap"
            bpy.context.object.modifiers["Ngon Cap"].decimate_type = 'DISSOLVE'

            create_prop("Ngon Cap", self.top, 'Ngon Cap', True, True, True, True, True, 0, 1, 0, 1)
            create_driver('Ngon Cap', 'show_viewport', 'var', '["Ngon Cap"]')
            create_driver('Ngon Cap', 'show_render', 'var', 'modifiers["Ngon Cap"].show_viewport')

        else:
            pass
        
        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers[3 if self.top else 2].name = "Depth"
        bpy.context.object.modifiers["Depth"].offset = 1
        bpy.context.object.modifiers["Depth"].thickness = self.depth

        create_prop("Depth", self.depth, 'Depth', True, False, True, True, True, 0.001, 1, 0.001, 100.0)
        create_driver('Depth', 'thickness', 'var', '["Depth"]')
        
        bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
        bpy.context.object.modifiers[4 if self.top else 3].name = "Top Radius"
        bpy.context.object.modifiers["Top Radius"].deform_method = 'TAPER'
        bpy.context.object.modifiers["Top Radius"].origin = t_origin
        bpy.context.object.modifiers["Top Radius"].deform_axis = 'Z'
        bpy.context.object.modifiers["Top Radius"].factor = self.radius2-1

        create_prop("Tip Radius", self.radius2, 'Tip Radius', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('Top Radius', 'factor', 'var-1', '["Tip Radius"]')

        bpy.ops.object.modifier_add(type='WELD')

        for i in bpy.context.active_object.modifiers:
            i.show_expanded = False

        if self.apply:
            bpy.ops.mesh.primitive_cone_add(vertices=self.vertices, radius1=self.radius1, radius2=self.radius2, depth=self.depth, end_fill_type='NGON', enter_editmode=True)
            og_mode = bpy.context.tool_settings.mesh_select_mode[:]
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            bpy.ops.transform.translate(value=(0, 0, self.depth/2), orient_type='LOCAL')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_face_by_sides(number=3, type='GREATER')
            bpy.ops.mesh.poke()
            bpy.ops.mesh.ext_deselect_boundary()
            bpy.ops.mesh.subdivide(number_cuts=self.topSub-1)
            bpy.ops.object.editmode_toggle()
            new = bpy.context.selected_objects[0]

            bpy.ops.object.select_all(action='DESELECT')
            og.select_set(True)
            bpy.context.view_layer.objects.active = og

            bpy.ops.object.modifier_add(type='DATA_TRANSFER')
            bpy.context.object.modifiers["DataTransfer"].object = new
            bpy.context.object.modifiers["DataTransfer"].use_loop_data = True
            bpy.context.object.modifiers["DataTransfer"].data_types_loops = {'UV'}

            bpy.ops.object.convert(target='MESH')

            bpy.ops.object.select_all(action='DESELECT')
            new.select_set(True)
            t_origin.select_set(True)
            bpy.ops.object.delete()

            og.select_set(True)
            bpy.context.view_layer.objects.active = og

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.edges_select_sharp(sharpness=1.309)
            bpy.ops.transform.edge_bevelweight(value=1)
            bpy.ops.transform.edge_crease(value=1)
            bpy.ops.uv.seams_from_islands()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.context.tool_settings.mesh_select_mode = og_mode
            bpy.ops.object.editmode_toggle()

            del bpy.context.active_object['Base Radius']
            del bpy.context.active_object['Cap Subdivision']
            del bpy.context.active_object['Vertices']
            del bpy.context.active_object['Smooth Shading']
            del bpy.context.active_object['Depth']
            del bpy.context.active_object['Tip Radius']
            try:
                del bpy.context.active_object['Ngon Cap']
            except:
                pass
            delete_drivers()

        bpy.context.object.name = "EMC Cone"
        bpy.context.object.data.name = "EMC Cone"
        return{'FINISHED'}

class addSphere(bpy.types.Operator):
    bl_label = "Add Sphere"
    bl_idname = "emc.sphere"
    bl_description = "Create a Sphere Modifier Parametric Primitive"
    bl_options = {'REGISTER', 'UNDO'}

    segments: bpy.props.IntProperty(
        name = "Segments",
        description = "Segments",
        default = 32,
        min = 3
    )

    rings: bpy.props.IntProperty(
        name = "Rings",
        description = "Rings",
        default = 16,
        min = 3
    )

    radius: bpy.props.FloatProperty(
        name = "Radius", 
        description = "Radius", 
        default = 1.0,
        min = 0.001, max = 100
    )

    smooth: bpy.props.BoolProperty(
        name = "Smooth Shading",
        description = "Use Smooth Shading",
        default = True,
    )

    apply: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Create Primitive Non-Destructively if Disabled",
        default = False,
    )
      
    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=True)
        bpy.ops.mesh.merge(type='CENTER')
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers[0].name = "Radius"
        bpy.context.object.modifiers["Radius"].direction = 'Z'
        bpy.context.object.modifiers["Radius"].mid_level = 0
        bpy.context.object.modifiers["Radius"].strength = self.radius

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers[1].name = "Rings"
        bpy.context.object.modifiers["Rings"].axis = 'Y'
        bpy.context.object.modifiers["Rings"].steps = self.rings
        bpy.context.object.modifiers["Rings"].render_steps = self.rings
        bpy.context.object.modifiers["Rings"].use_merge_vertices = True
        bpy.context.object.modifiers["Rings"].angle = 3.14159

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers[2].name = "Segments"
        bpy.context.object.modifiers["Segments"].steps = self.segments
        bpy.context.object.modifiers["Segments"].render_steps = self.segments
        bpy.context.object.modifiers["Segments"].use_normal_calculate = True
        bpy.context.object.modifiers["Segments"].use_merge_vertices = True
        bpy.context.object.modifiers["Segments"].use_smooth_shade = self.smooth

        # --------------

        create_prop("Radius", self.radius, 'Radius', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('Radius', 'strength', 'var', '["Radius"]')
        
        create_prop("Rings", self.rings, 'Rings', True, True, True, True, True, 3, 96*2, 3, 96)
        create_driver('Rings', 'steps', 'var', '["Rings"]')
        create_driver('Rings', 'render_steps', 'var', 'modifiers["Rings"].steps')

        create_prop("Segments", self.segments, 'Segments', True, True, True, True, True, 3, 96*2, 3, 96)
        create_driver('Segments', 'steps', 'var', '["Segments"]')
        create_driver('Segments', 'render_steps', 'var', 'modifiers["Segments"].steps')

        create_prop("Smooth Shading", self.smooth, 'Use Smooth Shading', True, True, True, True, True, 0, 1, 0, 1)
        create_driver('Segments', 'use_smooth_shade', 'var', '["Smooth Shading"]')

        # --------------

        for i in bpy.context.active_object.modifiers:
            i.show_expanded = False

        if self.apply:
            og = bpy.context.selected_objects[0]
            bpy.ops.mesh.primitive_uv_sphere_add(segments=self.segments, ring_count=self.rings, radius=self.radius, enter_editmode=False)
            new = bpy.context.selected_objects[0]

            bpy.ops.object.select_all(action='DESELECT')
            og.select_set(True)
            bpy.context.view_layer.objects.active = og

            bpy.ops.object.modifier_add(type='DATA_TRANSFER')
            bpy.context.object.modifiers["DataTransfer"].object = new
            bpy.context.object.modifiers["DataTransfer"].use_loop_data = True
            bpy.context.object.modifiers["DataTransfer"].data_types_loops = {'UV'}

            bpy.ops.object.convert(target='MESH')

            bpy.ops.object.select_all(action='DESELECT')
            new.select_set(True)
            bpy.ops.object.delete()

            og.select_set(True)
            bpy.context.view_layer.objects.active = og

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.seams_from_islands()
            bpy.ops.object.editmode_toggle()

            del bpy.context.active_object['Radius']
            del bpy.context.active_object['Rings']
            del bpy.context.active_object['Segments']
            del bpy.context.active_object['Smooth Shading']
            delete_drivers()

        bpy.context.object.name = "EMC Sphere"
        bpy.context.object.data.name = "EMC Sphere"
        return{'FINISHED'}

class addTorus(bpy.types.Operator):
    bl_label = "Add Torus"
    bl_idname = "emc.torus"
    bl_description = "Create a Torus Modifier Parametric Primitive"
    bl_options = {'REGISTER', 'UNDO'}

    mj_segments: bpy.props.IntProperty(
        name = "Major Segments",
        description = "MajorSegments",
        default = 48,
        min = 3
    )

    mn_segments: bpy.props.IntProperty(
        name = "Minor Segments",
        description = "Minor Segments",
        default = 12,
        min = 3
    )

    mj_radius: bpy.props.FloatProperty(
        name = "Major Radius", 
        description = "Major Radius", 
        default = 1.0,
        min = 0.001, max = 100
    )

    mn_radius: bpy.props.FloatProperty(
        name = "Minor Radius", 
        description = "Minor Radius", 
        default = 0.25,
        min = 0.001, max = 100
    )

    smooth: bpy.props.BoolProperty(
        name = "Smooth Shading",
        description = "Use Smooth Shading",
        default = True,
    )

    apply: bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Create Primitive Non-Destructively if Disabled",
        default = False,
    )
      
    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=True)
        bpy.ops.mesh.merge(type='CENTER')
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers[0].name = "Minor Radius"
        bpy.context.object.modifiers["Minor Radius"].direction = 'Z'
        bpy.context.object.modifiers["Minor Radius"].mid_level = 0
        bpy.context.object.modifiers["Minor Radius"].strength = self.mn_radius

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers[1].name = "Minor Segments"
        bpy.context.object.modifiers["Minor Segments"].axis = 'Y'
        bpy.context.object.modifiers["Minor Segments"].steps = self.mn_segments
        bpy.context.object.modifiers["Minor Segments"].render_steps = self.mn_segments
        bpy.context.object.modifiers["Minor Segments"].use_merge_vertices = True

        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers[2].name = "Major Radius"
        bpy.context.object.modifiers["Major Radius"].direction = 'X'
        bpy.context.object.modifiers["Major Radius"].strength = self.mj_radius
        bpy.context.object.modifiers["Major Radius"].mid_level = 0

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers[3].name = "Major Segments"
        bpy.context.object.modifiers["Major Segments"].steps = self.mj_segments
        bpy.context.object.modifiers["Major Segments"].render_steps = self.mj_segments
        bpy.context.object.modifiers["Major Segments"].use_normal_calculate = True
        bpy.context.object.modifiers["Major Segments"].use_merge_vertices = True
        bpy.context.object.modifiers["Major Segments"].use_smooth_shade = self.smooth
        if self.mn_segments == 3:
            bpy.context.object.modifiers["Major Segments"].use_normal_flip = True

        # --------------

        create_prop("Minor Radius", self.mn_radius, 'Minor Radius', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('Minor Radius', 'strength', 'var', '["Minor Radius"]')

        create_prop("Minor Segments", self.mn_segments, 'Minor Segments', True, True, True, True, True, 3, 96*2, 3, 96)
        create_driver('Minor Segments', 'steps', 'var', '["Minor Segments"]')
        create_driver('Minor Segments', 'render_steps', 'var', 'modifiers["Minor Segments"].steps')

        create_prop("Major Radius", self.mj_radius, 'Major Radius', True, False, True, True, True, 0.001, 100.0, 0.001, 100.0)
        create_driver('Major Radius', 'strength', 'var', '["Major Radius"]')

        create_prop("Major Segments", self.mj_segments, 'Major Segments', True, True, True, True, True, 3, 96*2, 3, 96)
        create_driver('Major Segments', 'steps', 'var', '["Major Segments"]')
        create_driver('Major Segments', 'render_steps', 'var', 'modifiers["Major Segments"].steps')

        create_prop("Smooth Shading", self.smooth, 'Use Smooth Shading', True, True, True, True, True, 0, 1, 0, 1)
        create_driver('Major Segments', 'use_smooth_shade', 'var', '["Smooth Shading"]')

        create_driver('Major Segments', 'use_normal_flip', 'True if var == 3 else False', 'modifiers["Minor Segments"].steps')

        # --------------

        for i in bpy.context.active_object.modifiers:
            i.show_expanded = False

        if self.apply:
            og = bpy.context.selected_objects[0]
            bpy.ops.mesh.primitive_torus_add(major_segments=self.mj_segments, minor_segments=self.mn_segments, major_radius=self.mj_radius, minor_radius=self.mn_radius)
            new = bpy.context.selected_objects[0]

            bpy.ops.object.select_all(action='DESELECT')
            og.select_set(True)
            bpy.context.view_layer.objects.active = og

            bpy.ops.object.modifier_add(type='DATA_TRANSFER')
            bpy.context.object.modifiers["DataTransfer"].object = new
            bpy.context.object.modifiers["DataTransfer"].use_loop_data = True
            bpy.context.object.modifiers["DataTransfer"].data_types_loops = {'UV'}

            bpy.ops.object.convert(target='MESH')

            bpy.ops.object.select_all(action='DESELECT')
            new.select_set(True)
            bpy.ops.object.delete()

            og.select_set(True)
            bpy.context.view_layer.objects.active = og

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.seams_from_islands()
            bpy.ops.object.editmode_toggle()

            del bpy.context.active_object['Minor Radius']
            del bpy.context.active_object['Minor Segments']
            del bpy.context.active_object['Major Radius']
            del bpy.context.active_object['Major Segments']
            del bpy.context.active_object['Smooth Shading']
            delete_drivers()

        bpy.context.object.name = "EMC Torus"
        bpy.context.object.data.name = "EMC Torus"
        return{'FINISHED'}

class EmcBevelModal(bpy.types.Operator):
    """Create a Bevel Modifier"""
    bl_idname = "emc.bevelmod"
    bl_label = "Bevel"
    bl_options = {'REGISTER', 'UNDO'}

    first_mouse_x: bpy.props.IntProperty()
    current_mouse_x: bpy.props.IntProperty()
    offset: bpy.props.FloatProperty()
    profile: bpy.props.FloatProperty(
        name = "Profile", 
        description = "Profile", 
        default = 500,
        min = 0, max = 1000
    )
    segments: bpy.props.IntProperty(default = 4)
    temp_prof: bpy.props.FloatProperty()
    temp_offs: bpy.props.FloatProperty()
    temp_angl: bpy.props.FloatProperty()
    temp_last: bpy.props.StringProperty()
    init: bpy.props.BoolProperty()
    edit: bpy.props.BoolProperty()
    wires: bpy.props.BoolProperty()
    vert_select: bpy.props.BoolProperty()
    mod_loc: bpy.props.IntProperty()
    mods_with_bevel: bpy.props.IntProperty()
    og_mods_num: bpy.props.IntProperty()

    def modal(self, context, event):

        if event.type == 'LEFT_CTRL':
            if event.value == 'RELEASE':
                self.current_mouse_x = self.first_mouse_x - event.mouse_x
                self.temp_prof = self.current_mouse_x - self.temp_offs
                self.temp_last = "profile"
                # print(self.temp_prof)
            if event.value == 'PRESS':
                self.current_mouse_x = self.first_mouse_x - event.mouse_x
                if self.temp_last == "angle":
                    self.temp_offs = self.current_mouse_x - self.temp_angl
                elif self.temp_last == "profile":
                    self.temp_offs = self.current_mouse_x - self.temp_prof
                self.temp_last = "offset"
                # print(self.temp_offs)
        
        if event.type == 'LEFT_SHIFT':
            if event.value == 'RELEASE':
                self.current_mouse_x = self.first_mouse_x - event.mouse_x
                self.temp_angl = self.current_mouse_x - self.temp_offs
                self.temp_last = "angle"
                # print(self.temp_angl)
            if event.value == 'PRESS':
                self.current_mouse_x = self.first_mouse_x - event.mouse_x
                if self.temp_last == "angle":
                    self.temp_offs = self.current_mouse_x - self.temp_angl
                elif self.temp_last == "profile":
                    self.temp_offs = self.current_mouse_x - self.temp_prof
                self.temp_last = "offset"
                # print(self.temp_offs)
            
        if event.type == 'MOUSEMOVE':
            delta = self.first_mouse_x - event.mouse_x
            profile = (self.temp_prof + (delta - self.current_mouse_x) -500) * -0.001
            angle = (self.temp_angl + (delta - self.current_mouse_x) - 40) * -0.01
            width = (self.temp_offs + (delta - self.current_mouse_x)) * -0.005
            if event.ctrl:
                
                bpy.context.object.modifiers[self.mod_loc].profile = profile
                # print(self.temp_prof + (delta - self.current_mouse_x) -500)
            elif event.shift:
                try:
                    
                    bpy.context.object.modifiers[self.mod_loc].angle_limit = angle
                    # print(self.temp_prof + (delta - self.current_mouse_x))
                except:
                    pass
            else:
                if self.init == True:
                    bpy.context.object.modifiers[self.mod_loc].profile = 0.5
                    bpy.context.object.modifiers[self.mod_loc].angle_limit = 0.523599
                    self.init = False
                    
                bpy.context.object.modifiers[self.mod_loc].width = width
                # print(self.temp_offs + (delta - self.current_mouse_x))
            
        
        elif event.type == 'WHEELUPMOUSE':
            bpy.context.object.modifiers[self.mod_loc].segments += 1
            
        elif event.type == 'WHEELDOWNMOUSE':
            bpy.context.object.modifiers[self.mod_loc].segments -= 1
            
        elif event.type == 'A':
            bpy.context.object.modifiers[self.mod_loc].limit_method = 'ANGLE'
            
        elif event.type == 'N':
            bpy.context.object.modifiers[self.mod_loc].limit_method = 'NONE'
        
        elif event.type == 'W':
            bpy.context.object.modifiers[self.mod_loc].limit_method = 'WEIGHT'
            
        elif event.type == 'V':
            bpy.context.object.modifiers[self.mod_loc].limit_method = 'VGROUP'

        elif event.type == 'X':
            if event.value == 'PRESS':
                try:
                    bpy.context.object.modifiers[self.mod_loc].use_only_vertices = not bpy.context.object.modifiers[self.mod_loc].use_only_vertices
                except:
                    if bpy.context.object.modifiers[self.mod_loc].affect == 'EDGES':
                        bpy.context.object.modifiers[self.mod_loc].affect = 'VERTICES'
                    else:
                        bpy.context.object.modifiers[self.mod_loc].affect = 'EDGES'
            
        elif event.type == 'C':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[self.mod_loc].use_clamp_overlap = not bpy.context.object.modifiers[self.mod_loc].use_clamp_overlap
        
        elif event.type == 'S':
            if event.value == 'PRESS':
                if bpy.context.object.modifiers[self.mod_loc].miter_outer == 'MITER_SHARP':
                    bpy.context.object.modifiers[self.mod_loc].miter_outer = 'MITER_PATCH'
                elif bpy.context.object.modifiers[self.mod_loc].miter_outer == 'MITER_PATCH':
                    bpy.context.object.modifiers[self.mod_loc].miter_outer = 'MITER_ARC'
                else:
                    bpy.context.object.modifiers[self.mod_loc].miter_outer = 'MITER_SHARP'

        elif event.type == 'H':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[self.mod_loc].harden_normals = not bpy.context.object.modifiers[self.mod_loc].harden_normals

        elif event.type == 'Q':
            if event.value == 'PRESS':
                bpy.context.object.show_wire = not bpy.context.object.show_wire

        elif event.type == 'L':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[self.mod_loc].loop_slide = not bpy.context.object.modifiers[self.mod_loc].loop_slide


        elif event.type in {'MIDDLEMOUSE'}:
            return {'PASS_THROUGH'}

        elif event.type == 'LEFTMOUSE':
            if self.edit == True:
                bpy.ops.object.mode_set(mode='EDIT')
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.context.object.show_wire = self.wires
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.context.object.modifiers[self.mod_loc].width = self.offset
            bpy.context.object.modifiers[self.mod_loc].segments = self.segments
            bpy.context.object.modifiers[self.mod_loc].profile = self.profile
            bpy.context.object.modifiers[self.mod_loc].angle_limit = self.temp_angl                
            if self.edit == True:
                if self.vert_select:
                    bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
                else:
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.ed.undo()
                    if self.og_mods_num != len(bpy.context.object.modifiers):
                        bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
            else:
                bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.context.object.show_wire = self.wires
            return {'CANCELLED'}
        try:
            context.area.header_text_set(
                "Offset: " + str(round(bpy.context.object.modifiers[self.mod_loc].width, 2)) + " | " + 
                "Segments: " + str(bpy.context.object.modifiers[self.mod_loc].segments) + " | " + 
                "Profile: "  + str(round(bpy.context.object.modifiers[self.mod_loc].profile, 3)) + " | " + 
                "Angle: " + str(round(bpy.context.object.modifiers[self.mod_loc].angle_limit*180/math.pi, 1)) + " | " + 
                "Loop Slide: " + str(bpy.context.object.modifiers[self.mod_loc].loop_slide)
            )
            bpy.types.WorkSpace.status_text_set_internal("MMB Scroll: Segments | Ctrl: Profile | Shift: Angle | C: Clamp | N/A/W/V: Limit Method | X: Only Vertices | S: Outer Miter | H: Harden Normals | Q: Toggle Wireframe | L: Loop Slide")
        except:
            pass
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.first_mouse_x = event.mouse_x
        self.current_mouse_x = 0
        self.init = True
        self.wires = bpy.context.object.show_wire
        self.og_mods_num = len(bpy.context.object.modifiers)
        self.vert_select = True if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (True, False, False) else False
        self.mod_loc = -1
        self.mods_with_bevel = 0
        mod_temp_loc = 0

        bpy.context.object.data.use_auto_smooth = True
        bpy.context.object.show_wire = True

        if bpy.context.object.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(context.edit_object.data)
            selected_verts = [vertex for vertex in bm.verts if vertex.select]
            bpy.ops.object.modifier_add(type='BEVEL')
            bpy.context.object.modifiers[-1].harden_normals = True
            bpy.context.object.modifiers[-1].miter_outer = 'MITER_ARC'
            if len(selected_verts) > 0:
                if self.vert_select:
                    bpy.ops.object.vertex_group_add()
                    bpy.context.scene.tool_settings.vertex_group_weight = 1
                    bpy.ops.object.vertex_group_assign()
                    bpy.context.object.vertex_groups[-1].name = 'EMC Bevel'
                    bpy.context.object.modifiers[-1].vertex_group = bpy.context.object.vertex_groups[self.mod_loc].name
                    bpy.context.object.modifiers[-1].limit_method = 'VGROUP'
                else:
                    for modifier in bpy.context.object.modifiers:
                        mod_temp_loc += 1
                        if modifier.type == 'BEVEL':
                            if modifier.limit_method == 'WEIGHT':
                                self.mods_with_bevel += 1
                                self.mod_loc = mod_temp_loc - len(bpy.context.object.modifiers)
                    print(self.mod_loc)
                    bpy.ops.transform.edge_bevelweight(value=1)
                    bpy.context.object.modifiers[-1].limit_method = 'WEIGHT'
                    if self.mods_with_bevel > 0:
                        bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
                bpy.ops.object.mode_set(mode='OBJECT')
                self.edit = True
        elif bpy.context.object.mode == 'OBJECT':
            bpy.ops.object.modifier_add(type='BEVEL')
            bpy.context.object.modifiers[self.mod_loc].harden_normals = True
            bpy.context.object.modifiers[self.mod_loc].miter_outer = 'MITER_ARC'
            bpy.context.object.modifiers[self.mod_loc].limit_method = 'ANGLE'
            self.edit = False

        try:
            bpy.data.window_managers["WinMan"].ml_active_object_modifier_active_index = -1
        except:
            pass  
        
        try:
            self.offset = bpy.context.object.modifiers[self.mod_loc].width
            self.segments = bpy.context.object.modifiers[self.mod_loc].segments
            self.profile = bpy.context.object.modifiers[self.mod_loc].profile
            self.temp_angl = bpy.context.object.modifiers[self.mod_loc].angle_limit
        except:
            pass

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class EmcArrayModal(bpy.types.Operator):
    """Create an Array Modifier"""
    bl_idname = "emc.arraymod"
    bl_label = "Array"
    bl_options = {'REGISTER', 'UNDO', 'UNDO_GROUPED'}

    first_mouse_x: bpy.props.IntProperty()
    current_mouse_x: bpy.props.IntProperty()
    ctrl: bpy.props.FloatProperty()
    x_factor: bpy.props.FloatProperty()
    y_factor: bpy.props.FloatProperty()
    z_factor: bpy.props.FloatProperty()
    count: bpy.props.IntProperty(default = 2)
    temp_norm: bpy.props.FloatProperty()
    axis_num: bpy.props.IntProperty()
    axis_name: bpy.props.StringProperty()
    mod_index: bpy.props.IntProperty()
    curve: bpy.props.StringProperty()
    add_deform: bpy.props.BoolProperty()
    add_circle: bpy.props.BoolProperty()
    move: bpy.props.FloatProperty()
    init: bpy.props.BoolProperty()
    og_obj: bpy.props.StringProperty()
    obj_offset: bpy.props.StringProperty()
    obj_mode: bpy.props.StringProperty()
    wires: bpy.props.BoolProperty()

    def modal(self, context, event):

        orig_cur_loc = mathutils.Vector.copy(bpy.context.scene.cursor.location)
        orig_cur_rot = mathutils.Euler.copy(bpy.context.scene.cursor.rotation_euler)

        if event.type == 'C':
            if event.value == 'PRESS':
                if len(bpy.context.selected_objects) == 1:
                    if self.init:
                        self.add_circle = True
                    else:
                        bpy.ops.object.select_all(action='DESELECT')
                        try:
                            bpy.data.objects[self.obj_offset].select_set(True)
                            bpy.ops.object.delete()
                        except:
                            pass

                        bpy.data.objects[self.og_obj].select_set(True)
                    

                    self.og_obj = bpy.context.active_object.name
                    modName = bpy.context.object.modifiers[self.mod_index].name

                    bpy.context.scene.cursor.location = bpy.context.active_object.location
                    bpy.context.scene.cursor.rotation_euler = bpy.context.active_object.rotation_euler
                    bpy.ops.object.empty_add(type='ARROWS')

                    bpy.ops.object.location_clear(clear_delta=False)
                    bpy.ops.object.rotation_clear(clear_delta=False)

                    self.obj_offset = bpy.context.active_object.name

                    bpy.data.objects[self.obj_offset].parent = bpy.data.objects[self.og_obj]

                    # if bpy.data.objects[self.og_obj].type == "CURVE":
                    #     bpy.data.objects[self.obj_offset].matrix_parent_inverse = bpy.data.objects[self.og_obj].matrix_world.inverted()

                    # move to extras collection
                    move_to_col(bpy.data.objects[self.obj_offset], "EMC Extras", True, True)
                    
                    if self.axis_num == 0:
                        bpy.data.objects[self.obj_offset].driver_remove("rotation_euler", 1)
                        bpy.data.objects[self.obj_offset].driver_remove("rotation_euler", 0)
                        dr = bpy.data.objects[self.obj_offset].driver_add("rotation_euler", 2)
                    elif self.axis_num == 1:
                        bpy.data.objects[self.obj_offset].driver_remove("rotation_euler", 1)
                        bpy.data.objects[self.obj_offset].driver_remove("rotation_euler", 2)
                        dr = bpy.data.objects[self.obj_offset].driver_add("rotation_euler", 0)
                    elif self.axis_num == 2:
                        bpy.data.objects[self.obj_offset].driver_remove("rotation_euler", 0)
                        bpy.data.objects[self.obj_offset].driver_remove("rotation_euler", 2)
                        dr = bpy.data.objects[self.obj_offset].driver_add("rotation_euler", 1)
                    dr.driver.type='SCRIPTED'
                    dr.driver.expression = '(360/var)/(180/pi)'
                    var = dr.driver.variables.new()
                    var.type = 'SINGLE_PROP'
                    var.targets[0].id = bpy.data.objects[self.og_obj]
                    var.targets[0].data_path = 'modifiers["' + modName + '"].count'

                    bpy.ops.object.select_all(action='DESELECT')

                    bpy.data.objects[self.og_obj].select_set(True)
                    bpy.context.view_layer.objects.active = bpy.data.objects[self.og_obj]

                    if self.add_circle == True:
                        bpy.context.object.modifiers[self.mod_index].use_relative_offset = False
                        bpy.context.object.modifiers[self.mod_index].use_object_offset = True
                        bpy.context.object.modifiers[self.mod_index].offset_object = bpy.data.objects[self.obj_offset]

                        try:
                            
                            bpy.ops.object.modifier_add(type='DISPLACE')
                            try:
                                bpy.ops.object.modifier_move_up(modifier=bpy.context.object.modifiers[self.mod_index].name)
                            except:
                                bpy.ops.object.modifier_move_to_index(modifier=bpy.context.object.modifiers[self.mod_index].name, index=self.mod_index - 1)

                            bpy.context.object.modifiers[self.mod_index - 1].show_in_editmode = True
                            bpy.context.object.modifiers[self.mod_index - 1].direction = 'X'

                        except:
                            self.report({"WARNING"}, "Can't add displace modifier")
                        
                        self.init = False
                        self.add_circle = False
                    else:
                        if not self.init:
                            bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[self.mod_index - 1].name)
                            
                            bpy.ops.object.select_all(action='DESELECT')
                            bpy.data.objects[self.obj_offset].select_set(True)
                            bpy.ops.object.delete()

                            bpy.data.objects[self.og_obj].select_set(True)

                            bpy.context.view_layer.objects.active = bpy.data.objects[self.og_obj]
                            bpy.context.object.modifiers[self.mod_index].use_relative_offset = True
                            bpy.context.object.modifiers[self.mod_index].use_object_offset = False

                            if len(bpy.data.collections['EMC Extras'].objects) == 0:
                                bpy.data.collections.remove(bpy.data.collections['EMC Extras'])
                        self.add_circle = True

                else:
                    self.report({"WARNING"}, "Circular array cannot be applied to more than one selection")

        elif event.type == 'MOUSEMOVE':
            delta = self.first_mouse_x - event.mouse_x
            strength = (self.temp_norm + (delta - self.current_mouse_x)) * -0.025
            displace = (self.temp_norm + (delta - self.current_mouse_x)) * -0.005
            if not self.add_circle and not self.init:
                try:
                    bpy.context.object.modifiers[self.mod_index - 1].strength = strength
                except:
                    self.report({"WARNING"}, "Displacement modifier not found")
            else:
                bpy.context.object.modifiers[self.mod_index].relative_offset_displace[self.axis_num] = displace
        
        elif event.type == 'WHEELUPMOUSE':
            bpy.context.object.modifiers[self.mod_index].count += 1
            
        elif event.type == 'WHEELDOWNMOUSE':
            bpy.context.object.modifiers[self.mod_index].count -= 1
        
        elif event.type == 'X':
            if event.value == 'PRESS':
                self.axis_num = 0
                self.axis_name = 'X'
                bpy.context.object.modifiers[self.mod_index].relative_offset_displace[1] = 0
                bpy.context.object.modifiers[self.mod_index].relative_offset_displace[2] = 0
                try:
                    if not self.add_circle:
                        bpy.context.object.modifiers[self.mod_index - 1].direction = 'X'
                except:
                    pass
                try:
                    if event.shift:
                        bpy.context.object.modifiers[-1].deform_axis = 'NEG_X'
                    else:
                        bpy.context.object.modifiers[-1].deform_axis = 'POS_X'
                except:
                    pass

        elif event.type == 'Y':
            if event.value == 'PRESS':
                self.axis_num = 1
                self.axis_name = 'Y'
                bpy.context.object.modifiers[self.mod_index].relative_offset_displace[0] = 0
                bpy.context.object.modifiers[self.mod_index].relative_offset_displace[2] = 0
                try:
                    if not self.add_circle:
                        bpy.context.object.modifiers[self.mod_index - 1].direction = 'Y'
                except:
                    pass
                try:
                    if event.shift:
                        bpy.context.object.modifiers[-1].deform_axis = 'NEG_Y'
                    else:
                        bpy.context.object.modifiers[-1].deform_axis = 'POS_Y'
                except:
                    pass

        elif event.type == 'Z':
            if event.value == 'PRESS':
                self.axis_num = 2
                self.axis_name = 'Z'
                bpy.context.object.modifiers[self.mod_index].relative_offset_displace[0] = 0
                bpy.context.object.modifiers[self.mod_index].relative_offset_displace[1] = 0
                try:
                    if not self.add_circle:
                        bpy.context.object.modifiers[self.mod_index - 1].direction = 'Z'
                except:
                    pass
                try:
                    if event.shift:
                        bpy.context.object.modifiers[-1].deform_axis = 'NEG_Z'
                    else:
                        bpy.context.object.modifiers[-1].deform_axis = 'POS_Z'
                except:
                    pass

        elif event.type == 'Q':
            if event.value == 'PRESS':
                bpy.context.object.show_wire = not bpy.context.object.show_wire

        elif event.type == 'D':
            if event.value == 'PRESS':
                if len(bpy.context.selected_objects) == 2 and bpy.data.objects[self.curve].type == 'CURVE':
                    if self.add_deform == True:
                        self.add_deform = False
                        bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
                        self.mod_index += 1
                    else:
                        self.add_deform = True
                    if self.add_deform:
                            bpy.ops.object.modifier_add(type='CURVE')
                            bpy.context.object.modifiers[-1].object = bpy.data.objects[self.curve]
                            self.mod_index -= 1
                            try:
                                bpy.data.window_managers["WinMan"].ml_active_object_modifier_active_index = self.mod_index
                            except:
                                pass
                else:
                    self.report({"WARNING"}, "No selected curve")
        
        elif event.type == 'M':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[self.mod_index].use_merge_vertices = not bpy.context.object.modifiers[self.mod_index].use_merge_vertices

        elif event.type == 'F':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[self.mod_index].use_merge_vertices_cap = not bpy.context.object.modifiers[self.mod_index].use_merge_vertices_cap

        elif event.type in {'MIDDLEMOUSE'}:
            return {'PASS_THROUGH'}

        elif event.type == 'LEFTMOUSE':
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.ops.object.mode_set (mode =self.og_mode)
            bpy.context.object.show_wire = self.wires
            bpy.context.scene.cursor.location = orig_cur_loc
            bpy.context.scene.cursor.rotation_euler = orig_cur_rot
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.context.object.modifiers[self.mod_index].count = self.count
            bpy.context.object.modifiers[self.mod_index].relative_offset_displace[0] = self.x_factor
            bpy.context.object.modifiers[self.mod_index].relative_offset_displace[1] = self.y_factor
            bpy.context.object.modifiers[self.mod_index].relative_offset_displace[2] = self.z_factor
            bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
            if not self.add_circle:
                bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects[self.obj_offset].select_set(True)
                bpy.context.view_layer.objects.active = bpy.data.objects[self.obj_offset]
                bpy.ops.object.delete()
                bpy.data.objects[self.og_obj].select_set(True)
                bpy.context.view_layer.objects.active = bpy.data.objects[self.og_obj]
            if self.add_deform:
                bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.ops.object.mode_set (mode =self.og_mode)
            bpy.context.object.show_wire = self.wires
            bpy.context.scene.cursor.location = orig_cur_loc
            bpy.context.scene.cursor.rotation_euler = orig_cur_rot
            return {'CANCELLED'}
        try:
            if self.add_deform:
                srngt = round(bpy.context.object.modifiers[self.mod_index].relative_offset_displace[self.axis_num], 2)
            else:
                srngt = round(bpy.context.object.modifiers[self.mod_index].relative_offset_displace[self.axis_num], 2) if self.add_circle else round(bpy.context.object.modifiers[self.mod_index - 1].strength, 2)
            context.area.header_text_set(
                "Strength: " + str(srngt) + " | " + 
                "Count: " + str(bpy.context.object.modifiers[self.mod_index].count) + " | " + 
                "Axis: " + self.axis_name + " | " + 
                "Circular: " + str(not self.add_circle) + " | " +  
                "Curve Deform: " + str(self.add_deform) + " | " +  
                "Merge: " + str(bpy.context.object.modifiers[self.mod_index].use_merge_vertices) + " | " +  
                "First Last: " + str(bpy.context.object.modifiers[self.mod_index].use_merge_vertices_cap)
            )
            bpy.types.WorkSpace.status_text_set_internal("MMB Scroll: Count | X/Y/Z: Set Axis | C: Circular Array | D: Curve Deform | M: Merge Vertices | F: First Last | Q: Toggle Wireframe")
        except:
            pass
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.first_mouse_x = event.mouse_x
        self.current_mouse_x = 0
        self.add_circle = True
        self.add_deform = False
        self.init = True
        self.axis_name = 'X'
        self.og_mode = bpy.context.object.mode
        self.wires = bpy.context.object.show_wire
        self.mod_index = -1

        bpy.ops.object.mode_set (mode = 'OBJECT')

        bpy.ops.object.modifier_add(type='ARRAY')

        if len(bpy.context.selected_objects) == 2:
            curve = bpy.context.selected_objects
            active = bpy.context.view_layer.objects.active
            curve.remove(active)
            self.curve = curve[0].name
            if bpy.data.objects[self.curve].type == 'CURVE':
                try:
                    bpy.context.object.modifiers[self.mod_index].fit_type = 'FIT_CURVE'
                    bpy.context.object.modifiers[self.mod_index].curve = curve[0]
                except:
                    pass
            else:
                self.report({"ERROR"}, "Selected object must be CURVE type")
                # bpy.ops.ed.undo()
        else:
            pass

        try:
            bpy.data.window_managers["WinMan"].ml_active_object_modifier_active_index = self.mod_index
        except:
            pass 
        
        
        self.count = bpy.context.object.modifiers[self.mod_index].count
        self.x_factor = bpy.context.object.modifiers[self.mod_index].relative_offset_displace[0]
        self.y_factor = bpy.context.object.modifiers[self.mod_index].relative_offset_displace[1]
        self.z_factor = bpy.context.object.modifiers[self.mod_index].relative_offset_displace[2]

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class EmcScrewModal(bpy.types.Operator):
    """Create a Screw Modifier"""
    bl_idname = "emc.screwmod"
    bl_label = "Screw"
    bl_options = {'REGISTER', 'UNDO'}

    first_mouse_x: bpy.props.IntProperty()
    current_mouse_x: bpy.props.IntProperty()
    screw: bpy.props.FloatProperty()
    angle: bpy.props.IntProperty()
    steps: bpy.props.IntProperty()
    temp_ctrl: bpy.props.FloatProperty()
    temp_norm: bpy.props.FloatProperty()
    temp_alt: bpy.props.FloatProperty()
    temp_last: bpy.props.StringProperty()
    init: bpy.props.BoolProperty()
    edit: bpy.props.BoolProperty()
    wires: bpy.props.BoolProperty()

    def modal(self, context, event):

        if event.type == 'LEFT_CTRL':
            if event.value == 'RELEASE':
                self.current_mouse_x = self.first_mouse_x - event.mouse_x
                self.temp_ctrl = self.current_mouse_x - self.temp_norm
                self.temp_last = "screw"
                # print(self.temp_ctrl)
            if event.value == 'PRESS':
                self.current_mouse_x = self.first_mouse_x - event.mouse_x
                if self.temp_last == "angle":
                    self.temp_norm = self.current_mouse_x - self.temp_alt
                elif self.temp_last == "screw":
                    self.temp_norm = self.current_mouse_x - self.temp_ctrl
                self.temp_last = "steps"
                # print(self.temp_norm)
        
        if event.type == 'LEFT_ALT':
            if event.value == 'RELEASE':
                self.current_mouse_x = self.first_mouse_x - event.mouse_x
                self.temp_alt = self.current_mouse_x - self.temp_norm
                self.temp_last = "angle"
                # print(self.temp_alt)
            if event.value == 'PRESS':
                self.current_mouse_x = self.first_mouse_x - event.mouse_x
                if self.temp_last == "angle":
                    self.temp_norm = self.current_mouse_x - self.temp_alt
                elif self.temp_last == "screw":
                    self.temp_norm = self.current_mouse_x - self.temp_ctrl
                self.temp_last = "steps"
                # print(self.temp_norm)
            
        if event.type == 'MOUSEMOVE':
            delta = self.first_mouse_x - event.mouse_x
            screw = (self.temp_ctrl + (delta - self.current_mouse_x)) * -0.01
            angle = (self.temp_alt + (delta - self.current_mouse_x)) * -0.01
            steps = (self.temp_norm + (delta - self.current_mouse_x)) * -0.05

            if event.ctrl:
                bpy.context.object.modifiers[-1].screw_offset = screw
                # print(self.temp_ctrl + (delta - self.current_mouse_x) -500)

            elif event.alt:
                bpy.context.object.modifiers[-1].angle = angle
                # print(self.temp_ctrl + (delta - self.current_mouse_x))

            else:
                if self.init == True:
                    bpy.context.object.modifiers[-1].steps = 16
                    bpy.context.object.modifiers[-1].render_steps = 16
                    bpy.context.object.modifiers[-1].screw_offset = 0
                    self.init = False
                    
                bpy.context.object.modifiers[-1].steps = steps
                bpy.context.object.modifiers[-1].render_steps = steps
                # print(self.temp_norm + (delta - self.current_mouse_x))
            
        if event.type == 'WHEELUPMOUSE':
            bpy.context.object.modifiers[-1].iterations += 1

        if event.type == 'WHEELDOWNMOUSE':
            bpy.context.object.modifiers[-1].iterations -= 1

        elif event.type == 'S':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].use_smooth_shade = not bpy.context.object.modifiers[-1].use_smooth_shade
            
        elif event.type == 'M':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].use_merge_vertices = not bpy.context.object.modifiers[-1].use_merge_vertices
        
        elif event.type == 'C':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].use_normal_calculate = not bpy.context.object.modifiers[-1].use_normal_calculate
            
        elif event.type == 'F':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].use_normal_flip = not bpy.context.object.modifiers[-1].use_normal_flip

        elif event.type == 'X':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].axis = 'X'
            
        elif event.type == 'Y':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].axis = 'Y'
        
        elif event.type == 'Z':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].axis = 'Z'


        elif event.type in {'MIDDLEMOUSE'}:
            return {'PASS_THROUGH'}

        elif event.type == 'LEFTMOUSE':
            if self.edit == True:
                bpy.ops.object.mode_set(mode='EDIT')
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.context.object.show_wire = self.wires
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
            if self.edit == True:
                bpy.ops.object.mode_set(mode='EDIT')
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.context.object.show_wire = self.wires
            return {'CANCELLED'}
        try:
            context.area.header_text_set(
                "Steps: " + str(bpy.context.object.modifiers[-1].steps) + " | " + 
                "Angle: " + str(round(bpy.context.object.modifiers[-1].angle, 3)) + " | " + 
                "Screw: "  + str(round(bpy.context.object.modifiers[-1].screw_offset, 2)) + " | " + 
                "Calc Order: " + str(bpy.context.object.modifiers[-1].use_normal_calculate) + " | " + 
                "Flip: " + str(bpy.context.object.modifiers[-1].use_normal_flip) + " | " + 
                "Merge: " + str(bpy.context.object.modifiers[-1].use_merge_vertices)
            )
            bpy.types.WorkSpace.status_text_set_internal("Ctrl: Screw | Alt: Angle | C: Calc Order | F: Flip | X/Y/Z: Axis | S: Smooth Shading | M: Merge Vertices")
        except:
            pass
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.first_mouse_x = event.mouse_x
        self.current_mouse_x = 0
        self.init = True
        self.wires = bpy.context.object.show_wire

        bpy.context.object.data.use_auto_smooth = True
        bpy.context.object.show_wire = True

        if bpy.context.object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
            self.edit = True
        else:
            self.edit = False

        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers[-1].use_merge_vertices = True

        my_name = bpy.context.object.modifiers[-1].name
        my_mod = 'modifiers["{}"].steps'.format(my_name)
        create_driver(my_name, 'render_steps', 'var', my_mod)
            
        try:
            bpy.data.window_managers["WinMan"].ml_active_object_modifier_active_index = -1
        except:
            pass  

        self.screw = bpy.context.object.modifiers[-1].screw_offset
        self.angle = bpy.context.object.modifiers[-1].angle
        self.steps = bpy.context.object.modifiers[-1].steps

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class EmcDeformModal(bpy.types.Operator):
    """Create a Simple Deform Modifier"""
    bl_idname = "emc.deformmod"
    bl_label = "Simple Deform"
    bl_options = {'REGISTER', 'UNDO'}

    first_mouse_x: bpy.props.IntProperty()
    current_mouse_x: bpy.props.IntProperty()
    angle: bpy.props.FloatProperty()
    temp_norm: bpy.props.FloatProperty()
    init: bpy.props.BoolProperty()
    edit: bpy.props.BoolProperty()
    wires: bpy.props.BoolProperty()
    obj_origin: bpy.props.StringProperty()
    obj_main: bpy.props.StringProperty()

    def modal(self, context, event):
            
        if event.type == 'MOUSEMOVE':
            delta = self.first_mouse_x - event.mouse_x
            angle = (delta - self.current_mouse_x) * -0.01

            if self.init == True:
                bpy.context.object.modifiers[-1].angle = 0
                self.init = False

            if angle < -2 * math.pi:
                number = -2 * math.pi
            elif angle > 2 * math.pi:
                number = 2 * math.pi
            else:
                number = angle
                
            bpy.context.object.modifiers[-1].angle = number
            bpy.context.object.modifiers[-1].factor = number
            # print(self.temp_norm + (delta - self.current_mouse_x))
            
            
        elif event.type == 'T':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].deform_method = 'TWIST'
            
        elif event.type == 'B':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].deform_method = 'BEND'
        
        elif event.type == 'A':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].deform_method = 'TAPER'
            
        elif event.type == 'S':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].deform_method = 'STRETCH'

        elif event.type == 'W':
            if event.value == 'PRESS':
                bpy.context.object.show_wire = not bpy.context.object.show_wire
        
        elif event.type == 'X':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].deform_axis = 'X'
            if event.shift:
                bpy.context.object.modifiers[-1].lock_x = not bpy.context.object.modifiers[-1].lock_x
            
        elif event.type == 'Y':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].deform_axis = 'Y'
            if event.shift:
                bpy.context.object.modifiers[-1].lock_y = not bpy.context.object.modifiers[-1].lock_y
        
        elif event.type == 'Z':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].deform_axis = 'Z'
            if event.shift:
                bpy.context.object.modifiers[-1].lock_z = not bpy.context.object.modifiers[-1].lock_z


        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        elif event.type == 'LEFTMOUSE':
            if self.edit == True:
                bpy.ops.object.mode_set(mode='EDIT')
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.context.object.show_wire = self.wires
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
            if self.edit == True:
                bpy.ops.object.mode_set(mode='EDIT')
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.context.object.show_wire = self.wires

            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[self.obj_origin].select_set(True)
            bpy.ops.object.delete()

            bpy.data.objects[self.obj_main].select_set(True)

            bpy.context.view_layer.objects.active = bpy.data.objects[self.obj_main]

            if len(bpy.data.collections['EMC Extras'].objects) == 0:
                bpy.data.collections.remove(bpy.data.collections['EMC Extras'])
            return {'CANCELLED'}
        try:
            context.area.header_text_set(
                "Factor: " + str(round(bpy.context.object.modifiers[-1].angle, 3)) + " | " + 
                "Axis: "  + bpy.context.object.modifiers[-1].deform_axis + " | " + 
                "Deform Method: "  + bpy.context.object.modifiers[-1].deform_method
            )
            bpy.types.WorkSpace.status_text_set_internal("X/Y/Z: Axis | Shift + Axis: Lock Axis | T/B/A/S: Deform Method | W: Wireframe")
        except:
            pass
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.first_mouse_x = event.mouse_x
        self.current_mouse_x = 0
        self.init = True
        self.wires = bpy.context.object.show_wire

        bpy.context.object.show_wire = True

        if bpy.context.object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
            self.edit = True
        else:
            self.edit = False

        bpy.ops.view3d.snap_cursor_to_selected()
        bpy.context.scene.cursor.rotation_euler = bpy.context.object.rotation_euler
        active = bpy.context.active_object
        self.obj_main = active.name

        bpy.ops.object.empty_add(type='ARROWS')
        origin = bpy.context.active_object
        origin.name = "Simple Deform Origin"
        self.obj_origin = origin.name
        bpy.ops.transform.rotate(value=-1.5708, orient_axis='X', orient_type='LOCAL')
        bpy.context.object.show_in_front = True

        origin.parent = active
        origin.matrix_parent_inverse = active.matrix_world.inverted()

        bpy.ops.object.select_all(action='DESELECT')
        active.select_set(True)
        bpy.context.view_layer.objects.active = active

        bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
        bpy.context.object.modifiers[-1].deform_method = 'BEND'
        bpy.context.object.modifiers[-1].origin = origin
        bpy.context.object.modifiers[-1].deform_axis = 'Z'

        move_to_col(origin, "EMC Extras", True, True)
            
        try:
            bpy.data.window_managers["WinMan"].ml_active_object_modifier_active_index = -1
        except:
            pass  

        self.angle = bpy.context.object.modifiers[-1].angle

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class EmcSolidifyModal(bpy.types.Operator):
    """Create a Solidify Modifier"""
    bl_idname = "emc.solidifymod"
    bl_label = "Solidify"
    bl_options = {'REGISTER', 'UNDO'}

    first_mouse_x: bpy.props.IntProperty()
    current_mouse_x: bpy.props.IntProperty()
    thickness: bpy.props.FloatProperty()
    offset: bpy.props.FloatProperty()
    temp_ctrl: bpy.props.FloatProperty()
    temp_norm: bpy.props.FloatProperty()
    temp_last: bpy.props.StringProperty()
    edit: bpy.props.BoolProperty()
    wires: bpy.props.BoolProperty()

    def modal(self, context, event):

        if event.type == 'LEFT_CTRL':
            if event.value == 'RELEASE':
                self.current_mouse_x = self.first_mouse_x - event.mouse_x
                self.temp_ctrl = self.current_mouse_x - self.temp_norm
                self.temp_last = "offset"
                # print(self.temp_ctrl)
            if event.value == 'PRESS':
                self.current_mouse_x = self.first_mouse_x - event.mouse_x
                self.temp_norm = self.current_mouse_x - self.temp_ctrl
                self.temp_last = "thickness"
                # print(self.temp_norm)
            
        if event.type == 'MOUSEMOVE':
            delta = self.first_mouse_x - event.mouse_x
            offset = (self.temp_ctrl + (delta - self.current_mouse_x)) * -0.015
            thickness = (self.temp_norm + (delta - self.current_mouse_x)) * -0.015

            if offset < -1:
                used_offset = -1
            elif offset > 1:
                used_offset = 1
            else:
                used_offset = offset

            if event.ctrl:
                bpy.context.object.modifiers[-1].offset = used_offset

            else:
                bpy.context.object.modifiers[-1].thickness = thickness

        elif event.type == 'E':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].use_even_offset = not bpy.context.object.modifiers[-1].use_even_offset
            
        elif event.type == 'H':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].use_quality_normals = not bpy.context.object.modifiers[-1].use_quality_normals
        
        elif event.type == 'R':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].use_rim = not bpy.context.object.modifiers[-1].use_rim

        elif event.type == 'O':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].use_rim_only = not bpy.context.object.modifiers[-1].use_rim_only
            
        elif event.type == 'F':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].use_flip_normals = not bpy.context.object.modifiers[-1].use_flip_normals


        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        elif event.type == 'LEFTMOUSE':
            if self.edit == True:
                bpy.ops.object.mode_set(mode='EDIT')
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.context.object.show_wire = self.wires
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
            if self.edit == True:
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.ops.object.mode_set(mode='EDIT')
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.context.object.show_wire = self.wires
            return {'CANCELLED'}
        
        context.area.header_text_set(
            "Thickness: " + str(round(bpy.context.object.modifiers[-1].thickness, 2)) + " | " + 
            "Offset: " + str(round(bpy.context.object.modifiers[-1].offset, 2)) + " | " + 
            "Flip Normals: "  + str(bpy.context.object.modifiers[-1].use_flip_normals) + " | " + 
            "Even Thickness: " + str(bpy.context.object.modifiers[-1].use_even_offset) + " | " + 
            "High Quality Normals: " + str(bpy.context.object.modifiers[-1].use_quality_normals) + " | " + 
            "Fill Rim: " + str(bpy.context.object.modifiers[-1].use_rim) + " | " + 
            "Only Rim: " + str(bpy.context.object.modifiers[-1].use_rim_only)
        )
        bpy.types.WorkSpace.status_text_set_internal("Ctrl: Offset | F: Flip Normals | E: Even Thickness | H: High Quality Normals | R: Fill Rim | O: Only Rim")
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.first_mouse_x = event.mouse_x
        self.current_mouse_x = 0
        self.wires = bpy.context.object.show_wire

        bpy.context.object.show_wire = True

        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers[-1].offset = 1

        if bpy.context.object.mode == 'EDIT':
            bpy.ops.object.vertex_group_add()
            bpy.context.scene.tool_settings.vertex_group_weight = 1
            bpy.ops.object.vertex_group_assign()
            bpy.context.object.vertex_groups[-1].name = 'EMC Solidify'
            bpy.context.object.modifiers[-1].vertex_group = bpy.context.object.vertex_groups[-1].name
            bpy.context.object.modifiers[-1].thickness_vertex_group = 0.001
            bpy.ops.object.mode_set(mode='OBJECT')
            self.edit = True
        else:
            self.edit = False
            
        try:
            bpy.data.window_managers["WinMan"].ml_active_object_modifier_active_index = -1
        except:
            pass  

        self.screw = bpy.context.object.modifiers[-1].thickness
        self.angle = bpy.context.object.modifiers[-1].offset

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class EmcWeightedNormals(bpy.types.Operator):
    """Refresh modifier stack with a new Weighted Normals modifier"""
    bl_label = "Refresh Weighted Normals"
    bl_idname = "emc.weightmod"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        og = bpy.context.selected_objects
        sharp = False
        mode = 'FACE_AREA_WITH_ANGLE'

        for obj in og:
            for modifier in obj.modifiers:
                if modifier.type == 'BEVEL':
                    modifier.harden_normals = False
                elif modifier.type == 'WEIGHTED_NORMAL':
                    sharp = modifier.keep_sharp
                    mode = modifier.mode
                    bpy.ops.object.modifier_remove(modifier=modifier.name)
        
        bpy.ops.object.modifier_add(type='WEIGHTED_NORMAL')
        bpy.context.object.modifiers[-1].keep_sharp = sharp
        bpy.context.object.modifiers[-1].mode = mode
        bpy.context.object.data.use_auto_smooth = True
        bpy.context.object.modifiers[-1].show_expanded = False

        return{'FINISHED'}

class EmcDisplaceModal(bpy.types.Operator):
    """Create a Displace Modifier"""
    bl_idname = "emc.displacemod"
    bl_label = "Displace"
    bl_options = {'REGISTER', 'UNDO'}

    first_mouse_x: bpy.props.IntProperty()
    current_mouse_x: bpy.props.IntProperty()
    strength: bpy.props.FloatProperty()
    temp_norm: bpy.props.FloatProperty()
    edit: bpy.props.BoolProperty()
    wires: bpy.props.BoolProperty()
    v_group: bpy.props.BoolProperty()

    def modal(self, context, event):
            
        if event.type == 'MOUSEMOVE':
            delta = self.first_mouse_x - event.mouse_x
            strength = (self.temp_norm + (delta - self.current_mouse_x)) * -0.02

            bpy.context.object.modifiers[-1].strength = strength

        elif event.type == 'X':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].direction = 'X'
            
        elif event.type == 'Y':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].direction = 'Y'
        
        elif event.type == 'Z':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].direction = 'Z'

        elif event.type == 'N':
            if event.value == 'PRESS':
                bpy.context.object.modifiers[-1].direction = 'NORMAL'
            
        elif event.type == 'W':
            if event.value == 'PRESS':
                bpy.context.object.show_wire = not bpy.context.object.show_wire

        elif event.type == 'S':
            if event.value == 'PRESS':
                if bpy.context.object.modifiers[-1].space == 'GLOBAL':
                    bpy.context.object.modifiers[-1].space = 'LOCAL'
                else:
                    bpy.context.object.modifiers[-1].space = 'GLOBAL'


        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        elif event.type == 'LEFTMOUSE':
            if self.edit == True:
                bpy.ops.object.mode_set(mode='EDIT')
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.context.object.show_wire = self.wires
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[-1].name)
            if self.edit == True:
                bpy.ops.object.mode_set(mode='EDIT')
            if self.v_group == True:
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            context.area.header_text_set(None)
            bpy.types.WorkSpace.status_text_set_internal(None)
            bpy.context.object.show_wire = self.wires
            return {'CANCELLED'}
        
        context.area.header_text_set(
            "Strength: " + str(round(bpy.context.object.modifiers[-1].strength, 2)) + " | " + 
            "Direction: " + str(bpy.context.object.modifiers[-1].direction) + " | " + 
            "Space: "  + str(bpy.context.object.modifiers[-1].space)
        )
        bpy.types.WorkSpace.status_text_set_internal("X/Y/Z/N: Direction | S: Space")
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.first_mouse_x = event.mouse_x
        self.current_mouse_x = 0
        self.wires = bpy.context.object.show_wire
        self.v_group = False

        bpy.ops.object.modifier_add(type='DISPLACE')
        bpy.context.object.modifiers[-1].direction = 'X'

        if bpy.context.object.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(context.edit_object.data)
            selected_verts = [vertex for vertex in bm.verts if vertex.select]
            if len(selected_verts) > 0:
                bpy.ops.object.vertex_group_add()
                bpy.context.scene.tool_settings.vertex_group_weight = 1
                bpy.ops.object.vertex_group_assign()
                bpy.context.object.vertex_groups[-1].name = 'EMC Displace'
                bpy.context.object.modifiers[-1].vertex_group = bpy.context.object.vertex_groups[-1].name
                bpy.context.object.modifiers[-1].show_in_editmode = True
                bpy.context.object.modifiers[-1].show_on_cage = True

                self.v_group = True
            bpy.ops.object.mode_set(mode='OBJECT')
            self.edit = True
        else:
            self.edit = False
            
        try:
            bpy.data.window_managers["WinMan"].ml_active_object_modifier_active_index = -1
        except:
            pass  

        self.strength = bpy.context.object.modifiers[-1].strength

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class UvSelect(bpy.types.Operator):
    """Select edges by islands or seams"""
    bl_label = "Select by UV Info"
    bl_idname = "emc.uvselect"
    bl_options = {'REGISTER', 'UNDO'}

    select: bpy.props.EnumProperty(
        name="Select by",
        items=(("seam", "Seams", "Select geometry based on seams"),
               ("island", "Islands", "Select geometry based on islands")),
        description="Method used to select edges",
        default='island'
        )

    mark_seams: bpy.props.BoolProperty(
        name = "Mark Seams", 
        default = False,
    )

    mark_sharp: bpy.props.BoolProperty(
        name = "Mark Sharp", 
        default = False,
    )

    smooth: bpy.props.BoolProperty(
        name = "Setup Autosmooth", 
        description = "Set Autosmooth Angle to 180d", 
        default = False,
    )

    def execute(self, context):
        orig_mode = bpy.context.object.mode
        orig_sync = bpy.context.scene.tool_settings.use_uv_select_sync
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bm = bmesh.from_edit_mesh(bpy.context.active_object.data)

        og_seams = [edge for edge in bm.edges if edge.seam]

        if self.smooth:
            bpy.context.object.data.auto_smooth_angle = math.pi
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.faces_shade_smooth()

        if self.select == 'island':
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.mark_seam(clear=True)
            bpy.context.scene.tool_settings.use_uv_select_sync = True
            bpy.ops.uv.seams_from_islands()
            island_borders = [edge for edge in bm.edges if edge.seam]
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.mark_seam(clear=True)
            bpy.ops.mesh.select_all(action='DESELECT')

            for i in island_borders:
                i.select = True

        else:
            bpy.ops.mesh.select_all(action='DESELECT')
            for i in og_seams:
                i.select = True

        if self.mark_seams:
            bpy.ops.mesh.mark_seam(clear=False)
        else:
            for i in bm.edges:
                if i.select:
                    i.seam = False

            for i in og_seams:
                i.seam = True

        if self.mark_sharp:
            bpy.ops.mesh.mark_sharp()

        bpy.context.object.data.use_auto_smooth = self.smooth

        bpy.context.scene.tool_settings.use_uv_select_sync = orig_sync
        bpy.ops.object.mode_set(mode=orig_mode)
        return{'FINISHED'}

class FaceMapsUV(bpy.types.Operator):
    """Creates Face Maps from UV Islands"""
    bl_label = "Face Maps from UV Islands"
    bl_idname = "emc.islandmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        og = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')

        for obj in og:
            orig_mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
            orig_len = len(obj.face_maps)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            bpy.context.scene.tool_settings.uv_select_mode = 'FACE'
            bpy.context.scene.tool_settings.use_uv_select_sync = True

            all_faces = [face for face in bm.faces]
            obj.face_maps.active_index = len(obj.face_maps)-1

            num_o_times = 0

            while len(all_faces) > 0:
                try:
                    all_faces[0].select = True
                    bpy.ops.uv.select_linked()
                    bpy.ops.object.face_map_add()
                    bpy.ops.object.face_map_assign()
                    obj.face_maps[num_o_times+(orig_len)].name = "UV_Island_" + str(num_o_times+1)

                    selected = [face for face in bm.faces if face.select]
                    for i in selected:
                        all_faces.remove(i)
                    bpy.ops.mesh.select_all(action='DESELECT')
                    num_o_times += 1
                except:
                    bpy.ops.object.face_map_remove()
                    break
                
            # obj.face_maps[num_o_times+(orig_len-1)].name = "UV_Island"
            bpy.ops.object.mode_set(mode=orig_mode)
            if len(og) > 1:
                bpy.ops.object.select_all(action='DESELECT')
        return{'FINISHED'}

class UVselectMode(bpy.types.Operator):
    """UV Editor component select modes"""
    bl_label = "UV Editor select mode"
    bl_idname = "emc.uvselectmode"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        name="Select Mode",
        items=(("VERTEX", "Vertex", "Vertex Select"),
               ("EDGE", "Edge", "Edge Select"),
               ("FACE", "Face", "Face Select"),
               ("ISLAND", "Island", "Island Select"),
               ("SYNC", "Sync", "Sync Selection")),
        description="UV Editor component select modes",
        default='VERTEX'
        )

    def execute(self, context):
        if self.mode == 'SYNC':
            bpy.context.scene.tool_settings.use_uv_select_sync = not bpy.context.scene.tool_settings.use_uv_select_sync
        else:
            bpy.context.scene.tool_settings.uv_select_mode = self.mode
        return{'FINISHED'}

class MoveIsland(bpy.types.Operator):
    """move selected islands by a factor individually"""
    bl_label = "Move Selected Islands"
    bl_idname = "emc.moveislands"
    bl_options = {'REGISTER', 'UNDO'}

    factor: bpy.props.FloatProperty(
        name = "Factor", 
        description = "Gradual Factor", 
        default = 0,
        soft_min = -1, soft_max = 1,
    )

    axis: bpy.props.BoolProperty(
        name = 'U/V axis',
        description = "True = U, False = V", 
        default = True,
    )


    def execute(self, context):
        bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
        bpy.context.tool_settings.mesh_select_mode[2]

        # try:
        #     bpy.ops.uvpackmaster2.uv_select_similar()
        #     bpy.ops.uvpackmaster2.uv_align_similar()
        # except:
        #     pass

        bpy.ops.object.vertex_group_add()
        bpy.context.scene.tool_settings.vertex_group_weight = 1
        bpy.ops.object.vertex_group_assign()

        og_selected = [face for face in bm.faces if face.select]  
        num_o_times = 0
        
        if bpy.context.scene.tool_settings.use_uv_select_sync:
            while len(og_selected) > 0:
                for i in range(0, len(og_selected)):
                    try:
                        bpy.ops.uv.select_all(action='DESELECT')
                        og_selected[0].select = True
                        bpy.ops.uv.select_linked()
                        bpy.ops.transform.translate(value=((num_o_times*self.factor if self.axis else 0), (num_o_times*self.factor if not self.axis else 0), 0))

                        selected = [face for face in bm.faces if face.select]
                        for i in selected:
                            try:
                                og_selected.remove(i)
                            except:
                                pass
                        num_o_times += 1
                    except:
                        break

        else:
            self.report({"ERROR"}, "UV Sync must be on!")

        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
        return{'FINISHED'}

class BuildCorner(bpy.types.Operator):
    """Create corner topology from a selected edge between a triangle and a pentagon"""
    bl_label = "Build Corner"
    bl_idname = "emc.buildcorner"
    bl_options = {'REGISTER', 'UNDO'}

    angle: bpy.props.FloatProperty(
        name = "Face Angle", 
        description = "Maximum Face Angle", 
        default = 180.0,
        min = 0.0, max = 180.0,
        subtype = 'FACTOR',
    )

    o_angle: bpy.props.FloatProperty(
        name = "Shape Angle", 
        description = "Maximum Shape Angle", 
        default = 180.0,
        min = 0.0, max = 180.0,
        subtype = 'FACTOR',
    )

    def execute(self, context):
        og_mode = bpy.context.tool_settings.mesh_select_mode[:]
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')

        bpy.ops.mesh.subdivide(number_cuts=1)

        bpy.ops.mesh.select_less(use_face_step=False)
        bpy.ops.mesh.select_more(use_face_step=True)
            
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        bpy.ops.mesh.select_less(use_face_step=False)
        bpy.ops.mesh.vertices_smooth(factor=1)
        bpy.ops.mesh.select_more(use_face_step=True)
        bpy.ops.mesh.tris_convert_to_quads(face_threshold=(self.angle * (math.pi/180)), shape_threshold=(self.o_angle * (math.pi/180)))

        bpy.ops.mesh.select_less(use_face_step=False)

        bpy.context.tool_settings.mesh_select_mode[:] = og_mode
        return{'FINISHED'}

class PanelLines(bpy.types.Operator):
    """Create panel line separation on selected vertices (ONLY ACTIVATE ONCE. To add more lines, add vertices to the Panel Lines vertex group)"""
    bl_label = "Panel Lines"
    bl_idname = "emc.panellines"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.vertex_group_assign_new()
        bpy.context.object.vertex_groups[-1].name = 'EMC Panel Lines'

        bpy.ops.object.modifier_add(type='BEVEL')
        bpy.context.object.modifiers[-1].width = 0.0005
        bpy.context.object.modifiers[-1].segments = 2
        bpy.context.object.modifiers[-1].profile = 1
        bpy.context.object.modifiers[-1].limit_method = 'VGROUP'
        bpy.context.object.modifiers[-1].vertex_group = bpy.context.object.vertex_groups[-1].name

        bpy.ops.emc.addmod(modifier='VERTEX_WEIGHT_EDIT')
        bpy.context.object.modifiers[-1].show_in_editmode = True
        bpy.context.object.modifiers[-1].show_expanded = False

        bpy.ops.object.modifier_add(type='MASK')
        bpy.context.object.modifiers[-1].vertex_group = bpy.context.object.vertex_groups[-1].name
        bpy.context.object.modifiers[-1].invert_vertex_group = True
        bpy.context.object.modifiers[-1].show_in_editmode = True
        bpy.context.object.modifiers[-1].show_expanded = False

        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers[-1].use_rim_only = True
        bpy.context.object.modifiers[-1].thickness = 0.01

        bpy.ops.object.modifier_add(type='BEVEL')
        bpy.context.object.modifiers[-1].segments = 4
        bpy.context.object.modifiers[-1].profile = 0.5
        bpy.context.object.modifiers[-1].limit_method = 'ANGLE'
        bpy.context.object.modifiers[-1].angle_limit = 1.53589
        bpy.context.object.modifiers[-1].miter_outer = 'MITER_ARC'
        bpy.context.object.modifiers[-1].use_clamp_overlap = False
        bpy.context.object.modifiers[-1].width = 0.005

        bpy.ops.emc.weightmod()

        bpy.ops.emc.addmod(modifier='TRIANGULATE')
        bpy.context.object.modifiers[-1].show_expanded = False

        return{'FINISHED'}

class Purge(bpy.types.Operator):
    """Purge selected data types"""
    bl_label = "Purge"
    bl_idname = "emc.purge"
    bl_options = {'REGISTER', 'UNDO'}

    drivers: bpy.props.BoolProperty(
        name = "Drivers", 
        description = "Delete All drivers on selected object", 
        default = False
    )

    face_maps: bpy.props.BoolProperty(
        name = "Face Maps", 
        description = "Delete All Face Maps on selected object", 
        default = False
    )

    props: bpy.props.BoolProperty(
        name = "Custom Properties", 
        description = "Delete All Custom Properties on selected object (with the exception of cycles and _RNA_UI)", 
        default = False
    )

    def execute(self, context):
        for x in bpy.context.selected_objects:
            if self.drivers:
                delete_drivers()
            if self.face_maps:
                for i in x.face_maps:
                    x.face_maps.active_index = 0
                    bpy.ops.object.face_map_remove()
            if self.props:
                for i in x.keys():
                    if i == '_RNA_UI' or i == 'cycles':
                        pass
                    else:
                        del x[i]
        return{'FINISHED'}

class CustomNormals(bpy.types.Operator):
    """Add or Clear Custom Split Normals"""
    bl_label = "Add/Clear Custom Split Normals"
    bl_idname = "emc.customnormals"
    bl_options = {'REGISTER', 'UNDO'}

    whattodo: bpy.props.EnumProperty(
        name="Add/Clear",
        items=(("clear", "Clear", "Clear custom split normals from selected object(s)"),
               ("add", "Add", "Add custom split normals from selected object(s)")),
        description="Add or Clear custom split normals",
        default='clear'
        )

    def execute(self, context):
        selected = bpy.context.selected_objects
        active = bpy.context.active_object

        for i in selected:
            bpy.ops.object.select_all(action='DESELECT')
            i.select_set(True)
            bpy.context.view_layer.objects.active = i
            if self.whattodo == "clear":
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
            else:
                bpy.ops.mesh.customdata_custom_splitnormals_add()

        for i in selected:
            i.select_set(True)
        bpy.context.view_layer.objects.active = active
        return{'FINISHED'}

class SelLinked(bpy.types.Operator):
    """Select linked components/loops based on selection mode"""
    bl_label = "Select Linked Plus"
    bl_idname = "emc.sellink"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, True, False):
            bpy.ops.mesh.loop_multi_select(ring=False)
        elif tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, False, True):
            bpy.ops.mesh.select_linked(delimit={'UV'})
        else:
            bpy.ops.mesh.select_linked(delimit={'NORMAL'})
        return{'FINISHED'}


class AddModifierCustom(bpy.types.Operator):
    """Add various modifiers with some custom default parameters set"""
    bl_label = "Add Modifier Custom"
    bl_idname = "emc.addmod"
    bl_options = {'REGISTER', 'UNDO'}

    modifier: bpy.props.EnumProperty(
        name="Modifier",
        items=(("DECIMATE", "Decimate", "Decimate Modifier"),
               ("DATA_TRANSFER", "Data Transfer", "Data Transfer Modifier"),
               ("SHRINKWRAP", "Shrinkwrap", "Shrinkwrap Modifier"),
               ("MESH_DEFORM", "Mesh Deform", "Mesh Deform Modifier"),
               ("TRIANGULATE", "Triangulate", "Triangulate Modifier"),
               ("VERTEX_WEIGHT_EDIT", "Vertex Weight Edit", "Vertex Weight Edit Modifier"),
               ("CAST", "Cast", "Cast Modifier")),
        description="Modifiers with custom set parameters",
        default='DECIMATE'
        )

    def execute(self, context):
        objs = bpy.context.selected_objects
        active = bpy.context.active_object
        objs.remove(active)

        if self.modifier == "DECIMATE":
            bpy.ops.object.modifier_add(type=self.modifier)
            bpy.context.object.modifiers[-1].decimate_type = 'DISSOLVE'
            bpy.context.object.modifiers[-1].angle_limit = 0.0174533
            
        elif self.modifier == "DATA_TRANSFER":
            bpy.ops.object.modifier_add(type=self.modifier)
            try:
                bpy.context.object.modifiers[-1].object = objs[0]
            except:
                self.report({"INFO"}, "Selected object can be used as target")

        elif self.modifier == "SHRINKWRAP":
            bpy.ops.object.modifier_add(type=self.modifier)
            bpy.context.object.modifiers[-1].wrap_method = 'PROJECT'
            bpy.context.object.modifiers[-1].use_negative_direction = True
            try:
                bpy.context.object.modifiers[-1].target = objs[0]
            except:
                self.report({"INFO"}, "Selected object can be used as target")

        elif self.modifier == "MESH_DEFORM":
            bpy.ops.object.modifier_add(type=self.modifier)
            bpy.ops.object.meshdeform_bind(modifier=bpy.context.object.modifiers[-1].name)
            try:
                bpy.context.object.modifiers[-1].object = objs[0]
            except:
                self.report({"INFO"}, "Selected object can be used as target")

        elif self.modifier == "TRIANGULATE":
            bpy.ops.object.modifier_add(type=self.modifier)
            bpy.context.object.modifiers[-1].keep_custom_normals = True
            bpy.context.object.modifiers[-1].min_vertices = 5

        elif self.modifier == "VERTEX_WEIGHT_EDIT":
            bpy.ops.object.modifier_add(type=self.modifier)
            bpy.context.object.modifiers[-1].use_remove = True
            bpy.context.object.modifiers[-1].remove_threshold = 1
            try:
                bpy.context.object.modifiers[-1].vertex_group = bpy.context.object.vertex_groups[-1].name
                self.report({"INFO"}, "Last Vertex Group selected as target")
            except:
                self.report({"WARNING"}, "No Vertex Groups")

        else:
            bpy.ops.object.modifier_add(type='CAST')
            bpy.context.object.modifiers[-1].factor = 1
        return{'FINISHED'}


#-------------------------------------------------------------------
#Secondary Menus

class Smoothing(Menu):
    """Soften/Harden Edges"""
    bl_label = 'Smoothing'    
    bl_idname = 'emc.smoothing'
    bl_description = "Soften/Harden Edges"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        if bpy.context.object.mode == 'EDIT':
            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie.operator("emc.anglesharp", text="Mark Sharp by Angle", icon = "ALIASED")

            if bpy.context.space_data.overlay.show_edge_sharp == True:
                pie.operator("wm.context_toggle", text="Sharp Display", depress =True, icon = "FILE_3D").data_path="space_data.overlay.show_edge_sharp"
            else:
                pie.operator("wm.context_toggle", text="Sharp Display", depress =False, icon = "FILE_3D").data_path="space_data.overlay.show_edge_sharp"

            pie.operator("emc.facemapsharp", icon = "FACE_MAPS")

            pie.operator("emc.uvselect", text = 'Mark Sharp by Island Bounds', icon = "GROUP_UVS").mark_sharp = True

            pie.operator("emc.smooth", text="Clear Sharp", icon = "ANTIALIASED")

            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie.operator("emc.flat", text="Mark Sharp", icon = "SEQ_CHROMA_SCOPE")

        else:
            pie.operator("emc.smoothangle", text="Set Autosmooth Angle", icon = "SNAP_PERPENDICULAR")
            if bpy.context.object.data.use_auto_smooth == True:
                pie.operator("emc.autosmooth", depress=True, icon = "ALIASED")
            else:
                pie.operator("emc.autosmooth", depress=False, icon = "ALIASED")

            pie.operator("emc.customnormals", text="Clear Custom Split Normals", icon = "REMOVE").whattodo = 'clear'

            pie.operator("emc.customnormals", text="Add Custom Split Normals", icon = "ADD").whattodo = 'add'

            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie.operator("emc.smooth", icon = "ANTIALIASED")
            
            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie.operator("emc.flat", icon = "SEQ_CHROMA_SCOPE")

class Gears(Menu):
    bl_label = 'Gears'    
    bl_idname = 'emc.gears'
    bl_description = "Options for Two Gear Primitives"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.operator("mesh.primitive_gear", icon = "PREFERENCES")
        pie.operator("mesh.primitive_worm_gear", icon = "LIGHT_SUN")

class VIEW3D_MT_merge(Menu):
    bl_label = "EMC Merge"
    bl_idname = "Mesh.EMC_MT_Merge"
    bl_options = {'REGISTER', 'UNDO'}


    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        pie.operator("mesh.remove_doubles", icon='SNAP_INCREMENT')
        pie.operator("mesh.merge", text='Merge at Cursor', icon='CURSOR').type='CURSOR'
        pie.operator("mesh.merge", text='Collapse', icon='SNAP_FACE_CENTER').type='COLLAPSE'
        pie.operator("mesh.merge", text='Merge at Center', icon='SNAP_MIDPOINT').type='CENTER'
        
        if bmesh_vert_active(bmesh.from_edit_mesh(bpy.context.object.data)) == None:
            pass
        else:
            pie.operator("mesh.merge", text='Merge at First', icon='BACK').type='FIRST'
            pie.operator("mesh.merge", text='Merge at Last', icon='FORWARD').type='LAST'

class VertNorm(Menu):
    '''Options for Normals'''
    bl_label = 'Normals'    
    bl_idname = 'emc.vertnorm'
    bl_description = "Options for Normals"
    bl_options = {'REGISTER', 'UNDO'}


    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (True, False, False):
            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie.operator("transform.rotate_normal", icon = "ORIENTATION_GIMBAL")
            if bpy.context.space_data.overlay.show_split_normals == True:
                pie.operator("wm.context_toggle", text="Vertex Normal View", depress =True, icon = "NORMALS_VERTEX").data_path="space_data.overlay.show_split_normals"
            else:
                pie.operator("wm.context_toggle", text="Vertex Normal View", depress =False, icon = "NORMALS_VERTEX").data_path="space_data.overlay.show_split_normals"


            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie.operator("mesh.normals_make_consistent", icon = "CON_FOLLOWPATH").inside=False

            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie.operator("mesh.set_normals_from_faces", icon = "ORIENTATION_NORMAL").keep_sharp=True
        else:
            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie.operator("mesh.flip_normals", icon = "UV_SYNC_SELECT")
            if bpy.context.space_data.overlay.show_face_normals == True:
                pie.operator("wm.context_toggle", text="Face Normal View", depress =True, icon = "NORMALS_FACE").data_path="space_data.overlay.show_face_normals"
            else:
                pie.operator("wm.context_toggle", text="Face Normal View", depress =False, icon = "NORMALS_FACE").data_path="space_data.overlay.show_face_normals"
            pie.operator("mesh.normals_make_consistent", text='Recalculate Inside', icon = "FULLSCREEN_EXIT").inside=True


            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie.operator("emc.propreverse", icon = "DECORATE_OVERRIDE")

            pie = pie.row()
            pie.label(text='')
            pie = layout.menu_pie()

            pie.operator("mesh.normals_make_consistent", icon = "CON_FOLLOWPATH").inside=False

class RotEdge(Menu):
    bl_label = 'Rotate Edge'    
    bl_idname = 'emc.rotedge'
    bl_description = "Options for rotating an edge clockwise and counter clockwise"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        
        pie.operator("mesh.edge_rotate", text='Rotate Counter Clockwise', icon = "RECOVER_LAST").use_ccw=True
        pie.operator("mesh.edge_rotate", text='Rotate Clockwise', icon = "TIME").use_ccw=False

class BoolMenu(Menu):
    bl_label = 'EMC Booleans'    
    bl_idname = 'emc.boolmenu'
    bl_description = "EMC Booleans Options"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        
        pie.operator("emc.bool", text = "Difference", icon='SELECT_SUBTRACT').operation = "diff"
        pie.operator("emc.bool", text = "Union", icon='SELECT_EXTEND').operation = "uni"
        pie.operator("emc.bool", text = "Intersection", icon='SELECT_INTERSECT').operation = "inter"
        pie.operator("emc.bool", text = "Slice", icon='SELECT_DIFFERENCE').operation = "slice"

class EmcSymmetry(Menu):
    bl_label = 'Symmetry'    
    bl_idname = 'emc.symmetry'
    bl_description = "Symmetry Options for Edit Mode"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        pie = pie.row()
        pie.label(text='')
        pie = layout.menu_pie()

        pie = pie.row()
        pie.label(text='')
        pie = layout.menu_pie()

        if bpy.context.object.data.use_mirror_y == True:
            pie.operator("wm.context_toggle", text='Y Mirror', depress=True, icon='CHECKBOX_HLT').data_path="object.data.use_mirror_y"
        else:
            pie.operator("wm.context_toggle", text='Y Mirror', depress=False, icon='EVENT_Y').data_path="object.data.use_mirror_y"

        if bpy.context.object.data.use_mirror_topology == True:
            pie.operator("wm.context_toggle", text='Topology Mirror', depress=True, icon='CHECKBOX_HLT').data_path="object.data.use_mirror_topology"
        else:
            pie.operator("wm.context_toggle", text='Topology Mirror', depress=False, icon='CHECKBOX_DEHLT').data_path="object.data.use_mirror_topology"

        pie = pie.row()
        pie.label(text='')
        pie = layout.menu_pie()

        pie = pie.row()
        pie.label(text='')
        pie = layout.menu_pie()
        
        if bpy.context.object.data.use_mirror_x == True:
            pie.operator("wm.context_toggle", text='X Mirror', depress=True, icon='CHECKBOX_HLT').data_path="object.data.use_mirror_x"
        else:
            pie.operator("wm.context_toggle", text='X Mirror', depress=False, icon='EVENT_X').data_path="object.data.use_mirror_x"

        if bpy.context.object.data.use_mirror_z == True:
            pie.operator("wm.context_toggle", text='Z Mirror', depress=True, icon='CHECKBOX_HLT').data_path="object.data.use_mirror_z"
        else:
            pie.operator("wm.context_toggle", text='Z Mirror', depress=False, icon='EVENT_Z').data_path="object.data.use_mirror_z"


#-------------------------------------------------------------------
#Just Shortcuts

class ToggleSubD(bpy.types.Operator):
    """Toggle all SubD Modifier Viewport Visibility. If none exist, one will be added"""
    bl_label = "Toggle SubD"
    bl_idname = "emc.togglesubd"
    bl_options = {'REGISTER', 'UNDO'}

    showViewport: bpy.props.EnumProperty(
        name="Viewport Visibility",
        items=(("toggle", "Toggle", "Toggle Visibility"),
               ("on", "ON", "Enable Visibility"),
               ("off", "OFF", "Disable Visibility")),
        description="Visibility Options",
        default='toggle'
        )

    cage: bpy.props.BoolProperty(
        name = "Edit Mode Visibility", 
        description = "Affect Edit Mode Visibility", 
        default = False
    )

    showCage: bpy.props.EnumProperty(
        name="Edit Mode Visibility",
        items=(("toggle", "Toggle", "Toggle Visibility"),
               ("on", "ON", "Enable Visibility"),
               ("off", "OFF", "Disable Visibility")),
        description="Visibility Options",
        default='off'
        )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "showViewport")
        row = layout.row(align=True)
        row.prop(self, "cage")
        row = layout.row(align=True)
        row.active = self.cage
        row.prop(self, "showCage")
    
    def execute(self, context):
        og = bpy.context.selected_objects
        has = False

        for obj in og:
            for modifier in obj.modifiers:
                if modifier.type == 'SUBSURF':
                    has = True
                    if self.showViewport == "on":
                        modifier.show_viewport = True
                        modifier.show_in_editmode = True
                    elif self.showViewport == "off":
                        modifier.show_viewport = False
                        modifier.show_in_editmode = False
                    else:
                        if modifier.show_viewport == False:
                            modifier.show_viewport = True
                            modifier.show_in_editmode = True
                        else:
                            modifier.show_viewport = False
                            modifier.show_in_editmode = False

                    if self.showCage == "on":
                        modifier.show_on_cage = True
                    elif self.showCage == "off":
                        modifier.show_on_cage = False
                    else:
                        if modifier.show_on_cage == False:
                            modifier.show_on_cage = True
                        else:
                            modifier.show_on_cage = False
                            modifier.show_in_editmode = False
        
        if has == False:
            bpy.ops.object.modifier_add(type='SUBSURF')
            bpy.context.object.modifiers[-1].levels = 2
            bpy.context.object.modifiers[-1].show_only_control_edges = False
            bpy.context.object.modifiers[-1].show_viewport = True if self.showViewport == "on" else False
            bpy.context.object.modifiers[-1].show_in_editmode = True if self.showViewport == "on" else False
            bpy.context.object.modifiers[-1].show_on_cage = True if self.showCage == "on" else False

        return{'FINISHED'}

class KeyframeDel(bpy.types.Operator):
    """Delete keyframes without question"""
    bl_label = "Delete Keyframe(s)"
    bl_idname = "emc.keyframedel"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.graph.delete()
        return{'FINISHED'}


#-------------------------------------------------------------------
#Blender required stuff

class PreferencesNotes(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    looptools: bpy.props.BoolProperty(name = 'Loop Tools')
    extraObjects: bpy.props.BoolProperty(name = 'Extra Objects')
    f2: bpy.props.BoolProperty(name = 'F2')
    editmesh: bpy.props.BoolProperty(name = 'Edit Mesh Tools')
    material: bpy.props.BoolProperty(name = 'Material Utilities')
    polyquilt: bpy.props.BoolProperty(name = 'PolyQuilt')

    def draw(self, context):
        layout = self.layout
        layout.label(text='DISCLAIMER: The buttons below are just there to show the current status of the addon')
        layout.label(text="they don't actually do anything!")
        layout.label(text='MAKE SURE TO ENABLE THE UNCHECKED ADDONS:')
        layout.prop(self, "looptools")
        layout.prop(self, "extraObjects")
        layout.prop(self, "f2")
        layout.prop(self, "editmesh")
        layout.prop(self, "material")
        layout.label(text='- OPTIONAL EXTERNAL ADDON')
        layout.prop(self, "polyquilt")
        row = layout.row()
        layout.label(text='Search for "EMC" in the Keymap Editor for All Available Shortcuts')
        layout.label(text='IMPORTANT! The Default Shortcuts are Based on the Ones Found in Maya. I Encourage you to Re-Assign Your Own Shortcuts!')

class Nothing(bpy.types.Operator):
    """Nothing Here Jimbo"""
    bl_label = "Nothing"
    bl_idname = "emc.null"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        self.report({"ERROR"}, "Action(s) Unavailable")
        return{'FINISHED'}


classes = (
    VIEW3D_MT_merge,
    VIEW3D_MT_selectMode,
    VIEW3D_MT_Context,
    VIEW3D_MT_EditContext,
    VIEW3D_MT_customMenu, 
    VIEW3D_MT_Extras,  
    VIEW3D_MT_EmcModifiers,
    VIEW3D_MT_uvMenu,
    Gears,
    Helix,
    Pipe,
    Prism,
    Mobius,
    PolyDraw,
    Knife,
    OffsetEdge,
    Extrude,
    Spin,
    EdgeSlide,
    LoopCut,
    KnifeProject,
    Weld,
    VertexM,
    EdgeM,
    FaceM,
    MultiM,
    VertFaceM,
    FillHoles,
    Smooth,
    Flat,
    Smoothing,
    Autosmooth,
    SmoothAngle,
    MarkSharp,
    EmcUV,
    SelHier,
    SelSim,
    ExtrudeVert,
    VertNorm,
    RotEdge,
    PropReverse,
    SmoothFaces,
    EmcMirror,
    ProjectCurve,
    Separate,
    EmcTris,
    BoolMenu,
    EmcCage,
    EmcHoleLoop,
    LocalOr,
    GlobalOr,
    NormalOr,
    GimbalOr,
    EmcSymmetry,
    CheckerLoop,
    EMCpatch,
    EmcRepeat,
    PreferencesNotes,
    Reset,
    FaceMapSharp,
    FaceMapsMaterial,
    EMCsplit,
    ToggleSubD,
    addCylinder,
    addPlane,
    addCube,
    addCircle,
    addCone,
    addSphere,
    addTorus,
    EmcBevelModal,
    EmcArrayModal,
    KeyframeDel,
    EMCbool,
    EmcScrewModal,
    EmcDeformModal,
    EmcSolidifyModal,
    EmcWeightedNormals,
    EmcDisplaceModal,
    AddModifierCustom,
    UvSelect,
    FaceMapsUV,
    Nothing,
    UVselectMode,
    MoveIsland,
    BuildCorner,
    PanelLines,
    Purge,
    CustomNormals,
    SelLinked,
)

addon_keymaps = []

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    if 'mesh_looptools' in bpy.context.preferences.addons.keys():
        bpy.context.preferences.addons[__name__].preferences.looptools = True

    if 'add_mesh_extra_objects' in bpy.context.preferences.addons.keys():
        bpy.context.preferences.addons[__name__].preferences.extraObjects = True

    if 'mesh_f2' in bpy.context.preferences.addons.keys():
        bpy.context.preferences.addons[__name__].preferences.f2 = True

    if 'mesh_tools' in bpy.context.preferences.addons.keys():
        bpy.context.preferences.addons[__name__].preferences.editmesh = True
    
    if 'materials_utils' in bpy.context.preferences.addons.keys():
        bpy.context.preferences.addons[__name__].preferences.material = True

    if 'PolyQuilt' in bpy.context.preferences.addons.keys():
        bpy.context.preferences.addons[__name__].preferences.polyquilt = True


    wm = bpy.context.window_manager  

    km = wm.keyconfigs.addon.keymaps.new(name="Mesh")
    
    # kmi = km.keymap_items.new("wm.call_menu_pie", "X", "PRESS", shift=True)
    # kmi.properties.name="Mesh.EMC_MT_Merge"
    # addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("wm.call_menu_pie", "RIGHTMOUSE", "CLICK_DRAG", shift=True)
    kmi.properties.name="Mesh.EMC_MT_Edit"  
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("emc.sellink", "LEFTMOUSE", "DOUBLE_CLICK", shift=True) 
    addon_keymaps.append((km, kmi))


    km = wm.keyconfigs.addon.keymaps.new(name="Object Mode")

    kmi = km.keymap_items.new("wm.call_menu_pie", "RIGHTMOUSE", "CLICK_DRAG", shift=True)
    kmi.properties.name="Mesh.EMC_MT_Add"  
    addon_keymaps.append((km, kmi))

    # kmi = km.keymap_items.new("wm.call_menu_pie", "B", "PRESS", ctrl=True, shift=True)
    # kmi.properties.name="Mesh.EMC_MT_BoolTul"
    # addon_keymaps.append((km, kmi))


    km = wm.keyconfigs.addon.keymaps.new(name = "3D View", space_type = "VIEW_3D")

    kmi = km.keymap_items.new("wm.call_menu_pie", "RIGHTMOUSE", "CLICK_DRAG")
    kmi.properties.name="Mesh.EMC_MT_SelectMode"
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("wm.call_menu_pie", "RIGHTMOUSE", "CLICK_DRAG", shift=True, ctrl=True)
    kmi.properties.name="Mesh.EMC_MT_Extras"  
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("wm.call_menu_pie", "RIGHTMOUSE", "CLICK_DRAG", shift=True, ctrl=True, alt=True)
    kmi.properties.name="Mesh.EMC_MT_ToolsMenu"  
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("emc.togglesubd", "V", "PRESS", shift=True, ctrl=True) 
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("wm.call_menu_pie", "A", "CLICK_DRAG", shift=True, ctrl=True)
    kmi.properties.name="Mesh.EMC_MT_Modifiers"  
    addon_keymaps.append((km, kmi))


    km = wm.keyconfigs.addon.keymaps.new(name = "Graph Editor", space_type = "GRAPH_EDITOR")

    kmi = km.keymap_items.new("emc.keyframedel", "X", "PRESS", ctrl=True) 
    addon_keymaps.append((km, kmi))


    km = wm.keyconfigs.addon.keymaps.new(name="UV Editor")

    kmi = km.keymap_items.new("wm.call_menu_pie", "RIGHTMOUSE", "CLICK_DRAG")
    kmi.properties.name="Mesh.EMC_MT_SelectUV"
    addon_keymaps.append((km, kmi))


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
        
    print("undone")


if __name__ == "__main__":
    register()
    
#, key_modifier='SPACE'
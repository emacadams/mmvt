import bpy
import os.path as op
from scripts_panel import ScriptsPanel
import nibabel as nib
import numpy as np

TRANS = [0, 0.8, 1]
TRANS = [0, 0.8, 0.8, 1]
COLORS = ['green', 'red', 'lightcyan', 'white']


def _mmvt():
    return ScriptsPanel.addon


def run(mmvt):
    mu = mmvt.mmvt_utils
    surface_vertices, _ = mu.read_ply_file(op.join(
        mmvt.utils.get_user_fol(), 'surf', '{}.ply'.format(bpy.context.scene.bem_surfaces)))
    surface = bpy.data.objects[bpy.context.scene.bem_surfaces]
    for ind, vert in enumerate(surface.data.vertices):
        vert.co = surface_vertices[ind] + vert.normal * bpy.context.scene.inflate_bem_surface_factor


def import_bem_surfaces():
    mmvt = _mmvt()
    surf_fol = op.join(mmvt.utils.get_user_fol(), 'surf')
    watershed_files = ['brain_surface', 'inner_skull_surface', 'outer_skull_surface', 'outer_skin_surface']
    watershed_fnames = [op.join(surf_fol, '{}.ply'.format(watershed_name)) for watershed_name in watershed_files]
    if not all([op.isfile(f) for f in watershed_fnames]):
        print('Not all bem surfaces exist, trying to create them')
        mmvt.utils.run_mmvt_func('src.preproc.anatomy', 'load_bem_surfaces')
        return
    for ind, (bem_fname, watershed_name) in enumerate(zip(watershed_fnames, watershed_files)):
        material_name = '{}_mat'.format(watershed_name)
        surf_obj = mmvt.utils.get_obj(watershed_name)
        if surf_obj is None:
            surf_obj = mmvt.data.load_ply(bem_fname, watershed_name, new_material_name=material_name)
        mmvt.appearance.set_transparency(material_name, TRANS[ind])
        mmvt.appearance.set_layers_depth_trans(material_name, 10)
        data = mmvt.coloring.get_obj_color_data(surf_obj, COLORS[ind])
        mmvt.coloring.activity_map_obj_coloring(watershed_name, data)


def get_surface_obj():
    surface_obj = bpy.data.objects.get(bpy.context.scene.bem_surfaces)
    if surface_obj is None:
        print('{} wasn\'t imported into MMVT!'.format(bpy.context.scene.bem_surfaces))
    return surface_obj


def surface_vis_update(self, context):
    mu = _mmvt().mmvt_utils
    surface_obj = get_surface_obj()
    if surface_obj is None:
        return
    mu.show_hide_obj(surface_obj, bpy.context.scene.inflate_bem_surface_show)


def surface_show_all_update(self, context):
    mu = _mmvt().mmvt_utils
    for surf_item in bpy.types.Scene.bem_surfaces[1]['items']:
        surf_name = surf_item[0]
        surf_obj = bpy.data.objects.get(surf_name)
        if surf_obj is None:
            print('{} wasn\'t imported into MMVT!'.format(surf_name))
            continue
        mu.show_hide_obj(surf_obj, bpy.context.scene.inflate_bem_surface_show_all)
    bpy.context.scene.inflate_bem_surface_show = bpy.context.scene.inflate_bem_surface_show_all



def bem_surfaces_update(self, context):
    surface_obj = get_surface_obj()
    if surface_obj is None:
        return
    bpy.context.scene.inflate_bem_surface_show = not surface_obj.hide


def export_surface():
    mu = _mmvt().mmvt_utils
    bem_fol = op.join(mu.get_subjects_dir(), mu.get_user(), 'bem')
    backup_fol = mu.make_dir(op.join(bem_fol, 'backup'))
    for surf_item in bpy.types.Scene.bem_surfaces[1]['items']:
        surf_name = surf_item[0]
        surf_obj = bpy.data.objects.get(surf_name)
        if surf_obj is None:
            print('{} wasn\'t imported into MMVT!'.format(surf_name))
            continue
        surf_fname = op.join(bem_fol, '{}.surf'.format(surf_name[:-len('_surface')]))
        mu.copy_file(surf_fname, backup_fol)
        surf_vertices = np.array([v.co.to_tuple() for v in surf_obj.data.vertices])
        surf_faces = np.array([f.vertices for f in surf_obj.data.polygons])
        nib.freesurfer.write_geometry(surf_fname, surf_vertices, surf_faces)


class ExportSurface(bpy.types.Operator):
    bl_idname = "mmvt.bem_export_surface"
    bl_label = "mmvt bem_export_surface"
    bl_description = 'Export BEM surfaces'
    bl_options = {"UNDO"}

    @staticmethod
    def invoke(self, context, event=None):
        export_surface()
        return {"FINISHED"}


class ImportSurface(bpy.types.Operator):
    bl_idname = "mmvt.bem_import_surface"
    bl_label = "mmvt bem_import_surface"
    bl_description = 'Import BEM surfaces'
    bl_options = {"UNDO"}

    @staticmethod
    def invoke(self, context, event=None):
        import_bem_surfaces()
        return {"FINISHED"}


bpy.types.Scene.inflate_bem_surface_factor = bpy.props.FloatProperty(default=0)
bpy.types.Scene.inflate_bem_surface_show = bpy.props.BoolProperty(default=True, update=surface_vis_update)
bpy.types.Scene.inflate_bem_surface_show_all = bpy.props.BoolProperty(default=True, update=surface_show_all_update)


def draw(self, context):
    layout = self.layout
    layout.prop(context.scene, 'bem_surfaces', '')
    row = layout.row(align=True)
    row.prop(context.scene, 'inflate_bem_surface_show', 'Show')
    row.prop(context.scene, 'inflate_bem_surface_show_all', 'Show all')
    layout.prop(context.scene, 'inflate_bem_surface_factor', text='inf factor')

    layout.operator(ImportSurface.bl_idname, text="Import BEM", icon='IMPORT')
    layout.operator(ExportSurface.bl_idname, text="Export BEM", icon='FORCE_TURBULENCE')


def init(mmvt):
    register()
    surfaces = ['brain_surface', 'inner_skull_surface', 'outer_skull_surface', 'outer_skin_surface']
    bpy.types.Scene.bem_surfaces = bpy.props.EnumProperty(
        items=[(s, s.replace('_', ' '), '', c) for c, s in enumerate(surfaces)],
        description='BEM surfaces', update=bem_surfaces_update)
    bpy.context.scene.bem_surfaces = 'outer_skin_surface'
    surface_obj = get_surface_obj()
    if surface_obj is None:
        return
    bpy.context.scene.inflate_bem_surface_show = not surface_obj.hide


def register():
    try:
        bpy.utils.register_class(ExportSurface)
        bpy.utils.register_class(ImportSurface)
    except:
        pass


def unregister():
    try:
        bpy.utils.unregister_class(ExportSurface)
        bpy.utils.unregister_class(ImportSurface)
    except:
        pass

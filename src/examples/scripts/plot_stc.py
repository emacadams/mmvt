import bpy
import mne



def plot(stc, subject=None, surface='inflated', hemi='lh',
           colormap='auto', time_label='auto', smoothing_steps=10,
           transparent=True, alpha=1.0, time_viewer=False, subjects_dir=None,
           figure=None, views='lat', colorbar=True, clim='auto',
           cortex="classic", size=800, background="black",
           foreground="white", initial_time=None, time_unit='s',
           backend='auto', spacing='oct6', title=None, verbose=None):
    pass


bpy.types.Scene.plot_stc_fname = bpy.props.StringProperty(subtype='FILE_PATH')


def draw(self, context):
    layout = self.layout
    layout.prop(context.scene, 'plot_stc_fname', text="STC Fname")


def run(mmvt):
    stc = mne.read_source_estimate(bpy.context.scene.plot_stc_fname)
    plot(stc)

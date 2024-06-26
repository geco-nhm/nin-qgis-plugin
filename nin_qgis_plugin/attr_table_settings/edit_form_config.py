"""
Programmatically specifies a "drag and drop" layer editor
widget. Necessary because QField does not support .ui files
for editor widgets. 
"""

def adjust_layer_edgit_form(layer):
    '''TODO.'''

    editFormConfig = layer.editFormConfig()
    editFormConfig.setLayout(1)
    editFormConfig.addTab(....)
    layer.setEditFormConfig(editFormConfig)
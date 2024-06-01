import random
from PyQt5.QtWidgets import QComboBox, QTextBrowser


def my_form_open(dialog, layer, feature) -> None:

    # Replace 'myComboBox' with the actual objectName set in Qt Designer
    grunntyper_combo_box = dialog.findChild(QComboBox, 'grunntype_or_klenhet')
    variable_text_browser = dialog.findChild(
        QTextBrowser, 'variableDisplayBox')

    # Define the slot function
    def combobox_value_changed(index):
        # index is the new index of the combobox after the user's selection
        # Execute the function you want when the combobox is filled in

        content_to_display = f"Lucky number of today: {random.randint(1, 100)}"
        # ... (potentially more complex operations to define content_to_display)
        variable_text_browser.setText(content_to_display)

    # Connect the signal to the slot function
    grunntyper_combo_box.currentIndexChanged.connect(combobox_value_changed)

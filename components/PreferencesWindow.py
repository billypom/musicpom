from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QListWidgetItem,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QListWidget,
    QWidget,
    QStyle,
)
from logging import debug
from PyQt5.QtGui import QFont
from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir


class PreferencesWindow(QDialog):
    reloadConfigSignal = pyqtSignal()
    reloadDatabaseSignal = pyqtSignal()

    def __init__(self):
        super(PreferencesWindow, self).__init__()
        # Config
        self.setWindowTitle("Preferences")
        self.setMinimumSize(800, 600)
        self.cfg_file = (
            Path(user_config_dir(appname="musicpom", appauthor="billypom"))
            / "config.ini"
        )
        self.config = ConfigParser()
        self.config.read(self.cfg_file)
        self.current_category = ""
        # # Labels & input fields
        self.input_fields: dict[str, QLineEdit] = {}
        self.edit_button: QPushButton

        # Widgets
        self.content_area = QWidget()
        nav_pane = QListWidget()

        # Layouts
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        central_widget.setLayout(main_layout)
        self.content_area.setLayout(self.content_layout)

        # Navigation pane
        for category in self.config.sections():
            nav_pane.addItem(category)
        nav_pane.itemClicked.connect(self.on_nav_item_clicked)

        # Pretend to click on 1st category in nav pane
        nav_pane.setCurrentRow(0)
        first_category = nav_pane.item(0)
        assert first_category is not None
        self.on_nav_item_clicked(first_category)

        # Add widgets to the layout
        main_layout.addWidget(nav_pane)
        main_layout.addWidget(self.content_area)

        # Set the layout
        self.setLayout(main_layout)

    def on_nav_item_clicked(self, item: QListWidgetItem):
        self.current_category = item
        self.clear_layout(self.content_layout)

        # Edit toggle button
        self.edit_button = QPushButton()
        self.edit_button.setText("view mode")
        self.edit_button.clicked.connect(self.on_edit_toggled)
        self.content_layout.addWidget(self.edit_button)

        # dict of text input fields
        self.input_fields  = {}
        if isinstance(item, str):
            self.current_category_str = item
        else:
            self.current_category_str = item.text()
        # Labels
        category_label = QLabel(f"{self.current_category_str}")
        category_label.setFont(QFont("Sans", weight=QFont.Bold))
        category_label.setStyleSheet("text-transform:uppercase;")
        self.content_layout.addWidget(category_label)
        # Input fields
        for key in self.config[self.current_category_str]:
            label = QLabel(key)
            input_field = QLineEdit(self.config[self.current_category_str][key])
            input_field.setEnabled(False)
            self.content_layout.addWidget(label)
            self.content_layout.addWidget(input_field)
            self.input_fields[key] = input_field

        # Save button
        pixmapi = QStyle.StandardPixmap.SP_DialogSaveButton
        style = self.style()
        if not style:
            style = QStyle()
        icon = style.standardIcon(pixmapi)
        save_button = QPushButton("Save")
        save_button.setIcon(icon)
        save_button.clicked.connect(self.save_preferences)
        self.content_layout.addWidget(save_button)

    def on_edit_toggled(self):
        """Toggle editable text or not"""
        # kinda ugly
        is_button_on: bool = True
        for _, field in self.input_fields.items():
            if field.isEnabled():
                is_button_on = False
            field.setEnabled(not field.isEnabled())
        if is_button_on:
            self.edit_button.setText("edit mode")
        else:
            self.edit_button.setText("view mode")

    def clear_layout(self, layout):
        """Clears all widgets in the current layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def save_preferences(self):
        """Save preferences, reload the config, then reload the database if necessary"""

        # Upcate the config fields
        try:
            for key in self.input_fields:
                for category in self.config.sections():
                    if key in self.config[category]:
                        value = self.input_fields[key].text()
                        self.config[self.current_category_str][key] = value

            # Write the config file
            with open(self.cfg_file, "w") as configfile:
                self.config.write(configfile)

            self.reloadConfigSignal.emit()
            self.on_edit_toggled()
            # only reload db if we changed the db
            if self.current_category_str == "db":
                self.reloadDatabaseSignal.emit()
        except Exception as e:
            debug(e)

from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
import configparser


class ResizableHeaderView(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.parent = parent
        # FIXME: last column needs to not leave the screen when other columns become big...
        # howwww

        # table_view_column_widths = str(self.config["table"]["column_widths"]).split(",")
        # for i in range(self.parent.model.columnCount() - 1):
        #     self.setColumnWidth(i, int(table_view_column_widths[i]))
        # self.setStretchLastSection(True)
        self.setSectionResizeMode(QHeaderView.Interactive)
        self.setCascadingSectionResizes(True)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.adjust_section_sizes()

    def sectionResized(self, logicalIndex, oldSize, newSize):
        super().sectionResized(logicalIndex, oldSize, newSize)
        self.adjust_section_sizes()

    def adjust_section_sizes(self):
        column_count = self.count()
        total_width = 0

        for i in range(column_count):
            total_width += self.sectionSize(i)
        print(f"total_width = {total_width}")

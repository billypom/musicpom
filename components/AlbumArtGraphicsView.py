import os
import tempfile
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QMenu, QAction
from PyQt5.QtCore import QEvent, Qt, pyqtSignal, QUrl, QPoint
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QClipboard, QPixmap


class AlbumArtGraphicsView(QGraphicsView):
    albumArtDropped = pyqtSignal(str)
    albumArtDeleted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scene = QGraphicsScene
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.qapp = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handles drag and drop pic onto view to add album art to songs"""
        urls = event.mimeData().urls()
        if urls:
            first_url = urls[0].toLocalFile()
            if first_url.lower().endswith((".png", ".jpg", ".jpeg")):
                print(f"dropped {first_url}")
                self.albumArtDropped.emit(
                    first_url
                )  # emit signal that album art was dropped
                event.accept()
                return
        event.ignore()

    def showContextMenu(self, position: QPoint):
        """Handles showing a context menu when right clicking the album art"""
        contextMenu = QMenu(self)  # Create the menu

        copyAction = QAction("Copy", self)  # Add the actions
        pasteAction = QAction("Paste", self)
        deleteAction = QAction("Delete", self)

        copyAction.triggered.connect(
            self.copy_album_art_to_clipboard
        )  # Add the signal triggers
        pasteAction.triggered.connect(self.paste_album_art_from_clipboard)
        deleteAction.triggered.connect(self.delete_album_art)

        contextMenu.addAction(copyAction)  # Add actions to the menu
        contextMenu.addAction(pasteAction)
        contextMenu.addAction(deleteAction)
        # DO
        contextMenu.exec_(self.mapToGlobal(position))  # Show the menu

    def copy_album_art_to_clipboard(self):
        """Copies album art to the clipboard"""
        if not self.scene().items():
            return  # dont care if no pic
        clipboard = self.qapp.clipboard()
        pixmap_item = self.scene().items()[0]
        clipboard.setPixmap(pixmap_item.pixmap())

    def paste_album_art_from_clipboard(self):
        """Handles pasting album art into a song via system clipboard"""
        clipboard = self.qapp.clipboard()
        mime_data = clipboard.mimeData()
        # Check if clipboard data is raw data or filepath
        pixmap = None
        if mime_data.hasUrls():
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    pixmap = QPixmap(file_path)
        else:
            pixmap = clipboard.pixmap()
        # Put image on screen and emit signal for ID3 tags to be updated
        if pixmap != None:  # Add pixmap raw data image
            try:
                self.scene().clear()
            except Exception:
                pass
            self.scene().addPixmap(pixmap)
            # Create temp file for pic
            temp_file, file_path = tempfile.mkstemp(suffix=".jpg")
            os.close(temp_file)  # close the file
            pixmap.save(file_path, "JPEG")
            self.albumArtDropped.emit(
                file_path
            )  # emit signal that album art was pasted

    def delete_album_art(self):
        """Emits a signal for the album art to be deleted"""
        # Signal emits and ID3 tag is updated
        self.albumArtDeleted.emit()

    def load_qapp(self, qapp):
        """Necessary for talking between components..."""
        self.qapp = qapp

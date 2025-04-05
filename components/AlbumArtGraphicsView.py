import os
import tempfile
from logging import debug
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QAbstractScrollArea,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QMenu,
    QAction,
)
from PyQt5.QtCore import QEvent, QMimeData, Qt, pyqtSignal, QUrl, QPoint
from PyQt5.QtGui import (
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QClipboard,
    QPixmap,
)


class AlbumArtGraphicsView(QGraphicsView):
    """
    Displays the album art of the currently playing song
    """

    # drag&drop / copy&paste will update album art for all selected songs
    albumArtDropped = pyqtSignal(str)
    # delete will only delete album art for current song
    albumArtDeleted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setMinimumSize(200, 200)
        self.setMaximumSize(200, 200)  # Also set maximum size to maintain square shape
        # self.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Fixed)  # Keep fixed size
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        self.setInteractive(False)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.album_art_scene: QGraphicsScene = QGraphicsScene()
        self.customContextMenuRequested.connect(self.showContextMenu)

    def dragEnterEvent(self, event: QDragEnterEvent | None):
        if not event:
            return
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent | None):
        if event is None:
            return
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent | None):
        """Handles drag and drop pic onto view to add album art to songs"""
        if event is None:
            return
        urls = event.mimeData().urls()
        if urls:
            first_url = urls[0].toLocalFile()
            if first_url.lower().endswith((".png", ".jpg", ".jpeg")):
                debug(f"dropped {first_url}")
                self.albumArtDropped.emit(
                    first_url
                )  # emit signal that album art was dropped
                event.accept()
                return
        event.ignore()

    def showContextMenu(self, position: QPoint):
        """Handles showing a context menu when right clicking the album art"""
        menu = QMenu(self)  # Create the menu

        copy_action = QAction("Copy", self)  # Add the actions
        paste_action = QAction("Paste", self)
        delete_action = QAction("Delete", self)

        copy_action.triggered.connect(self.copy_album_art_to_clipboard)
        paste_action.triggered.connect(self.paste_album_art_from_clipboard)
        delete_action.triggered.connect(self.delete_album_art)

        menu.addAction(copy_action)  # Add actions to the menu
        menu.addAction(paste_action)
        menu.addAction(delete_action)
        # DO
        menu.exec_(self.mapToGlobal(position))  # Show the menu

    def load_album_art(self, album_art_data: bytes) -> None:
        """Displays the album art for the currently playing track in the GraphicsView"""
        if album_art_data:
            # Clear the scene
            try:
                self.album_art_scene.clear()
            except Exception:
                pass
            # Reset the scene
            self.setScene(self.album_art_scene)
            # Create pixmap for album art
            pixmap = QPixmap()
            pixmap.loadFromData(album_art_data)
            # Create a QGraphicsPixmapItem for more control over pic
            pixmap_item = QGraphicsPixmapItem(pixmap)
            pixmap_item.setTransformationMode(
                Qt.TransformationMode.SmoothTransformation
            )  # For better quality scaling
            # Add pixmap item to the scene
            self.album_art_scene.addItem(pixmap_item)
            # Set the scene
            self.setScene(self.album_art_scene)
            # Adjust the album art scaling
            self.adjust_pixmap_scaling(pixmap_item)

    def copy_album_art_to_clipboard(self):
        """Copies album art to the clipboard"""
        scene = self.scene()
        if scene is None:
            return
        if not scene.items():
            return  # dont care if no pic

        clipboard = self.qapp.clipboard
        pixmap_item = scene.items()[0]
        if hasattr(pixmap_item, "pixmap"):
            clipboard.setPixmap(pixmap_item.pixmap())

    def paste_album_art_from_clipboard(self):
        """Handles pasting album art into a song via system clipboard"""
        clipboard = self.qapp.clipboard
        scene = self.scene()
        if scene is None:
            return
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
        if pixmap is not None:  # Add pixmap raw data image
            # try:
            #     self.scene().clear()
            # except Exception:
            #     pass
            scene.addPixmap(pixmap)
            # Create temp file for pic
            temp_file, file_path = tempfile.mkstemp(suffix=".jpg")
            os.close(temp_file)  # close the file
            pixmap.save(file_path, "JPEG")
            self.albumArtDropped.emit(
                file_path
            )  # emit signal that album art was pasted

    def delete_album_art(self):
        """Emits a signal for the album art of the current song to be deleted"""
        self.albumArtDeleted.emit()

    def adjust_pixmap_scaling(self, pixmap_item) -> None:
        """Adjust the scaling of the pixmap item to fit the QGraphicsView, maintaining aspect ratio"""
        viewWidth = self.width()
        viewHeight = self.height()
        pixmapSize = pixmap_item.pixmap().size()
        # Calculate scaling factor while maintaining aspect ratio
        scaleX = viewWidth / pixmapSize.width()
        scaleY = viewHeight / pixmapSize.height()
        scaleFactor = min(scaleX, scaleY)
        # Apply scaling to the pixmap item
        pixmap_item.setScale(scaleFactor)

    def load_qapp(self, qapp):
        """Necessary for talking between components..."""
        self.qapp = qapp

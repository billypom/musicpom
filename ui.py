# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1152, 894)
        MainWindow.setStatusTip("")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setContentsMargins(-1, -1, 0, -1)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.hLayoutHead = QtWidgets.QHBoxLayout()
        self.hLayoutHead.setObjectName("hLayoutHead")
        self.vlayoutAlbumArt = QtWidgets.QVBoxLayout()
        self.vlayoutAlbumArt.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.vlayoutAlbumArt.setObjectName("vlayoutAlbumArt")
        self.albumGraphicsView = AlbumArtGraphicsView(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.albumGraphicsView.sizePolicy().hasHeightForWidth())
        self.albumGraphicsView.setSizePolicy(sizePolicy)
        self.albumGraphicsView.setMinimumSize(QtCore.QSize(200, 200))
        self.albumGraphicsView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.albumGraphicsView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.albumGraphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.albumGraphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.albumGraphicsView.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self.albumGraphicsView.setInteractive(False)
        self.albumGraphicsView.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.albumGraphicsView.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.albumGraphicsView.setObjectName("albumGraphicsView")
        self.vlayoutAlbumArt.addWidget(self.albumGraphicsView)
        self.hLayoutHead.addLayout(self.vlayoutAlbumArt)
        self.vLayoutSongDetails = QtWidgets.QVBoxLayout()
        self.vLayoutSongDetails.setObjectName("vLayoutSongDetails")
        self.artistLabel = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(24)
        font.setBold(True)
        font.setWeight(75)
        self.artistLabel.setFont(font)
        self.artistLabel.setObjectName("artistLabel")
        self.vLayoutSongDetails.addWidget(self.artistLabel)
        self.titleLabel = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(18)
        self.titleLabel.setFont(font)
        self.titleLabel.setObjectName("titleLabel")
        self.vLayoutSongDetails.addWidget(self.titleLabel)
        self.albumLabel = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(False)
        font.setItalic(True)
        font.setWeight(50)
        self.albumLabel.setFont(font)
        self.albumLabel.setObjectName("albumLabel")
        self.vLayoutSongDetails.addWidget(self.albumLabel)
        self.hLayoutHead.addLayout(self.vLayoutSongDetails)
        self.vLayoutPlaybackVisuals = QtWidgets.QVBoxLayout()
        self.vLayoutPlaybackVisuals.setObjectName("vLayoutPlaybackVisuals")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.playbackSlider = QtWidgets.QSlider(self.centralwidget)
        self.playbackSlider.setOrientation(QtCore.Qt.Horizontal)
        self.playbackSlider.setObjectName("playbackSlider")
        self.horizontalLayout.addWidget(self.playbackSlider)
        self.timeHorizontalLayout2 = QtWidgets.QHBoxLayout()
        self.timeHorizontalLayout2.setObjectName("timeHorizontalLayout2")
        self.startTimeLabel = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Monospace")
        font.setItalic(False)
        self.startTimeLabel.setFont(font)
        self.startTimeLabel.setObjectName("startTimeLabel")
        self.timeHorizontalLayout2.addWidget(self.startTimeLabel)
        self.slashLabel = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Monospace")
        font.setItalic(False)
        self.slashLabel.setFont(font)
        self.slashLabel.setObjectName("slashLabel")
        self.timeHorizontalLayout2.addWidget(self.slashLabel)
        self.endTimeLabel = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Monospace")
        font.setBold(True)
        font.setItalic(False)
        font.setWeight(75)
        self.endTimeLabel.setFont(font)
        self.endTimeLabel.setObjectName("endTimeLabel")
        self.timeHorizontalLayout2.addWidget(self.endTimeLabel)
        self.horizontalLayout.addLayout(self.timeHorizontalLayout2)
        self.speedSlider = QtWidgets.QSlider(self.centralwidget)
        self.speedSlider.setMinimum(0)
        self.speedSlider.setMaximum(100)
        self.speedSlider.setSingleStep(1)
        self.speedSlider.setProperty("value", 50)
        self.speedSlider.setOrientation(QtCore.Qt.Horizontal)
        self.speedSlider.setInvertedAppearance(False)
        self.speedSlider.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.speedSlider.setObjectName("speedSlider")
        self.horizontalLayout.addWidget(self.speedSlider)
        self.speedLabel = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Monospace")
        self.speedLabel.setFont(font)
        self.speedLabel.setObjectName("speedLabel")
        self.horizontalLayout.addWidget(self.speedLabel)
        self.horizontalLayout.setStretch(0, 4)
        self.horizontalLayout.setStretch(2, 4)
        self.horizontalLayout.setStretch(3, 1)
        self.vLayoutPlaybackVisuals.addLayout(self.horizontalLayout)
        self.PlotWidget = PlotWidget(self.centralwidget)
        self.PlotWidget.setObjectName("PlotWidget")
        self.vLayoutPlaybackVisuals.addWidget(self.PlotWidget)
        self.hLayoutHead.addLayout(self.vLayoutPlaybackVisuals)
        self.hLayoutHead.setStretch(0, 1)
        self.hLayoutHead.setStretch(1, 4)
        self.hLayoutHead.setStretch(2, 6)
        self.verticalLayout.addLayout(self.hLayoutHead)
        self.hLayoutMusicTable = QtWidgets.QHBoxLayout()
        self.hLayoutMusicTable.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.hLayoutMusicTable.setContentsMargins(0, -1, 0, -1)
        self.hLayoutMusicTable.setObjectName("hLayoutMusicTable")
        self.playlistTreeView = PlaylistsPane(self.centralwidget)
        self.playlistTreeView.setObjectName("playlistTreeView")
        self.hLayoutMusicTable.addWidget(self.playlistTreeView)
        self.tableView = MusicTable(self.centralwidget)
        self.tableView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.tableView.setAcceptDrops(True)
        self.tableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableView.setEditTriggers(QtWidgets.QAbstractItemView.AnyKeyPressed|QtWidgets.QAbstractItemView.EditKeyPressed)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableView.setSortingEnabled(True)
        self.tableView.setObjectName("tableView")
        self.tableView.verticalHeader().setVisible(False)
        self.hLayoutMusicTable.addWidget(self.tableView)
        self.hLayoutMusicTable.setStretch(0, 2)
        self.hLayoutMusicTable.setStretch(1, 10)
        self.verticalLayout.addLayout(self.hLayoutMusicTable)
        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 2)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.hLayoutControls = QtWidgets.QHBoxLayout()
        self.hLayoutControls.setSpacing(6)
        self.hLayoutControls.setObjectName("hLayoutControls")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hLayoutControls.addItem(spacerItem)
        self.previousButton = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(28)
        self.previousButton.setFont(font)
        self.previousButton.setObjectName("previousButton")
        self.hLayoutControls.addWidget(self.previousButton)
        self.playButton = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(28)
        self.playButton.setFont(font)
        self.playButton.setObjectName("playButton")
        self.hLayoutControls.addWidget(self.playButton)
        self.nextButton = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(28)
        self.nextButton.setFont(font)
        self.nextButton.setObjectName("nextButton")
        self.hLayoutControls.addWidget(self.nextButton)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hLayoutControls.addItem(spacerItem1)
        self.hLayoutControls.setStretch(0, 1)
        self.hLayoutControls.setStretch(1, 2)
        self.hLayoutControls.setStretch(2, 2)
        self.hLayoutControls.setStretch(3, 2)
        self.hLayoutControls.setStretch(4, 1)
        self.verticalLayout_3.addLayout(self.hLayoutControls)
        self.hLayoutControls2 = QtWidgets.QHBoxLayout()
        self.hLayoutControls2.setSpacing(6)
        self.hLayoutControls2.setObjectName("hLayoutControls2")
        self.volumeSlider = QtWidgets.QSlider(self.centralwidget)
        self.volumeSlider.setMinimum(-1)
        self.volumeSlider.setMaximum(101)
        self.volumeSlider.setProperty("value", 50)
        self.volumeSlider.setOrientation(QtCore.Qt.Horizontal)
        self.volumeSlider.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.volumeSlider.setObjectName("volumeSlider")
        self.hLayoutControls2.addWidget(self.volumeSlider)
        self.volumeLabel = QtWidgets.QLabel(self.centralwidget)
        self.volumeLabel.setObjectName("volumeLabel")
        self.hLayoutControls2.addWidget(self.volumeLabel)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hLayoutControls2.addItem(spacerItem2)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.hLayoutControls2.addWidget(self.pushButton)
        self.hLayoutControls2.setStretch(0, 1)
        self.hLayoutControls2.setStretch(2, 4)
        self.hLayoutControls2.setStretch(3, 1)
        self.verticalLayout_3.addLayout(self.hLayoutControls2)
        self.verticalLayout_3.setStretch(0, 20)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1152, 41))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        self.menuQuick_Actions = QtWidgets.QMenu(self.menubar)
        self.menuQuick_Actions.setObjectName("menuQuick_Actions")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionPreferences = QtWidgets.QAction(MainWindow)
        self.actionPreferences.setObjectName("actionPreferences")
        self.actionScanLibraries = QtWidgets.QAction(MainWindow)
        self.actionScanLibraries.setObjectName("actionScanLibraries")
        self.actionDeleteLibrary = QtWidgets.QAction(MainWindow)
        self.actionDeleteLibrary.setObjectName("actionDeleteLibrary")
        self.actionSortColumns = QtWidgets.QAction(MainWindow)
        self.actionSortColumns.setObjectName("actionSortColumns")
        self.actionOpenFiles = QtWidgets.QAction(MainWindow)
        self.actionOpenFiles.setObjectName("actionOpenFiles")
        self.actionDeleteDatabase = QtWidgets.QAction(MainWindow)
        self.actionDeleteDatabase.setObjectName("actionDeleteDatabase")
        self.actionNewPlaylist = QtWidgets.QAction(MainWindow)
        self.actionNewPlaylist.setObjectName("actionNewPlaylist")
        self.actionExportPlaylist = QtWidgets.QAction(MainWindow)
        self.actionExportPlaylist.setObjectName("actionExportPlaylist")
        self.menuFile.addAction(self.actionOpenFiles)
        self.menuFile.addAction(self.actionNewPlaylist)
        self.menuFile.addAction(self.actionExportPlaylist)
        self.menuEdit.addAction(self.actionPreferences)
        self.menuQuick_Actions.addAction(self.actionScanLibraries)
        self.menuQuick_Actions.addAction(self.actionDeleteLibrary)
        self.menuQuick_Actions.addAction(self.actionDeleteDatabase)
        self.menuQuick_Actions.addAction(self.actionSortColumns)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuQuick_Actions.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.artistLabel.setText(_translate("MainWindow", "artist"))
        self.titleLabel.setText(_translate("MainWindow", "song title"))
        self.albumLabel.setText(_translate("MainWindow", "album"))
        self.startTimeLabel.setText(_translate("MainWindow", "00:00"))
        self.slashLabel.setText(_translate("MainWindow", "/"))
        self.endTimeLabel.setText(_translate("MainWindow", "00:00"))
        self.speedLabel.setText(_translate("MainWindow", "1.00"))
        self.previousButton.setText(_translate("MainWindow", "⏮️"))
        self.playButton.setText(_translate("MainWindow", "▶️"))
        self.nextButton.setText(_translate("MainWindow", "⏭️"))
        self.volumeLabel.setText(_translate("MainWindow", "50"))
        self.pushButton.setText(_translate("MainWindow", "nothing"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.menuView.setTitle(_translate("MainWindow", "View"))
        self.menuQuick_Actions.setTitle(_translate("MainWindow", "Quick-Actions"))
        self.actionPreferences.setText(_translate("MainWindow", "Preferences"))
        self.actionPreferences.setStatusTip(_translate("MainWindow", "Open preferences"))
        self.actionScanLibraries.setText(_translate("MainWindow", "Scan libraries"))
        self.actionDeleteLibrary.setText(_translate("MainWindow", "Delete Library"))
        self.actionSortColumns.setText(_translate("MainWindow", "Sort Columns"))
        self.actionOpenFiles.setText(_translate("MainWindow", "Open file(s)"))
        self.actionDeleteDatabase.setText(_translate("MainWindow", "Delete Database"))
        self.actionNewPlaylist.setText(_translate("MainWindow", "New playlist"))
        self.actionExportPlaylist.setText(_translate("MainWindow", "Export playlist"))
from components import AlbumArtGraphicsView, MusicTable, PlaylistsPane
from pyqtgraph import PlotWidget

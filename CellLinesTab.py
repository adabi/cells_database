from PyQt5 import QtWidgets, QtCore
from main_models import CellLinesModel
from dbfunctions import RetrieveCellLines, addNewCellLine, deleteCellLine, editCellLineComment

class CellLines_Tab:

    def __init__(self):
        self.update_cell_lines_from_database()
        self.cellLinesTable.verticalHeader().hide()
        self.cellLinesTable.setColumnWidth(0, 200)
        self.cellLinesTable.setColumnWidth(1, 130)
        self.cellLinesTable.horizontalHeader().setStretchLastSection(True)
        self.cellLinesTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.cellLinesTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.bttnAddCellLine.clicked.connect(self.addCellLine)
        self.bttnDeleteCellLine.clicked.connect(self.deleteCellLine)


    def populateCellLines(self, data):
        self.cellLinesModel = CellLinesModel(data, len(data))
        self.cellLinesTable.setModel(self.cellLinesModel)
        self.cellLinesModel.sig_invalidentry.connect(self.forceEditCellLine, QtCore.Qt.QueuedConnection)
        self.cellLinesModel.sig_changed.connect(self.cellLinesDataChanged)
        self.cellLinesTable.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.cellLinesTable.doubleClicked.connect(self.cellLinesTableDoubleClick)

    def addCellLine(self, data):
        if ["NEW", 0, ""] not in self.dataCellLines:
            self.cellLinesModel.newItem()
            index = self.cellLinesModel.createIndex(len(self.cellLinesModel.data) - 1, 0)
            self.cellLinesTable.setCurrentIndex(index)
            self.cellLinesTable.edit(index)

    def forceEditCellLine(self, index):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setText("Please enter a valid name")
        msgbox.exec_()
        self.cellLinesTable.setFocus()
        self.cellLinesTable.setCurrentIndex(index)
        self.cellLinesTable.edit(index)

    def cellLinesDataChanged(self, index, new):
        if index.column() == 0:
            try:
                addNewCellLine(new)
                msgbox = QtWidgets.QMessageBox()
                msgbox.setText("New cell line added successfully")
                msgbox.exec_()
                self.lstCellLines = [item[0] for item in self.cellLinesModel.data]
                self.lstCellLines.sort()
                self.lstCellLines.append(None)
                self.dComboBox.updateList(self.lstCellLines)
                self.combo_CellType.clear()
                self.combo_CellType.addItems(self.lstCellLines)
            except Exception as e:
                msgbox = QtWidgets.QMessageBox()
                msgbox.setText("Something went wrong. Please try again.")
                msgbox.exec_()
                raise e
        else:
            if new == "":
                new = None

            cell_line = self.cellLinesModel.data[index.row()][0]
            editCellLineComment(cell_line, new)

    def deleteCellLine(self):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setText("Are you sure you would like to delete the selected cell line?")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        decision = msgbox.exec_()
        if decision == QtWidgets.QMessageBox.Yes:
            selectionModel = self.cellLinesTable.selectionModel()
            row = selectionModel.selectedIndexes()[0].row()
            CellLine = self.cellLinesModel.data[row][0]
            deleteCellLine(CellLine)
            self.cellLinesModel.delete_row(row)
            self.lstCellLines = [item[0] for item in self.cellLinesModel.data]
            self.lstCellLines.sort()
            self.lstCellLines.append(None)
            self.dComboBox.updateList(self.lstCellLines)
            self.combo_CellType.clear()
            self.combo_CellType.addItems(self.lstCellLines)

    def cellLinesTableDoubleClick(self, index):
        if index.column() != 2:
            cell_line = self.cellLinesModel.data[index.row()][0]
            self.txtCellsRetreive.setText(cell_line)
            self.bttnFindCells.animateClick()
            self.tab.setCurrentIndex(1)

    def update_cell_lines_from_database(self):
        self.dataCellLines = RetrieveCellLines()
        self.lstCellLines = [item[0] for item in self.dataCellLines]
        self.lstCellLines.sort()
        self.lstCellLines.append(None)
        self.populateCellLines(self.dataCellLines)

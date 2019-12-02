from PyQt5 import QtCore, QtWidgets, QtGui
from dateutil.parser import parse


class StoreTableModel(QtCore.QAbstractTableModel):
    sig_NoMorePositions = QtCore.pyqtSignal()

    def __init__(self, data, numberofRows):
        super(StoreTableModel, self).__init__()
        self.data = data
        for item in self.data:
            item.append(0)

        self.numberofRows = numberofRows
        self.headers = ["", "Cells", "Passage", "Dewar", "Cylinder", "Cane Color", "Cane ID", "Position", "Initials", "Date", "Comments"]
        self.rowsColored = False



    def rowCount(self, parent=None, *args, **kwargs):
        return self.numberofRows

    def columnCount(self, parent=None, *args, **kwargs):
        return 11

    def headerData(self, p_int, Qt_Orientation, role=None):
        if role == QtCore.Qt.DisplayRole:
            if Qt_Orientation == QtCore.Qt.Horizontal:
                return self.headers[p_int]


    def data(self, QModelIndex, role=None):
        row = QModelIndex.row()
        column = QModelIndex.column()
        if role == QtCore.Qt.TextAlignmentRole:
            if column in {1, 3, 5, 6, 8}:
                return QtCore.Qt.AlignCenter
            else:
                return QtCore.Qt.AlignVCenter
        elif role == QtCore.Qt.CheckStateRole and QModelIndex.column() == 0:
            if self.data[row][11] == 1:
                return QtCore.Qt.Checked
            else:
                return QtCore.Qt.Unchecked
        elif role == QtCore.Qt.DisplayRole and column > 0:
                return self.data[row][column]

        elif role == QtCore.Qt.BackgroundRole and column != 0 and self.rowsColored:
            if self.data[row][11] == 0:
                return QtGui.QColor("white")
            else:
                return QtGui.QColor("lightblue")

        elif role == QtCore.Qt.EditRole:
            return self.data[row][column]



    def flags(self, QModelIndex):
        if QModelIndex.isValid():
            column = QModelIndex.column()
            if self.rowsColored or (column > 2 and column < 8):
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
            else:
                if column == 0:
                    return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable
                else:
                    return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable


    def setData(self, QModelIndex, Any, role=None):
        row = QModelIndex.row()
        column = QModelIndex.column()
        if role == QtCore.Qt.CheckStateRole and column == 0:
            if Any == QtCore.Qt.Checked:
                self.data[row][11] = 1
            else:
                self.data[row][11] = 0
        elif role == QtCore.Qt.EditRole and column == 9:
            date = self.ValidateDate(Any)
            if date is not False:
                self.data[row][9] = date.strftime("%m/%d/%Y")


        elif role == QtCore.Qt.EditRole:
            self.data[row][column] = Any

        self.dataChanged.emit(QModelIndex, QModelIndex)
        return True


    def findAnotherPosition(self):
        for i in range(self.numberofRows):
            if self.data[i][11] == 1:
                if len(self.data) == self.numberofRows:
                    self.sig_NoMorePositions.emit()
                    break
                else:
                    self.data[i] = self.data[self.numberofRows]
                    del self.data[self.numberofRows]
                    index = self.createIndex(i,1)
                    index2 = self.createIndex(i, 4)
                    self.dataChanged.emit(index,index2)

    def colorRows(self, color):
        self.rowsColored = color
        index = self.createIndex(0,1)
        index1 = self.createIndex(len(self.data), 10)
        self.dataChanged.emit(index, index1)


    def appendData(self, data):
        self.beginInsertRows(QtCore.QModelIndex(), self.numberofRows, self.numberofRows + len(data) - 1)
        for i in range(len(data)):
            self.data.insert(self.numberofRows + i, list(data[i]))
            self.data[self.numberofRows + i].append(1)
        index1 = self.createIndex(self.numberofRows, 0)
        index2 = self.createIndex(len(self.data), 4)
        self.numberofRows += len(data)
        self.endInsertRows()
        self.dataChanged.emit(index1, index2)

    def addCells(self, data):
        for i in range(0, self.numberofRows):
            if self.data[i][11] == 1:
                self.data[i][1] = data[0]
                self.data[i][2] = data[1]
                self.data[i][8] = data[2]
                self.data[i][9] = data[3]
                self.data[i][10] = data[4]
                self.data[i][11] = 0
                index1 = self.createIndex(i,0)
                index2 = self.createIndex(i,10)
                self.dataChanged.emit(index1, index2)

    def delete_rows(self, rows):
        for row in sorted(rows, reverse=True):
            self.beginRemoveRows(QtCore.QModelIndex(), row, row)
            self.removeRow(row)
            del self.data[row]
            self.numberofRows -= 1
            self.endRemoveRows()





    def ValidateDate(self, date):
        try:
            date = parse(date)
             #datetime.datetime.strptime(self.lineEdit.text(), '%M/%d/%Y')
            return date
        except ValueError:
            messageBox = QtWidgets.QMessageBox()
            messageBox.setText("Incorrect date. Please enter dd/MM/YYYY format.")
            messageBox.exec_()
            return False

    def sort(self, p_int, order=None):
        self.data = sorted(self.data,key=lambda x: x[p_int], reverse = order == 1)
        index1 = self.createIndex(0, 0)
        index2 = self.createIndex(len(self.data) - 1, 10)
        self.dataChanged.emit(index1, index2)


class RetrieveTableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(RetrieveTableModel, self).__init__()
        self.data = data
        for item in self.data:
            item.insert(11, 1)
        self.headers = ["", "Cells", "Passage", "Dewar", "Cylinder", "Cane Color", "Cane ID", "Position", "Initials",
                        "Date", "Comments"]
        self.rowsColored = False

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.data)

    def columnCount(self, parent=None, *args, **kwargs):
        return 11

    def headerData(self, p_int, Qt_Orientation, role=None):
        if role == QtCore.Qt.DisplayRole:
            if Qt_Orientation == QtCore.Qt.Horizontal:
                return self.headers[p_int]

    def data(self, QModelIndex, role=None):
        row = QModelIndex.row()
        column = QModelIndex.column()
        if role == QtCore.Qt.TextAlignmentRole:
            if column in {1, 3, 5, 6, 8}:
                return QtCore.Qt.AlignCenter
            else:
                return QtCore.Qt.AlignVCenter
        elif role == QtCore.Qt.CheckStateRole and QModelIndex.column() == 0:
            if self.data[row][11] == 1:
                return QtCore.Qt.Checked
            else:
                return QtCore.Qt.Unchecked
        elif role == QtCore.Qt.DisplayRole and column > 0:
            if column == 9:
                try:
                    return self.data[row][column].strftime("%m/%d/%Y")
                except:
                    return self.data[row][column]
            else:
                return self.data[row][column]
        elif role == QtCore.Qt.BackgroundRole and column != 0 and self.rowsColored:
            if self.data[row][11] == 0:
                return QtGui.QColor("white")
            else:
                return QtGui.QColor("lightgreen")

    def flags(self, QModelIndex):
        if QModelIndex.isValid():
            if QModelIndex.column() == 0 and not self.rowsColored:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable
            else:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


    def setData(self, QModelIndex, Any, role=None):
        row = QModelIndex.row()
        column = QModelIndex.column()
        if role == QtCore.Qt.CheckStateRole and column == 0:
            if Any == QtCore.Qt.Checked:
                self.data[row][11] = 1
            else:
                self.data[row][11] = 0

        self.dataChanged.emit(QModelIndex, QModelIndex)
        return True

    def appendData(self, data):
        self.beginInsertRows(QtCore.QModelIndex(), len(self.data), len(self.data) + len(data) - 1)

        index1 = self.createIndex(len(self.data), 0)
        for i in range(len(data)):
            self.data.append(list(data[i]))
            self.data[len(self.data)-1].append(1)
        self.endInsertRows()
        index2 = self.createIndex(len(self.data), 10)
        self.dataChanged.emit(index1, index2)

    def colorRows(self, color):
        self.rowsColored = color
        index = self.createIndex(0,1)
        index1 = self.createIndex(len(self.data), 10)
        self.dataChanged.emit(index, index1)


    def sort(self, p_int, order=None):
        self.data = sorted(self.data, key = lambda x: x[p_int], reverse=order == 1)
        index1 = self.createIndex(0, 0)
        index2 = self.createIndex(len(self.data) - 1, 10)
        self.dataChanged.emit(index1, index2)



class CellLinesModel(QtCore.QAbstractTableModel):
    sig_invalidentry = QtCore.pyqtSignal(object)
    sig_changed = QtCore.pyqtSignal(object, str)

    def __init__(self, data, numberofRows):
        super(CellLinesModel, self).__init__()
        self.data = data
        self.numberofRows = numberofRows
        self.headers = ["Cell Lines","Number in Storage", "Notes"]

    def rowCount(self, parent=None, *args, **kwargs):
        return self.numberofRows

    def columnCount(self, parent=None, *args, **kwargs):
        return 3

    def headerData(self, p_int, Qt_Orientation, role=None):
        if role == QtCore.Qt.DisplayRole:
            if Qt_Orientation == QtCore.Qt.Horizontal:
                return self.headers[p_int]

    def data(self, QModelIndex, role=None):
        row = QModelIndex.row()
        column = QModelIndex.column()
        if role == QtCore.Qt.TextAlignmentRole:
            if column == 1:
                return QtCore.Qt.AlignCenter
            else:
                return QtCore.Qt.AlignVCenter

        elif role == QtCore.Qt.DisplayRole:
                return self.data[row][column]

        elif role == QtCore.Qt.EditRole:
            return self.data[row][column]

    def flags(self, QModelIndex):
        if QModelIndex.isValid():
            if self.data[QModelIndex.row()][0] == "NEW" or QModelIndex.column() == 2:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
            else:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, QModelIndex, Any, role=None):
        row = QModelIndex.row()
        column = QModelIndex.column()

        if role == QtCore.Qt.EditRole:
            if QModelIndex.column == 0 and (Any == "" or Any.lower() == "new"):
                self.sig_invalidentry.emit(QModelIndex)
            else:
                self.data[row][column] = Any
                self.sig_changed.emit(QModelIndex, Any)

        self.dataChanged.emit(QModelIndex, QModelIndex)
        return True

    def newItem(self):
        self.beginInsertRows(QtCore.QModelIndex(), len(self.data), len(self.data))
        self.data.append(["NEW", 0, ""])
        self.numberofRows += 1
        self.endInsertRows()

    def appendData(self, data):
        self.beginInsertRows(QtCore.QModelIndex(), self.numberofRows, self.numberofRows + len(data) - 1)
        for i in range(len(data)):
            self.data.insert(self.numberofRows + i, list(data[i]))
            self.data[self.numberofRows + i].append(1)
        index1 = self.createIndex(self.numberofRows, 0)
        index2 = self.createIndex(len(self.data), 4)
        self.numberofRows += len(data)
        self.endInsertRows()
        self.dataChanged.emit(index1, index2)

    def delete_row(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        self.removeRow(row)
        del self.data[row]
        self.numberofRows -= 1
        self.endRemoveRows()

    def sort(self, p_int, order=None):
        self.data = sorted(self.data,key=lambda x: x[p_int], reverse=order == 1)
        index1 = self.createIndex(0, 0)
        index2 = self.createIndex(len(self.data) - 1, 10)
        self.dataChanged.emit(index1, index2)






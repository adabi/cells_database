from PyQt5 import QtWidgets, QtCore, QtGui
from dateutil.parser import parse


class CylinderListModel(QtCore.QAbstractListModel):
    def __init__(self, data):
        super(CylinderListModel, self).__init__()
        self.data = data

    def rowCount(self, parent=None, *args, **kwargs):
        return(len(self.data))

    def data(self, QModelIndex, role=None):
        row = QModelIndex.row()
        if role == QtCore.Qt.DisplayRole:
                return self.data[row]

class ListModel(QtCore.QAbstractListModel):
    sig_changed = QtCore.pyqtSignal(str, tuple, str, str)
    sig_invalidentry = QtCore.pyqtSignal(str, object)

    def __init__(self, name, data):
        super(ListModel,self).__init__()
        self.data = data
        self.display = 0
        self.colors = {}
        self.name = name

    def rowCount(self, parent=None, *args, **kwargs):
        if self.display == 0:
            return 0
        else:
            return len(self.data[self.display])

    def data(self, QModelIndex, role=None):
        row = QModelIndex.row()
        if not self.display == 0 and row < len(self.data[self.display]):
            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                return self.data[self.display][row]
            if role == QtCore.Qt.BackgroundRole:
                if (self.display, row) in self.colors.keys():
                    return QtGui.QColor(self.colors[(self.display, row)])


    def switchDisplay(self, display):
        if self.display == 0:
            index2 = self.createIndex(0,0)
        else:
            index2 = self.createIndex(len(self.data[self.display]) - 1, 0)
        self.display = display
        index1 = self.createIndex(0,0)

        self.dataChanged.emit(index1, index2)

    def newItem(self):
        self.beginInsertRows(QtCore.QModelIndex(), len(self.data[self.display]) - 1, len(self.data[self.display]))
        self.data[self.display].append("NEW")
        self.endInsertRows()
        index = self.createIndex(len(self.data[self.display]) -1, 0)
        self.colors.update({(self.display, len(self.data[self.display]) -1) : "chartreuse"})
        self.dataChanged.emit(index, index)

    def deleteItem(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self.data[self.display][row]
        self.endRemoveRows()
        index1 = self.createIndex(row, 0)
        index2 = self.createIndex(len(self.data[self.display]) - 2, 0)
        self.dataChanged.emit(index1, index2)

    def setData(self, QModelIndex, Any, role=None):
        row = QModelIndex.row()
        if Any == "" or Any.lower() == "new":
            self.sig_invalidentry.emit(self.name, QModelIndex)

        else:
            if Any != self.data[self.display][row]:
                old = self.data[self.display][row]
                self.data[self.display][row] = Any
                if (self.display, row) not in self.colors.keys():
                    self.colors.update({(self.display, row): "yellow"})

                self.dataChanged.emit(QModelIndex, QModelIndex)
                if self.name == "Co":
                    self.sig_changed.emit(self.name, (self.display,), old, Any)
                else:
                    self.sig_changed.emit(self.name, self.display, old, Any)

        return True

    def flags(self, QModelIndex):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable


class TableModel(QtCore.QAbstractTableModel):
    sig_changed = QtCore.pyqtSignal(list, str, str)
    def __init__(self, data):
        super(TableModel, self).__init__()
        self.data = data
        self.headers = ['Position', 'Cells', 'Passage', 'Initials', 'Date', 'Comments']
        self.changes = []
        self.colors = {}
        self.display = 0

    def rowCount(self, parent=None, *args, **kwargs):
        return 5

    def columnCount(self, parent=None, *args, **kwargs):
        return 6

    def flags(self, QModelIndex):
        if QModelIndex.column() > 0:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable
        else:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def data(self, QModelIndex, role=None):
        row = QModelIndex.row()
        column = QModelIndex.column()
        try:
            if not self.display == 0 and (role== QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole):
                if column == 4:
                    try:
                        return self.data[self.display][row][column].strftime("%m/%d/%Y")
                    except:
                        pass
                else:
                    return self.data[self.display][row][column]
        except:
            pass

    def switchDisplay(self, display):
        if self.display == 0:
            index2 = self.createIndex(0,5)
        else:
            index2 = self.createIndex(len(self.data[self.display]) - 1, 5)
        self.display = display
        index1 = self.createIndex(0,0)
        self.dataChanged.emit(index1, index2)

    def headerData(self, p_int, Qt_Orientation, role=None):
        if role == QtCore.Qt.DisplayRole and Qt_Orientation == QtCore.Qt.Horizontal:
            return self.headers[p_int]

    def setData(self, QModelIndex, Any, role=None):
        row = QModelIndex.row()
        column = QModelIndex.column()
        if Any == "":
            Any = None
        if self.display != 0:
            if column == 4 and Any != None:
                try:
                    date = parse(Any).date()
                    if date != self.data[self.display][row][column]:
                        old = self.data[self.display][row][column]
                        self.data[self.display][row][column] = date
                        location = [self.display[0][0], self.display[0][1], self.display[1], row + 1,
                                    self.headers[column]]
                        self.sig_changed.emit(location, str(old), str(date))
                        self.dataChanged.emit(QModelIndex, QModelIndex)
                except Exception as E:
                    print(E)
                    msgbox = QtWidgets.QMessageBox()
                    msgbox.setText("Please enter a valid date (mm/dd/YYYY)")
                    msgbox.exec_()

            else:
                if Any != self.data[self.display][row][column]:
                    old = self.data[self.display][row][column]
                    self.data[self.display][row][column] = Any
                    location = [self.display[0][0], self.display[0][1], self.display[1], row + 1, self.headers[column]]
                    self.sig_changed.emit(location, str(old), str(Any))
                    self.dataChanged.emit(QModelIndex, QModelIndex)

        return True



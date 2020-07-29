import sys
from PyQt5 import QtWidgets, Qt, QtCore
from scheme_models import ListModel, TableModel, CylinderListModel
from dbfunctions import retrieve_for_cylinder_population, execute_sql_query, commit_to_db, retrieve_for_backup
import pandas as pd

class Changes(object):
    def __init__(self, parent=None, initval = 0):
        self.parent = parent
        self.value = initval

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        self.value = value
        instance.lblChanges.setText(str(self.value))

class Database_Scheme_Tab:

    changes = Changes()

    def __init__(self):

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(sys.exit)
        self.populateCylinders(self.combo_Dewar.currentText())
        self.lstCylinders.clicked.connect(self.populateColors)
        self.lstColor.clicked.connect(self.populateIDs)
        self.lstID.clicked.connect(self.populatePositions)
        self.tblPositions.horizontalHeader().setStretchLastSection(True)
        self.tblPositions.verticalHeader().hide()
        self.tblPositions.setItemDelegateForColumn(1, self.dComboBox)
        self.combo_Dewar.currentTextChanged.connect(self.dewarChanged)
        self.changeslst = []
        self.changesactual = []
        self.bttnNewColor.clicked.connect(self.newColor)
        self.bttnNewID.clicked.connect(self.newID)
        self.bttnDeleteColor.clicked.connect(self.deleteColor)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.commitChanges)
        self.bttnDeleteID.clicked.connect(self.deleteID)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.cancelChanges)
        self.bttnCopyDown.clicked.connect(self.copy_down)
        self.bttnCopyUp.clicked.connect(self.copy_up)
        self.bttnBackupDB.clicked.connect(self.backup_db)


    def populateCylinders(self, dewar=None):
        try:
            self.colorsmodel.switchDisplay(0)
            self.IDsmodel.switchDisplay(0)
            self.positionsModel.switchDisplay(0)
        except:
            pass
        if not dewar == None:
            self.currentDewar = dewar
        lst = retrieve_for_cylinder_population(dewar)
        self.fullst = []
        i = 0
        for item in lst:
            self.fullst.append(list(item))
            if self.fullst[i][1] != None:
                self.fullst[i][1] = str(self.fullst[i][1])
            i += 1
        lstcylinders = [x[2] for x in self.fullst]
        lstcylinders = list(set(lstcylinders))
        self.dictColors = {}
        self.dictIDs = {}
        self.dictPositions = {}
        for item in lstcylinders:
            self.dictColors.update({item:[]})
            for i in self.fullst:
                if i[2] == item and i[3] not in self.dictColors[item]:
                    self.dictColors[item].append(i[3])
        for key in self.dictColors.keys():
            for item in self.dictColors[key]:
                self.dictIDs.update({(key, item):[]})
                for i in self.fullst:
                    if i[2] == key and i[3] == item and i[4] not in self.dictIDs[(key, item)]:
                        self.dictIDs[(key, item)].append(i[4])
        for key in self.dictIDs.keys():
            for item in self.dictIDs[key]:
                self.dictPositions.update({(key, item):[]})
                for i in self.fullst:
                    if i[2] == key[0] and i[3] == key[1] and i[4] == item:
                        self.dictPositions[(key, item)].append([i[5]] + i[0:2] + i[6:10])
        for key in self.dictPositions.keys():
            self.dictPositions[key].sort(key= lambda x: x[0])
        self.cylindersmodel = CylinderListModel(lstcylinders)
        self.lstCylinders.setModel(self.cylindersmodel)
        self.colorsmodel = ListModel("Co", self.dictColors)
        self.lstColor.setModel(self.colorsmodel)
        self.IDsmodel = ListModel("Id", self.dictIDs)
        self.lstID.setModel(self.IDsmodel)
        self.positionsModel = TableModel(self.dictPositions)
        self.positionsModel.sig_changed.connect(self.dataChangedPositions)
        self.tblPositions.setModel(self.positionsModel)
        self.colorsmodel.sig_changed.connect(self.dataChanged)
        self.colorsmodel.sig_invalidentry.connect(self.forceEdit, Qt.Qt.QueuedConnection)
        self.IDsmodel.sig_changed.connect(self.dataChanged)
        self.IDsmodel.sig_invalidentry.connect(self.forceEdit, Qt.Qt.QueuedConnection)
        self.changes = 0


    def populateColors(self, index):
        self.currentCylinder = self.cylindersmodel.data[index.row()]
        self.colorsmodel.switchDisplay(self.currentCylinder)
        self.IDsmodel.switchDisplay(0)
        self.positionsModel.switchDisplay(0)

    def populateIDs(self, index):
        self.currentColor = self.colorsmodel.data[self.colorsmodel.display][index.row()]
        self.IDsmodel.switchDisplay((self.currentCylinder, self.currentColor))

    def populatePositions(self, index):
        self.currentID = self.IDsmodel.data[self.IDsmodel.display][index.row()]
        self.positionsModel.switchDisplay(((self.currentCylinder, self.currentColor), self.currentID))

    def dataChanged(self, model_name, display, old, new):
        if model_name == "Co":
            for key in self.dictIDs.keys():
                if key[0] == display[0] and key[1] == old:
                    self.dictIDs[(display[0], new)] = self.dictIDs.pop(key)
            for key in self.dictPositions.keys():
                if key[0] == (display[0], old):
                    self.dictPositions[((display[0], new), key[1])] = self.dictPositions.pop(key)
            self.IDsmodel.display = (display[0], new)
            self.update_changes_count()
        elif model_name == "Id":
            for key in self.dictPositions.keys():
                if key == (display, old):
                    self.dictPositions[(display, new)] = self.dictPositions.pop(key)
            self.positionsModel.display = (display, new)
            self.update_changes_count()
        if old == "NEW":
            self.changeslst.append(["N", display, new])
        else:
            self.changeslst.append(["C", display, old, new])

    def dataChangedPositions(self, location, old, new):
        if new == "None":
            new = None
        self.changeslst.append(["C", location, old, new])
        self.changes += 1

    def dprint(self):
        print(self.changeslst)

    def newColor(self):
        if not self.colorsmodel.display == 0:
            if "NEW" not in self.colorsmodel.data[self.colorsmodel.display]:
                self.colorsmodel.newItem()
                self.dictIDs.update({(self.currentCylinder, "NEW"): []})
                self.lstColor.setFocus()
                index = self.colorsmodel.createIndex(len(self.colorsmodel.data[self.colorsmodel.display]) -1, 0)
                self.lstColor.setCurrentIndex(index)
                self.lstColor.edit(index)

    #Method for forcing the user to reedit the name of a new item in case it is not valid:
    def forceEdit(self, model_name, index):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setText("Please enter a valid name")
        msgbox.exec_()
        if model_name == "Co":
            self.lstColor.setFocus()
            self.lstColor.setCurrentIndex(index)
            self.lstColor.edit(index)
        else:
            self.lstID.setFocus()
            self.lstID.setCurrentIndex(index)
            self.lstID.edit(index)

    def newID(self):
        if not self.IDsmodel.display == 0:
            if "NEW" not in self.IDsmodel.data[self.IDsmodel.display]:
                self.IDsmodel.newItem()
                self.dictPositions.update({((self.currentCylinder, self.currentColor), "NEW"):[]})
                for i in range (1,6):
                    self.dictPositions[((self.currentCylinder, self.currentColor), "NEW")].append([i,
                                                                                                   None,None,None,None,None])
                index = self.IDsmodel.createIndex(len(self.IDsmodel.data[self.IDsmodel.display]) - 1, 0)
                self.lstID.setCurrentIndex(index)
                self.lstID.edit(index)

    def deleteColor(self):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setText("Are you sure you want to delete the item?".format(self.changes))
        msgbox.setStandardButtons(QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
        reply = msgbox.exec_()
        if reply == QtWidgets.QMessageBox.Yes:
            if self.colorsmodel.display != 0:
                self.changeslst.append(['D', (self.currentCylinder, self.currentColor)])
                self.positionsModel.switchDisplay(0)
                self.IDsmodel.switchDisplay(0)
                toDelete = []
                row = self.lstColor.currentIndex().row()
                self.colorsmodel.deleteItem(row)
                del self.dictIDs[(self.currentCylinder, self.currentColor)]
                for key in self.dictPositions.keys():
                    if key[0] == (self.currentCylinder, self.currentColor):
                        toDelete.append(key)
                for key in toDelete:
                    del self.dictPositions[key]
            self.changes += 1

    def deleteID(self):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setText("Are you sure you want to delete the item?".format(self.changes))
        msgbox.setStandardButtons(QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
        reply = msgbox.exec_()
        if reply == QtWidgets.QMessageBox.Yes:
            if self.IDsmodel.display != 0:
                self.changeslst.append(['D', (self.currentCylinder, self.currentColor, self.currentID)])
                self.positionsModel.switchDisplay(0)
                toDelete = []
                row = self.lstID.currentIndex().row()
                self.IDsmodel.deleteItem(row)
                for key in self.dictPositions.keys():
                    if key == ((self.currentCylinder, self.currentColor), self.currentID):
                        toDelete.append(key)
                for key in toDelete:
                    del self.dictPositions[key]
            self.changes += 1


    def commitChanges(self, bypass=False):
        if bypass == False:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText("Are you sure you want to commit {} changes?".format(self.changes))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
            reply = msgbox.exec_()
        else:
            reply = QtWidgets.QMessageBox.Yes

        if reply == QtWidgets.QMessageBox.Yes:
            self.queries = []
            for item in self.changeslst:
                if item[0] == "C":
                    if len(item[1]) == 1:
                        current_color = item[2]
                        new_color = item[3]
                        cylinder = item[1][0]
                        parameters = (new_color, self.currentDewar, cylinder, current_color)
                        query = "UPDATE dewarupdated SET COLOR = %s WHERE Dewar = %s AND Cylinder = %s AND CANE_COLOR = %s"
                        self.queries.append([query, parameters])
                    elif len(item[1]) == 2:
                        cylinder = item[1][0]
                        color = item[1][1]
                        current_id = item[2]
                        new_id = item[3]
                        parameters = (new_id, self.currentDewar, cylinder, color, current_id)
                        query = "UPDATE dewarupdated SET CANE_ID = %s WHERE Dewar = %s AND Cylinder = %s AND CANE_COLOR = %s AND CANE_ID = %s".format(
                            new_id, self.currentDewar, cylinder, color, current_id)
                        self.queries.append([query, parameters])
                    elif len(item[1]) == 5:
                        cylinder = item[1][0]
                        color = item[1][1]
                        id = item[1][2]
                        position = item[1][3]
                        field = item[1][4]
                        value = item[3]
                        if field == "Cells":
                            if value is None or value == "":
                                available = 'T'
                            else:
                                available = "F"
                            query = "UPDATE dewarupdated SET Available = %s WHERE Dewar = %s AND Cylinder = %s AND Cane_Color = %s AND Cane_ID = %s AND Position = %s"
                            parameters = (available, self.currentDewar, cylinder, color, id, position)
                            self.queries.append([query, parameters])
                        parameters = (value, self.currentDewar, cylinder, color, id, position)
                        query = "UPDATE dewarupdated SET {} = %s WHERE Dewar = %s AND Cylinder = %s AND Cane_Color = %s AND Cane_ID = %s AND Position = %s".format(field)
                        self.queries.append([query, parameters])
                elif item[0] == "D":
                    if len(item[1]) == 2:
                        cylinder = item[1][0]
                        color = item[1][1]
                        parameters = (self.currentDewar, cylinder, color)
                        query = "DELETE FROM dewarupdated WHERE Dewar = %s AND CYLINDER = %s AND CANE_COLOR = %s"
                        self.queries.append([query, parameters])
                    elif len(item[1]) == 3:
                        cylinder = item[1][0]
                        color = item[1][1]
                        id = item[1][2]
                        parameters = (self.currentDewar, cylinder, color, id)
                        query = "DELETE FROM dewarupdated WHERE Dewar = %s AND CYLINDER = %s AND CANE_COLOR = %s AND CANE_ID = %s"
                        self.queries.append([query, parameters])
                elif item[0] == "N":
                    if len(item[1]) == 2:
                        cylinder = item[1][0]
                        color = item[1][1]
                        id = item[2]
                        for i in range(1,6):
                            parameters = (self.currentDewar, cylinder, color, id, i)
                            query = "INSERT INTO dewarupdated (Cells, Passage, Dewar, Cylinder, Cane_Color, Cane_ID, Position, Initials, Date, Comments, Available) "  \
                                    "VALUES (NULL, NULL, %s, %s, %s, %s, %s,  NULL, NULL, NULL, 'F')"
                            self.queries.append([query, parameters])

            for query in self.queries:
                execute_sql_query(query)
            commit_to_db()
            self.changes = 0
            self.resetColors()
            self.UpdateStorageCount()
            self.update_cell_lines_from_database()



    def dewarChanged(self):
        if self.changes == 0:
            self.populateCylinders(self.combo_Dewar.currentText())
        else:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            msgbox.setText("Changes to the current dewar have been made. Would you like to save or discard the changes?")
            reply = msgbox.exec_()
            if reply == QtWidgets.QMessageBox.Save:

                self.commitChanges(bypass=True)
            elif reply == QtWidgets.QMessageBox.Discard:
                self.populateCylinders(self.combo_Dewar.currentText())
            else:
                pass

    def cancelChanges(self):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
        msgbox.setText("Cancel all changes?")
        self.changeslst = []
        reply = msgbox.exec_()
        if reply == QtWidgets.QMessageBox.Yes:
            self.populateCylinders(self.currentDewar)

    def resetColors(self):
        self.colorsmodel.colors = {}
        self.IDsmodel.colors = {}


    def update_changes_count(self):
        self.changes = len(self.IDsmodel.colors.keys()) + len(self.colorsmodel.colors.keys())

    def copy_down(self):
        if self.positionsModel.display != 0:
            dict_columns = {}
            selectionModel = self.tblPositions.selectionModel()
            for index in selectionModel.selectedIndexes():
                if index.column() > 0:
                    if index.column() not in dict_columns.keys():
                        dict_columns[index.column()] = []
                    dict_columns[index.column()].append(index.row())
            for column in dict_columns:
                for row in range(1, len(dict_columns[column])):
                    index = self.positionsModel.createIndex(row, column)
                    top_row = dict_columns[column][0]
                    if column == 4:
                        self.positionsModel.setData(index, str(self.positionsModel.data[self.positionsModel.display][top_row][column]))
                    else:
                        self.positionsModel.setData(index, self.positionsModel.data[self.positionsModel.display][top_row][column])


    def copy_up(self):
        if self.positionsModel.display != 0:
            dict_columns = {}
            selectionModel = self.tblPositions.selectionModel()
            for index in selectionModel.selectedIndexes():
                if index.column() > 0:
                    if index.column() not in dict_columns.keys():
                        dict_columns[index.column()] = []
                    dict_columns[index.column()].append(index.row())
            for column in dict_columns:
                for row in range(len(dict_columns[column]) -1 ,-1, -1):
                    index = self.positionsModel.createIndex(row, column)
                    bottom_row = dict_columns[column][len(dict_columns[column]) - 1]
                    if column == 4:
                        self.positionsModel.setData(index, str(self.positionsModel.data[self.positionsModel.display][bottom_row][column]))
                    else:
                        self.positionsModel.setData(index, self.positionsModel.data[self.positionsModel.display][bottom_row][column])

    def backup_db(self):
        lst = retrieve_for_backup()
        data_dict = {}
        field_names = ['Dewar', 'Cells', 'Passage', 'Cylinder', 'Cane_Color', 'Cane_ID', 'Position', 'Initials', 'Date', 'Comments']
        for i,field_name in enumerate(field_names):
            data_dict[field_name] = [x[i] for x in lst]
        df = pd.DataFrame(data=data_dict)
        file_save_dialog = QtWidgets.QFileDialog()
        file_save_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        file_save_dialog.setNameFilter("CSV (*.csv)")
        file_save_dialog.setDefaultSuffix("csv")
        if file_save_dialog.exec():
            file_save_path = file_save_dialog.selectedFiles()[0]
            df.to_csv(path_or_buf=file_save_path, index=False)
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText("File Save Successful")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()


from PyQt5 import QtWidgets, QtCore
import sys
import os
import re
from dateutil.parser import parse
from interface.MainInterface import Ui_MainWindow
from interface.newcane import Ui_DlgNewCane
import dbfunctions
from dbfunctions import FindEmptyPositions, CalculateStorage, StoreCells, FindCompletions, login_with_credentials, retrieve_for_cylinder_population
from main_models import StoreTableModel, RetrieveTableModel
import smtplib
import datetime
import platform
import pathlib
from DatabaseSchemeTab import Database_Scheme_Tab
from CellLinesTab import CellLines_Tab
from interface.addcellsdialog import Ui_DialogAddCells
import signal
import keyring
from keyring import set_keyring
from keyring.backends import OS_X, Windows


#Remember to enable checking updates at startup before distributing!!
CURRENT_VERSION = "2.9"

if platform.system() == "Darwin":
    set_keyring(OS_X.Keyring())
elif platform.system() == "Windows":
    set_keyring(Windows.WinVaultKeyring())


class CompletionThread(QtCore.QThread):

    started = QtCore.pyqtSignal(QtCore.QObject)

    def __init__(self):
        super(CompletionThread, self).__init__()

    def start(self, caller, priority=None):
        self.started.emit(caller)

CURRENT_PATH = pathlib.Path(os.path.split(sys.executable)[0])

#A worker that retrieves cells in the database and completes the LineEdit
class CompletionWorker(QtCore.QObject):
    sig_step = QtCore.pyqtSignal(list, QtCore.QObject)
    sig_done = QtCore.pyqtSignal()

    def __init__(self):
        super(CompletionWorker, self).__init__()

    def complete(self, parentLineEdit):
        self.parentLineEdit = parentLineEdit
        word = ""
        # Make sure to grab suggestions again if user changes text while worker is running.
        while word != self.parentLineEdit.text():
            word = self.parentLineEdit.text()
            lst = FindCompletions(word)
            self.sig_step.emit(lst, self.parentLineEdit)
        self.sig_done.emit()


class UpdateWorker(QtCore.QObject):
    sig_done = QtCore.pyqtSignal(bool, bool, str)
    def __init__(self, fromButton):
        super(UpdateWorker, self).__init__()
        self.fromButton = fromButton
        self.currentPath = os.path.split(sys.executable)[0]

    def start(self):
        try:
            '''
            credential_path = os.path.join(self.currentPath, "drive-python-quickstart.json")
            credential_path = os.path.realpath(credential_path)
            store = Storage(credential_path)
            credentials = store.get()
            http = credentials.authorize(httplib2.Http())
            service = discovery.build('drive', 'v3', http=http)
            version = "None"
            results = service.files().list(
                pageSize=10, fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])
            updateAvailable = False
            if not items:
                pass
            else:
                for item in items:
                    if item['name'] == "currentversion.txt":
                        request = service.files().export_media(fileId=item['id'], mimeType='text/plain')
                        downloadPath = os.path.join(self.currentPath, "currentversion.txt")
                        fh = io.FileIO(downloadPath, "wb")
                        downloader = apiclient.http.MediaIoBaseDownload(fh, request)
                        done = False
                        while done is False:
                            done = downloader.next_chunk()

                        f = open(os.path.join(self.currentPath, "currentversion.txt"), "rb", )
                        version = f.read().decode("utf-8-sig").strip()

            if version == "None":
                pass
            elif StrictVersion(version) <= StrictVersion(CURRENT_VERSION):
                pass
            else:
                updateAvailable = True
            self.sig_done.emit(updateAvailable, self.fromButton, version)'''
            pass
        except Exception as e:
            raise(e)
            pass

class DelegateLineEdit(QtWidgets.QStyledItemDelegate):

    textchanged = QtCore.pyqtSignal(QtCore.QObject)

    def __init__(self, parent):
        super(DelegateLineEdit, self).__init__(parent)

    def createEditor(self, QWidget, QStyleOptionViewItem, QModelIndex):
        self.line_edit = QtWidgets.QLineEdit(QWidget)
        self.line_edit.setStyle(QWidget.style())
        self.line_edit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.cmpltr = QtWidgets.QCompleter()
        self.cmpltr.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)
        self.cmpltr.setModel(QtCore.QStringListModel())
        self.line_edit.setCompleter(self.cmpltr)
        self.line_edit.textChanged.connect(self.text_changed)
        return self.line_edit

    def text_changed(self):
        self.textchanged.emit(self.line_edit)

    def text(self):
        return self.line_edit.text()

    def completer(self):
        return self.cmpltr

class DelegateDropBox(QtWidgets.QStyledItemDelegate):

    textchanged = QtCore.pyqtSignal(QtCore.QObject)
    def __init__(self, parent, listCellLines):
        super(DelegateDropBox, self).__init__(parent)
        self.lstCellLines = listCellLines

    def createEditor(self, QWidget, QStyleOptionViewItem, QModelIndex):
        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.setParent(QWidget)
        self.combo_box.setStyle(QWidget.style())
        self.combo_box.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.combo_box.addItems(self.lstCellLines)
        return self.combo_box

    def updateList(self, listCellLines):
        self.lstCellLines = listCellLines


#The dialog box for creating a new cane
class NewCaneDialog(QtWidgets.QDialog, Ui_DlgNewCane):

    sig_newcane = QtCore.pyqtSignal(list)

    def __init__(self, parent,):
        super(NewCaneDialog, self).__init__(parent)
        self.setupUi(self)
        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.createNewCane)

    def createNewCane(self):
        # Validate the input
        if self.txtCaneColor.text() != "" and self.txtCaneID.text() != "" and self.spnCylinder.value() < 7:
            # If valid, create a list of the inputs and pass it to the main window in a signal
            lst = [self.spnCylinder.value(), self.txtCaneColor.text(), self.txtCaneID.text()]
            self.sig_newcane.emit(lst)
            self.accept()
        else:
            # Display message box if input is invalid
            messageBox = QtWidgets.QMessageBox()
            messageBox.setText("Please enter valid cane information")
            messageBox.exec_()


class AddCellsDialog(QtWidgets.QDialog, Ui_DialogAddCells):
    sig_addcells = QtCore.pyqtSignal(list)

    def __init__(self, parent):
        super(AddCellsDialog, self).__init__(parent)
        self.setupUi(self)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow, Database_Scheme_Tab, CellLines_Tab):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.lblVersion.setText(CURRENT_VERSION)
        self.grab_fields_from_config()
        self.bttnConnect.clicked.connect(self.connect_to_database)
        self.bttnDisconnect.clicked.connect(self.disconnect_from_database)
        self.tab.setCurrentIndex(0)

        for i in range(1,5):
            self.tab.setTabEnabled(i, False)

        if self.checkConnectOnStartup.isChecked:
            if (self.txtDatabaseLocation.text().strip() != "" and self.txtDatabaseName.text().strip() != "" and
                    self.txtUsername.text().strip() != "" and self.txtPassword.text().strip() != ""):
                self.connect_to_database(False, from_button=False)

    def _init(self):
        CellLines_Tab.__init__(self)
        self.dComboBox = DelegateDropBox(self.tblStoreCells, self.lstCellLines)
        Database_Scheme_Tab.__init__(self)

        lst = retrieve_for_cylinder_population("GR")
        self.currentPath = os.path.split(sys.executable)[0]
        # Auto completion objects. This section creates a thread and moves an auto completion worker into it.
        self.completer = QtWidgets.QCompleter()
        self.completionmodel = QtCore.QStringListModel()
        self.completer.setModel(self.completionmodel)
        self.completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)
        self.completionWorker = CompletionWorker()
        self.completionThread = CompletionThread()
        self.completionWorker.sig_step.connect(self.populateCells)
        self.completionWorker.sig_done.connect(self.completionThread.quit)
        self.completionThread.started.connect(self.completionWorker.complete)
        self.completionWorker.moveToThread(self.completionThread)
        self.cellList = []

        # Store Tab stuff:
        self.tab.setCurrentIndex(0)
        self.tblStoreCells.horizontalHeader().setStretchLastSection(True)
        self.bttnFindStorage.clicked.connect(self.FindStorage)
        self.bttnSelectAllStore.clicked.connect(self.selectAll)
        self.bttnDeselectAllStore.clicked.connect(self.deselectAll)
        self.bttnAnotherPositionStore.clicked.connect(self.anotherPosition)
        self.bttnSelectAllStore.setDisabled(True)
        self.bttnDeselectAllStore.setDisabled(True)
        self.storetblmodel = StoreTableModel([], 0)
        self.storetblmodel.sig_NoMorePositions.connect(self.noMorePositions)
        self.tblStoreCells.setModel(self.storetblmodel)
        self.tblStoreCells.setColumnWidth(0, 25)
        self.tblStoreCells.setColumnWidth(1, 225)
        self.tblStoreCells.setColumnWidth(2, 65)
        self.tblStoreCells.setColumnWidth(3, 65)
        self.tblStoreCells.setColumnWidth(4, 65)
        self.tblStoreCells.setColumnWidth(7, 65)
        self.tblStoreCells.setColumnWidth(8, 65)
        self.tblStoreCells.setColumnWidth(9, 85)
        self.tblStoreCells.verticalHeader().hide()
        self.tblStoreCells.clicked.connect(self.tblStoreCellsClicked)
        self.statusLbl = QtWidgets.QLabel()
        self.statusBar.addWidget(self.statusLbl)
        self.UpdateStorageCount()
        self.bttnNewCane.clicked.connect(self.newCane)
        self.BttnBoxStore.clicked.connect(self.buttonboxfunctions)
        self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)
        self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Cancel).setEnabled(False)
        self.bttnStore.setDisabled(True)
        self.bttnAnotherPositionStore.setDisabled(True)
        self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(self.exit_app)
        self.bttnStore.clicked.connect(self.colorRowsStore)
        self.bttnEmailPositionsStore.clicked.connect(self.sendEmailStore)
        self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.StoreCellsInDB)
        self.combo_CellType.addItems(self.lstCellLines)
        # self.txtCellsStore.textChanged.connect(self.startcompletion)
        # self.txtCellsStore.setCompleter(self.completer)
        # Contains a list of all similar cells in the database. Used for the LineEdit completion.
        self.todaysdate = datetime.date.today().strftime("%m/%d/%Y")
        self.txtDate.setText(self.todaysdate)
        self.numberofselectedStore = 0
        self.bttnAddCells.clicked.connect(self.addCells)

        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

        # Retrieve Tab stuff:

        self.retreivetblmodel = RetrieveTableModel([])
        self.tblRetreiveCells.setModel(self.retreivetblmodel)
        self.tblRetreiveCells.setColumnWidth(0, 25)
        self.tblRetreiveCells.verticalHeader().hide()
        self.tblRetreiveCells.horizontalHeader().setStretchLastSection(True)
        self.tblRetreiveCells.clicked.connect(self.tblRetreiveCellsClicked)
        self.bttnFindCells.clicked.connect(self.findCells)
        self.txtCellsRetreive.setCompleter(self.completer)
        self.txtCellsRetreive.textChanged.connect(self.startcompletion)
        self.bttnSelectAllRetreive.setDisabled(True)
        self.bttnDeselectAllRetreive.setDisabled(True)
        self.bttnRetreive.setDisabled(True)
        self.bttnRetreive.clicked.connect(self.colorRowsRetrieve)
        self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Apply).setDisabled(True)
        self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Cancel).setDisabled(True)
        self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(self.exit_app)
        self.bttnSelectAllRetreive.clicked.connect(self.selectAllRetreive)
        self.bttnDeselectAllRetreive.clicked.connect(self.deselectAllRetreive)
        self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.retreiveCells)
        self.bttnEmailPositionsRetreive.clicked.connect(self.sendEmailRetreive)
        self.bttnBoxRetreive.clicked.connect(self.buttonboxfunctionsRetreive)

    def grab_fields_from_config(self):
        try:
            with open(CURRENT_PATH / 'config' , 'r') as file:
                file_contents = file.read()
                dbname = re.search(r'^dbname=(.*)$', file_contents, re.MULTILINE)
                if dbname:
                    self.txtDatabaseName.setText(dbname.group(1))
                dblocation = re.search(r'^dblocation=(.*)$', file_contents, re.MULTILINE)
                if dblocation:
                    self.txtDatabaseLocation.setText(dblocation.group(1))
                username = re.search(r'^username=(.*)$', file_contents, re.MULTILINE)
                if username:
                    self.txtUsername.setText(username.group(1))
                    try:
                        password = keyring.get_password("Cells Database", self.txtUsername.text())
                        if password:
                            self.txtPassword.setText(password)
                    except:
                        pass
                keyring.get_password("Cells Database", username.group(1))
                saveusername = re.search(r'^saveusername=(.*)$', file_contents, re.MULTILINE)
                if saveusername:
                    self.checkSaveUsername.setChecked(saveusername.group(1) == 'True')
                savepassword = re.search(r'^savepassword=(.*)$', file_contents, re.MULTILINE)
                if savepassword:
                    self.checkSavePassword.setCecked(savepassword.group(1) == 'True')
                connect_on_startup = re.search(r'^connectonstartup=(.*)$', file_contents, re.MULTILINE)
                if connect_on_startup:
                    self.checkConnectOnStartup.setChecked(connect_on_startup.group(1) == 'True')

        except:
            pass

    def connect_to_database(self, checked, from_button=True):

        username = self.txtUsername.text()
        password = self.txtPassword.text()
        database = self.txtDatabaseName.text()
        host = self.txtDatabaseLocation.text()
        try:
            login_with_credentials(username, password, database, host)
            self._init()
            for i in range(1, 5):
                self.tab.setTabEnabled(i, True)
            self.bttnConnect.setEnabled(False)
            self.bttnDisconnect.setEnabled(True)
            self.lblStatus.setText("Connected")


            if from_button:
                print("from button")
                self.store_fields_in_config()
            else:
                self.tab.setCurrentIndex(1)


        except Exception as E:
            print(E)
            if from_button:
                msgbox = QtWidgets.QMessageBox()
                msgbox.setText("Could not connect to database. Please check location, name, and credentials.")
                msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msgbox.exec_()

    def disconnect_from_database(self):
        self.bttnDisconnect.setEnabled(False)
        self.lblStatus.setText("Disconnecting..")
        for i in range(1, 5):
            self.tab.setTabEnabled(i, False)
        dbfunctions.close_db_connection()

        self.lblStatus.setText("Disconnected")
        self.bttnConnect.setEnabled(True)

    def store_fields_in_config(self):

        print("Storing")
        string_to_store = []
        if self.checkSaveDatabase.isChecked():
            string_to_store.append(f'dblocation={self.txtDatabaseLocation.text()}\n')
            string_to_store.append(f'dbname={self.txtDatabaseName.text()}\n')

        if self.checkSaveUsername.isChecked():
            string_to_store.append(f'username={self.txtUsername.text()}\n')

        string_to_store.append(f'saveusername={self.checkSaveUsername.isChecked()}\n'
                               f'savepassword={self.checkSavePassword.isChecked()}\n'
                               f'connectonstartup={self.checkConnectOnStartup.isChecked()}\n')

        if self.checkSavePassword.isChecked():
            if self.txtUsername.text() != "" and self.txtPassword.text() != "":
                keyring.set_password("Cells Database", self.txtUsername.text(), self.txtPassword.text())

        try:
            with open(CURRENT_PATH / 'config', 'w+') as file:
                buff = ''.join(string_to_store)
                file.write(buff)
        except Exception as e:
            print(e)
            raise e






    def UpdateStorageCount(self):
        display = "Total Storage: "
        self.available_storage = {}
        for i in range(self.cmbDewarStore.count()):
            item = self.cmbDewarStore.itemText(i)
            storage = CalculateStorage(item)
            strg = "{} : {} - ".format(item, storage)
            display += strg
            self.available_storage[item] = int(storage.split("/")[0])
        display = display[:-3]
        self.statusLbl.setText(display)

    def FindStorage(self):
        self.bttnAnotherPositionStore.setDisabled(False)
        self.number_of_positions = self.spnNumberStore.value()
        Dewar = self.cmbDewarStore.currentText()
        if self.number_of_positions > self.available_storage[Dewar]:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText("Not enough free positions available.")
            msgbox.exec_()
        else:
            data = FindEmptyPositions(Dewar)
            date = self.ValidateDate(self.txtDate.text())
            if date is not False:
                for item in data:
                    item.insert(1, None)
                    item.insert(2, None)
                    item.insert(3, self.cmbDewarStore.currentText())
                    item.insert(8, None)
                    item.insert(9, None)
                    item.insert(10, "")
                self.storetblmodel = StoreTableModel(data, self.number_of_positions)
                self.completer.complete()
                self.storetblmodel.sig_NoMorePositions.connect(self.noMorePositions)
                self.storetblmodel.dataChanged.connect(self.updateSelectedStore)
                self.tblStoreCells.setModel(self.storetblmodel)
                self.tblStoreCells.setItemDelegateForColumn(1, self.dComboBox)
                self.bttnSelectAllStore.setDisabled(False)
                self.bttnDeselectAllStore.setDisabled(False)
                self.bttnStore.setDisabled(False)
                self.bttnEmailPositionsStore.setDisabled(False)
                self.numberofselectedStore = 0
                self.lblSelectedStoreLabel.setText("Selected:")
                self.lblSelectedStore.setText(str(self.numberofselectedStore))

    def selectAll(self):
        for i in range(self.number_of_positions):
            index = self.storetblmodel.createIndex(i, 0)
            self.storetblmodel.setData(index, QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)

    def deselectAll(self):
        for i in range(self.number_of_positions):
            index = self.storetblmodel.createIndex(i, 0)
            self.storetblmodel.setData(index, QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

    def anotherPosition(self):
        self.storetblmodel.findAnotherPosition()

    def noMorePositions(self):
        self.bttnAnotherPositionStore.setDisabled(True)

    def sendEmailStore(self):
        gmail_user = 'dewarstorage@gmail.com'
        gmail_password = 'BruceLab2017'
        Message = ""
        send_to = self.txtEmailStore.text()
        for i in range(self.storetblmodel.numberofRows):
            if self.storetblmodel.data[i][11] == 1:
                Message += ', '.join(str(x) for x in self.storetblmodel.data[i][1:8]) + "\n"
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, send_to, Message)
            server.close()
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText("Email sent successfully!")
            msgbox.exec_()
        except Exception as E:
            print(E)
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText("Something went wrong. Email could not be sent!")
            msgbox.exec_()

    def sendEmailRetreive(self):
        gmail_user = 'dewarstorage@gmail.com'
        gmail_password = 'BruceLab2017'
        Message = ""
        send_to = self.txtEmailRetreive.text()
        for item in self.retreivetblmodel.data:
            if item[11] == 1:
                Message += ','.join(str(x) for x in item[1:8]) + "\n"

        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, send_to, Message)
            server.close()
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText("Email sent successfully!")
            msgbox.exec_()
        except:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText("Something went wrong. Email could not be sent!")
            msgbox.exec_()

    def buttonboxfunctions(self, button):
        try:
            button = self.BttnBoxStore.standardButton(button)
        except:
            pass
        if button == QtWidgets.QDialogButtonBox.Reset:
            self.storetblmodel = StoreTableModel([], 0)
            self.storetblmodel.sig_NoMorePositions.connect(self.noMorePositions)
            self.tblStoreCells.setModel(self.storetblmodel)
            self.tblStoreCells.sortByColumn(0, 0)
            self.bttnSelectAllStore.setDisabled(True)
            self.bttnDeselectAllStore.setDisabled(True)
            self.bttnAnotherPositionStore.setDisabled(True)
            self.bttnEmailPositionsStore.setDisabled(True)
            self.bttnFindStorage.setEnabled(True)
            self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Reset).setEnabled(True)
            self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)
            self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Cancel).setEnabled(False)
            self.bttnStore.setDisabled(True)
            self.UpdateStorageCount()
            #self.txtCellsStore.setFocus()
            self.txtDate.setText(self.todaysdate)
            self.lblSelectedStore.setText("")
            self.lblSelectedStoreLabel.setText("")
        elif button == QtWidgets.QDialogButtonBox.Cancel:
            self.storetblmodel.colorRows(False)
            self.bttnStore.setDisabled(False)
            self.bttnFindStorage.setDisabled(False)
            self.bttnSelectAllStore.setDisabled(False)
            self.bttnDeselectAllStore.setDisabled(False)
            self.bttnAnotherPositionStore.setDisabled(False)
            self.bttnEmailPositionsStore.setDisabled(False)
            self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Reset).setDisabled(False)
            self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Cancel).setEnabled(False)
            self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)

    def buttonboxfunctionsRetreive(self, button):
        try:
            button = self.bttnBoxRetreive.standardButton(button)
        except:
            pass
        if button == QtWidgets.QDialogButtonBox.Reset:
            self.retreivetblmodel = RetrieveTableModel([])
            self.tblRetreiveCells.setModel(self.retreivetblmodel)
            self.tblRetreiveCells.sortByColumn(0, 0)
            self.bttnSelectAllRetreive.setDisabled(True)
            self.bttnDeselectAllRetreive.setDisabled(True)
            self.bttnEmailPositionsRetreive.setDisabled(True)
            self.bttnFindCells.setEnabled(True)
            self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Reset).setEnabled(True)
            self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)
            self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Cancel).setEnabled(False)
            self.bttnRetreive.setDisabled(True)
            self.UpdateStorageCount()
            self.txtCellsRetreive.setFocus()
            self.lblSelectedRetreiveLabel.setText("")
            self.lblSelectedRetreive.setText("")
        elif button == QtWidgets.QDialogButtonBox.Cancel:
            self.retreivetblmodel.colorRows(False)
            self.bttnRetreive.setDisabled(False)
            self.bttnFindCells.setDisabled(False)
            self.bttnSelectAllRetreive.setDisabled(False)
            self.bttnDeselectAllRetreive.setDisabled(False)
            self.bttnEmailPositionsRetreive.setDisabled(False)
            self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Reset).setDisabled(False)
            self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Cancel).setEnabled(False)
            self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)


    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == QtCore.Qt.Key_Return:
            if self.tab.currentIndex() == 0:
                self.connect_to_database(False, from_button=True)
            if not (self.tblStoreCells.hasFocus() or self.tblRetreiveCells.hasFocus()):
                if self.txtEmailStore.hasFocus():
                    self.bttnEmailPositionsStore.animateClick()
                elif self.txtEmailRetreive.hasFocus():
                    self.bttnEmailPositionsRetreive.animateClick()
                elif (self.combo_CellType.hasFocus() or self.spnPassageStore.hasFocus() or self.txtInitials.hasFocus()
                    or self.txtDate.hasFocus() or self.txtComments.hasFocus()):
                    self.bttnAddCells.animateClick()
                else:
                    if self.tab.currentIndex() == 1:
                        self.bttnFindStorage.animateClick()
                    else:
                        self.bttnFindCells.animateClick()



    def colorRowsStore(self):
        #grab the selection indicator column from the store table model and check if any rows are actually selected
        selection_list = [row[11] for row in self.storetblmodel.data]
        #if a row is selected, color the selected rows and only give the user the option to store the cells or cancel
        if 1 in selection_list:
            self.storetblmodel.colorRows(True)
            self.bttnStore.setDisabled(True)
            self.bttnFindStorage.setDisabled(True)
            self.bttnSelectAllStore.setDisabled(True)
            self.bttnDeselectAllStore.setDisabled(True)
            self.bttnAnotherPositionStore.setDisabled(True)
            self.bttnEmailPositionsStore.setDisabled(True)
            self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Reset).setDisabled(True)
            self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Cancel).setEnabled(True)
            self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(True)
        #if no rows are selected, tell the user to go select a row first
        else:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText(
                "No rows are selected for storage. Please use the first column to check which rows are to be stored.")
            msgbox.exec_()

    def StoreCellsInDB(self):
        Data = []
        rows = []
        for i in range(self.storetblmodel.numberofRows):
            if self.storetblmodel.data[i][11] == 1:
                date = self.ValidateDate(self.storetblmodel.data[i][9])
                lst = self.storetblmodel.data[i][0:9]
                lst += [date]
                lst += [self.storetblmodel.data[i][10]]
                Data.append(lst)
                rows.append(i)

        StoreCells(Data)
        msgbox = QtWidgets.QMessageBox()
        msgbox.setText("{} cells stored successfully!".format(len(Data)))
        msgbox.exec_()
        #self.buttonboxfunctions(QtWidgets.QDialogButtonBox.Reset)
        self.storetblmodel.delete_rows(rows)
        self.UpdateStorageCount()
        self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)
        self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Reset).setEnabled(True)
        self.BttnBoxStore.button(QtWidgets.QDialogButtonBox.Cancel).setEnabled(False)
        self.bttnStore.setEnabled(True)
        self.bttnSelectAllStore.setEnabled(True)
        self.bttnDeselectAllStore.setEnabled(True)
        self.bttnAnotherPositionStore.setEnabled(True)
        self.bttnFindStorage.setEnabled(True)
        self.numberofselectedStore = 0
        self.lblSelectedStore.setText("0")
        Database_Scheme_Tab.populateCylinders(self, "GR")
        self.update_cell_lines_from_database()





    def ValidateDate(self, date):
        try:
            date = parse(date)
            return date.strftime("%Y-%m-%d")
        except ValueError:
            messageBox = QtWidgets.QMessageBox()
            messageBox.setText("Invalid date. Please enter dd/MM/YYYY format.")
            messageBox.exec_()
            return False

    def newCane(self):
        newCaneDlg = NewCaneDialog(self)
        newCaneDlg.show()
        newCaneDlg.sig_newcane.connect(self.addNewCane)

    def addNewCane(self, lst):
        dewar = self.cmbDewarStore.currentText()
        data = dbfunctions.NewCane(dewar, lst[0], lst[1], lst[2])
        self.number_of_positions += len(data)
        self.storetblmodel.appendData(data)

    def findCells(self):
        celltype = self.txtCellsRetreive.text().strip()
        data = dbfunctions.FindCells(celltype)
        # Convert the items in the list from tuple to list type
        data_lst = [list(x) for x in data]
        self.retreivetblmodel = RetrieveTableModel(data_lst)
        self.tblRetreiveCells.setModel(self.retreivetblmodel)
        self.bttnRetreive.setEnabled(True)
        self.bttnSelectAllRetreive.setEnabled(True)
        self.bttnDeselectAllRetreive.setEnabled(True)
        self.retreivetblmodel.dataChanged.connect(self.updateSelectedRetreive)
        self.numberofselectedRetreive = len(self.retreivetblmodel.data)
        self.lblSelectedRetreiveLabel.setText("Selected")
        self.lblSelectedRetreive.setText(str(self.numberofselectedRetreive))
        dbfunctions.close_db_connection()


    def startcompletion(self):
        if self.sender().text() not in self.cellList:
            self.completionThread.start(self.sender())

    def populateCells(self, lst, caller):
        self.cellList = lst
        (caller.completer().model().setStringList(self.cellList))


    def colorRowsRetrieve(self):
        self.retreivetblmodel.colorRows(True)
        self.bttnSelectAllRetreive.setDisabled(True)
        self.bttnDeselectAllRetreive.setDisabled(True)
        self.bttnRetreive.setDisabled(True)
        self.bttnFindCells.setDisabled(True)
        self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(True)
        self.bttnBoxRetreive.button(QtWidgets.QDialogButtonBox.Cancel).setEnabled(True)

    def selectAllRetreive(self):
        for i, item in enumerate(self.retreivetblmodel.data):
            index = self.retreivetblmodel.createIndex(i, 0)
            self.retreivetblmodel.setData(index,QtCore.Qt.Checked,QtCore.Qt.CheckStateRole)

    def deselectAllRetreive(self):
        for i, item in enumerate(self.retreivetblmodel.data):
            index = self.retreivetblmodel.createIndex(i, 0)
            self.retreivetblmodel.setData(index,QtCore.Qt.Unchecked,QtCore.Qt.CheckStateRole)

    def retreiveCells(self):
        data = []
        for item in self.retreivetblmodel.data:
            if item[11] == 1:
                data.append(item)
        if self.chkTrash.isChecked():
            trash = True
        else:
            trash = False
        dbfunctions.RetrieveCells(data, trash)
        msgbox = QtWidgets.QMessageBox()
        if len(data) > 1:
            plural = "s"
        else:
            plural = ""
        msgbox.setText("Retreived {} cell{} successfully!".format(len(data), plural))
        msgbox.exec_()
        self.buttonboxfunctionsRetreive(QtWidgets.QDialogButtonBox.Reset)
        Database_Scheme_Tab.populateCylinders(self, "GR")
        self.update_cell_lines_from_database()

    # This function is implemented to allow the user to shift click and select all rows in-between
    def tblRetreiveCellsClicked(self, index):
        row = index.row()
        # Check if the shift key is pressed
        if app.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            # Check if the clicked column is the first
            if index.column() == 0:
                # Check if the clicked checkbox is unchecked when clicked (in this case if checked after being clicked):
                if self.retreivetblmodel.data[row][11] == 1:
                    # If yes, iterate backwards through each row until you find one that is checked
                    for i in range(row - 1, -1, -1):
                        if self.retreivetblmodel.data[i][11] == 1:
                            # Once you find a checked row, check all the rows in-between and break the loop
                            index1 = self.retreivetblmodel.createIndex(i+1, 0)
                            index2 = self.retreivetblmodel.createIndex(row-1, 0)
                            for j in range(i, row + 1):
                                self.retreivetblmodel.data[j][11] = 1
                            self.retreivetblmodel.dataChanged.emit(index1, index2)
                            break

    # Same funciton as above but for the cells storage table
    def tblStoreCellsClicked(self, index):
        row = index.row()
        # Check if the shift key is pressed
        if app.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            # Check if the clicked column is the first
            if index.column() == 0:
                # Check if the clicked checkbox is unchecked when clicked (in this case if checked after being clicked):
                if self.storetblmodel.data[row][11] == 1:
                    # If yes, iterate backwards through each row until you find one that is checked
                    for i in range(row - 1, -1, -1):
                        if self.storetblmodel.data[i][11] == 1:
                            # Once you find a checked row, check all the rows in-between and break the loop
                            index1 = self.storetblmodel.createIndex(i+1, 0)
                            index2 = self.storetblmodel.createIndex(row-1, 0)
                            for j in range(i, row + 1):
                                self.storetblmodel.data[j][11] = 1
                            self.storetblmodel.dataChanged.emit(index1, index2)
                            break


    def updateSelectedStore(self, index1, index2):
        if index1.column() == 0:
            if self.storetblmodel.data[index1.row()][11] == 0:
                increment = -1
            else:
                increment = 1
            for i in range(index1.row(), index2.row() + 1):
                self.numberofselectedStore += increment
            if self.numberofselectedStore < 0:
                self.numberofselectedStore = 0
            elif self.numberofselectedStore > self.storetblmodel.numberofRows:
                self.numberofselectedStore = self.storetblmodel.numberofRows


        self.lblSelectedStoreLabel.setText("Selected:")
        self.lblSelectedStore.setText(str(self.numberofselectedStore))

    def updateSelectedRetreive(self, index1, index2):
        if index1.column() == 0:
            if self.retreivetblmodel.data[index1.row()][11] == 0:
                increment = -1
            else:
                increment = 1
            for i in range(index1.row(), index2.row() + 1):
                self.numberofselectedRetreive += increment
            if self.numberofselectedRetreive < 0:
                self.numberofselectedRetreive = 0
            elif self.numberofselectedRetreive > len(self.retreivetblmodel.data):
                self.numberofselectedRetreive= len(self.retreivetblmodel.data)

        self.lblSelectedRetreiveLabel.setText("Selected:")
        self.lblSelectedRetreive.setText(str(self.numberofselectedRetreive))

    def addCells(self):
        Date = self.txtDate.text()
        if not self.ValidateDate(Date) == False:
            CellType = self.combo_CellType.currentText()
            Passage = self.spnPassageStore.value()
            Initials = self.txtInitials.text()
            Comments = self.txtComments.text()
            self.storetblmodel.addCells([CellType, Passage, Initials, Date, Comments])

    def exit_app(self):
        sys.exit(0)


def cleanup():
    msgbox = QtWidgets.QMessageBox()
    msgbox.setText("You sure you wanna exit?")
    msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    decision = msgbox.exec_()
    if decision == QtWidgets.QMessageBox.Yes:
        sys.exit(0)
    else:
        pass


app = QtWidgets.QApplication(sys.argv)
MainWin = MainWindow()
MainWin.show()
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGABRT, cleanup)
sys.exit(app.exec_())

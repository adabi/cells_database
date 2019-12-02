from PyQt5 import QtWidgets, Qt, QtCore
from updaterinterface import Ui_MainWindow
import psutil
import sys
import os
import io
from oauth2client.file import Storage
import httplib2
import apiclient
from apiclient import discovery
import tempfile
import zipfile
import subprocess
import time

class Worker(Qt.QObject):

    sig_app_closed = QtCore.pyqtSignal()
    sig_done = QtCore.pyqtSignal(bool)

    def __init__(self, appPath):
        super(Worker, self).__init__()
        self.t = tempfile.NamedTemporaryFile()
        self.appPath = appPath

    def start(self):
        proc = subprocess.Popen(["pgrep", "Cells Database"], stdout=subprocess.PIPE)
        for PID in proc.stdout:
            process = psutil.Process(int(PID))
            try:
                for proc in process.children(recursive=True):
                    proc.kill()
                process.kill()
            except Exception as e:
                raise e
        time.sleep(3)
        self.sig_app_closed.emit()



    def copytofolder(self):
        try:
            with zipfile.ZipFile(self.t.name, 'r') as myzip:
                myzip.extractall(os.path.split(self.appPath)[0])
            self.t.close()
            self.sig_done.emit(True)
        except Exception as e:
            self.sig_done.emit(False)
            raise e



class downloadWorker(Qt.QObject):
    sig_chunk_downloaded = QtCore.pyqtSignal(int)
    sig_download_done = QtCore.pyqtSignal(bool)

    def __init__(self, currentPath):
        super(downloadWorker, self).__init__()
        self.t = mw.worker.t
        self.currentPath = currentPath

    def start(self):
        credential_path = os.path.join(self.currentPath, "drive-python-quickstart.json")
        credential_path = os.path.realpath(credential_path)
        store = Storage(credential_path)
        credentials = store.get()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http)
        results = service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        success = False
        if not items:
            pass
        else:
            for item in items:
                print(item['name'])
                if item['name'] == "Cells Database.app.zip":
                    try:
                        request = service.files().get_media(fileId=item['id'])
                        downloadPath = self.t.name
                        fh = io.FileIO(downloadPath, "wb")
                        downloader = apiclient.http.MediaIoBaseDownload(fh, request)
                        done = False
                        while done is False:
                            status, done = downloader.next_chunk()
                            self.sig_chunk_downloaded.emit(status.progress() * 100)
                        success = True
                        break
                    except Exception as e:
                        raise e
        if success:
            self.sig_download_done.emit(True)
        else:
            self.sig_download_done.emit(False)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.appPath = sys.executable
        for i in range(3):
            self.appPath = os.path.split(self.appPath)[0]
        self.currentPath = os.path.split(sys.executable)[0]
        self.setupUi(self)
        self.buttonBox.clicked.connect(self.cancel)
        self.worker = Worker(self.appPath)
        self.worker.sig_app_closed.connect(self.app_closed)
        self.worker.sig_done.connect(self.done)
        self.thread = Qt.QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start)
        self.thread.start()

    def cancel(self):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgbox.setText("Are you sure you would like to cancel the update?")
        answer = msgbox.exec_()
        if answer == QtWidgets.QMessageBox.Yes:
            try:
                self.downloadWorker.t.close()
            except:
                pass
            sys.exit(0)

    def launch(self):
        processes = psutil.process_iter()
        for process in processes:
            if process.name() == "Cells Database":
                try:
                    path = process.cmdline()
                    for i in range(3):
                        path = os.path.split(path[0])
                    break
                except:
                    pass
        os.system("osascript -e 'quit app \"Cells Database\"'")
        msgbox = QtWidgets.QMessageBox()
        msgbox.setText(sys.executable)
        msgbox.exec_()

    def app_closed(self):
        self.downloadthread = Qt.QThread()
        self.downloadWorker = downloadWorker(self.currentPath)
        self.downloadWorker.sig_chunk_downloaded.connect(self.chunk_downloaded)
        self.downloadWorker.sig_download_done.connect(self.download_done)
        self.downloadWorker.moveToThread(self.downloadthread)
        self.downloadthread.started.connect(self.downloadWorker.start)
        self.lblStatus.setText("Downloading new version...")
        self.downloadthread.start()


    def chunk_downloaded(self, progress):
        self.progressBar.setValue(progress)

    def download_done(self, success):
        if success:
            self.lblStatus.setText("Installing app...")
            self.worker.copytofolder()
        else:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText("Could not download files. Please make sure the app file exists in the drive folder.")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Retry | QtWidgets.QMessageBox.Abort)
            answer = msgbox.exec_()
            if answer == QtWidgets.QMessageBox.Retry:
                self.progressBar.setValue(0)
                self.downloadWorker.start()
            else:
                sys.exit(0)

    def done(self, success):
        msgbox = QtWidgets.QMessageBox()
        if success:
            msgbox.setText("App updated successfully!")
            msgbox.exec_()
            subprocess.Popen(os.path.join((self.appPath), "Contents/MacOS/Cells Database"))
            sys.exit(0)
        else:
            msgbox.setText("Couldn't copy files for some reason...")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Retry | QtWidgets.QMessageBox.Abort)
            answer = msgbox.exec_()
            if answer == QtWidgets.QMessageBox.Retry:
                self.worker.copytofolder()
            else:
                sys.exit(0)

app = QtWidgets.QApplication(sys.argv)
mw = MainWindow()
mw.show()
sys.exit(app.exec_())
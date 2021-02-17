import sys
import os
import re
import binascii
import zlib

from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QFileDialog, QProgressBar, QTableWidgetItem
from PyQt5.uic import loadUi
from PyQt5.QtCore import QDir, QThread, Qt, QObject, QRunnable, pyqtSignal, pyqtSlot, QThreadPool
from PyQt5.QtGui import QColor

class WorkerData():
    def __init__(self):
        self.row_id = None
        self.text = None
        self.bacground_color = None

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    progress
        int progress complete,from 0-100
    '''
    worker_data = pyqtSignal(int, str, tuple)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals
    and wrap-up.
    '''

    def __init__(self, files_list):
        super(Worker, self).__init__()
        self.signals = WorkerSignals()
        self.files_list = files_list

    @pyqtSlot()
    def run(self):
        for row_index, file in enumerate(self.files_list):
            crc32_from_name = file.crc32_from_name
            crc32_from_file = file.get_crc_from_file()

            if (crc32_from_name):
                if crc32_from_file == crc32_from_name:
                    color = (0, 255, 0)
                else:
                    color = (255, 0, 0)
            else:
                color = (255, 255, 255)

            self.signals.worker_data.emit(row_index, crc32_from_file, color)


class MainWindow(QMainWindow):
    def __init__(self, folderpath):
        super().__init__()


        self.app_name = "CRC32 GUI"
        self.app_version = "0.2.0"

        self.init_ui()
        self.setup_events()

        self.threadpool = QThreadPool()

        self.root_folderpath = ""
        #self.includes = (".avi", ".mp4", ".mkv", ".ogm", ".mpg")
        includes = self.allowed_extensions.text()
        self.includes = tuple(includes.replace(" ", "").split(","))
        self.files_list = []

        # Si on passe un dossier en argument
        if folderpath:
            self.root_folderpath = folderpath
            self.recursive_file_list()
            self.update_table()


    def init_ui(self):
        loadUi(os.path.join(QDir.currentPath(), 'gui.ui'), self)
        self.setWindowTitle("{} - {}".format(self.app_name, self.app_version))


    def setup_events(self):
        self.pushButton.clicked.connect(self.event_on_launch_button_clicked)
        self.pushButton_3.clicked.connect(self.event_on_select_folder_button_clicked)


    def event_on_select_folder_button_clicked(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Choisir un dossier pour l'analyse")
        if folder_path and os.path.exists(folder_path):
            self.root_folderpath = folder_path

            if self.checkBox.checkState() != Qt.Checked:
                self.files_list.clear()

            # Et on liste les fichiers -> voir vue personalisée ?
            self.recursive_file_list()
            self.update_table()


    def update_table(self):
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(len(self.files_list))

        for row_index, file in enumerate(self.files_list):
            self.tableWidget.setItem(row_index, 0, QTableWidgetItem(file.filename))
            self.tableWidget.setItem(row_index, 1, QTableWidgetItem(file.folder_path))
            self.tableWidget.setItem(row_index, 2, QTableWidgetItem(file.crc32_from_name))

        self.label.setText("{} éléments".format(len(self.files_list)))


    def recursive_file_list(self):
        for root, directories, filenames in os.walk(self.root_folderpath):
            for filename in human_sort(filenames):
                file_path = os.path.join(root, filename)
                if filename.endswith(self.includes) and file_path not in self.files_list:
                    file_object = File(file_path)

                    # On affiche tout les fichier si coché
                    if self.checkBox_2.checkState() == Qt.Checked:
                        if file_object.crc32_from_name:
                            self.files_list.append(file_object)
                    else:
                        self.files_list.append(file_object)


    def event_on_launch_button_clicked(self):
        if self.root_folderpath and os.path.exists(self.root_folderpath):
            # Init progressbar current value
            self.progressbar.setValue(self.progressbar.minimum())

            # Create thread
            worker = Worker(self.files_list)
            worker.signals.worker_data.connect(self.file_is_checked_event)

            # Execute
            self.threadpool.start(worker)


    def file_is_checked_event(self, row_index, crc32_from_file, color):
        self.update_row_color(row_index, crc32_from_file, color)
        self.update_progress_bar(row_index)


    def update_row_color(self, row_index, crc32_from_file, color):
        item = QTableWidgetItem(crc32_from_file)
        item.setBackground(QColor(color[0], color[1], color[2]))
        self.tableWidget.setItem(row_index, 3, item)


    def update_progress_bar(self, row_index):
        percentage = (row_index + 1) * (100 / len(self.files_list))
        self.progressbar.setValue(int(percentage))


class File():
    def __init__(self, filepath):
        self.filepath = filepath
        self.folder_path = os.path.dirname(self.filepath)
        self.filename = os.path.basename(self.filepath)
        self.crc32_from_name = self.get_crc_from_name()
        self.crc32_from_data = None


    def __repr__(self):
        return self.filepath


    def __str__(self):
        return self.filepath


    def exists(self):
        return os.path.exists(self.filepath)


    def get_crc_from_name(self):
        # Regex trouvé dans AnimeCheck
        split_regex = re.split('([a-f0-9]{8})', self.filename, flags=re.IGNORECASE)
        return None if len(split_regex) < 2 else split_regex[-2]


    def get_crc_from_file(self):
        # https://www.matteomattei.com/how-to-calculate-the-crc32-of-a-file-in-python/

        blocksize = 4096
        with open(self.filepath, 'rb') as f:
            data = f.read(blocksize)
            crcvalue = 0
            while len(data) > 0:
                crcvalue = zlib.crc32(data, crcvalue)
                data = f.read(blocksize)

        return format(crcvalue & 0xFFFFFFFF, '08x').upper() # Exemple: a509ae4b


    def is_file_ok(self):
        return (self.crc32_from_name == self.crc32_from_data)


class ProgressThread(QThread):
    pass


class CustomTableView(QTableView):
    def __init__(self):
        super().__init__()


def human_sort(data: list):
    return data

#recursive_file_list("/home/seigneurfuo/Téléchargements", include=(".avi"))

def main():
    application = QApplication(sys.argv)

    folderpath = None
    if len(sys.argv) == 2 and os.path.isdir(sys.argv[1]):
        folderpath = sys.argv[1]

    mainwindow = MainWindow(folderpath)
    mainwindow.show()
    application.exec_()

if __name__ == "__main__":
    main()
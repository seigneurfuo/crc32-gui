import sys
import os
import re
import platform
import zlib

from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QFileDialog, QProgressBar, QTableWidgetItem
from PyQt5.uic import loadUi
from PyQt5.QtCore import QDir, QThread, Qt, QObject, QRunnable, pyqtSignal, pyqtSlot, QThreadPool, QUrl
from PyQt5.QtGui import QColor


class WorkerData():
    """"""

    def __init__(self):
        self.row_id = None
        self.text = None
        self.background_color = None


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    progress
        int progress complete,from 0-100
    '''

    main_progression_signal = pyqtSignal(int, str, tuple) # row_index, crc32_from_file, color)
    current_file_progression = pyqtSignal(int) # pourcentage actuel


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
        """"""

        for row_index, file in enumerate(self.files_list):
            crc32_from_name = file.crc32_from_name
            #crc32_from_file = file.get_crc_from_file()


            # region ----- Calcul du CRC -----
            # https://www.matteomattei.com/how-to-calculate-the-crc32-of-a-file-in-python/
            current_block = 0
            blocksize = 4096
            old_percentage = 0

            # TODO: if os.path.isfile(file.filepath):

            with open(file.filepath, 'rb') as f:
                crcvalue = 0
                data = f.read(blocksize)
                file_byte_size = os.path.getsize(file.filepath)
                self.signals.current_file_progression.emit(0)

                while len(data) > 0:
                    crcvalue = zlib.crc32(data, crcvalue)
                    data = f.read(blocksize)

                    # region ----- Progression of the current file -----
                    current_block += blocksize
                    percentage = int(current_block * (100 / file_byte_size))

                    # Percentage increase only if different (avoid too much refresh
                    if percentage != old_percentage:
                        self.signals.current_file_progression.emit(percentage)

                    old_percentage = percentage
                    # endregion

            crc32_from_file = format(crcvalue & 0xFFFFFFFF, '08x').upper()  # Exemple: a509ae4b
            # endregion

            if (crc32_from_name):
                if crc32_from_file == crc32_from_name:
                    color = (0, 255, 0)
                else:
                    color = (255, 0, 0)
            else:
                color = (255, 255, 255)

            self.signals.main_progression_signal.emit(row_index, crc32_from_file, color)


class TableWidgetColumns:
    """"""

    name = 0
    size = 1
    folder = 2
    saved_crc = 3
    current_crc = 4


class MainWindow(QMainWindow):
    def __init__(self, folderpath):
        super().__init__()

        self.app_name = "CRC32 GUI"
        self.app_version = "0.3.3"

        self.init_ui()
        self.setup_events()

        self.threadpool = QThreadPool()

        self.root_folderpath = ""

        includes = self.allowed_extensions.text()
        self.includes = tuple(includes.replace(" ", "").split(","))
        self.files_list = []

        # Si on passe un dossier en argument
        if folderpath:
            self.root_folderpath = folderpath
            self.recursive_file_list()
            self.update_table()


    def init_ui(self):
        """"""

        loadUi(os.path.join(os.path.join(os.path.dirname(__file__)), 'gui.ui'), self)
        self.setWindowTitle("{} - {}".format(self.app_name, self.app_version))

        self.setAcceptDrops(True)


    def setup_events(self):
        """"""

        self.pushButton.clicked.connect(self.event_on_launch_button_clicked)
        self.pushButton_3.clicked.connect(self.event_on_select_folder_button_clicked)

        #
        self.pushButton_4.clicked.connect(self.on_open_folder_button_click)

    def dragEnterEvent(self, event):

        folderpath = QUrl(event.mimeData().text()).toLocalFile()

        self.root_folderpath = folderpath
        self.recursive_file_list()
        self.update_table()


    def on_open_folder_button_click(self):
        """"""

        current_row_index = self.tableWidget.currentRow()
        if(current_row_index != -1):
            print(current_row_index)
            folder_path = self.files_list[current_row_index].folder_path
            open_filebrowser(folder_path)


    def event_on_select_folder_button_clicked(self):
        """"""

        folder_path = QFileDialog.getExistingDirectory(self, "Choisir un dossier pour l'analyse")
        if folder_path and os.path.exists(folder_path):
            self.root_folderpath = folder_path

            if self.checkBox.checkState() != Qt.Checked:
                self.files_list.clear()

            # Et on liste les fichiers -> voir vue personalisée ?
            self.recursive_file_list()
            self.update_table()


    def update_table(self):
        """"""

        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(len(self.files_list))

        for row_index, file in enumerate(self.files_list):
            self.tableWidget.setItem(row_index, TableWidgetColumns.name, QTableWidgetItem(file.filename))
            self.tableWidget.setItem(row_index, TableWidgetColumns.size, QTableWidgetItem(file.size))
            self.tableWidget.setItem(row_index, TableWidgetColumns.folder, QTableWidgetItem(file.folder_path))
            self.tableWidget.setItem(row_index, TableWidgetColumns.saved_crc, QTableWidgetItem(file.crc32_from_name))

        self.tableWidget.resizeColumnsToContents()

        self.label.setText("{} éléments".format(len(self.files_list)))


    def recursive_file_list(self):
        """"""

        print("Recursive folder:", self.root_folderpath)

        for root, directories, filenames in os.walk(self.root_folderpath):
            print('bite ?')
            for filename in human_sort(filenames):
                file_path = os.path.join(root, filename)

                print(file_path)

                if filename.endswith(self.includes) and file_path not in self.files_list:
                    file_object = File(file_path)

                    # On affiche tout les fichier si coché
                    if self.checkBox_2.checkState() == Qt.Checked:
                        if file_object.crc32_from_name:
                            self.files_list.append(file_object)
                    else:
                        self.files_list.append(file_object)


    def event_on_launch_button_clicked(self):
        """"""

        if self.root_folderpath and os.path.exists(self.root_folderpath):
            # Init progressbar current value
            self.progressbar.setValue(self.progressbar.minimum())

            # Create thread
            worker = Worker(self.files_list)
            worker.signals.main_progression_signal.connect(self.when_file_is_checked)
            worker.signals.current_file_progression.connect(self.current_file_progression)

            # Execute
            self.threadpool.start(worker)


    def when_file_is_checked(self, row_index, crc32_from_file, color):
        """"""

        self.update_row_color(row_index, crc32_from_file, color)
        self.update_progress_bar(row_index)


    def current_file_progression(self, percentage):
        """"""

        self.progressbar_2.setValue(int(percentage))


    def update_row_color(self, row_index, crc32_from_file, color, row_id=TableWidgetColumns.current_crc):
        """"""

        item = QTableWidgetItem(crc32_from_file)
        item.setBackground(QColor(color[0], color[1], color[2]))
        self.tableWidget.setItem(row_index, row_id, item)


    def update_progress_bar(self, row_index):
        """"""

        percentage = (row_index + 1) * (100 / len(self.files_list))
        self.progressbar.setValue(int(percentage))


class File():
    def __init__(self, filepath):
        self.filepath = filepath
        self.folder_path = os.path.dirname(self.filepath)
        self.filename = os.path.basename(self.filepath)
        self.size = self.get_size()
        self.crc32_from_name = self.get_crc_from_name()
        self.crc32_from_data = None


    def __repr__(self):
        return self.filepath


    def __str__(self):
        return self.filepath


    def exists(self):
        """"""

        return os.path.exists(self.filepath)


    def get_crc_from_name(self):
        """"""

        # Regex trouvé dans AnimeCheck
        split_regex = re.split('([a-f0-9]{8})', self.filename, flags=re.IGNORECASE)
        return None if len(split_regex) < 2 else str(split_regex[-2]).upper()


    def get_size(self):
        """"""

        size_in_bytes = os.path.getsize(self.filepath)

        if size_in_bytes > 1024 * 1024 * 1024:
            size = int(size_in_bytes / (1024 * 1024 * 1024))
            label = "Go"
        elif size_in_bytes > 1024 * 1024:
            size = int(size_in_bytes / (1024 * 1024))
            label = "Mo"
        elif size_in_bytes > 1024:
            size = int(size_in_bytes / 1024)
            label = "Ko"
        else:
            size = size_in_bytes
            label = "o"

        return "{} {}".format(size, label)


    def get_crc_from_file(self):
        """"""

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
        """"""

        return (self.crc32_from_name == self.crc32_from_data)


class CustomTableView(QTableView):
    """"""

    def __init__(self):
        super().__init__()


def human_sort(data: list):
    return data

def open_filebrowser(path):
    """Ouvre un explorateur de fichiers à l'adresse indiquée en argument"""

    try:
        if platform.system() == "Windows":
            from os import startfile
            startfile(path)

        elif platform.system() == "Darwin":
            from subprocess import Popen
            Popen(["open", path])

        else:
            from subprocess import Popen
            Popen(["xdg-open", path])

    except:
        return None

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
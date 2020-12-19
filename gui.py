import sys
import os
import re

from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QFileDialog, QProgressBar, QTableWidgetItem
from PyQt5.uic import loadUi
from PyQt5.QtCore import QDir, QThread, Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.app_name = "CRC32 GUI"
        self.app_version = "0.1"

        self.init_ui()
        self.setup_events()

        self.root_folderpath = ""
        self.includes = (".avi", ".mp4", ".mkv", ".ogm", ".mpg")
        self.files_list = []


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
            self.tableWidget.setItem(row_index, 2, QTableWidgetItem(file.crc32))

        self.label.setText("{} éléments".format(len(self.files_list)))


    def event_on_launch_button_clicked(self):
        if self.root_folderpath and os.path.exists(self.root_folderpath):
            print("On Lance !")
            pass


    def recursive_file_list(self):
        for root, directories, filenames in os.walk(self.root_folderpath):
            for filename in human_sort(filenames):
                file_path = os.path.join(root, filename)
                if filename.endswith(self.includes) and file_path not in self.files_list:
                    file_object = File(file_path)
                    print(file_object)
                    self.files_list.append(file_object)

class File():
    def __init__(self, filepath):
        self.filepath = filepath
        self.folder_path = os.path.dirname(self.filepath)
        self.filename = os.path.basename(self.filepath)
        self.crc32 = self.get_crc_from_name()

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


    def check_crc(self):
        pass


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
    mainwindow = MainWindow()
    mainwindow.show()
    application.exec_()

if __name__ == "__main__":
    main()
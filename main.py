import sqlite3
import sys

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from PyQt5.QtWidgets import *


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.previous_tracks = None
        uic.loadUi('please_be_final.ui', self)
        self.init_UI()
        self.action_methods_player = {
            'play': self.player.play,
            'pause': self.player.pause,
            'stop': self.player.stop
        }

    def init_UI(self):
        self.setWindowTitle("???")

        self.current_duration = 0

        self.player = QMediaPlayer(self)
        self.Volume_dial.setMinimum(0)
        self.Volume_dial.setMaximum(100)
        self.Volume_label.setText('100')
        self.Volume_dial.setValue(100)
        self.Volume_dial.setDisabled(True)
        self.con = sqlite3.connect("playlist.db")

        # Создание курсора
        self.cur = self.con.cursor()

        self.previous_tracks.itemClicked.connect(self.on_item_clicked)

        FileMenu = self.menuBar().addMenu('&File')

        OpenFileAction = QAction('Open...', self)
        OpenFileAction.setStatusTip('Open')
        OpenFileAction.setShortcut(QKeySequence.Open)
        OpenFileAction.triggered.connect(self.Open_File)
        FileMenu.addAction(OpenFileAction)

        PlaylistMenu = self.menuBar().addMenu('&Playlists')

        CreatePlaylistsAction = QAction('Create playlist...', self)
        CreatePlaylistsAction.setStatusTip('Create playlist')
        CreatePlaylistsAction.triggered.connect(self.create_playlist)
        PlaylistMenu.addAction(CreatePlaylistsAction)

        ExportMenu = self.menuBar().addMenu('&Export')

        Export_with_txtAction = QAction('as txt...', self)
        Export_with_txtAction.setStatusTip('as txt')
        Export_with_txtAction.triggered.connect(self.export_tracks_as_txt)
        ExportMenu.addAction(Export_with_txtAction)

        Export_with_fileAction = QAction('as files in folder...', self)
        Export_with_fileAction.setStatusTip('as files in folder...')
        Export_with_fileAction.triggered.connect(self.export_tracks_as_files)
        ExportMenu.addAction(Export_with_fileAction)

        info_about_ExportAction = QAction('info...', self)
        info_about_ExportAction.setStatusTip('info')
        info_about_ExportAction.triggered.connect(self.infoExport)
        ExportMenu.addAction(info_about_ExportAction)

        About_btn = QAction('About...', self)
        Export_with_fileAction.setStatusTip('About...')
        Export_with_fileAction.triggered.connect(self.about_programm)
        self.menuBar().addAction(About_btn)

        self.Play_btn.clicked.connect(self.play_music)
        self.Pause_btn.clicked.connect(self.pause_music)
        self.Stop_btn.clicked.connect(self.stop_music)
        self.Exit_btn.clicked.connect(self.exit_music)

        self.timelime_slider.setMinimum(0)
        self.timelime_slider.setMaximum(self.player.duration())
        self.timelime_slider.valueChanged.connect(self.on_slider_value_changed)

        self.Volume_dial.valueChanged.connect(self.set_volume)

        self.message_box_isMedia = QMessageBox(self)

        self.timer_of_timeline = QTimer()
        self.timer_of_timeline.timeout.connect(self.update_label_value_slider)
        self.timer_of_timeline.start(1000)

    def Open_File(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open", '.', "All Files (*);;")
        # "Files (*.mp3, *.wav, *.ogg, *.flac, *.flac, *.aac, *.m4a, *.alac, *.wma, *.aiff, *.opus)"
        # self.load_mp3(fileName)
        self.previous_tracks.addItem(fileName)
        self.current_duration = self.player.duration()
        self.cur.execute("""INSERT INTO tracks(playlist_id, title, track_link) VALUES('1', ?, ?)""",
                             (fileName[fileName.index('Finally') + 8:], fileName)).fetchall()
        # self.cur.close()
        self.con.commit()

    def load_mp3(self, filename):
        media = QUrl.fromLocalFile(filename)
        content = QMediaContent(media)
        self.player.setMedia(content)

    def create_playlist(self):
        pass

    def set_volume(self):
        value = self.Volume_dial.value()
        self.Volume_label.setText(str(value))
        self.player.setVolume(int(value))

    def play_music(self):
        self.check_isMedia_now('play')

    def pause_music(self):
        self.check_isMedia_now('pause')

    def stop_music(self):
        self.check_isMedia_now('stop')

    def check_isMedia_now(self, action=None):
        if self.player.media().isNull():
            self.message_box_isMedia.setWindowTitle("Сообщение")
            self.message_box_isMedia.setText("Выберите файл для воспроизведения!")
            self.message_box_isMedia.setStandardButtons(QMessageBox.Ok)
            self.message_box_isMedia.setDefaultButton(QMessageBox.Ok)
            self.message_box_isMedia.setIcon(QMessageBox.Information)

            self.message_box_isMedia.button(QMessageBox.Ok).setEnabled(False)  # делаем неактивной кнопку ОК на 3 сек
            timer = QTimer(self)
            timer.timeout.connect(self.enable_message_box_isMedia_button)
            timer.setSingleShot(True)
            timer.start(4000)
            self.message_box_isMedia.exec_()
        else:
            what_to_do = self.action_methods_player.get(action)  # забираем метод из словаря
            what_to_do()  # запускаем метод

    def enable_message_box_isMedia_button(self):
        # Включаем кнопку у MessageBox
        self.message_box_isMedia.button(QMessageBox.Ok).setEnabled(True)

    def keyPressEvent(self, event):
        # Реализация управления стрелочками self.VolumeDial😀
        if event.key() == Qt.Key_Left or event.key() == Qt.Key_Down:
            if self.Volume_dial.value() == self.Volume_dial.minimum():
                self.Volume_dial.setValue(self.Volume_dial.maximum())
            else:
                self.Volume_dial.setValue(self.Volume_dial.value() - 1)
        if event.key() == Qt.Key_Right or event.key() == Qt.Key_Up:
            if self.Volume_dial.value() == self.Volume_dial.maximum():
                self.Volume_dial.setValue(self.Volume_dial.minimum())
            else:
                self.Volume_dial.setValue(self.Volume_dial.value() + 1)

    def export_tracks_as_txt(self):
        pass

    def export_tracks_as_files(self):
        pass

    def infoExport(self):
        pass

    def about_programm(self):
        pass

    def exit_music(self):
        self.player.setMedia(QMediaContent())

    def on_item_clicked(self, item):
        print(item.text())
        self.load_mp3(item.text())

    def on_slider_value_changed(self, value):
        self.player.setPosition(value)

    def update_label_value_slider(self):
        self.current_duration = self.player.duration() / 1000
        current_position = self.player.position() / 1000
        minutes_now = int(current_position // 60)
        seconds_now = int(current_position % 60)
        self.NowTime_label.setText(f'{minutes_now:02}:{seconds_now:02}')
        remain = self.current_duration - current_position
        minutes_remain = int(remain // 60)
        seconds_remain = int((remain % 60))
        self.RemainTime_label.setText(f'-{minutes_remain:02}:{seconds_remain:02}')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())

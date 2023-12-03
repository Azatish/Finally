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
        self.init_database()

    def init_database(self):  # заполнение QTreeWidget-а актуальными плейлистами из db
        cursor = self.con.cursor()
        cursor.execute("SELECT id, name FROM playlist_s")
        playlists = cursor.fetchall()
        cursor.execute("SELECT playlist_id, title, track_link FROM tracks")
        tracks = cursor.fetchall()
        playlist_tracks = {}
        for track in tracks:
            playlist_id = track[0]
            if playlist_id in playlist_tracks:
                playlist_tracks[playlist_id].append(track)
            else:
                playlist_tracks[playlist_id] = [track]

        for playlist in playlists:
            playlist_item = QTreeWidgetItem(self.tree, [playlist[1]])
            playlist_id = playlist[0]
            if playlist_id in playlist_tracks:
                for track in playlist_tracks[playlist_id]:
                    track_item = QTreeWidgetItem(playlist_item, [track[1]])
                    track_item.setToolTip(0, track[2])
                    track_item.setFlags(track_item.flags() | ~Qt.ItemIsEditable)

        self.tree.itemClicked.connect(self.track_clicked)
        button = QTreeWidgetItem(self.tree, ['Create New Playlist'])
        button.setFlags(button.flags() & ~Qt.ItemIsEditable)
        self.tree.show()

    def init_UI(self):
        self.setWindowTitle("???")

        self.current_duration = 0

        # player от QMediaPlayer
        self.player = QMediaPlayer(self)

        # настройка dial-а для управления громкости музыки
        self.Volume_dial.setMinimum(0)
        self.Volume_dial.setMaximum(100)
        self.Volume_label.setText('100')
        self.Volume_dial.setValue(100)
        self.Volume_dial.valueChanged.connect(self.set_volume)

        # db
        self.con = sqlite3.connect("playlist.db")
        self.cur = self.con.cursor()

        #
        self.previous_tracks.itemClicked.connect(self.on_item_clicked)

        # создание menu_bar-ов
        FileMenu = self.menuBar().addMenu('&File')

        OpenFileAction = QAction('Open...', self)
        OpenFileAction.setStatusTip('Open')
        OpenFileAction.setShortcut(QKeySequence.Open)
        OpenFileAction.triggered.connect(self.Open_File)
        FileMenu.addAction(OpenFileAction)

        PlaylistMenu = self.menuBar().addMenu('&Playlists')

        CreatePlaylistsAction = QAction('Create playlist...', self)
        CreatePlaylistsAction.setStatusTip('Create playlist')
        CreatePlaylistsAction.triggered.connect(self.create_new_playlist)
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

        # подключаем кнопки к функциям воспроизведения, паузы и приостановки трека в player-е
        self.Play_btn.clicked.connect(self.play_music)
        self.Pause_btn.clicked.connect(self.pause_music)
        self.Stop_btn.clicked.connect(self.stop_music)
        # self.add_to_playlist.clicked.connect(self.add_to_playlist)

        # слайдер для перемещения по треку
        self.timelime_slider.setMinimum(0)
        self.timelime_slider.setMaximum(self.player.duration())
        self.timelime_slider.valueChanged.connect(self.on_slider_value_changed)

        # создание messagebox-ов
        self.message_box_isMedia = QMessageBox(self)
        self.message_box_new_playlist = QMessageBox(self)

        #
        self.timer_of_timeline = QTimer()
        self.timer_of_timeline.timeout.connect(self.update_label_value_slider)
        self.timer_of_timeline.start(1000)

        # подключаем к плейлистам возможность при нажатии на правую кнопку мыши открывать контексное меню
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(show_context_menu)

    def Open_File(self):  # открытие файла
        try:
            fileName, _ = QFileDialog.getOpenFileName(self, "Open", '.', "All Files (*);;")
            # "Files (*.mp3, *.wav, *.ogg, *.flac, *.flac, *.aac, *.m4a, *.alac, *.wma, *.aiff, *.opus)"
            # self.load_mp3(fileName)
            self.previous_tracks.addItem(fileName)
            self.current_duration = self.player.duration()
            self.cur.execute("""INSERT INTO tracks(playlist_id, title, track_link) VALUES('1', ?, ?)""",
                             (fileName[fileName.index('Finally') + 8:], fileName)).fetchall()
            # self.cur.close()
            self.con.commit()
        except ValueError:
            pass

    def load_mp3(self, filename):  # загрузить в плеер музыку
        media = QUrl.fromLocalFile(filename)
        content = QMediaContent(media)
        self.player.setMedia(content)

    def set_volume(self):  # установить громкость музыки
        value = self.Volume_dial.value()
        self.Volume_label.setText(str(value))
        self.player.setVolume(int(value))

    def play_music(self):  # играть музыку
        self.check_isMedia_now('play')

    def pause_music(self):  # пауза музыки
        self.check_isMedia_now('pause')

    def stop_music(self):  # остановить воспроизведение музыки
        self.check_isMedia_now('stop')

    def check_isMedia_now(self, action=None):  # проверка(занят ли плеер в данный момент)
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
            activate = self.action_methods_player.get(action)  # забираем метод из словаря
            activate()  # запускаем метод

    def enable_message_box_isMedia_button(self):  # Включаем кнопку у MessageBox
        self.message_box_isMedia.button(QMessageBox.Ok).setEnabled(True)

    # def keyPressEvent(self, event):
    #     # Реализация управления стрелочками self.VolumeDial😀
    #     if event.key() == Qt.Key_Left or event.key() == Qt.Key_Down:
    #         if self.Volume_dial.value() == self.Volume_dial.minimum():
    #             self.Volume_dial.setValue(self.Volume_dial.maximum())
    #         else:
    #             self.Volume_dial.setValue(self.Volume_dial.value() - 1)
    #     if event.key() == Qt.Key_Right or event.key() == Qt.Key_Up:
    #         if self.Volume_dial.value() == self.Volume_dial.maximum():
    #             self.Volume_dial.setValue(self.Volume_dial.minimum())
    #         else:
    #             self.Volume_dial.setValue(self.Volume_dial.value() + 1)

    def export_tracks_as_txt(self):  # экспорт треков плейлиста в txt файл
        pass

    def export_tracks_as_files(self):  # экспорт треков плейлиста в папку
        pass

    def infoExport(self):  # информация о экспорте треков
        pass

    def about_programm(self):  # информация о программе
        pass

    # def add_to_playlist(self):
    #     pass

    def on_item_clicked(self, item):  # загрузка файла в player
        print(item.text())
        self.load_mp3(item.text())

    def on_slider_value_changed(self, value):  # изменение громкости player-а
        self.player.setPosition(value)

    def update_label_value_slider(self):  # текущее время трека
        self.current_duration = self.player.duration() / 1000
        current_position = self.player.position() / 1000
        minutes_now = int(current_position // 60)
        seconds_now = int(current_position % 60)
        self.NowTime_label.setText(f'{minutes_now:02}:{seconds_now:02}')
        remain = self.current_duration - current_position
        minutes_remain = int(remain // 60)
        seconds_remain = int((remain % 60))
        self.RemainTime_label.setText(f'-{minutes_remain:02}:{seconds_remain:02}')

    def create_new_playlist(self):
        name, ok = QInputDialog.getText(None, 'Create New Playlist', 'Enter playlist name:')
        if ok and name:
            self.cur.execute('INSERT INTO playlist_s (name) VALUES (?)', (name,))
            self.con.commit()
            playlist_item = QTreeWidgetItem(self.tree, [name])
            playlist_item.setFlags(playlist_item.flags() | Qt.ItemIsEditable)
            self.tree.setCurrentItem(playlist_item)
        else:
            QMessageBox.warning(None, "Invalid Input", "Invalid playlist name.")

    def track_clicked(self, item, column):
        track_link = item.toolTip(column)
        print("Track Path:", track_link)

    def show_context_menu(position):  # контекстное меню для добавления треков в плейлист
        # Определение выбранного элемента
        item = tree_widget.itemAt(position)

        # Проверка, является ли выбранный элемент главным элементом
        if item and item.parent() is None:
            # Создаем контекстное меню
            context_menu = QMenu(tree_widget)

            # Действия в контекстном меню
            action1 = QAction("Действие 1", tree_widget)
            action2 = QAction("Действие 2", tree_widget)

            # Добавляем действия в контекстное меню
            context_menu.addAction(action1)
            context_menu.addAction(action2)

            # Показываем контекстное меню в указанной позиции
            context_menu.exec_(tree_widget.mapToGlobal(position))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())

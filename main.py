import sqlite3

import sys

from os.path import basename as bs

from PyQt5 import uic
from PyQt5.QtCore import Qt, QTime, QUrl, QTimer
from PyQt5.QtGui import QPixmap, QKeySequence
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import (QMainWindow, QApplication, QAction, QMessageBox, QTreeWidgetItem, QFileDialog, \
                             QInputDialog, QMenu)

from mutagen.id3 import ID3
from mutagen import MutagenError

from export_files import PlaylistExporter_file
from export_txts import PlaylistExporter_txt


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi('please_be_final.ui', self)

        self.init_UI()

        self.action_methods_player = {
            'play': self.player.play,
            'pause': self.player.pause,
            'stop': self.player.stop
        }
        self.player.positionChanged.connect(self.position_ch)
        self.player.durationChanged.connect(self.duration_ch)
        self.timelime_slider.sliderMoved.connect(self.slider_triggered)

        self.init_database()

    def init_database(self):  # заполнение QTreeWidget-а актуальными плейлистами из db
        self.tree.clear()
        self.tree.setHeaderHidden(True)
        self.previous_tracks.clear()

        cursor_for_prev_tracks = self.con.cursor()
        cursor_for_prev_tracks.execute("SELECT track_link FROM tracks WHERE playlist_id = 1")
        tracks = cursor_for_prev_tracks.fetchall()
        for track in tracks:
            track_link = track[0]
            file_name = bs(track_link)
            self.previous_tracks.addItem(file_name)

        cursor = self.con.cursor()
        cursor.execute("SELECT id, name FROM playlist_s WHERE id <> 1")
        playlists = cursor.fetchall()
        cursor.execute("SELECT playlist_id, title, track_link FROM tracks WHERE playlist_id <> 1")
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
                    track_item.setFlags(track_item.flags() | Qt.ItemIsSelectable)

        self.tree.itemClicked.connect(self.track_clicked)
        self.tree.show()

    def init_UI(self):
        self.setWindowTitle("???")
        self.setWindowFlags(
            Qt.CustomizeWindowHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.setFixedSize(775, 608)
        pixmap = QPixmap('background.jpg')
        self.label.resize(433, 439)
        self.label.setPixmap(pixmap.scaled(self.label.size(), Qt.KeepAspectRatioByExpanding))
        print(self.label.size())

        # player от QMediaPlayer
        self.player = QMediaPlayer(self)

        # настройка dial-а для управления громкости музыки
        self.Volume_dial.setMinimum(0)
        self.Volume_dial.setMaximum(100)
        self.Volume_label.setText('100')
        self.Volume_dial.setValue(100)
        self.Volume_dial.valueChanged.connect(self.set_volume)

        # db + cursor
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

        # подключаем кнопки к функциям воспроизведения, паузы и приостановки трека в player-е
        self.Play_btn.clicked.connect(self.play_music)
        self.Pause_btn.clicked.connect(self.pause_music)
        self.Stop_btn.clicked.connect(self.stop_music)
        self.exit_btn.clicked.connect(self.exit_music)

        # слайдер для перемещения по треку
        self.timelime_slider.setMinimum(0)

        # создание messagebox-ов
        self.message_box_isMedia = QMessageBox(self)
        self.message_box_new_playlist = QMessageBox(self)
        self.message_box_about_export = QMessageBox(self)

        # подключаем к плейлистам возможность при нажатии на правую кнопку мыши открывать контексное меню
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        self.NowTime_label.setText('00:00:00')

    def Open_File(self):  # открытие файла
        fileName, _ = QFileDialog.getOpenFileName(self, "Open", '.', "*.mp3;; *.wav;; *.ogg;; *.flac;; *.m4a;; *.wma")
        self.previous_tracks.addItem(bs(fileName))
        self.cur.execute("""INSERT INTO tracks(playlist_id, title, track_link) VALUES('1', ?, ?)""",
                         (bs(fileName), fileName)).fetchall()
        # self.cur.close()
        self.con.commit()

    def load_mp3(self, filename):  # загрузить в плеер музыку
        print(filename)
        media = QUrl.fromLocalFile(filename)
        content = QMediaContent(media)
        self.player.setMedia(content)

        if filename.split('.')[-1] == 'mp3':
            try:
                audio = ID3(filename)
                print(audio)
                pixmap = QPixmap()
                if 'APIC:' in audio:
                    apic = audio['APIC:'].data
                    pixmap.loadFromData(apic)
                else:
                    pixmap = QPixmap('background.jpg')
            except MutagenError:
                pixmap = QPixmap('background.jpg')
        else:
            pixmap = QPixmap('background.jpg')

        self.label.resize(433, 439)
        self.label.setPixmap(pixmap.scaled(self.label.size(), Qt.KeepAspectRatioByExpanding))
        # self.label.setPixmap(pixmap)

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
        self.NowTime_label.setText('00:00:00')

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

    def export_tracks_as_txt(self):  # экспорт треков плейлиста в txt файл
        widget = PlaylistExporter_txt()
        widget.show()

    def export_tracks_as_files(self):  # экспорт треков плейлиста в папку
        widget = PlaylistExporter_file()
        widget.show()

    def infoExport(self):  # информация о экспорте треков
        self.message_box_about_export.setWindowTitle("Важное сообщение")
        # Устанавливаем текст сообщения
        self.message_box_about_export.setText(
            "Моя программа мп3-плеер предлагает удобную функцию экспорта файлов в текстовый формат, а также создания "
            "копии в определенной папке. Этот важный функционал позволяет сохранять информацию о ваших аудиофайлах в "
            "читаемом и удобном для обработки формате.' Выбирая экспорт в текстовый файл, вы можете создать подробное "
            "описание своих музыкальных композиций, включая информацию о названии, исполнителе, альбоме, годе выпуска и "
            "других дополнительных данных. Экспортированный текстовый файл можно легко редактировать и делиться с другими "
            "пользователями или использовать в качестве резервной копии для вашей музыкальной коллекции. Копирование файлов "
            "в определенную папку также позволяет вам организовать вашу музыкальную библиотеку по вашим предпочтениям. Вы "
            "можете выбрать папку, которая будет содержать полные копии ваших файлов, и управлять этими копиями на ваше "
            "усмотрение. Это удобно, когда вы хотите иметь дополнительные копии файлов или перенести их на другие устройства.")
        # Добавляем кнопку "ОК" для закрытия окна
        self.message_box_about_export.show()

    def on_item_clicked(self, item):
        # загрузка файла в player
        self.load_mp3(item.text())

    def create_new_playlist(self):
        name, ok = QInputDialog.getText(None, 'Create New Playlist', 'Enter playlist name:')
        if ok and name:
            cursor = self.con.cursor()
            cursor.execute("SELECT name FROM playlist_s WHERE name = ?", (name,))
            existing_playlist = cursor.fetchone()
            if existing_playlist:
                QMessageBox.warning(None, "Invalid Input", "Playlist with this name already exists!")
            else:
                self.cur.execute('INSERT INTO playlist_s (name) VALUES (?)', (name,))
                self.con.commit()
                playlist_item = QTreeWidgetItem(self.tree, [name])
                playlist_item.setFlags(playlist_item.flags() | Qt.ItemIsEditable)
                self.tree.setCurrentItem(playlist_item)
        else:
            QMessageBox.warning(None, "Invalid Input", "Invalid playlist name.")

    def track_clicked(self, item, column): # загрузка трека в player(QTreeWidget)
        track_link = item.toolTip(column)
        print(track_link)
        self.load_mp3(track_link)

    def show_context_menu(self, position):  # контекстное меню для добавления треков в плейлист
        # Определение выбранного элемента
        item = self.tree.itemAt(position)

        # Проверка, является ли выбранный элемент главным элементом
        if item and item.parent() is None:
            # Создаем контекстное меню
            context_menu = QMenu(self.tree)

            # Действия в контекстном меню
            self.action1 = QAction("Добавить трек", self.tree)
            self.action1.triggered.connect(self.do_action)
            # Добавляем действия в контекстное меню
            context_menu.addAction(self.action1)

            # Показываем контекстное меню в указанной позиции
            context_menu.exec_(self.tree.mapToGlobal(position))

    def do_action(self):
        current_item = self.tree.currentItem()
        if current_item:
            playlist_name = current_item.text(0)
            file_dialog = QFileDialog()
            file_path = file_dialog.getOpenFileName(self, 'Choose file:')[0]
            if file_path:
                cursor = self.con.cursor()
                cursor.execute("SELECT id FROM playlist_s WHERE name = ?", (playlist_name,))
                playlist_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO tracks (playlist_id, title, track_link) VALUES (?, ?, ?)",
                               (playlist_id, bs(file_path), file_path))
                self.con.commit()
                self.init_database()
            else:
                QMessageBox.warning(None, "Invalid Input", "Invalid file path.")
        else:
            QMessageBox.warning(None, "Invalid Input", "Please select a playlist first.")

    def exit_music(self):
        self.player.setMedia(QMediaContent())
        self.NowTime_label.setText('00:00:00')

    def duration_ch(self, duration):
        self.timelime_slider.setRange(0, duration)

    def position_ch(self, position):
        if(self.timelime_slider.maximum() != self.player.duration()):
            self.timelime_slider.setMaximum(round(self.player.duration() / 2))

        self.timelime_slider.setValue(position)

        seconds = (position / 1000) % 60
        minutes = (position / 60000) % 60
        hours = (position / 2600000) % 24
        time = QTime(round(hours), round(minutes), round(seconds))

        if position != self.player.duration():
            self.NowTime_label.setText(time.toString())

    def slider_triggered(self, position):
        self.player.setPosition(position)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())

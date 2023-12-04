import sqlite3

import sys

from os.path import basename as bs

from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QKeySequence, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import (QMainWindow, QApplication, QAction, QMessageBox, QTreeWidgetItem, QFileDialog, \
                             QInputDialog, QMenu)

from mutagen.id3 import ID3

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
        self.init_database()

    def init_database(self):  # заполнение QTreeWidget-а актуальными плейлистами из db
        self.tree.clear()
        self.tree.setHeaderHidden(True)

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

        self.current_duration = 0

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

        About_btn = QAction('About...', self)
        Export_with_fileAction.setStatusTip('About...')
        Export_with_fileAction.triggered.connect(self.about_programm)
        self.menuBar().addAction(About_btn)

        # подключаем кнопки к функциям воспроизведения, паузы и приостановки трека в player-е
        self.Play_btn.clicked.connect(self.play_music)
        self.Pause_btn.clicked.connect(self.pause_music)
        self.Stop_btn.clicked.connect(self.stop_music)
        self.exit_btn.clicked.connect(self.exit_music)

        # слайдер для перемещения по треку
        self.timelime_slider.setMinimum(0)
        # self.timelime_slider.setMaximum(self.player.duration())
        self.timelime_slider.valueChanged.connect(self.on_slider_value_changed)
        self.timelime_slider.setEnabled(True)

        # создание messagebox-ов
        self.message_box_isMedia = QMessageBox(self)
        self.message_box_new_playlist = QMessageBox(self)
        self.message_box_about_export = QMessageBox(self)

        #
        self.timer_of_timeline = QTimer()
        self.timer_of_timeline.timeout.connect(self.update_label_value_slider)
        self.timer_of_timeline.start(1000)

        # подключаем к плейлистам возможность при нажатии на правую кнопку мыши открывать контексное меню
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

    def Open_File(self):  # открытие файла
        fileName, _ = QFileDialog.getOpenFileName(self, "Open", '.', "All Files (*);;")
        # "Files (*.mp3, *.wav, *.ogg, *.flac, *.flac, *.aac, *.m4a, *.alac, *.wma, *.aiff, *.opus)"
        self.previous_tracks.addItem(bs(fileName))
        self.cur.execute("""INSERT INTO tracks(playlist_id, title, track_link) VALUES('1', ?, ?)""",
                         (bs(fileName), fileName)).fetchall()
        print(fileName)
        # self.cur.close()
        self.con.commit()

    def load_mp3(self, filename):  # загрузить в плеер музыку
        media = QUrl.fromLocalFile(filename)
        content = QMediaContent(media)
        self.player.setMedia(content)
        self.timelime_slider.setMaximum(self.player.duration())

        if filename.split('.')[-1] == 'mp3':
            audio = ID3(filename)
            print(audio)
            pixmap = QPixmap()
            if 'APIC:' in audio:
                apic = audio['APIC:'].data
                pixmap.loadFromData(apic)
            else:
                pixmap = QPixmap('background.jpg')
        else:
            pixmap = QPixmap('background.jpg')
        self.label.setPixmap(pixmap.scaled(self.label.size(), Qt.KeepAspectRatio))
        # self.label.setPixmap(pixmap)

    def set_volume(self):  # установить громкость музыки
        value = self.Volume_dial.value()
        self.Volume_label.setText(str(value))
        self.player.setVolume(int(value))

    def play_music(self):  # играть музыку
        self.update_labels()
        self.check_isMedia_now('play')

    def pause_music(self):  # пауза музыки
        self.check_isMedia_now('pause')

    def stop_music(self):  # остановить воспроизведение музыки
        self.check_isMedia_now('stop')
        self.NowTime_label.setText('00:00')
        self.RemainTime_label.setText('00:00')

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
        self.message_box_about_export.addButton(QMessageBox.Ok)
        self.message_box_about_export.show()

    def on_item_clicked(self, item):
        # загрузка файла в player
        self.load_mp3(item.text())

    def on_slider_value_changed(self, value):  # перемещение по треку в player-е
        self.timer_of_timeline.stop()
        # Установка текущей позиции трека в соответствии со значением слайдера
        self.player.setPosition(value * 1000)

    def update_label_value_slider(self):  # текущее время трека
        self.timelime_slider.setEnabled(True)

        self.current_duration = self.player.duration() / 1000
        current_position = self.player.position() / 1000
        minutes_now = int(current_position // 60)
        seconds_now = int(current_position % 60)
        self.NowTime_label.setText(f'{minutes_now:02}:{seconds_now:02}')
        remain = self.current_duration - current_position
        minutes_remain = int(remain // 60)
        seconds_remain = int((remain % 60))
        self.RemainTime_label.setText(f'-{minutes_remain:02}:{seconds_remain:02}')

        self.timelime_slider.setValue(int(current_position))

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
        # Получить текущий элемент QTreeWidgetItem
        current_item = self.tree.currentItem()

        playlist_name = current_item.text(0)

        # Выполнить нужные действия с выбранным плейлистом
        # Например, открыть диалоговое окно выбора файла мп3
        file_dialog = QFileDialog()
        file_path = file_dialog.getOpenFileName(self, 'Выбрать файл:')[0]

        # Добавить трек в базу данных с нужным playlist_id
        cursor = self.con.cursor()
        cursor.execute("SELECT id FROM playlist_s WHERE name = ?", (playlist_name,))
        playlist_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO tracks (playlist_id, title, track_link) VALUES (?, ?, ?)",
                       (playlist_id, bs(file_path), file_path))
        self.con.commit()
        # cursor.close()
        self.init_database()

    def update_labels(self):
        self.current_duration = self.player.duration() / 1000
        current_position = self.player.position() / 1000
        minutes_now = int(current_position // 60)
        seconds_now = int(current_position % 60)
        self.NowTime_label.setText(f'{minutes_now:02}:{seconds_now:02}')
        remain = self.current_duration - current_position
        minutes_remain = int(remain // 60)
        seconds_remain = int((remain % 60))
        self.RemainTime_label.setText(f'-{minutes_remain:02}:{seconds_remain:02}')

    def exit_music(self):
        self.player.setMedia(QMediaContent())
        self.update_labels()
        self.label.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())

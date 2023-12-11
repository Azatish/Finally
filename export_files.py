from PyQt5.QtWidgets import QApplication, QFileDialog, QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
import sqlite3
import sys
import shutil

class PlaylistExporter_file(QWidget):
    def __init__(self):
        super().__init__()
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)

        layout = QVBoxLayout(self)

        layout.addWidget(self.tree)

        # Задаем виджету максимальную ширину и высоту
        self.setMaximumSize(400, 300)

        # Подключаемся к базе данных
        self.con = sqlite3.connect("dist/playlist.db")
        cursor = self.con.cursor()

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

        self.tree.show()

        self.tree.itemClicked.connect(lambda item, column: self.save_playlist_tracks(item))

    def save_playlist_tracks(self, item):
        arr = []
        new_arr = []
        # Открываем файл для записи
        for i in range(item.childCount()):
            track_item = item.child(i)
            track_name = track_item.text(0)
            arr.append(track_name)
        for el in arr:
            new_arr += self.con.cursor().execute('''SELECT track_link FROM tracks WHERE title = ?''', (el,)).fetchall()

        file_dialog = QFileDialog()
        self.file_path = file_dialog.getExistingDirectory(self, "Выбрать папку")

        try:
            for file_name in new_arr:
                shutil.copy(str(file_name[0]), self.file_path)
        except FileNotFoundError:
            pass

        self.close()
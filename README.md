### **Проект:** МП3 плеер
### ФИО автора/авторов: 
[![Typing SVG](https://readme-typing-svg.herokuapp.com?color=%2336BCF7&lines=Хайруллин+Азат)](https://git.io/typing-svg)
### Введение: 
#### Идея проекта состоит в создании МП3 плеера, который позволяет воспроизводить аудиофайлы различных форматов и управлять ими. Плеер разработан для решения задач прослушивания музыки, создания плейлистов, а также экспорта информации о композициях.
### **Описание реализации:**
#### Приложение реализовано на языке программирования Python с использованием библиотек PyQt5 и mutagen. Основная структура приложения состоит из класса MainWindow, который наследуется от класса QMainWindow. В приложении используются различные виджеты, такие как QTreeWidget, QMediaPlayer, QSlider и другие. Технологии, используемые в приложении:
* ![Qt](https://img.shields.io/badge/Qt-%23217346.svg?style=for-the-badge&logo=Qt&logoColor=white)PyQt5 - библиотека для создания графических интерфейсов;
* ![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)sqlite3 - модуль для работы с базами данных SQLite;
* ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)mutagen - библиотека для работы с метаданными аудиофайлов.

Код приложения охватывает функции управления воспроизведением, загрузки и экспорта аудиофайлов, создания и управления плейлистами. Приложение также предоставляет графический интерфейс, включающий различные элементы управления для удобства пользователя.
Описание функций по коду:
* ```except_hook(cls, exception, traceback)``` Функция, которая перехватывает исключения и отображает их в консоли.
* ```MainWindow(QMainWindow)``` Класс главного окна приложения. Инициализирует графический интерфейс, настраивает виджеты и подключает обработчики событий.
* ```init_database(self)``` Заполняет QTreeWidget актуальными плейлистами из базы данных.
* ```init_UI(self)``` Инициализирует пользовательский интерфейс, создает меню, подключает обработчики кнопок и действий.
* ```Open_File(self)``` Обработчик события открытия файла. Открывает диалоговое окно для выбора файла и добавляет его в список предыдущих треков.
* ```set_volume(self)``` Устанавливает громкость музыки в плеере в соответствии со значением настроенного диала.
* ```play_music(self)``` Запускает воспроизведение музыки.
* ```pause_music(self)``` Приостанавливает воспроизведение музыки.
* ```stop_music(self)``` Останавливает воспроизведение музыки и обнуляет текущую позицию трека.
* ```check_isMedia_now(self, action=None)``` Проверяет, занят ли плеер в данный момент и выполняет соответствующие действия в зависимости от состояния плеера.
* ```enable_message_box_isMedia_button(self)``` Включает кнопку в сообщении MessageBox.
* ```vexport_tracks_as_txt(self)``` Выполняет экспорт треков плейлиста в текстовый файл.
* ```export_tracks_as_files(self)``` Выполняет экспорт треков плейлиста в папку.
* ```infoExport(self)``` Отображает информацию о функции экспорта треков в MessageBox.
* ```on_item_clicked(self, item)``` Обработчик события клика на QListWidget previous_tracks. Загружает выбранный трек в плеер.
* ```on_slider_value_changed(self, value)``` Обновляет текущую позицию трека в плеере в соответствии со значением слайдера.
* ```update_label_value_slider(self)``` Обновляет информацию о текущем времени воспроизведения и оставшемся времени трека.
* ```create_new_playlist(self)``` Создает новый плейлист с введенным пользователем названием.
* ```track_clicked(self, item, column)``` Обработчик события клика на трек в плейлисте. Загружает выбранный трек в плеер.
* ```show_context_menu(self, position)``` Отображает контекстное меню для добавления треков в плейлист.
* ```do_action(self)``` Выполняет действие при выборе пункта контекстного меню для добавления трека в плейлист.
* ```update_labels(self)``` Обновляет информацию о времени воспроизведения и оставшемся времени трека.
* ```exit_music(self)``` Очищает текущий трек из плеера и обновляет информацию о времени воспроизведения. *
Это основные функции в коде. Они реализуют основной функционал приложения для работы с плейлистами и воспроизведением музыки

<br> **Доработки:** <br/>
Улучшение дизайна и пользовательского интерфейса для более удобного и привлекательного пользовательского опыта.
Реализация функционала поиска и фильтрации музыкальных композиций в базе данных.
Расширение возможностей управления плейлистами, такие как переименование, удаление и перемещение треков.

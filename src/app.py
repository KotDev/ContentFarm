import asyncio
import json
import os
from pathlib import Path

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QCheckBox, QVBoxLayout, QFileDialog
from gologin import GoLogin

from farm import FarmContents
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QMetaObject, Q_ARG
import sys


def recourse_path(file_name: str):
    """Получение абсолютного пути к ресурсу для работы с PyInstaller"""
    try:
        base_path = sys._MEIPASS  # Путь к временной папке PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")  # Обычный путь при разработке
    print(f"Resource base path: {base_path}")
    return os.path.join(base_path, file_name)

class AsyncWorker(QThread):
    """
    Класс для асинхронной фкнкции
    """

    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, coro, parent=None):
        super().__init__(parent)
        self.coro = coro

    def run(self) -> None:
        """
        Функция запуска event_loop
        :return:
        """
        asyncio.set_event_loop(asyncio.new_event_loop())
        try:
            asyncio.run(self.coro)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class CustomCheckBox(QCheckBox):
    """
    Кастомный класс chekBox
    """

    def __init__(self, text, data: dict | None = None, parent=None):
        super().__init__(text, parent)
        self.data: dict = data

    def get_data(self) -> dict:
        """
        getter метод
        :return: словарь chekBox
        """
        return self.data


class ConnectAPIWindow(QtWidgets.QMainWindow):
    """
    Класс окна подключения к API gologin
    """

    def __init__(self):
        super().__init__()
        uic.loadUi(recourse_path("utils/script_desktop.ui"), self)
        self.ConnectButton.clicked.connect(self.api_connect)

    def api_connect(self) -> None:
        """
        Метод проверки и подключения к api gologin
        :return: None
        """
        with open(recourse_path("utils/config.json"), "r+") as file:
            try:
                data = json.load(file)
                api_key_config = data.get("api_key")
                input_api_key = self.API_text.toPlainText().strip()
                if (
                    api_key_config
                    and not input_api_key
                    and self.api_key_valid(api_key_config)
                ):
                    self.open_window_script()
                elif (
                    not api_key_config
                    and input_api_key
                    and self.api_key_valid(input_api_key)
                ):
                    self.write_json(data, file, input_api_key)
                    self.open_window_script()
                elif api_key_config and input_api_key and self.api_key_valid(input_api_key):
                    self.write_json(data, file, input_api_key)
                    self.open_window_script()
                elif not api_key_config and not input_api_key:
                    self.API_text.clear()
                    self.API_text.setPlainText("Введите API ключ!")
                return
            except UnicodeEncodeError:
                self.API_text.setPlainText("Ключ содержит кириллицу")
                return

    def api_key_valid(self, api_key) -> bool:
        """
        Метод проверки валидации api токена
        :param api_key: api токен
        :return: True / False
        """
        gl = GoLogin(
            {
                "token": api_key,
            }
        )
        profiles = gl.profiles()
        if profiles.get("statusCode") == 401:
            self.API_text.clear()
            self.API_text.setPlainText("Ошибка: неверный API ключ!")
            return False
        return True

    def open_window_script(self) -> None:
        """
        Метод перехода к следующему окну приложения
        :return: None
        """
        self.script_window = ScriptWindow()
        self.script_window.show()
        self.hide()

    @classmethod
    def write_json(
        cls, data: dict, file, input_data: str
    ) -> None:
        """
        Метод записи данных api в config фалй формата json
        :param data: данные файла
        :param file: сам объект файла для записи
        :param input_data: вводимое api
        :return: None
        """
        data["api_key"] = input_data
        file.seek(0)
        json.dump(data, file)
        file.truncate()


class ScriptWindow(QtWidgets.QMainWindow):
    """
    Класс основного окна
    """

    def __init__(self):
        super().__init__()
        self.completed: int = 0
        self.task_percent: int = 0
        uic.loadUi(recourse_path("utils/script_desktop1.ui"), self)

        self.threads = []
        self.commandLinkButton.clicked.connect(self.back_api)
        with open(recourse_path("utils/config.json"), "r+") as file:
            data = json.load(file)
        self.farm = FarmContents(API_KEY=data.get("api_key"))
        self.run_async_with_result(self.get_profiles_data(), self.update_checkboxes)
        self.RloudButton.clicked.connect(
            lambda: self.run_async_with_result(
                self.get_profiles_data(), self.update_checkboxes
            )
        )
        self.browser.clicked.connect(lambda: self.run_async(self.open_browsers()))
        self.FileButton.clicked.connect(self.open_file_dialog)
        self.file_path = None
        self.progressBar.setValue(0)
        self.FilterProfileBox.addItems(["all", "instagram", "youtube", "tik-tok"])
        self.FilterProfileBox.currentTextChanged.connect(self.filter_checkbox)
        self.InstagramButton.clicked.connect(
            lambda: self.run_async(self.instagram_script())
        )
        self.AllCheckBox.stateChanged.connect(self.choose_all_profiles)
        self.errorLable.setStyleSheet("color: red;")

    def run_async(self, coro) -> None:
        """
        Метод запуска асинхронных функций
        :param coro: асинхронная функция
        :return: None
        """
        worker = AsyncWorker(coro)
        worker.finished.connect(lambda: self.threads.remove(worker))
        self.threads.append(worker)
        worker.start()

    def run_async_with_result(self, coro, callback) -> None:
        """
        Метод для асинхронных функций возвращающие результат
        :param coro: асинхронная функция
        :param callback: объект функции принимающая аргументы
        :return: None
        """

        class ResultWorker(AsyncWorker):
            result = pyqtSignal(object)
            def run(self_nonlocal):
                asyncio.set_event_loop(asyncio.new_event_loop())
                try:
                    result = asyncio.run(self_nonlocal.coro)
                    self_nonlocal.result.emit(result)
                except Exception as e:
                    self_nonlocal.error.emit(str(e))
                finally:
                    self_nonlocal.finished.emit()

        worker = ResultWorker(coro)
        worker.result.connect(callback)
        worker.finished.connect(lambda: self.threads.remove(worker))
        self.threads.append(worker)
        worker.start()

    def back_api(self) -> None:
        """
        Метод возвращения к окну ввода api клча
        :return: None
        """
        self.api_window: ConnectAPIWindow = ConnectAPIWindow()
        self.api_window.show()
        self.hide()

    async def get_profiles_data(self) -> list | None:
        """
        Метод получения всех профилей
        :return: список словарей профилей
        """
        profiles = list()
        pages = 1
        prof = await self.farm.get_profiles(pages)
        if prof is None:
            self.add_debug("Не удалось загрузить профили, проверьте корректность API")
            return None
        while prof["profiles"]:
            profiles.append(prof)
            pages += 1
            prof = await self.farm.get_profiles(pages)
        return profiles

    @classmethod
    def clear_checkbox(cls, layout) -> None:
        """
        Метод очистки chekBox
        :param layout: лояут скроллбара
        :return: None
        """
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def update_checkboxes(self, profiles: list[dict]) -> None:
        """
        Метод обновления chekbox
        :param profiles: Профили gologin
        :return:
        """
        scroll_content = self.scrollAreaWidgetContents
        layout = scroll_content.layout()
        if not layout:
            layout = QVBoxLayout(scroll_content)
            scroll_content.setLayout(layout)
        self.clear_checkbox(layout)
        if not profiles:
            return None
        for prof in profiles:
            for profile in prof["profiles"]:
                checkbox = CustomCheckBox(
                    text=profile.get("name", "Без имени"),
                    data={"folders": profile.get("folders")},
                )
                checkbox.setObjectName(profile.get("id"))
                layout.addWidget(checkbox)
        return None

    def filter_checkbox(self, filter_param: str):
        """
        Метод фильтра chekBox
        :param filter_param: параметр фильтра
        :return: None
        """
        layout = self.scrollAreaWidgetContents.layout()
        if not layout:
            return
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, CustomCheckBox):
                if (
                    filter_param not in widget.data.get("folders")
                    and filter_param != "all"
                ):
                    widget.hide()
                else:
                    widget.show()

    def choose_all_profiles(self) -> None:
        """
        Метод выбора всех chekBox
        :return: None
        """
        layout = self.scrollAreaWidgetContents.layout()
        if not layout:
            return
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, CustomCheckBox):
                if widget.isVisible() and self.AllCheckBox.isChecked():
                    widget.setChecked(True)
                else:
                    widget.setChecked(False)

    def open_file_dialog(self):
        """
        Метод открытия файлового диалогового окна
        :return: None
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбор файла", "", options=options
        )
        if not file_path:
            return

        file_path = str(Path(file_path).resolve())

        if not Path(file_path).exists():
            self.fileLable.setText("Файл не найден!")
            self.fileLable.setStyleSheet("color: red;")
            return None

        if Path(file_path).suffix.lower() not in ('.mp4', '.jpeg', '.jpg', '.png', '.img'):
            self.fileLable.setText("Неверный формат файла")
            self.fileLable.setStyleSheet("color: red;")
            return None

        self.file_path = file_path
        self.fileLable.setText(Path(file_path).name)
        self.fileLable.setStyleSheet("color: white;")
        return file_path

    def add_debug(self, text) -> None:
        """
        Метод записи в debug окно
        :param text: Текст для debug окна
        :return: None
        """
        QMetaObject.invokeMethod(
            self.textBrowser, "append", Qt.QueuedConnection, Q_ARG(str, text)
        )

    def clear_debug(self) -> None:
        """
        Метод очистки debug окна
        :return: None
        """
        QMetaObject.invokeMethod(
            self.textBrowser,
            "clear",
            Qt.QueuedConnection,
        )

    def check_any_profiles(self, layout) -> bool:
        """
        Метод для проверки хотя бы одного активированного chekBox
        :param layout: лояулт скролбара
        :return: True / False
        """
        if not any(
            [layout.itemAt(i).widget().isChecked() for i in range(layout.count())]
        ):
            self.errorLable.setText("Вы не выбрали ни один из профилей")
            return False
        return True

    async def open_browsers(self) -> None:
        """
        Метод открытия браузеров профилей
        :return: None
        """
        layout = self.scrollAreaWidgetContents.layout()
        if not layout:
            return
        elif not self.check_any_profiles(layout):
            return
        self.clear_debug()
        self.browser.setEnabled(False)
        try:
            tasks = []
            for i in range(layout.count()):
                item = layout.itemAt(i)
                widget = item.widget()
                if isinstance(widget, CustomCheckBox) and widget.isChecked():
                    self.add_debug(f"Браузер - {widget.text()} открывается")
                    task = asyncio.create_task(
                        self.open_browser(profile_id=widget.objectName(), widget=widget)
                    )
                    tasks.append(task)
            await asyncio.gather(*tasks)
        finally:
            self.browser.setEnabled(True)

    async def open_browser(self, profile_id: str, widget) -> None:
        """
        Метод открытия самого браузера
        :param profile_id: id профиля gologin
        :param widget: виджет chekBox
        :return: None
        """
        try:
            self.add_debug(f"Открывается браузер - {widget.text()}")
            await self.farm.open_browser_profile(profile_id=profile_id)
            self.add_debug(f"Браузер - {widget.text()} закрыт")
        except Exception as e:
            if "402 Payment Required" in str(e):
                self.add_debug(f"Не оплаченный прокси у {widget.text()}")
            else:
                self.add_debug(f"Браузер выдал ошибку - {e}")

    def chek_file_path(self) -> bool:
        """
        Метод проверки выбранного файла
        :return: True / False
        """
        if self.file_path is None:
            self.errorLable.setText("Вы не выбрали файл для загрузки")
            return False
        return True

    async def instagram_script(self) -> None:
        """
        Метод запуска инстаграм скрипта
        :return: None
        """
        layout = self.scrollAreaWidgetContents.layout()
        if not layout or not self.check_any_profiles(layout) or not self.chek_file_path():
            return

        self.clear_debug()
        self.InstagramButton.setEnabled(False)

        self.completed = 0
        self.progressBar.setValue(self.completed)

        # Собираем профили
        selected_widgets = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, CustomCheckBox) and widget.isChecked():
                selected_widgets.append(widget)

        if not selected_widgets:
            self.add_debug("Нет выбранных профилей для загрузки.")
            self.InstagramButton.setEnabled(True)
            return

        self.task_percent = 100 // len(selected_widgets)
        descript = self.plainTextEdit.toPlainText().strip()
        BATCH_SIZE = 2
        profile_ids = []
        for i in range(0, len(selected_widgets), BATCH_SIZE):
            batch = selected_widgets[i:i + BATCH_SIZE]
            tasks = [
                self.instagram_download_content(descript=descript, widget=widget)
                for widget in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for widget, result in zip(batch, results):
                profile_ids.append(widget.objectName())
                if isinstance(result, Exception):
                    self.add_debug(f"❌ Профиль {widget.text()} завершился с ошибкой: {str(result)}")
                else:
                    self.add_debug(f"✅ Профиль {widget.text()} успешно завершил загрузку.")

        self.farm.gl.refreshProfilesFingerprint(profileIds=profile_ids)
        self.InstagramButton.setEnabled(True)

    async def instagram_download_content(self, descript: str, widget):
        """
        Метод загрузки instagram видео
        :param descript: описание к видео
        :param widget: виджет chekBox
        :return: None
        """
        profile_id = widget.objectName()
        file_name = Path(self.file_path).name
        MAX_ATTEMPTS = 3
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                self.add_debug(f"🔁 Попытка {attempt} загрузки: {widget.text()} → {file_name}")
                relative_path = "_internal/instagram_scripts/upload.js"
                absolute_path = os.path.abspath(relative_path)

                await self.farm.instagram.download_content(
                    profile_id=profile_id,
                    file_path=str(self.file_path),
                    descript=descript,
                    js_file=absolute_path
                )

                self.completed += self.task_percent
                self.progressBar.setValue(self.completed)
                self.add_debug(f"✅ Профиль {widget.text()} успешно загрузил {file_name}")
                return  # успешно — выходим
            except Exception as e:
                self.add_debug(f"⚠️ Ошибка на попытке {attempt} профиля {widget.text()}: {str(e)}")
                if attempt == MAX_ATTEMPTS:
                    raise





def main():
    sys.path.insert(0, "src/libs")
    app = QtWidgets.QApplication(sys.argv)
    window = ConnectAPIWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

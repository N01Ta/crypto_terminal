# src/widgets/login_widget.py
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot

from ..ui.login_form_ui import LoginFormUi # Наш UI для логина
from ..core.auth_service import AuthService # Наш сервис для запросов к бэкенду

# --- Worker для выполнения запроса логина в отдельном потоке
class LoginWorker(QThread):
    # Сигнал: (dict_user_data_or_None, str_error_message_or_None)
    login_finished = pyqtSignal(object, object)

    def __init__(self, auth_service_instance, login_data_dict, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service_instance
        self.login_data = login_data_dict #  {"service_login": "...", "service_password": "..."}

    def run(self):
        try:
            print(f"[LoginWorker] Attempting to login with data: {self.login_data}")
            user_info, error_msg = self.auth_service.login_user(
                service_login=self.login_data["service_login"],
                service_password=self.login_data["service_password"]
            )
            print(f"[LoginWorker] Service call finished. User info: {user_info}, Error: {error_msg}")
            self.login_finished.emit(user_info, error_msg)
        except Exception as e:
            print(f"LoginWorker critical error: {e}")
            self.login_finished.emit(None, f"Критическая ошибка при входе в потоке: {e}")


class LoginWidget(QWidget):
    # Сигналы этого виджета
    login_successful = pyqtSignal(dict) # Передает user_info (login, api_keys: {mexc_api_key, mexc_api_secret})
    navigate_to_register = pyqtSignal()   # Сигнал для перехода на экран регистрации

    def __init__(self, auth_service: AuthService, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.ui = LoginFormUi(self) # Создаем и встраиваем UI

        layout = QVBoxLayout(self)
        layout.addWidget(self.ui)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        self.auth_worker = None # Для хранения экземпляра QThread

        self._connect_signals()

    def _connect_signals(self):
        self.ui.login_button.clicked.connect(self.handle_login_attempt)
        self.ui.go_to_register_button.clicked.connect(self.request_navigation_to_register)

    def request_navigation_to_register(self):
        self.ui.clear_error()
        self.navigate_to_register.emit() # Испускаем сигнал для MainWindow

    def _set_buttons_enabled(self, enabled: bool):
        self.ui.login_button.setEnabled(enabled)
        self.ui.go_to_register_button.setEnabled(enabled)

    def handle_login_attempt(self):
        self.ui.clear_error()
        login_data = self.ui.get_login_data() # {"service_login": "...", "service_password": "..."}

        if not login_data["service_login"] or not login_data["service_password"]:
            self.ui.display_error("Логин и пароль должны быть заполнены.")
            return

        self._set_buttons_enabled(False) # Блокируем кнопки

        self.auth_worker = LoginWorker(self.auth_service, login_data, self)
        self.auth_worker.login_finished.connect(self._handle_login_response)
        self.auth_worker.finished.connect(self._on_worker_finished)
        self.auth_worker.start()

    @pyqtSlot(object, object)
    def _handle_login_response(self, user_info, error_message):
        self._set_buttons_enabled(True)

        if error_message:
            self.ui.display_error(str(error_message))
        elif user_info:
            # user_info это dict: {"login": "...", "api_keys": {"mexc_api_key": "...", "mexc_api_secret": "..."}}
            # нужно передать дальше весь user_info, чтобы MainWindow имел доступ к login и api_keys
            print(f"Login successful for {user_info.get('login')}")
            self.ui.clear_input_fields()
            self.login_successful.emit(user_info) # Передаем весь словарь user_info
        else:
            self.ui.display_error("Произошла неизвестная ошибка при входе.")

    def _on_worker_finished(self):
        if self.auth_worker and not self.auth_worker.isRunning():
            self.auth_worker.deleteLater()
            self.auth_worker = None
            print("LoginWorker finished and scheduled for deletion.")

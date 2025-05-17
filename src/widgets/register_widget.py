# src/widgets/register_widget.py
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot

from ..ui.register_form_ui import RegisterFormUi # Наш UI для регистрации
from ..core.auth_service import AuthService    # Наш сервис для запросов к бэкенду

# --- Worker для выполнения запроса регистрации в отдельном потоке ---
class RegisterWorker(QThread):
    # Сигнал: (dict_user_data_or_None, str_error_message_or_None)
    registration_finished = pyqtSignal(object, object)

    def __init__(self, auth_service_instance, reg_data_dict, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service_instance
        self.reg_data = reg_data_dict

    def run(self):
        try:
            # Отладочный print перед вызовом сервиса
            print(f"[RegisterWorker] Attempting to register with data: {self.reg_data}")
            user_info, error_msg = self.auth_service.register_user(
                service_login=self.reg_data["service_login"],
                service_password=self.reg_data["service_password"],
                mexc_api_key=self.reg_data["mexc_api_key"],
                mexc_api_secret=self.reg_data["mexc_api_secret"]
            )
            print(f"[RegisterWorker] Service call finished. User info: {user_info}, Error: {error_msg}") # Отладка
            self.registration_finished.emit(user_info, error_msg)
        except Exception as e:
            print(f"RegisterWorker critical error: {e}")
            self.registration_finished.emit(None, f"Критическая ошибка при регистрации в потоке: {e}")


class RegisterWidget(QWidget):
    registration_successful = pyqtSignal(dict)
    navigate_to_login = pyqtSignal()

    def __init__(self, auth_service: AuthService, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service # Сохраняем экземпляр
        self.ui = RegisterFormUi(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.ui)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        self.auth_worker = None

        self._connect_signals()

    def _connect_signals(self):
        self.ui.register_button.clicked.connect(self.handle_registration_attempt)
        self.ui.go_to_login_button.clicked.connect(self.request_navigation_to_login)

    def request_navigation_to_login(self):
        self.ui.clear_error()
        self.navigate_to_login.emit()

    def _set_buttons_enabled(self, enabled: bool):
        self.ui.register_button.setEnabled(enabled)
        self.ui.go_to_login_button.setEnabled(enabled)

    def handle_registration_attempt(self):
        self.ui.clear_error()
        reg_data = self.ui.get_registration_data()

        if not all(reg_data.values()):
            self.ui.display_error("Все поля должны быть заполнены.")
            return
        if len(reg_data["service_password"]) < 6:
            self.ui.display_error("Пароль должен содержать не менее 6 символов.")
            return

        self._set_buttons_enabled(False)

        self.auth_worker = RegisterWorker(self.auth_service, reg_data, self) # Передаем self как parent для QThread
        self.auth_worker.registration_finished.connect(self._handle_registration_response)
        self.auth_worker.finished.connect(self._on_worker_finished)
        self.auth_worker.start()

    @pyqtSlot(object, object)
    def _handle_registration_response(self, user_info, error_message):
        self._set_buttons_enabled(True)

        if error_message:
            self.ui.display_error(str(error_message))
        elif user_info:
            QMessageBox.information(self,
                                    "Регистрация успешна",
                                    f"Пользователь {user_info.get('login')} успешно зарегистрирован!\n"
                                    "Теперь вы можете войти.")
            self.ui.clear_input_fields()
            self.registration_successful.emit(user_info)
            self.navigate_to_login.emit()
        else:
            self.ui.display_error("Произошла неизвестная ошибка при регистрации.")

    def _on_worker_finished(self):
        # Важно! Не удаляйте воркер сразу, если он еще может быть нужен или испускать сигналы.
        # deleteLater() планирует удаление, когда это будет безопасно.
        if self.auth_worker and not self.auth_worker.isRunning(): # Убедимся, что он завершен
            self.auth_worker.deleteLater()
            self.auth_worker = None
            print("RegisterWorker finished and scheduled for deletion.")


# Для тестирования этого виджета
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    # Создаем экземпляр AuthService (он будет читать .env)
    auth_service_instance = AuthService()

    main_window = QMainWindow()
    main_window.setWindowTitle("Register Widget Test")

    register_widget_instance = RegisterWidget(auth_service_instance, main_window) # Передаем parent

    def go_to_login_test():
        QMessageBox.information(main_window, "Навигация", "Запрос перехода на страницу Вход!")

    def registration_success_test(user_data):
        print(f"TEST: Registration successful in main app for {user_data.get('login')}")

    register_widget_instance.navigate_to_login.connect(go_to_login_test)
    register_widget_instance.registration_successful.connect(registration_success_test)

    main_window.setCentralWidget(register_widget_instance)
    main_window.resize(500, 800) # Немного больше места для формы регистрации
    main_window.show()

    sys.exit(app.exec_())
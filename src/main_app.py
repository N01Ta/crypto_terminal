# src/main_app.py
import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QFont

# --- Блок для sys.path (оставляем закомментированным, если запускаем через -m) ---
# if __name__ == '__main__':
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     project_root = os.path.dirname(current_dir)
#     if project_root not in sys.path:
#         sys.path.insert(0, project_root)

from src.main_window import MainWindow
from src.config import CLIENT_APP_VERSION, BACKEND_BASE_URL  # Импортируем версию клиента
from src.core.auth_service import AuthService  # Импортируем сервис


def run_version_check():
    """Выполняет проверку версии клиента и возвращает True, если все ОК."""
    auth_service = AuthService(BACKEND_BASE_URL)  # Создаем экземпляр сервиса
    is_ok, message = auth_service.check_client_version(CLIENT_APP_VERSION)

    if not is_ok:
        # Показываем сообщение об ошибке перед закрытием QApplication
        # QMessageBox нужно создавать после QApplication
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Ошибка версии")
        error_dialog.setText("Не удалось запустить приложение:")
        error_dialog.setInformativeText(message)
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec_()  # Показываем диалог модально
        return False
    return True


def main():
    app = QApplication(sys.argv)

    # Сначала выполняем проверку версии
    if not run_version_check():
        print("Version check failed or update required. Exiting.")
        sys.exit(1)  # Выходим, если проверка не прошла

    # Если проверка прошла, продолжаем запуск приложения
    print("Client version OK. Starting main application...")

    # default_font = QFont("Segoe UI", 10)
    # app.setFont(default_font)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
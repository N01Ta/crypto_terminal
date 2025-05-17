# src/ui/login_form_ui.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QApplication, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class LoginFormUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LoginFormUi")
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setContentsMargins(50, 50, 50, 50)

        self.login_form_container = QWidget()
        self.login_form_container.setObjectName("formContainer")
        # self.login_form_container.setMinimumWidth(380) # Увеличим немного для теней
        # self.login_form_container.setMaximumWidth(420)

        login_form_layout = QVBoxLayout(self.login_form_container)
        login_form_layout.setContentsMargins(35, 35, 35, 35)  # Чуть больше отступы для контейнера
        login_form_layout.setSpacing(20)
        login_form_layout.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel("Вход в Терминал")
        self.title_label.setObjectName("titleLabel")
        title_font = QFont()
        title_font.setPointSize(22)  # Немного крупнее заголовок
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        login_form_layout.addWidget(self.title_label)

        self.service_login_input = QLineEdit()
        self.service_login_input.setPlaceholderText("Логин для терминала")
        self.service_login_input.setObjectName("textInput")
        self.service_login_input.setMinimumHeight(48)  # Чуть выше поля
        login_form_layout.addWidget(self.service_login_input)

        self.service_password_input = QLineEdit()
        self.service_password_input.setPlaceholderText("Пароль от терминала")
        self.service_password_input.setEchoMode(QLineEdit.Password)
        self.service_password_input.setObjectName("textInput")
        self.service_password_input.setMinimumHeight(48)
        login_form_layout.addWidget(self.service_password_input)

        self.login_button = QPushButton("Авторизация")
        self.login_button.setObjectName("accentButton")
        self.login_button.setMinimumHeight(52)  # Чуть выше кнопка
        self.login_button.setCursor(Qt.PointingHandCursor)
        login_form_layout.addWidget(self.login_button)

        login_form_layout.addSpacing(15)

        self.go_to_register_button = QPushButton("Нет аккаунта? Зарегистрироваться")
        self.go_to_register_button.setObjectName("linkButton")
        self.go_to_register_button.setFlat(True)
        self.go_to_register_button.setCursor(Qt.PointingHandCursor)
        login_form_layout.addWidget(self.go_to_register_button, alignment=Qt.AlignCenter)

        self.version_label = QLabel("version: 1.0.3")
        self.version_label.setObjectName("versionLabel")
        self.version_label.setAlignment(Qt.AlignCenter)
        login_form_layout.addWidget(self.version_label)

        self.main_layout.addWidget(self.login_form_container)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setMinimumHeight(40)
        self.error_label.hide()
        self.main_layout.addWidget(self.error_label)
        self.main_layout.addStretch(1)

    def _apply_styles(self):
        # Основные цвета
        dark_bg_color = "#282c34"  # Более нейтральный темно-серый, близкий к #1e1e2f, но менее синий
        primary_text_color = "#d0d0e0"  # Светло-серый с легким лавандовым оттенком

        # Пастельные фиолетовые акценты
        pastel_purple_accent = "#9b88c7"  # Приглушенный аметистовый/лавандовый
        pastel_purple_hover = "#a995d1"  # Чуть светлее для ховера
        pastel_purple_pressed = "#8d7ab5"  # Чуть темнее для нажатия

        glass_bg_color = "rgba(50, 52, 60, 0.65)"  # Полупрозрачный темно-серый для "стекла"
        glass_border_color = "rgba(155, 136, 199, 0.35)"  # Полупрозрачный пастельно-фиолетовый для границ "стекла"

        input_bg_color = "rgba(60, 62, 70, 0.7)"
        input_border_color = pastel_purple_accent
        input_focus_border_color = pastel_purple_hover

        error_color = "#e74c3c"  # Яркий, но не кислотный красный
        link_color = "#bca0dc"  # Более светлый пастельно-фиолетовый для ссылок

        self.setStyleSheet(f"""
            QWidget#LoginFormUi {{
                background-color: {dark_bg_color};
            }}
            QWidget#formContainer {{
                background-color: {glass_bg_color};
                border-radius: 18px; /* Чуть больше скругление */
                border: 1px solid {glass_border_color};
            }}
            QLabel#titleLabel {{
                color: {primary_text_color};
                padding-bottom: 15px; /* Больше отступ снизу */
            }}
            QLineEdit#textInput {{
                background-color: {input_bg_color};
                color: {primary_text_color};
                border: 1px solid {input_border_color};
                border-radius: 10px; /* Больше скругление */
                padding: 12px 15px; /* Увеличим паддинг */
                font-size: 15px; /* Чуть крупнее шрифт в полях */
            }}
            QLineEdit#textInput:focus {{
                border: 1.5px solid {input_focus_border_color}; /* Чуть толще рамка при фокусе */
            }}
            QPushButton#accentButton {{
                background-color: {pastel_purple_accent};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 17px; /* Крупнее шрифт кнопки */
                font-weight: bold;
            }}
            QPushButton#accentButton:hover {{
                background-color: {pastel_purple_hover};
            }}
            QPushButton#accentButton:pressed {{
                background-color: {pastel_purple_pressed};
            }}
            QPushButton#linkButton {{
                color: {link_color};
                font-size: 14px; /* Крупнее шрифт ссылки */
                border: none;
                background-color: transparent;
                padding-top: 5px; /* Небольшой отступ сверху */
            }}
            QPushButton#linkButton:hover {{
                color: {primary_text_color};
            }}
            QLabel#versionLabel {{
                color: rgba(208, 208, 224, 0.55); /* Полупрозрачный основной текст */
                font-size: 11px; /* Крупнее версия */
                padding-top: 15px;
            }}
            QLabel#errorLabel {{
                color: {error_color};
                font-size: 13px;
                font-weight: bold;
            }}
        """)

        # Добавление тени для "стеклянного" эффекта
        shadow = QGraphicsDropShadowEffect(self)  # Тень на всё окно для глубины
        shadow.setBlurRadius(35)  # Больше размытие
        shadow.setXOffset(0)
        shadow.setYOffset(5)  # Небольшое смещение тени вниз
        shadow.setColor(QColor(0, 0, 0, 80))  # Мягкая темная тень
        self.login_form_container.setGraphicsEffect(shadow)  # Применяем к контейнеру формы

    def get_login_data(self):
        return {
            "service_login": self.service_login_input.text().strip(),
            "service_password": self.service_password_input.text()
        }

    def display_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()

    def clear_error(self):
        self.error_label.hide()
        self.error_label.setText("")

    def clear_input_fields(self):
        self.service_login_input.clear()
        self.service_password_input.clear()


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    # Для лучшего отображения шрифтов, если стандартный не очень
    # default_font = QFont("Arial", 10) # Segoe UI может быть не у всех
    # app.setFont(default_font)

    login_ui_instance = LoginFormUi()
    login_ui_instance.setWindowTitle("Терминал - Вход (Pastel Dark)")
    login_ui_instance.resize(500, 700)  # Используем resize для установки начального размера
    login_ui_instance.show()
    sys.exit(app.exec_())
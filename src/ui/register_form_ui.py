# src/ui/register_form_ui.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QApplication, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class RegisterFormUi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RegisterFormUi")  # Для применения стилей к конкретному окну
        self._setup_ui()
        self._apply_styles()  # Применяем стили

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setContentsMargins(50, 30, 50, 30)  # Отступы окна (вертикальные меньше)

        # Контейнер для формы, к которому будем применять "стеклянный" стиль
        self.register_form_container = QWidget()
        self.register_form_container.setObjectName("formContainer")
        # self.register_form_container.setMinimumWidth(380)
        # self.register_form_container.setMaximumWidth(420)

        register_form_layout = QVBoxLayout(self.register_form_container)
        register_form_layout.setContentsMargins(35, 30, 35, 30)  # Внутренние отступы формы
        register_form_layout.setSpacing(18)  # Немного меньше расстояние между элементами
        register_form_layout.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel("Регистрация в Терминале")
        self.title_label.setObjectName("titleLabel")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        register_form_layout.addWidget(self.title_label)

        self.service_login_input = QLineEdit()
        self.service_login_input.setPlaceholderText("Придумайте логин для терминала")
        self.service_login_input.setObjectName("textInput")
        self.service_login_input.setMinimumHeight(48)
        register_form_layout.addWidget(self.service_login_input)

        self.service_password_input = QLineEdit()
        self.service_password_input.setPlaceholderText("Придумайте пароль для терминала")
        self.service_password_input.setEchoMode(QLineEdit.Password)
        self.service_password_input.setObjectName("textInput")
        self.service_password_input.setMinimumHeight(48)
        register_form_layout.addWidget(self.service_password_input)

        self.mexc_api_key_input = QLineEdit()
        self.mexc_api_key_input.setPlaceholderText("MEXC API Key")
        self.mexc_api_key_input.setObjectName("textInput")
        self.mexc_api_key_input.setMinimumHeight(48)
        register_form_layout.addWidget(self.mexc_api_key_input)

        self.mexc_api_secret_input = QLineEdit()
        self.mexc_api_secret_input.setPlaceholderText("MEXC API Secret")
        self.mexc_api_secret_input.setEchoMode(QLineEdit.Password)
        self.mexc_api_secret_input.setObjectName("textInput")
        self.mexc_api_secret_input.setMinimumHeight(48)
        register_form_layout.addWidget(self.mexc_api_secret_input)

        self.register_button = QPushButton("Регистрация")
        self.register_button.setObjectName("accentButton")  # Используем тот же стиль для акцентной кнопки
        self.register_button.setMinimumHeight(52)
        self.register_button.setCursor(Qt.PointingHandCursor)
        register_form_layout.addWidget(self.register_button)

        register_form_layout.addSpacing(15)

        self.go_to_login_button = QPushButton("Уже есть аккаунт? Войти")
        self.go_to_login_button.setObjectName("linkButton")
        self.go_to_login_button.setFlat(True)
        self.go_to_login_button.setCursor(Qt.PointingHandCursor)
        register_form_layout.addWidget(self.go_to_login_button, alignment=Qt.AlignCenter)

        self.version_label = QLabel("version: 1.0.3")
        self.version_label.setObjectName("versionLabel")
        self.version_label.setAlignment(Qt.AlignCenter)
        register_form_layout.addWidget(self.version_label)

        self.main_layout.addWidget(self.register_form_container)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setMinimumHeight(40)
        self.error_label.hide()
        self.main_layout.addWidget(self.error_label)
        self.main_layout.addStretch(1)

    def _apply_styles(self):
        # Цвета и стили идентичны LoginFormUi для консистентности
        dark_bg_color = "#282c34"
        primary_text_color = "#d0d0e0"
        pastel_purple_accent = "#9b88c7"
        pastel_purple_hover = "#a995d1"
        pastel_purple_pressed = "#8d7ab5"
        glass_bg_color = "rgba(50, 52, 60, 0.65)"
        glass_border_color = "rgba(155, 136, 199, 0.35)"
        input_bg_color = "rgba(60, 62, 70, 0.7)"
        input_border_color = pastel_purple_accent
        input_focus_border_color = pastel_purple_hover
        error_color = "#e74c3c"
        link_color = "#bca0dc"

        self.setStyleSheet(f"""
            QWidget#RegisterFormUi {{
                background-color: {dark_bg_color};
            }}
            QWidget#formContainer {{
                background-color: {glass_bg_color};
                border-radius: 18px;
                border: 1px solid {glass_border_color};
            }}
            QLabel#titleLabel {{
                color: {primary_text_color};
                padding-bottom: 15px;
            }}
            QLineEdit#textInput {{
                background-color: {input_bg_color};
                color: {primary_text_color};
                border: 1px solid {input_border_color};
                border-radius: 10px;
                padding: 12px 15px;
                font-size: 15px;
            }}
            QLineEdit#textInput:focus {{
                border: 1.5px solid {input_focus_border_color};
            }}
            QPushButton#accentButton {{ /* Стиль для кнопки Регистрация */
                background-color: {pastel_purple_accent}; /* Основной акцентный цвет */
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 17px;
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
                font-size: 14px;
                border: none;
                background-color: transparent;
                padding-top: 5px;
            }}
            QPushButton#linkButton:hover {{
                color: {primary_text_color};
            }}
            QLabel#versionLabel {{
                color: rgba(208, 208, 224, 0.55);
                font-size: 11px;
                padding-top: 15px;
            }}
            QLabel#errorLabel {{
                color: {error_color};
                font-size: 13px;
                font-weight: bold;
            }}
        """)

        # Добавление тени для "стеклянного" эффекта
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.register_form_container.setGraphicsEffect(shadow)

    # ... (методы get_registration_data, display_error и т.д. остаются) ...
    def get_registration_data(self):
        return {
            "service_login": self.service_login_input.text().strip(),
            "service_password": self.service_password_input.text(),
            "mexc_api_key": self.mexc_api_key_input.text().strip(),
            "mexc_api_secret": self.mexc_api_secret_input.text()
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
        self.mexc_api_key_input.clear()
        self.mexc_api_secret_input.clear()


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    register_ui_instance = RegisterFormUi()
    register_ui_instance.setWindowTitle("Терминал - Регистрация (Pastel Dark)")
    register_ui_instance.resize(500, 750)  # Окно чуть выше из-за 4х полей
    register_ui_instance.show()
    sys.exit(app.exec_())
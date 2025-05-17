# src/main_window.py
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QMessageBox, QWidget
from PyQt5.QtCore import pyqtSlot
from src.config import BACKEND_BASE_URL
from .core.auth_service import AuthService
from .core.mexc_service import MexcService
from .widgets.login_widget import LoginWidget
from .widgets.register_widget import RegisterWidget
from .widgets.coin_list_widget import CoinListWidget
from .widgets.trade_widget import TradeWidget

# --- Цветовая палитра (для фона MainWindow) ---
DARK_BG_COLOR = "#282c34" 

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Крипто-Терминал")
        self.setGeometry(100, 100, 1000, 700) # Начальный размер и позиция
        self.setStyleSheet(f"QMainWindow {{ background-color: {DARK_BG_COLOR}; }}") # Фон для всего окна

        # Сервисы
        self.auth_service = AuthService(BACKEND_BASE_URL)
        self.mexc_service = MexcService() # Инициализируем без ключей для публичных данных

        # Данные текущего пользователя (после логина)
        self.current_user_login = None
        self.current_user_api_key = None
        self.current_user_api_secret = None

        # QStackedWidget для управления экранами
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        # Создаем виджеты для каждого экрана
        self.login_widget = LoginWidget(self.auth_service, self)
        self.register_widget = RegisterWidget(self.auth_service, self)
        self.coin_list_widget = CoinListWidget(self.mexc_service, self) # Передаем MexcService
        self.trade_widget = TradeWidget(self.mexc_service, self)       # Передаем MexcService

        # Добавляем виджеты в QStackedWidget
        self.stacked_widget.addWidget(self.login_widget)    # index 0
        self.stacked_widget.addWidget(self.register_widget) # index 1
        self.stacked_widget.addWidget(self.coin_list_widget)# index 2
        self.stacked_widget.addWidget(self.trade_widget)    # index 3

        self._connect_widget_signals()

        # По умолчанию показываем экран логина
        self.show_login_screen()

    def _connect_widget_signals(self):
        # Сигналы от LoginWidget
        self.login_widget.login_successful.connect(self.handle_login_success)
        self.login_widget.navigate_to_register.connect(self.show_register_screen)

        # Сигналы от RegisterWidget
        self.register_widget.registration_successful.connect(self.handle_registration_success)
        self.register_widget.navigate_to_login.connect(self.show_login_screen)

        # Сигналы от CoinListWidget
        self.coin_list_widget.coin_trade_requested.connect(self.show_trade_screen)


        # Сигналы от TradeWidget
        self.trade_widget.navigate_back.connect(self.show_coin_list_screen)


    def show_login_screen(self):
        print("Navigating to Login Screen")
        self.login_widget.ui.clear_input_fields() # Очищаем поля при переходе
        self.login_widget.ui.clear_error()
        self.stacked_widget.setCurrentWidget(self.login_widget)
        self.setWindowTitle("Терминал - Вход")


    def show_register_screen(self):
        print("Navigating to Register Screen")
        self.register_widget.ui.clear_input_fields()
        self.register_widget.ui.clear_error()
        self.stacked_widget.setCurrentWidget(self.register_widget)
        self.setWindowTitle("Терминал - Регистрация")

    @pyqtSlot(dict) # user_info: {"login": "...", "api_keys": {"mexc_api_key": "...", "mexc_api_secret": "..."}}
    def handle_login_success(self, user_info: dict):
        self.current_user_login = user_info.get("login")
        api_keys = user_info.get("api_keys", {})
        self.current_user_api_key = api_keys.get("mexc_api_key")
        self.current_user_api_secret = api_keys.get("mexc_api_secret")

        print(f"Login successful for user: {self.current_user_login}")
        QMessageBox.information(self, "Успех", f"Добро пожаловать, {self.current_user_login}!")

        if self.current_user_api_key and self.current_user_api_secret:
            self.mexc_service.set_api_credentials(
                api_key=self.current_user_api_key,
                api_secret=self.current_user_api_secret
            )

        self.show_coin_list_screen()

    @pyqtSlot(dict) # user_info от бэкенда (login, api_keys)
    def handle_registration_success(self, user_info: dict):
        # Сообщение об успехе уже показывается в RegisterWidget
        # Здесь мы просто решаем, что делать дальше (например, перейти на логин)
        print(f"Registration was successful for {user_info.get('login')}, navigating to login.")
        # RegisterWidget уже сам эмитирует navigate_to_login после успешного QMessageBox
        # поэтому здесь можно ничего не делать дополнительно, или, если нужно,
        # self.show_login_screen() # Но это может быть избыточно, если RegisterWidget уже это делает

    def show_coin_list_screen(self):
        print("Navigating to Coin List Screen")
        # Перед показом списка монет, мы можем захотеть обновить его данные
        self.coin_list_widget.load_initial_markets_and_prices() # Загружаем/обновляем список и цены
        self.stacked_widget.setCurrentWidget(self.coin_list_widget)
        self.setWindowTitle(f"Терминал - {self.current_user_login or 'Список монет'}")

    @pyqtSlot(dict) # market_data: словарь с данными о выбранной паре
    def show_trade_screen(self, market_data: dict):
        pair_symbol = market_data.get('symbol', "N/A")
        print(f"Navigating to Trade Screen for: {pair_symbol}")
        self.trade_widget.set_market_data(market_data) # Передаем данные о паре в TradeWidget
        self.stacked_widget.setCurrentWidget(self.trade_widget)
        self.setWindowTitle(f"Торговля: {pair_symbol} - {self.current_user_login or ''}")

    def handle_n_button_action(self):
        # TODO: Реализовать действие для кнопки "N" (например, меню, настройки)
        QMessageBox.information(self, "Кнопка N", "Функционал кнопки 'N' еще не реализован.")

    def closeEvent(self, event):
        # Останавливаем таймеры в дочерних виджетах перед закрытием
        self.coin_list_widget.stop_updates()
        self.trade_widget.stop_all_updates()
        print("MainWindow closing, timers in child widgets stopped.")
        super().closeEvent(event)

# Для запуска основного приложения (этот блок будет в main_app.py)
# if __name__ == '__main__':
#     import sys
#     from PyQt5.QtWidgets import QApplication
#     app = QApplication(sys.argv)
#     main_win = MainWindow()
#     main_win.show()
#     sys.exit(app.exec_())
# src/widgets/trade_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot, QTimer, Qt, QUrl
from PyQt5.QtGui import QColor, QPalette, QDesktopServices

try:
    from ..ui.trade_ui import TradeUi
    from ..core.mexc_service import MexcService
    from ..core.simple_predictor import get_simple_price_prediction
except ImportError:
    print("TradeWidget: Failed to import. Using mocks for standalone test if in __main__.")
    TradeUi = None
    MexcService = None
    get_simple_price_prediction = None


class FetchOhlcvWorker(QThread):
    fetch_finished = pyqtSignal(str, list, object)  # symbol, ohlcv_data, error_message

    def __init__(self, mexc_service_instance: MexcService, symbol: str, timeframe: str, limit: int, parent=None):
        super().__init__(parent)
        self.mexc_service = mexc_service_instance
        self.symbol = symbol
        self.timeframe = timeframe
        self.limit = limit
        self._is_running = True

    def run(self):
        if not self.mexc_service:
            if self._is_running:
                self.fetch_finished.emit(self.symbol, [], "MexcService не инициализирован")
            return
        try:
            ohlcv_data, error_msg = self.mexc_service.fetch_ohlcv(
                symbol=self.symbol, timeframe=self.timeframe, limit=self.limit
            )
            if self._is_running:
                self.fetch_finished.emit(self.symbol, ohlcv_data or [], error_msg)
        except Exception as e:
            if self._is_running:
                self.fetch_finished.emit(self.symbol, [], f"Ошибка в FetchOhlcvWorker: {e}")

    def stop(self):
        self._is_running = False


class FetchBalancesWorker(QThread):
    fetch_finished = pyqtSignal(object, object)  # balances_data, error_message

    def __init__(self, mexc_service_instance: MexcService, parent=None):
        super().__init__(parent)
        self.mexc_service = mexc_service_instance
        self._is_running = True

    def run(self):
        if not self.mexc_service:
            if self._is_running:
                self.fetch_finished.emit(None, "MexcService не инициализирован")
            return
        try:
            balances_data, error_msg = self.mexc_service.fetch_balances()
            if self._is_running:
                self.fetch_finished.emit(balances_data, error_msg)
        except Exception as e:
            if self._is_running:
                self.fetch_finished.emit(None, f"Ошибка в FetchBalancesWorker: {e}")

    def stop(self):
        self._is_running = False


class TradeWidget(QWidget):
    navigate_back = pyqtSignal()

    OHLCV_TIMEFRAME = '5m'
    OHLCV_LIMIT = 100
    OHLCV_UPDATE_INTERVAL_MS = 30 * 1000  # 30 секунд
    PREDICTION_LOOKBACK = 5
    BALANCES_UPDATE_INTERVAL_MS = 60 * 1000  # 1 минута

    def __init__(self, mexc_service: MexcService, parent=None):
        super().__init__(parent)
        if None in [TradeUi, MexcService, get_simple_price_prediction] and not isinstance(self, MockTradeWidgetForTest):
            raise ImportError("TradeWidget: Critical components (UI, Service, Predictor) not available.")

        self.mexc_service = mexc_service
        self.ui = TradeUi(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.ui)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.current_market_data = None
        self.current_ohlcv_data = []

        self.fetch_ohlcv_worker = None
        self.fetch_balances_worker = None

        self.ohlcv_update_timer = QTimer(self)
        self.ohlcv_update_timer.timeout.connect(self._request_ohlcv_update)

        self.balances_update_timer = QTimer(self)
        self.balances_update_timer.timeout.connect(self._request_balances_update)

        self._connect_ui_signals()

    def _connect_ui_signals(self):
        self.ui.back_button_clicked.connect(self.navigate_back.emit)
        self.ui.buy_button_clicked.connect(self._handle_buy_action)
        self.ui.sell_button_clicked.connect(self._handle_sell_action)

    def set_market_data(self, market_data: dict):
        # print(f"[TradeWidget] set_market_data for {market_data.get('symbol') if market_data else 'None'}")
        self.stop_all_updates()

        self.current_market_data = market_data
        self.current_ohlcv_data = []
        self.ui.clear_chart()

        if not market_data:
            self.ui.set_coin_pair_price("N/A", "N/A")
            self.ui.set_prediction("Выберите пару", self.ui.prediction_label.palette().color(QPalette.WindowText))
            self.ui.set_balances("BASE", "---", "QUOTE", "---")
            return

        symbol = market_data.get('symbol', "N/A")
        initial_price = str(market_data.get('current_price_from_list', "---"))
        self.ui.set_coin_pair_price(symbol, initial_price)

        base_asset = market_data.get('base', 'BASE')
        quote_asset = market_data.get('quote', 'QUOTE')
        self.ui.set_balances(base_asset, "загрузка...", quote_asset, "загрузка...")

        self.ui.set_prediction("Загрузка графика...", self.ui.prediction_label.palette().color(QPalette.WindowText))
        self.ui.hide_order_status()
        self.ui.clear_amount()

        self.start_ohlcv_updates()
        self.start_balances_updates()

    def start_ohlcv_updates(self):
        if self.current_market_data:
            QTimer.singleShot(0, self._request_ohlcv_update)  # Отложенный первый вызов
            if not self.ohlcv_update_timer.isActive():
                self.ohlcv_update_timer.start(self.OHLCV_UPDATE_INTERVAL_MS)

    def start_balances_updates(self):
        if self.mexc_service.api_key and self.mexc_service.api_secret:
            QTimer.singleShot(0, self._request_balances_update)
            if not self.balances_update_timer.isActive():
                self.balances_update_timer.start(self.BALANCES_UPDATE_INTERVAL_MS)
        else:
            base = self.current_market_data.get('base', 'BASE') if self.current_market_data else 'BASE'
            quote = self.current_market_data.get('quote', 'QUOTE') if self.current_market_data else 'QUOTE'
            self.ui.set_balances(base, "Нет API", quote, "Нет API")

    def _request_ohlcv_update(self):
        if not self.current_market_data:
            return
        if self.fetch_ohlcv_worker and self.fetch_ohlcv_worker.isRunning():
            return

        symbol = self.current_market_data['symbol']
        self.fetch_ohlcv_worker = FetchOhlcvWorker(
            self.mexc_service, symbol, self.OHLCV_TIMEFRAME, self.OHLCV_LIMIT, self
        )
        self.fetch_ohlcv_worker.fetch_finished.connect(self._handle_ohlcv_fetched)
        self.fetch_ohlcv_worker.finished.connect(self._on_ohlcv_worker_finished)
        self.fetch_ohlcv_worker.start()

    def _request_balances_update(self):
        if not self.mexc_service.api_key or not self.mexc_service.api_secret:
            if self.current_market_data:
                base = self.current_market_data.get('base', 'BASE')
                quote = self.current_market_data.get('quote', 'QUOTE')
                # Проверяем, что у labels есть текст, чтобы избежать AttributeError с моками
                if hasattr(self.ui, 'balance_base_label') and self.ui.balance_base_label:
                    current_base_text = self.ui.balance_base_label.text()
                    if "загрузка..." in current_base_text or "---" in current_base_text:
                        self.ui.set_balances(base, "Нет API", quote, "Нет API")
            return

        if self.fetch_balances_worker and self.fetch_balances_worker.isRunning():
            return

        self.fetch_balances_worker = FetchBalancesWorker(self.mexc_service, self)
        self.fetch_balances_worker.fetch_finished.connect(self._handle_balances_fetched)
        self.fetch_balances_worker.finished.connect(self._on_balances_worker_finished)
        self.fetch_balances_worker.start()

    @pyqtSlot(str, list, object)
    def _handle_ohlcv_fetched(self, symbol: str, ohlcv_data: list, error_message):
        if not self.current_market_data or symbol != self.current_market_data.get('symbol'):
            return

        if error_message:
            self.ui.set_prediction(f"Ошибка графика: {error_message}", QColor("red"))
            return

        price_precision = self.current_market_data.get('precision', {}).get('price', 2)

        if not ohlcv_data:
            self.ui.draw_price_chart([], None, price_precision)
            self.ui.set_prediction("Нет данных для графика", QColor("gray"))
            return

        self.current_ohlcv_data = ohlcv_data
        last_candle_close = ohlcv_data[-1][4]

        try:
            price_str = f"{float(last_candle_close):.{price_precision}f}"
            self.ui.set_coin_pair_price(symbol, price_str)
        except Exception:
            self.ui.set_coin_pair_price(symbol, str(last_candle_close))

        predicted_price, trend_desc, trend_color = get_simple_price_prediction(
            self.current_ohlcv_data, self.PREDICTION_LOOKBACK
        )
        self.ui.set_prediction(trend_desc, trend_color)

        prediction_chart_data = (predicted_price, trend_desc, trend_color) if predicted_price is not None else None
        self.ui.draw_price_chart(self.current_ohlcv_data, prediction_chart_data, price_precision)

    @pyqtSlot(object, object)
    def _handle_balances_fetched(self, balances_data, error_message):
        base_asset = self.current_market_data.get('base', 'BASE') if self.current_market_data else 'BASE'
        quote_asset = self.current_market_data.get('quote', 'QUOTE') if self.current_market_data else 'QUOTE'

        base_precision = self.current_market_data.get('precision', {}).get('amount',
                                                                           4) if self.current_market_data else 4
        quote_precision = self.current_market_data.get('precision', {}).get('cost',
                                                                            2) if self.current_market_data else 2

        if error_message:
            print(f"[TradeWidget] Error fetching balances: {error_message}")
            self.ui.set_balances(base_asset, "Ошибка", quote_asset, "Ошибка")
            return

        if not balances_data or not self.current_market_data:
            self.ui.set_balances(base_asset, "---", quote_asset, "---")
            return

        base_balance_val = 0.0
        quote_balance_val = 0.0

        if 'free' in balances_data and isinstance(balances_data['free'], dict):
            base_balance_val = balances_data['free'].get(base_asset, 0.0)
            quote_balance_val = balances_data['free'].get(quote_asset, 0.0)
        else:
            print(f"[TradeWidget] Unexpected balance data structure from API.")

        try:
            base_balance_str = f"{float(base_balance_val):.{base_precision}f}"
        except:
            base_balance_str = str(base_balance_val)
        try:
            quote_balance_str = f"{float(quote_balance_val):.{quote_precision}f}"
        except:
            quote_balance_str = str(quote_balance_val)

        self.ui.set_balances(base_asset, base_balance_str, quote_asset, quote_balance_str)

    def _on_ohlcv_worker_finished(self):
        if self.fetch_ohlcv_worker and self.sender() == self.fetch_ohlcv_worker:
            self.fetch_ohlcv_worker.deleteLater()
            self.fetch_ohlcv_worker = None

    def _on_balances_worker_finished(self):
        if self.fetch_balances_worker and self.sender() == self.fetch_balances_worker:
            self.fetch_balances_worker.deleteLater()
            self.fetch_balances_worker = None

    def _handle_buy_action(self):
        if not self.current_market_data:
            QMessageBox.warning(self, "Ошибка", "Торговая пара не выбрана.")
            return
        amount_str = self.ui.get_amount()
        symbol = self.current_market_data['symbol']
        base_asset = self.current_market_data.get('base', 'BASE')

        if not amount_str:
            QMessageBox.warning(self, "Ошибка", "Введите количество для покупки.")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Количество должно быть положительным")
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", f"Некорректное количество: {e}")
            return

        QMessageBox.information(self, "Покупка", f"КУПИТЬ {amount} {base_asset} на {symbol} (СИМУЛЯЦИЯ)")
        self.ui.show_order_status(f"Куплено {amount} {base_asset} (сим.)", True)
        self.ui.clear_amount()

    def _handle_sell_action(self):
        if not self.current_market_data:
            QMessageBox.warning(self, "Ошибка", "Торговая пара не выбрана.")
            return
        amount_str = self.ui.get_amount()
        symbol = self.current_market_data['symbol']
        base_asset = self.current_market_data.get('base', 'BASE')

        if not amount_str:
            QMessageBox.warning(self, "Ошибка", "Введите количество для продажи.")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Количество должно быть положительным")
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", f"Некорректное количество: {e}")
            return

        QMessageBox.information(self, "Продажа", f"ПРОДАТЬ {amount} {base_asset} на {symbol} (СИМУЛЯЦИЯ)")
        self.ui.show_order_status(f"Продано {amount} {base_asset} (сим.)", True)
        self.ui.clear_amount()

    def stop_all_updates(self):
        self.ohlcv_update_timer.stop()
        self.balances_update_timer.stop()
        for worker_attr in ["fetch_ohlcv_worker", "fetch_balances_worker"]:
            worker = getattr(self, worker_attr, None)
            if worker and worker.isRunning():
                worker.stop()
            if worker and not worker.isRunning():  # Если уже остановлен или завершился
                worker.deleteLater()
                setattr(self, worker_attr, None)

    def closeEvent(self, event):
        self.stop_all_updates()
        super().closeEvent(event)


class MockTradeWidgetForTest(QWidget): pass  # Для __main__ тестового блока


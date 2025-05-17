# src/widgets/trade_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot, QTimer, Qt, QUrl
from PyQt5.QtGui import QColor, QPalette, QDesktopServices

try:
    from ..ui.trade_ui import TradeUi
    from ..core.mexc_service import MexcService
    from ..core.simple_predictor import get_simple_price_prediction
except ImportError:
    TradeUi = None
    MexcService = None
    get_simple_price_prediction = None


class FetchOhlcvWorker(QThread):
    fetch_finished = pyqtSignal(str, list, object)

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
    fetch_finished = pyqtSignal(object, object)

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


class CreateOrderWorker(QThread):
    order_finished = pyqtSignal(object, object, str)

    def __init__(self, mexc_service_instance: MexcService, symbol: str, side: str,
                 amount_from_user: float, current_price: float,
                 market_data: dict, parent=None):
        super().__init__(parent)
        self.mexc_service = mexc_service_instance
        self.symbol = symbol
        self.side = side
        self.amount_from_user = amount_from_user
        self.current_price = current_price
        self.market_data = market_data
        self._is_running = True

    def run(self):
        if not self.mexc_service or not self.mexc_service.exchange:
            if self._is_running: self.order_finished.emit(None, "MexcService или exchange не инициализирован",
                                                          self.side); return

        actual_side = self.side.lower()
        api_amount_arg = self.amount_from_user

        precision_amount = self.market_data.get('precision', {}).get('amount', 8)
        precision_cost = self.market_data.get('precision', {}).get('cost', 2)
        limits_amount_min = self.market_data.get('limits', {}).get('amount', {}).get('min')
        limits_cost_min = self.market_data.get('limits', {}).get('cost', {}).get('min')

        try:
            amount_base_adjusted = float(
                self.mexc_service.exchange.amount_to_precision(self.symbol, self.amount_from_user))
        except Exception as e_prec_amount:
            if self._is_running: self.order_finished.emit(None, f"Ошибка округления кол-ва: {e_prec_amount}",
                                                          actual_side); return
            amount_base_adjusted = self.amount_from_user

        if actual_side == 'buy':
            if self.current_price is None or self.current_price <= 0:
                if self._is_running: self.order_finished.emit(None, "Нет цены для расчета стоимости покупки.",
                                                              actual_side); return
            cost_calculated = amount_base_adjusted * self.current_price
            try:
                api_amount_arg = float(self.mexc_service.exchange.cost_to_precision(self.symbol, cost_calculated))
            except Exception as e_prec_cost:
                if self._is_running: self.order_finished.emit(None, f"Ошибка округления стоимости: {e_prec_cost}",
                                                              actual_side); return
                api_amount_arg = cost_calculated
            if limits_cost_min is not None and api_amount_arg < limits_cost_min:
                msg = f"Сумма ({api_amount_arg:.{precision_cost}f}) < min ({limits_cost_min})."
                if self._is_running: self.order_finished.emit(None, msg, actual_side); return

        elif actual_side == 'sell':
            api_amount_arg = amount_base_adjusted
            if limits_amount_min is not None and api_amount_arg < limits_amount_min:
                msg = f"Кол-во ({api_amount_arg:.{precision_amount}f}) < min ({limits_amount_min})."
                if self._is_running: self.order_finished.emit(None, msg, actual_side); return

        try:
            order_response, error_msg = self.mexc_service.create_market_order(
                symbol=self.symbol, side=actual_side, amount=api_amount_arg
            )
            if self._is_running:
                self.order_finished.emit(order_response, error_msg, self.side)
        except Exception as e:
            if self._is_running:
                self.order_finished.emit(None, f"Критическая ошибка создания ордера: {e}", self.side)

    def stop(self):
        self._is_running = False


class TradeWidget(QWidget):
    navigate_back = pyqtSignal()
    OHLCV_TIMEFRAME = '5m'
    OHLCV_LIMIT = 100
    OHLCV_UPDATE_INTERVAL_MS = 30 * 1000
    PREDICTION_LOOKBACK = 5
    BALANCES_UPDATE_INTERVAL_MS = 60 * 1000

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
        self.current_last_price = None

        self.fetch_ohlcv_worker = None
        self.fetch_balances_worker = None
        self.create_order_worker = None

        self.ohlcv_update_timer = QTimer(self)
        self.ohlcv_update_timer.timeout.connect(self._request_ohlcv_update)  # ИСПРАВЛЕНО

        self.balances_update_timer = QTimer(self)
        self.balances_update_timer.timeout.connect(self._request_balances_update)

        self._connect_ui_signals()

    def _connect_ui_signals(self):
        self.ui.back_button_clicked.connect(self.navigate_back.emit)
        self.ui.buy_button_clicked.connect(self._handle_buy_action)
        self.ui.sell_button_clicked.connect(self._handle_sell_action)

    def set_market_data(self, market_data: dict):
        self.stop_all_updates()
        self.current_market_data = market_data
        self.current_ohlcv_data = []
        self.current_last_price = None
        self.ui.clear_chart()

        if not market_data:
            self.ui.set_coin_pair_price("N/A", "N/A")
            if hasattr(self.ui, 'prediction_label') and self.ui.prediction_label:
                self.ui.set_prediction("Выберите пару", self.ui.prediction_label.palette().color(QPalette.WindowText))
            self.ui.set_balances("BASE", "---", "QUOTE", "---")
            return

        symbol = market_data.get('symbol', "N/A")
        if 'current_price_from_list' in market_data:
            try:
                self.current_last_price = float(market_data['current_price_from_list'])
            except (ValueError, TypeError):
                self.current_last_price = None
            initial_price = str(self.current_last_price) if self.current_last_price is not None else "---"
        else:
            initial_price = "---"
        self.ui.set_coin_pair_price(symbol, initial_price)

        base_asset = market_data.get('base', 'BASE')
        quote_asset = market_data.get('quote', 'QUOTE')
        self.ui.set_balances(base_asset, "загрузка...", quote_asset, "загрузка...")

        if hasattr(self.ui, 'prediction_label') and self.ui.prediction_label:
            self.ui.set_prediction("Загрузка графика...", self.ui.prediction_label.palette().color(QPalette.WindowText))

        self.ui.hide_order_status()
        self.ui.clear_amount()

        self.start_ohlcv_updates()
        self.start_balances_updates()

    def start_ohlcv_updates(self):
        if self.current_market_data:
            QTimer.singleShot(0, self._request_ohlcv_update)
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
        if not self.current_market_data: return
        if self.fetch_ohlcv_worker and self.fetch_ohlcv_worker.isRunning(): return

        symbol = self.current_market_data['symbol']
        self.fetch_ohlcv_worker = FetchOhlcvWorker(
            self.mexc_service, symbol, self.OHLCV_TIMEFRAME, self.OHLCV_LIMIT, self
        )
        self.fetch_ohlcv_worker.fetch_finished.connect(self._handle_ohlcv_fetched)
        self.fetch_ohlcv_worker.finished.connect(self._on_ohlcv_worker_finished)
        self.fetch_ohlcv_worker.start()

    def _request_balances_update(self):
        if not (self.mexc_service.api_key and self.mexc_service.api_secret):
            if self.current_market_data and hasattr(self.ui, 'balance_base_label') and self.ui.balance_base_label:
                if "загрузка..." in self.ui.balance_base_label.text() or "---" in self.ui.balance_base_label.text():
                    b = self.current_market_data.get('base', 'B');
                    q = self.current_market_data.get('quote', 'Q')
                    self.ui.set_balances(b, "Нет API", q, "Нет API")
            return
        if self.fetch_balances_worker and self.fetch_balances_worker.isRunning(): return

        self.fetch_balances_worker = FetchBalancesWorker(self.mexc_service, self)
        self.fetch_balances_worker.fetch_finished.connect(self._handle_balances_fetched)
        self.fetch_balances_worker.finished.connect(self._on_balances_worker_finished)
        self.fetch_balances_worker.start()

    @pyqtSlot(str, list, object)
    def _handle_ohlcv_fetched(self, symbol: str, ohlcv_data: list, error_message):
        if not self.current_market_data or symbol != self.current_market_data.get('symbol'): return
        if error_message:
            self.ui.set_prediction(f"Ошибка графика: {error_message}", QColor("red"))
            return

        price_precision = self.current_market_data.get('precision', {}).get('price', 2)
        if not ohlcv_data:
            self.ui.draw_price_chart([], None, price_precision)
            self.ui.set_prediction("Нет данных для графика", QColor("gray"))
            self.current_last_price = None
            return

        self.current_ohlcv_data = ohlcv_data
        try:
            self.current_last_price = float(ohlcv_data[-1][4])
            self.ui.set_coin_pair_price(symbol, f"{self.current_last_price:.{price_precision}f}")
        except Exception:
            self.current_last_price = None
            self.ui.set_coin_pair_price(symbol, str(ohlcv_data[-1][4]))

        predicted_price, trend_desc, trend_color = get_simple_price_prediction(
            self.current_ohlcv_data, self.PREDICTION_LOOKBACK
        )
        self.ui.set_prediction(trend_desc, trend_color)
        prediction_chart_data = (predicted_price, trend_desc, trend_color) if predicted_price is not None else None
        self.ui.draw_price_chart(self.current_ohlcv_data, prediction_chart_data, price_precision)

    @pyqtSlot(object, object)
    def _handle_balances_fetched(self, balances_data, error_message):
        base_asset = self.current_market_data.get('base', 'B') if self.current_market_data else 'B'
        quote_asset = self.current_market_data.get('quote', 'Q') if self.current_market_data else 'Q'
        base_precision = self.current_market_data.get('precision', {}).get('amount',
                                                                           4) if self.current_market_data else 4
        quote_precision = self.current_market_data.get('precision', {}).get('cost',
                                                                            2) if self.current_market_data else 2

        if error_message: self.ui.set_balances(base_asset, "Ошибка", quote_asset, "Ошибка");return
        if not balances_data or not self.current_market_data: self.ui.set_balances(base_asset, "---", quote_asset,
                                                                                   "---");return

        base_val = 0.0;
        qv = 0.0
        if 'free' in balances_data and isinstance(balances_data['free'], dict):
            base_val = balances_data['free'].get(base_asset, 0.0)
            qv = balances_data['free'].get(quote_asset, 0.0)

        try:
            base_s = f"{float(base_val):.{base_precision}f}"
        except:
            base_s = str(base_val)
        try:
            quote_s = f"{float(qv):.{quote_precision}f}"
        except:
            quote_s = str(qv)

        self.ui.set_balances(base_asset, base_s, quote_asset, quote_s)

    @pyqtSlot(object, object, str)
    def _handle_order_finished(self, order_response, error_message, order_side_str):
        self.ui.buy_button.setEnabled(True)
        self.ui.sell_button.setEnabled(True)

        if error_message:
            self.ui.show_order_status(f"Ошибка ({order_side_str}): {error_message}", False)
            return

        if order_response:
            order_id = order_response.get('id', 'N/A')
            filled = order_response.get('filled', 0.0)
            status_msg = f"Ордер ({order_side_str}) ID:{order_id}."
            try:
                if filled is not None and float(filled) > 0:
                    p_amt = self.current_market_data.get('precision', {}).get('amount', 4)
                    status_msg += f" Исп.: {float(filled):.{p_amt}f}"
            except:
                pass

            self.ui.show_order_status(status_msg, True)
            self.ui.clear_amount()
            self._request_balances_update()
        else:
            self.ui.show_order_status(f"Ордер ({order_side_str}) не вернул данных.", False)

    def _on_worker_finished_generic(self, worker_attr_name):
        worker = getattr(self, worker_attr_name, None)
        if worker and self.sender() == worker:
            worker.deleteLater();
            setattr(self, worker_attr_name, None)

    def _on_ohlcv_worker_finished(self):
        self._on_worker_finished_generic("fetch_ohlcv_worker")

    def _on_balances_worker_finished(self):
        self._on_worker_finished_generic("fetch_balances_worker")

    def _on_create_order_worker_finished(self):
        self._on_worker_finished_generic("create_order_worker")

    def _initiate_trade(self, side: str):
        if not self.current_market_data:
            QMessageBox.warning(self, "Ошибка", "Торговая пара не выбрана.");
            return
        if not (self.mexc_service.api_key and self.mexc_service.api_secret):
            QMessageBox.warning(self, "Ошибка", "API ключи не установлены для торговли.");
            return
        if self.create_order_worker and self.create_order_worker.isRunning():
            QMessageBox.information(self, "Информация", "Предыдущий ордер еще обрабатывается.");
            return

        amount_str = self.ui.get_amount()
        if not amount_str:
            QMessageBox.warning(self, "Ошибка", f"Введите количество для {side.lower()}.");
            return
        try:
            amount_from_input_base = float(amount_str)
            if amount_from_input_base <= 0: raise ValueError("Количество должно быть положительным")
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", f"Некорректное количество: {e}");
            return

        symbol = self.current_market_data['symbol']
        price_for_buy_cost_calculation = self.current_last_price

        if side.lower() == 'buy' and (price_for_buy_cost_calculation is None or price_for_buy_cost_calculation <= 0):
            QMessageBox.warning(self, "Ошибка цены",
                                "Нет цены для расчета стоимости покупки. Дождитесь обновления графика.");
            return

        self.ui.show_order_status(f"Отправка {side.lower()} ордера...", False)
        self.ui.buy_button.setEnabled(False);
        self.ui.sell_button.setEnabled(False)

        self.create_order_worker = CreateOrderWorker(
            self.mexc_service, symbol, side,
            amount_from_user=amount_from_input_base,
            current_price=price_for_buy_cost_calculation,
            market_data=self.current_market_data,  # Передаем полные market_data
            parent=self
        )
        self.create_order_worker.order_finished.connect(self._handle_order_finished)
        self.create_order_worker.finished.connect(self._on_create_order_worker_finished)
        self.create_order_worker.start()

    def _handle_buy_action(self):
        self._initiate_trade("buy")

    def _handle_sell_action(self):
        self._initiate_trade("sell")

    def stop_all_updates(self):
        self.ohlcv_update_timer.stop();
        self.balances_update_timer.stop()
        for wa in ["fetch_ohlcv_worker", "fetch_balances_worker", "create_order_worker"]:
            w = getattr(self, wa, None)
            if w and w.isRunning(): w.stop()
            if w and not w.isRunning(): w.deleteLater();setattr(self, wa, None)

    def closeEvent(self, event):
        self.stop_all_updates(); super().closeEvent(event)


class MockTradeWidgetForTest(QWidget): pass



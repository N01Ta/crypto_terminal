# src/widgets/coin_list_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QApplication, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot, QTimer, Qt, QUrl
from PyQt5.QtGui import QDesktopServices

try:
    from ..ui.coin_list_ui import CoinListUi
    from ..core.mexc_service import MexcService
except ImportError:
    CoinListUi = None
    MexcService = None

MAX_COINS_TO_DISPLAY = 50


class LoadMarketsWorker(QThread):
    load_finished = pyqtSignal(object, object)

    def __init__(self, mexc_service_instance, parent=None):
        super().__init__(parent)
        self.mexc_service = mexc_service_instance

    def run(self):
        try:
            market_data_list, error_msg = self.mexc_service.load_markets_data()
            self.load_finished.emit(market_data_list, error_msg)
        except Exception as e:
            self.load_finished.emit(None, f"Ошибка загрузки рынков: {e}")


class FetchTickersWorker(QThread):
    fetch_finished = pyqtSignal(object, object)

    def __init__(self, mexc_service_instance, symbols_list, parent=None):
        super().__init__(parent)
        self.mexc_service = mexc_service_instance
        self.symbols = symbols_list
        self._is_running = True

    def run(self):
        if not self.symbols:
            self.fetch_finished.emit({}, None)
            return
        try:
            tickers_data, error_msg = self.mexc_service.fetch_tickers(symbols=self.symbols)
            if self._is_running:
                self.fetch_finished.emit(tickers_data, error_msg)
        except Exception as e:
            if self._is_running:
                self.fetch_finished.emit(None, f"Ошибка получения цен: {e}")

    def stop(self):
        self._is_running = False


class CoinListWidget(QWidget):
    coin_trade_requested = pyqtSignal(dict)
    GITHUB_URL = "https://github.com/N01Ta/crypto_terminal"  # ВАШ URL

    def __init__(self, mexc_service: MexcService, parent=None):
        super().__init__(parent)
        if CoinListUi is None and not (parent and parent.objectName() == "TestMainWindow"):
            raise ImportError("CoinListUi not imported for CoinListWidget.")

        self.mexc_service = mexc_service
        self.ui = CoinListUi(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.ui)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.load_markets_worker = None
        self.fetch_tickers_worker = None
        self.all_markets_data_full = []
        self.currently_displayed_items_info = []

        self._connect_signals()
        self.price_update_timer = QTimer(self)
        self.price_update_timer.timeout.connect(self.request_price_updates_for_displayed_items)
        self.PRICE_UPDATE_INTERVAL_MS = 7000

    def _connect_signals(self):
        self.ui.sort_option_changed.connect(self.handle_sort_or_search_changed)
        self.ui.search_text_changed.connect(self.handle_sort_or_search_changed)
        self.ui.coin_selected.connect(self._handle_coin_item_selected_from_ui_signal)

        if hasattr(self.ui, 'n_button') and hasattr(self.ui.n_button, 'clicked'):
            self.ui.n_button.clicked.connect(self._handle_n_button_action)
        elif hasattr(self.ui, 'n_button_clicked'):  # Если UI сам эмитирует сигнал
            self.ui.n_button_clicked.connect(self._handle_n_button_action)

    def _handle_n_button_action(self):
        QDesktopServices.openUrl(QUrl(self.GITHUB_URL))

    def _set_controls_enabled(self, enabled: bool):
        self.ui.sort_combo_box.setEnabled(enabled)
        self.ui.search_line_edit.setEnabled(enabled)

    def load_initial_markets_and_prices(self):
        if self.load_markets_worker and self.load_markets_worker.isRunning(): return
        self.ui.set_status_message("Загрузка рынков...", False)
        self._set_controls_enabled(False)
        self.ui.clear_list_widget()
        self.currently_displayed_items_info.clear()
        self.price_update_timer.stop()

        self.load_markets_worker = LoadMarketsWorker(self.mexc_service, self)
        self.load_markets_worker.load_finished.connect(self._handle_markets_loaded)
        self.load_markets_worker.finished.connect(lambda: self._on_worker_finished("load_markets_worker"))
        self.load_markets_worker.start()

    @pyqtSlot(object, object)
    def _handle_markets_loaded(self, market_data_list, error_message):
        self._set_controls_enabled(True)
        if error_message:
            self.ui.set_status_message(f"Ошибка рынков: {error_message}", True);
            return
        if market_data_list:
            self.all_markets_data_full = market_data_list
            self.handle_sort_or_search_changed()
        else:
            self.ui.set_status_message("Рынки не загружены.", True)

    def request_price_updates_for_displayed_items(self):
        if self.fetch_tickers_worker and self.fetch_tickers_worker.isRunning(): return
        symbols_to_fetch = [info['symbol'] for info in self.currently_displayed_items_info]
        if not symbols_to_fetch:
            if not self.price_update_timer.isActive() and self.all_markets_data_full:
                self.price_update_timer.start(self.PRICE_UPDATE_INTERVAL_MS)
            return

        self.ui.set_status_message(f"Обновление цен ({len(symbols_to_fetch)})...", False)
        self.fetch_tickers_worker = FetchTickersWorker(self.mexc_service, symbols_to_fetch, self)
        self.fetch_tickers_worker.fetch_finished.connect(self._handle_tickers_fetched)
        self.fetch_tickers_worker.finished.connect(lambda: self._on_worker_finished("fetch_tickers_worker"))
        self.fetch_tickers_worker.start()

    @pyqtSlot(object, object)
    def _handle_tickers_fetched(self, tickers_data_dict, error_message):
        if error_message: self.ui.set_status_message(f"Ошибка цен: {error_message}", True)
        updated_count = 0
        if isinstance(tickers_data_dict, dict) and tickers_data_dict:
            for item_info in self.currently_displayed_items_info:
                symbol = item_info['symbol']
                list_widget_item = item_info['q_list_item']
                if symbol in tickers_data_dict:
                    ticker_info = tickers_data_dict[symbol]
                    if isinstance(ticker_info, dict):
                        price = ticker_info.get('last_price')
                        market_data_for_item = list_widget_item.data(Qt.UserRole)
                        if price is not None and market_data_for_item:
                            price_precision = market_data_for_item.get('precision', {}).get('price', 8)
                            try:
                                price_str = f"{float(price):.{price_precision}f}"
                                list_widget_item.setText(f"{symbol}\t{price_str}")
                                updated_count += 1
                            except (ValueError, TypeError):
                                list_widget_item.setText(f"{symbol}\t{str(price)}")
            self.ui.set_status_message(
                f"Цены обновлены ({updated_count}). Отображено: {len(self.currently_displayed_items_info)}", False
            )
        elif updated_count == 0 and len(self.currently_displayed_items_info) > 0:
            self.ui.set_status_message(
                f"Цены не обновлены. Отображено: {len(self.currently_displayed_items_info)}", False
            )
        if not self.price_update_timer.isActive():
            self.price_update_timer.start(self.PRICE_UPDATE_INTERVAL_MS)

    def handle_sort_or_search_changed(self):
        search_text = self.ui.search_line_edit.text().lower().strip()
        sort_option_text = self.ui.sort_combo_box.currentText()
        filtered_markets = list(self.all_markets_data_full)
        if search_text:
            filtered_markets = [m for m in filtered_markets if search_text in m['symbol'].lower()]
        reverse_sort = "↓" in sort_option_text
        if "Имя" in sort_option_text or "Цена" in sort_option_text:  # Цена пока тоже по имени
            filtered_markets.sort(key=lambda x: x['symbol'], reverse=reverse_sort)
        self._populate_qlistwidget_with_data(filtered_markets[:MAX_COINS_TO_DISPLAY])
        if self.currently_displayed_items_info:
            self.request_price_updates_for_displayed_items()
        elif not self.price_update_timer.isActive() and self.all_markets_data_full:
            self.price_update_timer.start(self.PRICE_UPDATE_INTERVAL_MS)

    def _populate_qlistwidget_with_data(self, markets_to_display):
        self.ui.clear_list_widget()
        self.currently_displayed_items_info.clear()
        for market_data in markets_to_display:
            pair_symbol = market_data['symbol']
            list_item = QListWidgetItem(f"{pair_symbol}\t---")
            list_item.setData(Qt.UserRole, market_data)
            self.ui.coin_list_widget.addItem(list_item)
            self.currently_displayed_items_info.append({'symbol': pair_symbol, 'q_list_item': list_item})
        self.ui.set_status_message(f"Отображено: {self.ui.coin_list_widget.count()}.", False)

    @pyqtSlot(str)
    def _handle_coin_item_selected_from_ui_signal(self, pair_symbol: str):
        selected_market_info = None
        for item_info in self.currently_displayed_items_info:
            if item_info['symbol'] == pair_symbol:
                original_market_data = item_info['q_list_item'].data(Qt.UserRole)
                if original_market_data:
                    selected_market_info = dict(original_market_data)
                    try:
                        text_content = item_info['q_list_item'].text()
                        if '\t' in text_content:
                            _, price_str = text_content.split('\t', 1)
                            if price_str != "---":
                                selected_market_info['current_price_from_list'] = float(price_str)
                    except:
                        pass
                break
        if selected_market_info:
            self.coin_trade_requested.emit(selected_market_info)

    def _on_worker_finished(self, worker_attribute_name: str):
        worker = getattr(self, worker_attribute_name, None)
        if worker: worker.deleteLater(); setattr(self, worker_attribute_name, None)

    def stop_updates(self):
        self.price_update_timer.stop()
        for worker_attr in ["load_markets_worker", "fetch_tickers_worker"]:
            worker = getattr(self, worker_attr, None)
            if worker and worker.isRunning():
                if hasattr(worker, 'stop'): worker.stop()
                worker.quit()
                if not worker.wait(300): worker.terminate(); worker.wait(100)
            if worker: worker.deleteLater(); setattr(self, worker_attr, None)

    def closeEvent(self, event):
        self.stop_updates();
        super().closeEvent(event)


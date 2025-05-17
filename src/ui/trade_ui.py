# src/ui/trade_ui.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QSizePolicy, QGraphicsView, QGraphicsScene, QSpacerItem,
    QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsTextItem
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QPalette, QBrush

# --- Цветовая палитра ---
DARK_BG_COLOR = "#282c34"
PRIMARY_TEXT_COLOR = "#e8e8f0"
SECONDARY_TEXT_COLOR = "#b0b0d0"
ACCENT_COLOR = "#9b88c7"
ACCENT_HOVER_COLOR = "#a995d1"
PANEL_BG_COLOR = "rgba(45, 48, 56, 0.9)"
PANEL_BORDER_COLOR = "rgba(155, 136, 199, 0.25)"
INPUT_BG_COLOR = "rgba(30, 32, 40, 0.95)"
INPUT_BORDER_COLOR = ACCENT_COLOR
INPUT_FOCUS_BORDER_COLOR = ACCENT_HOVER_COLOR
BUY_COLOR = "#2ecc71"
BUY_HOVER_COLOR = "#27ae60"
SELL_COLOR = "#e74c3c"
SELL_HOVER_COLOR = "#c0392b"
PREDICTION_TEXT_COLOR_HEX = "#f1c40f"
CHART_LINE_COLOR = QColor(ACCENT_COLOR)
CHART_PREDICTION_MARKER_COLOR = QColor(PREDICTION_TEXT_COLOR_HEX)


class TradeUi(QWidget):
    back_button_clicked = pyqtSignal()
    buy_button_clicked = pyqtSignal()
    sell_button_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TradeUi")

        self.top_bar_widget = None
        self.back_button = None
        self.coin_pair_price_label = None
        self.content_layout = None
        self.chart_view = None
        self.chart_scene = None
        self.prediction_label_container = None
        self.prediction_label = None
        self.right_panel_widget = None
        self.balance_base_label = None
        self.balance_quote_label = None
        self.amount_input = None
        self.buy_button = None
        self.sell_button = None
        self.order_status_label = None

        self._padding = 15
        self._min_price_range_points = 50
        self._price_precision_default = 2

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- Верхняя панель ---
        self.top_bar_widget = QWidget()
        self.top_bar_widget.setObjectName("topBar")
        top_bar_layout = QHBoxLayout(self.top_bar_widget)
        top_bar_layout.setContentsMargins(10, 8, 10, 8)

        self.back_button = QPushButton("<")
        self.back_button.setObjectName("navigationButton")
        self.back_button.setFixedSize(QSize(35, 35))
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self.back_button_clicked.emit)
        top_bar_layout.addWidget(self.back_button)

        self.coin_pair_price_label = QLabel("ЗАГРУЗКА...")
        self.coin_pair_price_label.setObjectName("coinPairPriceLabel")
        pair_price_font = QFont()
        pair_price_font.setPointSize(16)
        pair_price_font.setBold(True)
        self.coin_pair_price_label.setFont(pair_price_font)
        self.coin_pair_price_label.setAlignment(Qt.AlignCenter)
        top_bar_layout.addWidget(self.coin_pair_price_label, stretch=1)
        top_bar_layout.addSpacerItem(QSpacerItem(35, 10, QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.main_layout.addWidget(self.top_bar_widget)

        # --- Основной контент ---
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)

        # Левая часть
        left_panel_widget = QWidget()
        left_panel_layout = QVBoxLayout(left_panel_widget)
        left_panel_layout.setContentsMargins(0, 0, 0, 0)
        left_panel_layout.setSpacing(10)

        self.chart_view = QGraphicsView()
        self.chart_view.setObjectName("chartView")
        self.chart_scene = QGraphicsScene(self)
        self.chart_view.setScene(self.chart_scene)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chart_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_panel_layout.addWidget(self.chart_view, stretch=3)

        self.prediction_label_container = QWidget()
        self.prediction_label_container.setObjectName("predictionContainer")
        prediction_layout = QHBoxLayout(self.prediction_label_container)
        prediction_layout.setContentsMargins(10, 10, 10, 10)

        self.prediction_label = QLabel("Предсказание: ОЖИДАНИЕ")
        self.prediction_label.setObjectName("predictionLabel")
        pred_font = QFont()
        pred_font.setPointSize(14)
        pred_font.setBold(True)
        self.prediction_label.setFont(pred_font)
        self.prediction_label.setAlignment(Qt.AlignCenter)
        prediction_layout.addWidget(self.prediction_label)
        left_panel_layout.addWidget(self.prediction_label_container, stretch=1)

        # Правая часть
        self.right_panel_widget = QWidget()
        self.right_panel_widget.setObjectName("orderPanel")
        self.right_panel_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.right_panel_widget.setFixedWidth(300)

        right_panel_layout = QVBoxLayout(self.right_panel_widget)
        right_panel_layout.setContentsMargins(15, 15, 15, 15)
        right_panel_layout.setSpacing(15)
        right_panel_layout.setAlignment(Qt.AlignTop)

        self.balance_base_label = QLabel("Баланс XXX: 0.00")
        self.balance_base_label.setObjectName("balanceLabel")
        self.balance_quote_label = QLabel("Баланс YYY: 0.00")
        self.balance_quote_label.setObjectName("balanceLabel")
        balance_font = QFont()
        balance_font.setPointSize(13)
        self.balance_base_label.setFont(balance_font)
        self.balance_quote_label.setFont(balance_font)
        right_panel_layout.addWidget(self.balance_base_label)
        right_panel_layout.addWidget(self.balance_quote_label)
        right_panel_layout.addSpacing(20)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Кол-во")
        self.amount_input.setObjectName("styledLineEdit")
        self.amount_input.setMinimumHeight(40)
        right_panel_layout.addWidget(self.amount_input)

        self.buy_button = QPushButton("Купить")
        self.buy_button.setObjectName("buyButton")
        self.buy_button.setMinimumHeight(45)
        self.buy_button.setCursor(Qt.PointingHandCursor)
        self.buy_button.clicked.connect(self.buy_button_clicked.emit)
        right_panel_layout.addWidget(self.buy_button)

        self.sell_button = QPushButton("Продать")
        self.sell_button.setObjectName("sellButton")
        self.sell_button.setMinimumHeight(45)
        self.sell_button.setCursor(Qt.PointingHandCursor)
        self.sell_button.clicked.connect(self.sell_button_clicked.emit)
        right_panel_layout.addWidget(self.sell_button)

        self.order_status_label = QLabel("")
        self.order_status_label.setObjectName("orderStatusLabel")
        self.order_status_label.setAlignment(Qt.AlignCenter)
        self.order_status_label.setWordWrap(True)
        self.order_status_label.setMinimumHeight(30)
        self.order_status_label.hide()
        right_panel_layout.addWidget(self.order_status_label)
        right_panel_layout.addStretch(1)

        self.content_layout.addWidget(left_panel_widget, stretch=3)
        self.content_layout.addWidget(self.right_panel_widget, stretch=0)
        self.main_layout.addLayout(self.content_layout, stretch=1)
        self.setLayout(self.main_layout)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget#TradeUi {{ background-color: {DARK_BG_COLOR}; }}
            QWidget#topBar {{ background-color: {PANEL_BG_COLOR}; border-bottom: 1px solid {PANEL_BORDER_COLOR}; }}
            QPushButton#navigationButton {{ 
                background-color: {ACCENT_COLOR}; color: white; border: none; 
                border-radius: 6px; font-size: 18px; font-weight: bold; 
            }}
            QPushButton#navigationButton:hover {{ background-color: {ACCENT_HOVER_COLOR}; }}
            QLabel#coinPairPriceLabel {{ color: {PRIMARY_TEXT_COLOR}; }}
            QGraphicsView#chartView {{ 
                background-color: {INPUT_BG_COLOR}; border-radius: 8px; 
                border: 1px solid {PANEL_BORDER_COLOR}; 
            }}
            QWidget#predictionContainer {{ 
                background-color: {INPUT_BG_COLOR}; border-radius: 8px; 
                border: 1px solid {PANEL_BORDER_COLOR}; margin-top: 5px; 
            }}
            QLabel#predictionLabel {{ color: {QColor(PREDICTION_TEXT_COLOR_HEX).name()}; }}
            QWidget#orderPanel {{ 
                background-color: {PANEL_BG_COLOR}; border-radius: 12px; 
                border: 1px solid {PANEL_BORDER_COLOR}; 
            }}
            QLabel#balanceLabel {{ color: {SECONDARY_TEXT_COLOR}; font-size: 14px; }}
            QLineEdit#styledLineEdit {{ 
                background-color: {INPUT_BG_COLOR}; color: {PRIMARY_TEXT_COLOR}; 
                border: 1px solid {INPUT_BORDER_COLOR}; border-radius: 6px; 
                padding: 8px 10px; font-size: 14px; 
            }}
            QLineEdit#styledLineEdit:focus {{ border: 1.5px solid {INPUT_FOCUS_BORDER_COLOR}; }}
            QPushButton#buyButton {{ 
                background-color: {BUY_COLOR}; color: white; border: none; 
                border-radius: 8px; padding: 10px; font-size: 16px; font-weight: bold; 
            }}
            QPushButton#buyButton:hover {{ background-color: {BUY_HOVER_COLOR}; }}
            QPushButton#sellButton {{ 
                background-color: {SELL_COLOR}; color: white; border: none; 
                border-radius: 8px; padding: 10px; font-size: 16px; font-weight: bold; 
            }}
            QPushButton#sellButton:hover {{ background-color: {SELL_HOVER_COLOR}; }}
            QLabel#orderStatusLabel {{ font-size: 12px; }}
        """)

    def clear_chart(self):
        if self.chart_scene:
            self.chart_scene.clear()

    def draw_price_chart(self, ohlcv_data: list, predicted_price_data: tuple = None, price_precision: int = None):
        if not self.chart_scene:
            return
        self.clear_chart()
        effective_price_precision = price_precision if price_precision is not None else self._price_precision_default

        if not ohlcv_data or len(ohlcv_data) < 2:
            text_item = QGraphicsTextItem("Недостаточно данных для графика")
            text_item.setDefaultTextColor(SECONDARY_TEXT_COLOR)
            font = QFont()
            font.setPointSize(12)
            text_item.setFont(font)
            self.chart_scene.addItem(text_item)
            view_rect = self.chart_view.viewport().rect()
            if view_rect.width() > 0 and view_rect.height() > 0:
                text_item.setPos(
                    view_rect.width() / 2 - text_item.boundingRect().width() / 2,
                    view_rect.height() / 2 - text_item.boundingRect().height() / 2
                )
            return

        try:
            close_prices = [float(candle[4]) for candle in ohlcv_data]
            min_price_hist = min(close_prices)
            max_price_hist = max(close_prices)

            min_price_overall = min_price_hist
            max_price_overall = max_price_hist
            predicted_value_numeric = None

            if predicted_price_data and predicted_price_data[0] is not None:
                try:
                    predicted_value_numeric = float(predicted_price_data[0])
                    min_price_overall = min(min_price_overall, predicted_value_numeric)
                    max_price_overall = max(max_price_overall, predicted_value_numeric)
                except (ValueError, TypeError):
                    predicted_value_numeric = None

            view_rect = self.chart_view.viewport().rect()
            chart_width = view_rect.width() - 2 * self._padding
            chart_height = view_rect.height() - 2 * self._padding

            if chart_width <= 0 or chart_height <= 0:
                return

            price_range = max_price_overall - min_price_overall
            if abs(price_range) < 1e-9:
                price_range_default_add = max(
                    abs(min_price_overall) * 0.02,
                    self._min_price_range_points * (10 ** -effective_price_precision)
                )
                if abs(price_range_default_add) < 1e-9:
                    price_range_default_add = (10 ** -effective_price_precision)
                min_price_overall -= price_range_default_add / 2
                max_price_overall += price_range_default_add / 2
                price_range = max_price_overall - min_price_overall
            if abs(price_range) < 1e-9:
                price_range = 1

            num_points_x_hist = len(close_prices)
            num_points_x_total_slots = num_points_x_hist
            if predicted_value_numeric is not None:
                num_points_x_total_slots += 1

            if num_points_x_total_slots <= 1:
                return

            x_step = chart_width / (num_points_x_total_slots - 1)

            line_pen = QPen(CHART_LINE_COLOR)
            line_pen.setWidth(2)
            points = []
            for i, price in enumerate(close_prices):
                x = self._padding + i * x_step
                y_ratio = 0.5
                if abs(price_range) > 1e-9:
                    y_ratio = (price - min_price_overall) / price_range
                y = self._padding + chart_height - (y_ratio * chart_height)
                points.append(QPointF(x, y))

            for i in range(len(points) - 1):
                line = QGraphicsLineItem(points[i].x(), points[i].y(), points[i + 1].x(), points[i + 1].y())
                line.setPen(line_pen)
                self.chart_scene.addItem(line)

            if predicted_value_numeric is not None and points:
                pred_x = self._padding + num_points_x_hist * x_step
                pred_y_ratio = 0.5
                if abs(price_range) > 1e-9:
                    pred_y_ratio = (predicted_value_numeric - min_price_overall) / price_range
                pred_y = self._padding + chart_height - (pred_y_ratio * chart_height)

                marker_radius = 4
                marker = QGraphicsEllipseItem(
                    pred_x - marker_radius, pred_y - marker_radius,
                    2 * marker_radius, 2 * marker_radius
                )
                pred_color = CHART_PREDICTION_MARKER_COLOR
                if len(predicted_price_data) > 2 and isinstance(predicted_price_data[2], QColor):
                    pred_color = predicted_price_data[2]
                marker.setPen(QPen(pred_color, 1))
                marker.setBrush(QBrush(pred_color))
                self.chart_scene.addItem(marker)

                last_hist_point = points[-1]
                dash_pen = QPen(pred_color, 1)
                dash_pen.setStyle(Qt.DashLine)
                prediction_line = QGraphicsLineItem(last_hist_point.x(), last_hist_point.y(), pred_x, pred_y)
                prediction_line.setPen(dash_pen)
                self.chart_scene.addItem(prediction_line)

            self.chart_scene.setSceneRect(0, 0, view_rect.width(), view_rect.height())
        except Exception as e_draw:
            print(f"[TradeUi CRITICAL] Exception in draw_price_chart: {e_draw}")
            try:
                self.clear_chart()
                err_text_item = QGraphicsTextItem(f"Ошибка отрисовки графика:\n{e_draw}")
                err_text_item.setDefaultTextColor(QColor("red"))
                self.chart_scene.addItem(err_text_item)
                err_text_item.setPos(5, 5)
            except Exception:
                pass  # Ошибка при отрисовке ошибки - ничего не поделать

    def set_coin_pair_price(self, pair: str, price: str):
        if self.coin_pair_price_label:
            self.coin_pair_price_label.setText(f"{pair} : {price}")

    def set_balances(self, base_asset: str, base_balance: str, quote_asset: str, quote_balance: str):
        if self.balance_base_label:
            self.balance_base_label.setText(f"Баланс {base_asset}: {base_balance}")
        if self.balance_quote_label:
            self.balance_quote_label.setText(f"Баланс {quote_asset}: {quote_balance}")

    def set_prediction(self, prediction_text: str, color: QColor = QColor(PREDICTION_TEXT_COLOR_HEX)):
        if not self.prediction_label:
            return
        self.prediction_label.setText(f"{prediction_text}")
        actual_color = color if isinstance(color, QColor) else QColor(PREDICTION_TEXT_COLOR_HEX)
        palette = self.prediction_label.palette()
        palette.setColor(QPalette.WindowText, actual_color)
        self.prediction_label.setPalette(palette)

    def get_amount(self) -> str:
        return self.amount_input.text().strip() if self.amount_input else ""

    def clear_amount(self):
        if self.amount_input:
            self.amount_input.clear()

    def show_order_status(self, message: str, is_success: bool):
        if not self.order_status_label:
            return
        self.order_status_label.setText(message)
        color_hex = BUY_COLOR if is_success else SELL_COLOR
        self.order_status_label.setStyleSheet(f"color: {color_hex}; font-size: 12px;")
        self.order_status_label.show()

    def hide_order_status(self):
        if self.order_status_label:
            self.order_status_label.hide()


# src/ui/coin_list_ui.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QListWidget, QAbstractItemView, QStyledItemDelegate, QStyleOptionViewItem,
    QStyle, QListWidgetItem
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QPalette

# --- Цветовая палитра ---
DARK_BG_COLOR = "#282c34"
PRIMARY_TEXT_COLOR = "#e8e8f0"
SECONDARY_TEXT_COLOR = "#b0b0d0"
ACCENT_COLOR = "#9b88c7"
ACCENT_HOVER_COLOR = "#a995d1"
PANEL_BG_COLOR = "rgba(45, 48, 56, 0.9)"
PANEL_BORDER_COLOR = "rgba(155, 136, 199, 0.25)"
LIST_AREA_BG_COLOR = QColor(35, 38, 46, 242)
ITEM_HOVER_BG_COLOR = QColor(155, 136, 199, 30)
LINE_SEPARATOR_COLOR = QColor(100, 100, 120, 100)
INPUT_BG_COLOR = "rgba(30, 32, 40, 0.95)"
INPUT_BORDER_COLOR = ACCENT_COLOR
INPUT_FOCUS_BORDER_COLOR = ACCENT_HOVER_COLOR


# --- Кастомный делегат для отрисовки элементов QListWidget ---
class CoinItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pair_font = QFont();
        self.pair_font.setPointSize(14)
        self.price_font = QFont();
        self.price_font.setPointSize(14)

        self.horizontal_padding = 15
        self.vertical_padding = 12
        self.line_v_padding = 8
        self.separator_h_margin = 5
        self.min_price_width = 90

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()

        display_text = index.data(Qt.DisplayRole)
        if not display_text or '\t' not in display_text:
            super().paint(painter, option, index)
            painter.restore()
            return

        pair_text, price_text = display_text.split('\t', 1)
        rect = option.rect

        current_bg_color = LIST_AREA_BG_COLOR
        if option.state & QStyle.State_MouseOver:
            current_bg_color = ITEM_HOVER_BG_COLOR
        painter.fillRect(rect, current_bg_color)

        pen_horizontal = QPen(LINE_SEPARATOR_COLOR);
        pen_horizontal.setWidth(1)
        painter.setPen(pen_horizontal)
        painter.drawLine(rect.left() + self.horizontal_padding, rect.bottom(),
                         rect.right() - self.horizontal_padding, rect.bottom())

        price_fm = painter.fontMetrics()
        price_text_width = price_fm.horizontalAdvance(price_text) + 5
        actual_price_width = max(self.min_price_width, price_text_width)
        price_rect = QRect(
            rect.right() - self.horizontal_padding - actual_price_width,
            rect.top(),
            actual_price_width,
            rect.height()
        )
        x_line_pos = price_rect.left() - self.separator_h_margin
        pair_rect = QRect(
            rect.left() + self.horizontal_padding,
            rect.top(),
            x_line_pos - (rect.left() + self.horizontal_padding) - self.separator_h_margin,
            rect.height()
        )

        pen_vertical = QPen(LINE_SEPARATOR_COLOR);
        pen_vertical.setWidth(1)
        painter.setPen(pen_vertical)
        if pair_rect.right() < x_line_pos:
            painter.drawLine(int(x_line_pos), rect.top() + self.line_v_padding,
                             int(x_line_pos), rect.bottom() - self.line_v_padding)

        painter.setFont(self.pair_font)
        painter.setPen(QColor(PRIMARY_TEXT_COLOR))
        painter.drawText(pair_rect, Qt.AlignLeft | Qt.AlignVCenter, pair_text)

        painter.setFont(self.price_font)
        painter.setPen(QColor(SECONDARY_TEXT_COLOR))
        painter.drawText(price_rect, Qt.AlignRight | Qt.AlignVCenter, price_text)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return QSize(super().sizeHint(option, index).width(), 50)


class CoinListUi(QWidget):
    sort_option_changed = pyqtSignal(str)
    search_text_changed = pyqtSignal(str)
    coin_selected = pyqtSignal(str)
    n_button_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CoinListUi")
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self);
        self.main_layout.setContentsMargins(0, 0, 0, 0);
        self.main_layout.setSpacing(0)
        self.top_panel_widget = QWidget();
        self.top_panel_widget.setObjectName("topPanel")
        top_panel_layout = QHBoxLayout(self.top_panel_widget);
        top_panel_layout.setContentsMargins(10, 8, 10, 8);
        top_panel_layout.setSpacing(10)
        self.n_button = QPushButton("N");
        self.n_button.setObjectName("nButton");
        n_font = QFont();
        n_font.setPointSize(16);
        n_font.setBold(True);
        self.n_button.setFont(n_font);
        self.n_button.setFixedSize(QSize(40, 40));
        self.n_button.setCursor(Qt.PointingHandCursor);
        self.n_button.clicked.connect(self.n_button_clicked);
        top_panel_layout.addWidget(self.n_button)
        self.sort_combo_box = QComboBox();
        self.sort_combo_box.setObjectName("styledComboBox");
        self.sort_combo_box.setMinimumWidth(130);
        self.sort_combo_box.setMinimumHeight(38);
        self.sort_combo_box.addItem("Сортировка");
        self.sort_combo_box.addItem("Имя ↑");
        self.sort_combo_box.addItem("Имя ↓");
        #self.sort_combo_box.addItem("Цена ↑");
        #self.sort_combo_box.addItem("Цена ↓");
        self.sort_combo_box.currentIndexChanged.connect(self._on_sort_changed);
        top_panel_layout.addWidget(self.sort_combo_box)
        self.search_line_edit = QLineEdit();
        self.search_line_edit.setObjectName("styledLineEdit");
        self.search_line_edit.setPlaceholderText("Поиск монеты");
        self.search_line_edit.setMinimumHeight(38);
        self.search_line_edit.setClearButtonEnabled(True);
        self.search_line_edit.textChanged.connect(self.search_text_changed);
        top_panel_layout.addWidget(self.search_line_edit, stretch=1)
        self.main_layout.addWidget(self.top_panel_widget)
        self.coin_list_widget = QListWidget();
        self.coin_list_widget.setObjectName("coinListView");
        self.coin_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        self.coin_list_widget.setAlternatingRowColors(False);
        self.coin_list_widget.setSpacing(0)
        self.coin_item_delegate = CoinItemDelegate(self.coin_list_widget);
        self.coin_list_widget.setItemDelegate(self.coin_item_delegate)
        self.coin_list_widget.setSelectionMode(QAbstractItemView.SingleSelection);
        self.coin_list_widget.itemClicked.connect(self._on_list_item_clicked)
        self.main_layout.addWidget(self.coin_list_widget, stretch=1)
        self.status_label = QLabel("Готов.");
        self.status_label.setObjectName("statusLabel");
        self.status_label.setFixedHeight(25);
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter);
        self.status_label.setContentsMargins(0, 0, 10, 0);
        self.main_layout.addWidget(self.status_label)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget#CoinListUi {{ background-color: {DARK_BG_COLOR}; }}
            QWidget#topPanel {{ background-color: {PANEL_BG_COLOR}; border-bottom: 1px solid {PANEL_BORDER_COLOR}; }}
            QPushButton#nButton {{ background-color: {ACCENT_COLOR}; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; }}
            QPushButton#nButton:hover {{ background-color: {ACCENT_HOVER_COLOR}; }}
            QComboBox#styledComboBox {{ background-color: {INPUT_BG_COLOR}; color: {PRIMARY_TEXT_COLOR}; border: 1px solid {INPUT_BORDER_COLOR}; border-radius: 6px; padding: 1px 10px 1px 10px; font-size: 14px; }}
            QComboBox#styledComboBox::drop-down {{ border: none; }}
            QComboBox#styledComboBox QAbstractItemView {{ background-color: {INPUT_BG_COLOR}; color: {PRIMARY_TEXT_COLOR}; border: 1px solid {INPUT_BORDER_COLOR}; selection-background-color: {ACCENT_COLOR}; outline: none; }}
            QLineEdit#styledLineEdit {{ background-color: {INPUT_BG_COLOR}; color: {PRIMARY_TEXT_COLOR}; border: 1px solid {INPUT_BORDER_COLOR}; border-radius: 6px; padding: 8px 10px; font-size: 14px; }}
            QLineEdit#styledLineEdit:focus {{ border: 1.5px solid {INPUT_FOCUS_BORDER_COLOR}; }}
            QListWidget#coinListView {{ background-color: {LIST_AREA_BG_COLOR.name()}; border: none; outline: 0; }}
            QScrollBar:vertical {{ border: none; background: rgba(0,0,0,0.15); width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: {ACCENT_COLOR}; min-height: 25px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background: {ACCENT_HOVER_COLOR}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QLabel#statusLabel {{ color: {SECONDARY_TEXT_COLOR}; font-size: 11px; }}
        """)

    def _on_sort_changed(self, index):
        if index > 0: self.sort_option_changed.emit(self.sort_combo_box.currentText())

    def _on_list_item_clicked(self, item: QListWidgetItem):
        market_data = item.data(Qt.UserRole)
        if market_data and isinstance(market_data, dict):
            pair_symbol = market_data.get('symbol')
            if pair_symbol: self.coin_selected.emit(pair_symbol)

    def add_item_to_list(self, pair: str, price: str, market_data: dict):
        display_text = f"{pair}\t{price}"
        list_item = QListWidgetItem(display_text)
        list_item.setData(Qt.UserRole, market_data)
        self.coin_list_widget.addItem(list_item)

    def update_item_in_list(self, pair_symbol: str, new_price: str):
        for i in range(self.coin_list_widget.count()):
            item = self.coin_list_widget.item(i)
            market_d = item.data(Qt.UserRole)
            if market_d and market_d.get('symbol') == pair_symbol:
                item.setText(f"{pair_symbol}\t{new_price}")
                return

    def clear_list_widget(self):
        self.coin_list_widget.clear()

    def set_status_message(self, message: str, is_error: bool = False):
        self.status_label.setText(message)
        if is_error:
            self.status_label.setStyleSheet(f"color: #e74c3c; font-size: 11px;")
        else:
            self.status_label.setStyleSheet(f"color: {SECONDARY_TEXT_COLOR}; font-size: 11px;")


# Тестовый блок
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QListWidgetItem

    app = QApplication(sys.argv)
    coin_list_ui_instance = CoinListUi()
    coin_list_ui_instance.setWindowTitle("Coin List UI - Delegate Full (Should Work)")
    coins_data_test = [("BTC/USDT", "70k", {"symbol": "BTC/USDT"}), ("ETH/USDT", "3.5k", {"symbol": "ETH/USDT"})]
    for pair, price, market_d in coins_data_test: coin_list_ui_instance.add_item_to_list(pair, price, market_d)


    def handle_selection(pair):
        print(f"UI Test - Selected: {pair}")


    coin_list_ui_instance.coin_selected.connect(handle_selection)
    coin_list_ui_instance.resize(380, 600);
    coin_list_ui_instance.show()
    sys.exit(app.exec_())
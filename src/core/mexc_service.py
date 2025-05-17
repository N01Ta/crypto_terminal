# src/core/mexc_service.py
import ccxt
from pprint import pprint
import os
import time
import math # Для log10

class MexcService:
    def __init__(self, api_key=None, api_secret=None, passphrase=None):
        self.exchange_id = 'mexc'
        self.exchange_class = getattr(ccxt, self.exchange_id)

        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase

        self.exchange = None
        self._initialize_exchange()
        # print(f"MEXC Service initialized. API Key set: {bool(self.api_key)}") # Можно закомментировать для уменьшения логов

    def _parse_precision_value(self, precision_input):
        if precision_input is None: return 8
        try:
            val = float(precision_input)
            if val == 0: return 8
            if val >= 1:
                if isinstance(precision_input, int) and precision_input > 0:
                    return precision_input
                # Для цены, если precision_input (ccxt) >= 1, это обычно 0 знаков после запятой.
                # Например, если шаг цены 1 (для BTC/USD на некоторых биржах), то 0 знаков.
                # Но ccxt для USDT пар обычно дает точность < 1.
                # Это упрощение, т.к. ccxt может возвращать и количество знаков, и сам шаг.
                # Если ccxt возвращает число знаков (например, 2 для 0.01), это правильно.
                # Если он возвращает шаг (0.01), то нужно извлечь кол-во знаков.
                # Данная логика больше ориентирована на извлечение из шага.
                num_str = format(val, '.16f').rstrip('0')
                if '.' in num_str:
                    return len(num_str.split('.')[1])
                return 0 # 0 знаков, если это целое число >= 1 (шаг 1, 2 и т.д.)

            s = format(val, '.16f')
            if '.' in s:
                return len(s.split('.')[1].rstrip('0'))
            else:
                return 0
        except ValueError: return 8
        except Exception: return 8


    def _initialize_exchange(self):
        try:
            config = {'enableRateLimit': True, 'options': {'defaultType': 'spot'}}
            if self.api_key and self.api_secret:
                config['apiKey'] = self.api_key
                config['secret'] = self.api_secret
                if self.passphrase: config['password'] = self.passphrase
            self.exchange = self.exchange_class(config)
        except Exception as e:
            print(f"Error initializing MEXC exchange: {e}"); self.exchange = None; raise

    def set_api_credentials(self, api_key: str, api_secret: str, passphrase: str = None):
        self.api_key = api_key; self.api_secret = api_secret; self.passphrase = passphrase
        self._initialize_exchange()
        print(f"MexcService: API credentials updated. API Key set: {bool(self.api_key)}")

    def load_markets_data(self):
        if not self.exchange: return None, "Биржа не инициализирована (load_markets_data)."
        try:
            if not self.exchange.markets: self.exchange.load_markets()
            markets = self.exchange.markets; filtered_markets = []
            for symbol, market_data in markets.items():
                if market_data.get('active', False) and market_data.get('spot', False) and \
                   market_data.get('quote', '').upper() == 'USDT':
                    price_prec_raw = market_data.get('precision',{}).get('price')
                    amount_prec_raw = market_data.get('precision',{}).get('amount')
                    parsed_price_prec = self._parse_precision_value(price_prec_raw)
                    parsed_amount_prec = self._parse_precision_value(amount_prec_raw)
                    filtered_markets.append({
                        'symbol': market_data['symbol'], 'base': market_data['base'],
                        'quote': market_data['quote'], 'id': market_data['id'],
                        'precision': {'price': parsed_price_prec, 'amount': parsed_amount_prec,
                                      'raw_price': price_prec_raw, 'raw_amount': amount_prec_raw},
                        'limits': market_data.get('limits', {}),
                    })
            # print(f"Loaded {len(filtered_markets)} active USDT spot markets.")
            return filtered_markets, None
        except Exception as e:
            return None, f"Ошибка загрузки рынков: {e}"

    def fetch_tickers(self, symbols: list = None):
        if not self.exchange: return None, "Биржа не инициализирована (fetch_tickers)."
        if not hasattr(self.exchange, 'fetch_tickers'): return None, "fetch_tickers не поддерживается."
        try:
            if symbols and not isinstance(symbols, list): symbols = [symbols]
            tickers_data = self.exchange.fetch_tickers(symbols=symbols)
            simplified_tickers = {}
            if tickers_data:
                for symbol, data in tickers_data.items():
                    if data and 'last' in data and data['last'] is not None:
                        simplified_tickers[symbol] = {
                            'symbol': symbol, 'last_price': data['last'], 'timestamp': data.get('timestamp'),
                            'bid': data.get('bid'), 'ask': data.get('ask'), 'volume': data.get('quoteVolume')
                        }
            return simplified_tickers, None
        except Exception as e:
            return None, f"Ошибка получения цен: {e}"

    def fetch_ohlcv(self, symbol: str, timeframe: str = '5m', since: int = None, limit: int = 100):
        if not self.exchange: return None, "Биржа не инициализирована (fetch_ohlcv)."
        if not self.exchange.has['fetchOHLCV']: return None, f"fetchOHLCV не поддерживается."
        try:
            ohlcv_data = self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            return ohlcv_data, None
        except Exception as e: return None, f"Ошибка OHLCV ({symbol}): {e}"

    def fetch_balances(self):
        if not self.exchange: return None, "Биржа не инициализирована (fetch_balances)."
        if not self.api_key or not self.api_secret: return None, "API ключи не установлены."
        try:
            # print("--- [MexcService] Attempting to fetch REAL balances from exchange ---")
            raw_balance_data = self.exchange.fetch_balance()
            # print(f"--- [MexcService] RAW balance data type from ccxt: {type(raw_balance_data)}")
            return raw_balance_data, None
        except Exception as e:
            print(f"MEXC UNEXPECTED error in fetch_balances: {type(e).__name__} - {e}")
            return None, f"Ошибка получения балансов: {e}"

    def create_market_order(self, symbol: str, side: str, amount: float):
        if not self.exchange: return None, "Биржа не инициализирована (create_market_order)."
        if not self.api_key or not self.api_secret: return None, "API ключи не установлены."
        if not (self.exchange.has['createMarketBuyOrder'] and self.exchange.has['createMarketSellOrder']):
            return None, "Создание рыночных ордеров не поддерживается."
        try:
            order_response = None
            # ВАЖНО: Для MEXC (и ccxt в целом) create_market_buy_order ожидает amount в QUOTE валюте (стоимость).
            # create_market_sell_order ожидает amount в BASE валюте.
            # Текущая логика кнопок в TradeWidget передает amount как есть, что для BUY может быть неверно.
            if side.lower() == 'buy':
                # Если amount - это сколько BASE купить, то это неправильно для MEXC.
                # Если amount - это сколько QUOTE потратить, то это правильно.
                # Для симуляции пока оставим так.
                print(f"Warning: MEXC market BUY expects 'amount' as QUOTE currency (cost). Received: {amount} (assumed base for now)")
                order_response = self.exchange.create_market_buy_order(symbol, amount)
            elif side.lower() == 'sell':
                order_response = self.exchange.create_market_sell_order(symbol, amount)
            else: return None, "Неверная сторона ордера."
            return order_response, None
        except Exception as e: return None, f"Ошибка создания ордера: {e}"

if __name__ == '__main__':
    # ... (тестовый блок как был, можно раскомментировать для проверки _parse_precision_value)
    print("Testing MexcService with precision parsing...")
    mexc_service = MexcService()
    markets, error = mexc_service.load_markets_data()
    if error: print(f"Error: {error}")
    elif markets:
        print(f"Loaded {len(markets)} USDT markets. Checking precision for a few:")
        for m_data in markets[:5]: # Первые 5
            print(f"  Symbol: {m_data['symbol']}, Raw Price: {m_data['precision']['raw_price']}, Parsed Price: {m_data['precision']['price']}")
        problem_symbols = ['SCC/USDT', 'PEPE/USDT', 'SHIB/USDT', 'BONK/USDT'] # Примеры монет с очень малой ценой
        for ps in problem_symbols:
            found = next((m for m in markets if m['symbol'] == ps), None)
            if found:
                 print(f"  Symbol: {found['symbol']}, Raw Price: {found['precision']['raw_price']}, Parsed Price: {found['precision']['price']}")
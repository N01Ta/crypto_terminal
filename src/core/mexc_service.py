import ccxt
import os
import time
import math


class MexcService:
    def __init__(self, api_key=None, api_secret=None, passphrase=None):
        self.exchange_id = 'mexc'
        self.exchange_class = getattr(ccxt, self.exchange_id)
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.exchange = None
        self._initialize_exchange()

    def _parse_precision_value(self, precision_input):
        # Преобразует значение точности от ccxt в количество знаков после запятой.
        if precision_input is None: return 8  # Значение по умолчанию
        try:
            val = float(precision_input)
            if val == 0: return 8
            if val >= 1:  # Обычно для количества, а не цены (если шаг >= 1)
                if isinstance(precision_input, int) and precision_input > 0: return precision_input
                num_str = format(val, '.16f').rstrip('0')  # Округление до целого
                return len(num_str.split('.')[1]) if '.' in num_str and num_str.split('.')[1] else 0
            # Для значений < 1 (0.1, 0.01, 1e-2, 1e-8)
            s = format(val, '.16f')  # Форматируем с запасом знаков
            if '.' in s:
                return len(s.split('.')[1].rstrip('0'))  # Убираем незначащие нули справа
            else:
                return 0  # Целое число (маловероятно для точности цены < 1)
        except (ValueError, TypeError):
            # print(f"MexcService: Warning: Could not parse precision value '{precision_input}'. Using default 8.")
            return 8
        except Exception:
            # print(f"MexcService: Warning: Unexpected error parsing precision '{precision_input}'. Using default 8.")
            return 8

    def _initialize_exchange(self):
        try:
            config = {'enableRateLimit': True, 'options': {'defaultType': 'spot'}}
            if self.api_key and self.api_secret:
                config['apiKey'] = self.api_key
                config['secret'] = self.api_secret
                if self.passphrase: config['password'] = self.passphrase
            self.exchange = self.exchange_class(config)
        except Exception as e:
            print(f"MexcService: Error initializing exchange: {e}")
            self.exchange = None;
            raise

    def set_api_credentials(self, api_key: str, api_secret: str, passphrase: str = None):
        self.api_key = api_key;
        self.api_secret = api_secret;
        self.passphrase = passphrase
        self._initialize_exchange()
        print(f"MexcService: API credentials updated. API Key: {'Set' if self.api_key else 'Not Set'}")

    def load_markets_data(self):
        if not self.exchange: return None, "Биржа не инициализирована"
        try:
            if not self.exchange.markets: self.exchange.load_markets()
            markets = self.exchange.markets;
            filtered_markets = []
            for symbol, market_data in markets.items():
                if market_data.get('active', False) and \
                        market_data.get('spot', False) and \
                        market_data.get('quote', '').upper() == 'USDT':
                    price_prec_raw = market_data.get('precision', {}).get('price')
                    amount_prec_raw = market_data.get('precision', {}).get('amount')
                    cost_prec_raw = market_data.get('precision', {}).get('cost')

                    parsed_price_prec = self._parse_precision_value(price_prec_raw)
                    parsed_amount_prec = self._parse_precision_value(amount_prec_raw)
                    parsed_cost_prec = self._parse_precision_value(cost_prec_raw) if cost_prec_raw is not None else 2

                    filtered_markets.append({
                        'symbol': market_data['symbol'], 'base': market_data['base'],
                        'quote': market_data['quote'], 'id': market_data['id'],
                        'precision': {
                            'price': parsed_price_prec, 'amount': parsed_amount_prec, 'cost': parsed_cost_prec,
                            'raw_price': price_prec_raw, 'raw_amount': amount_prec_raw, 'raw_cost': cost_prec_raw
                        },
                        'limits': market_data.get('limits', {}),
                    })
            return filtered_markets, None
        except Exception as e:
            return None, f"Ошибка загрузки рынков: {e}"

    def fetch_tickers(self, symbols: list = None):
        if not self.exchange: return None, "Биржа не инициализирована"
        if not hasattr(self.exchange, 'fetch_tickers'): return None, "fetch_tickers не поддерживается"
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
        if not self.exchange: return None, "Биржа не инициализирована"
        if not self.exchange.has['fetchOHLCV']: return None, "fetchOHLCV не поддерживается"
        try:
            ohlcv_data = self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            return ohlcv_data, None
        except Exception as e:
            return None, f"Ошибка OHLCV ({symbol}): {e}"

    def fetch_balances(self):
        if not self.exchange: return None, "Биржа не инициализирована"
        if not self.api_key or not self.api_secret: return None, "API ключи не установлены"
        try:
            raw_balance_data = self.exchange.fetch_balance()
            return raw_balance_data, None
        except Exception as e:
            return None, f"Ошибка получения балансов: {e}"

    def create_market_order(self, symbol: str, side: str, amount: float):
        if not self.exchange: return None, "Биржа не инициализирована"
        if not self.api_key or not self.api_secret: return None, "API ключи не установлены"

        actual_side = side.lower()
        order_response = None

        try:
            if actual_side == 'buy':
                if not self.exchange.has.get('createMarketBuyOrder'):
                    # Если ccxt не заявляет поддержку createMarketBuyOrder, это проблема для MEXC,
                    # так как покупка по рынку на сумму QUOTE - стандартная операция.
                    # Это может быть индикатором очень старой версии ccxt или неполной поддержки MEXC в ней.
                    # В этом случае, использование create_order потребует точного знания params для cost.
                    print(
                        f"MexcService: Предупреждение! ccxt не заявляет поддержку 'createMarketBuyOrder' для {self.exchange_id}. Ордер может не сработать как ожидается.")
                    # Тем не менее, попробуем стандартный вызов, возможно, он все же есть, но флаг has не выставлен.
                order_response = self.exchange.create_market_buy_order(symbol, amount)  # amount здесь - cost

            elif actual_side == 'sell':
                if not self.exchange.has.get('createMarketSellOrder'):
                    print(
                        f"MexcService: Предупреждение! ccxt не заявляет поддержку 'createMarketSellOrder' для {self.exchange_id}.")
                order_response = self.exchange.create_market_sell_order(symbol, amount)  # amount здесь - кол-во BASE
            else:
                return None, "Неверная сторона ордера (должно быть 'buy' или 'sell')."

            return order_response, None

        except ccxt.InsufficientFunds as e:
            return None, f"Недостаточно средств: {e}"
        except ccxt.InvalidOrder as e:
            return None, f"Некорректный ордер: {e}"
        except ccxt.NetworkError as e:
            return None, f"Ошибка сети: {e}"
        except ccxt.ExchangeError as e:
            return None, f"Ошибка биржи: {e}"
        except Exception as e:
            return None, f"Непредвиденная ошибка ордера: {e}"
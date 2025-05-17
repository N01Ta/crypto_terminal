# src/core/simple_predictor.py
from PyQt5.QtGui import QColor

# Цвета остаются для качественной оценки предсказания
PREDICTION_COLOR_BUY = QColor("#2ecc71")
PREDICTION_COLOR_SELL = QColor("#e74c3c")
PREDICTION_COLOR_HOLD = QColor("#f1c40f") # Используем для случаев, когда предсказание близко к текущей цене
PREDICTION_COLOR_UNCERTAIN = QColor("#95a5a6")

def get_simple_price_prediction(ohlcv_data: list, lookback_period: int = 2):
    """
    Делает очень простое "предсказание" числового значения цены закрытия
    следующей свечи путем линейной экстраполяции последних N свечей.

    Args:
        ohlcv_data (list): Список списков OHLCV данных.
                           Каждый внутренний список: [timestamp, open, high, low, close, volume]
                           Ожидается, что данные отсортированы от старых к новым.
        lookback_period (int): Количество последних свечей для анализа.
                               Должно быть минимум 2 для расчета изменения.

    Returns:
        tuple: (
            float: Предсказанная цена закрытия следующей свечи (или None если не удалось),
            str: Качественная оценка тренда ("Ожидается рост", "Ожидается падение", "Боковик"),
            QColor: Цвет для качественной оценки
        )
    """
    if not ohlcv_data or len(ohlcv_data) < max(2, lookback_period): # Нужно минимум 2 свечи для любого расчета, и не меньше lookback_period
        return None, "НЕДОСТАТОЧНО ДАННЫХ", PREDICTION_COLOR_UNCERTAIN

    # Берем последние N свечей для анализа
    # Если lookback_period=1, это не имеет смысла для расчета изменения, берем минимум 2
    actual_lookback = max(2, lookback_period)
    if len(ohlcv_data) < actual_lookback: # Еще одна проверка на случай, если lookback_period был изменен на 2
        return None, "НЕДОСТАТОЧНО ДАННЫХ (после корректировки)", PREDICTION_COLOR_UNCERTAIN

    recent_candles = ohlcv_data[-actual_lookback:]

    # Цены закрытия анализируемых свечей
    close_prices = [candle[4] for candle in recent_candles] # Индекс 4 - цена закрытия (close)
    
    # Текущая (последняя известная) цена закрытия
    current_price = close_prices[-1]

    # --- Логика предсказания (простая линейная экстраполяция) ---

    # Рассчитываем среднее изменение цены за одну свечу на анализируемом отрезке
    price_changes = []
    for i in range(1, len(close_prices)):
        price_changes.append(close_prices[i] - close_prices[i-1])
    
    if not price_changes: # Такое возможно, если lookback_period=1 и был скорректирован до 2, но в ohlcv_data всего 1 свеча (хотя это отсекается выше)
        avg_change = 0
    else:
        avg_change = sum(price_changes) / len(price_changes)

    # Предсказанная цена = текущая цена + среднее изменение
    predicted_price = current_price + avg_change

    # Форматируем предсказанную цену до разумного количества знаков после запятой
    # Для этого нужна информация о точности (precision) из market_data,
    # но для простоты пока округлим до 4 знаков, если цена > 1, или до 8, если < 1.
    # В идеале, precision нужно передавать в эту функцию.
    if predicted_price > 1:
        predicted_price_formatted = round(predicted_price, 4)
    else:
        predicted_price_formatted = round(predicted_price, 8)


    # --- Качественная оценка тренда ---
    trend_description = ""
    trend_color = PREDICTION_COLOR_UNCERTAIN

    # Порог изменения для определения значимого роста/падения (например, 0.1% от текущей цены)
    significance_threshold = current_price * 0.0005 # 0.05%

    if avg_change > significance_threshold:
        trend_description = f"Ожидается рост до ~{predicted_price_formatted}"
        trend_color = PREDICTION_COLOR_BUY
    elif avg_change < -significance_threshold:
        trend_description = f"Ожидается падение до ~{predicted_price_formatted}"
        trend_color = PREDICTION_COLOR_SELL
    else:
        trend_description = f"Ожидается боковик, цена ~{predicted_price_formatted}"
        trend_color = PREDICTION_COLOR_HOLD
        
    # Если предсказанная цена отрицательная, это явно ошибка или очень сильный дамп,
    # в таком случае лучше вернуть None или 0.
    if predicted_price_formatted < 0:
        return 0.0, "ПАДЕНИЕ ДО НУЛЯ?", PREDICTION_COLOR_SELL

    return predicted_price_formatted, trend_description, trend_color


# --- Тестовый блок для simple_predictor.py ---
if __name__ == '__main__':
    print("Тестирование simple_predictor.py (предсказание числовой цены):")

    # Пример данных OHLCV (timestamp, open, high, low, close, volume)
    # 1. Рост
    data_growth = [
        [1678886400000, 100.0, 105.0, 98.0, 102.0, 1000],
        [1678886700000, 102.0, 108.0, 101.0, 105.0, 1200], # change +3
        [1678887000000, 105.0, 112.0, 104.0, 110.0, 1500], # change +5, avg_change (3+5)/2 = +4. Expected 110+4 = 114
    ] # lookback = 2 (последние 2 свечи) -> цены 105, 110. avg_change = (110-105)/1 = +5. Expected 110+5=115
      # lookback = 3 (все 3) -> цены 102, 105, 110. changes: +3, +5. avg_change = (3+5)/2 = +4. Expected 110+4=114
    
    pred_price, trend_desc, trend_color = get_simple_price_prediction(data_growth, lookback_period=2)
    print(f"\nДанные (рост, lookback=2): {data_growth[-2:]}")
    print(f"Предсказание: Цена={pred_price}, Описание='{trend_desc}', Цвет: {trend_color.name()}")

    pred_price, trend_desc, trend_color = get_simple_price_prediction(data_growth, lookback_period=3)
    print(f"\nДанные (рост, lookback=3): {data_growth}")
    print(f"Предсказание: Цена={pred_price}, Описание='{trend_desc}', Цвет: {trend_color.name()}")

    # 2. Падение
    data_fall = [
        [1678886400000, 120.0, 122.0, 115.0, 118.0, 1000],
        [1678886700000, 118.0, 119.0, 110.0, 112.0, 1200], # change -6
        [1678887000000, 112.0, 113.0, 105.0, 107.0, 1500], # change -5. avg_change = (-6-5)/2 = -5.5. Expected 107-5.5=101.5
    ]
    pred_price, trend_desc, trend_color = get_simple_price_prediction(data_fall, lookback_period=3)
    print(f"\nДанные (падение, lookback=3): {data_fall}")
    print(f"Предсказание: Цена={pred_price}, Описание='{trend_desc}', Цвет: {trend_color.name()}")

    # 3. Боковик
    data_flat = [
        [1678886400000, 100.0, 102.0, 98.0, 100.1, 1000],
        [1678886700000, 100.1, 100.3, 99.9, 100.2, 900],  # change +0.1
        [1678887000000, 100.2, 100.4, 99.8, 100.1, 1100], # change -0.1. avg_change = 0. Expected 100.1
    ]
    pred_price, trend_desc, trend_color = get_simple_price_prediction(data_flat, lookback_period=3)
    print(f"\nДанные (боковик, lookback=3): {data_flat}")
    print(f"Предсказание: Цена={pred_price}, Описание='{trend_desc}', Цвет: {trend_color.name()}")

    # 4. Недостаточно данных
    data_short = [
        [1678886400000, 100.0, 102.0, 98.0, 101.0, 1000] # Всего одна свеча
    ]
    pred_price, trend_desc, trend_color = get_simple_price_prediction(data_short, lookback_period=2)
    print(f"\nДанные (мало): {data_short}")
    print(f"Предсказание: Цена={pred_price}, Описание='{trend_desc}', Цвет: {trend_color.name()}")

    # 5. Данные с очень маленькими ценами (для проверки форматирования)
    data_small_price = [
        [1678886400000, 0.00010200, 0.00010500, 0.00009800, 0.00010250, 1000],
        [1678886700000, 0.00010250, 0.00010800, 0.00010100, 0.00010530, 1200],
        [1678887000000, 0.00010530, 0.00011200, 0.00010400, 0.00011080, 1500],
    ]
    pred_price, trend_desc, trend_color = get_simple_price_prediction(data_small_price, lookback_period=3)
    print(f"\nДанные (маленькая цена, lookback=3): {data_small_price}")
    print(f"Предсказание: Цена={pred_price}, Описание='{trend_desc}', Цвет: {trend_color.name()}")
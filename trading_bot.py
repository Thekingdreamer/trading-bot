import os
import time
import pandas as pd
import numpy as np
import requests
from kucoin.client import Market, Trade, User  # ✅ Clases comunes
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar API de KuCoin
client = Client(
    api_key=os.getenv("KUCOIN_API_KEY"),
    api_secret=os.getenv("KUCOIN_API_SECRET"),
    passphrase=os.getenv("KUCOIN_API_PASSPHRASE")
)

# Configurar Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_alerta(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={mensaje}"
    requests.get(url).json()

def calcular_rsi(data, periodo=14):
    delta = data['close'].diff()
    ganancias = delta.clip(lower=0)
    perdidas = -delta.clip(upper=0)
    avg_ganancia = ganancias.rolling(periodo).mean()
    avg_perdida = perdidas.rolling(periodo).mean()
    rs = avg_ganancia / avg_perdida
    return 100 - (100 / (1 + rs))

def calcular_atr(data, periodo=14):
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(periodo).mean()

def estrategia_trading(symbol="BTC-USDT"):
    try:
        # Obtener datos históricos
        velas = client.get_kline_data(symbol=symbol, interval="1day")
        df = pd.DataFrame(velas, columns=["timestamp", "open", "close", "high", "low", "volume"])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Calcular indicadores
        df['MA50'] = df['close'].rolling(50).mean()
        df['MA200'] = df['close'].rolling(200).mean()
        df['RSI'] = calcular_rsi(df)
        df['ATR'] = calcular_atr(df)
        
        # Últimos valores
        ultimo_precio = df['close'].iloc[-1]
        ma50 = df['MA50'].iloc[-1]
        ma200 = df['MA200'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        atr = df['ATR'].iloc[-1]
        
        # Lógica de trading
        if (ma50 > ma200) and (rsi < 70):
            # Señal de COMPRA
            stop_loss = ultimo_precio - (atr * 1.5)
            enviar_alerta(f"🚀 COMPRAR {symbol} | Precio: {ultimo_precio} | Stop Loss: {stop_loss}")
            
        elif (ma50 < ma200) and (rsi > 30):
            # Señal de VENTA
            enviar_alerta(f"🔴 VENDER {symbol} | Precio: {ultimo_precio}")
            
    except Exception as e:
        enviar_alerta(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    while True:
        estrategia_trading()
        time.sleep(86400)  # Ejecutar cada 24 horas

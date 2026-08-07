"""Weather tool — Open-Meteo free API, no key required."""
import logging
import httpx

logger = logging.getLogger(__name__)

# Taipei coordinates
_LAT, _LON = 25.0375, 121.5625
_URL = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={_LAT}&longitude={_LON}"
    f"&current=temperature_2m,apparent_temperature,precipitation_probability,weathercode,windspeed_10m"
    f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode"
    f"&timezone=Asia%2FTaipei&forecast_days=1"
)

_WMO = {
    0: "晴天", 1: "大致晴朗", 2: "部分多雲", 3: "陰天",
    45: "霧", 48: "霧淞",
    51: "毛毛雨", 53: "毛毛雨", 55: "濃毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    80: "陣雨", 81: "中陣雨", 82: "強陣雨",
    95: "雷雨", 96: "雷雨夾冰雹", 99: "強雷雨夾冰雹",
}


async def get_weather() -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(_URL)
            r.raise_for_status()
            data = r.json()

        cur = data["current"]
        daily = data["daily"]
        code = cur.get("weathercode", 0)
        desc = _WMO.get(code, f"天氣代碼 {code}")

        return (
            f"🌤 **台北今日天氣**\n"
            f"天氣：{desc}\n"
            f"現在氣溫：{cur['temperature_2m']}°C（體感 {cur['apparent_temperature']}°C）\n"
            f"今日高／低：{daily['temperature_2m_max'][0]}°C / {daily['temperature_2m_min'][0]}°C\n"
            f"降雨機率：{daily['precipitation_probability_max'][0]}%\n"
            f"風速：{cur['windspeed_10m']} km/h"
        )
    except Exception as e:
        logger.error(f"Weather fetch error: {e}")
        return f"❌ 無法取得天氣資料：{e}"

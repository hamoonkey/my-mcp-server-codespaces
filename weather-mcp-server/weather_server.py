import json
import urllib.request
import urllib.parse
from typing import Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from mcp.server.fastmcp import FastMCP

# MCPサーバーのインスタンスを作成
mcp = FastMCP("Weather MCP Server")

def fetch_weather_data(latitude: float, longitude: float) -> Dict[str, Any]:
    """Open-Meteo JMA APIから天気データを取得する"""
    base_url = "https://api.open-meteo.com/v1/jma"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "hourly": "temperature_2m,weather_code,precipitation",
        "timezone": "Asia/Tokyo",
        "forecast_days": 7
    }

    # URLエンコード
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        return data
    except Exception as e:
        return {"error": f"APIリクエストに失敗しました: {str(e)}"}

def weather_code_to_description(code: int) -> str:
    """WMO天気コードを日本語の説明に変換"""
    weather_codes = {
        # 0–3: 雲量・天気概況
        0: "快晴",
        1: "おおむね晴れ",
        2: "晴れ時々曇り",
        3: "曇り",

        # 45,48: 霧
        45: "霧",
        48: "着氷性の霧",

        # 51–57: 霧雨（着氷性含む）
        51: "霧雨（弱い）",
        53: "霧雨（中程度）",
        55: "霧雨（強い）",
        56: "着氷性の霧雨（弱い）",
        57: "着氷性の霧雨（強い）",

        # 61–67: 雨（着氷性含む）
        61: "雨（弱い）",
        63: "雨（中程度）",
        65: "雨（強い）",
        66: "着氷性の雨（弱い）",
        67: "着氷性の雨（強い）",

        # 71–77: 雪
        71: "雪（弱い）",
        73: "雪（中程度）",
        75: "雪（強い）",
        77: "雪粒（スノーグレイン）",

        # 80–86: にわか雨・にわか雪
        80: "にわか雨（弱い）",
        81: "にわか雨（中程度）",
        82: "にわか雨（強い）",
        85: "にわか雪（弱い）",
        86: "にわか雪（強い）",

        # 95–99: 雷雨（ひょう）
        95: "雷雨（弱い〜中程度）",
        96: "雷雨（ひょうを伴う、弱い〜中程度）",
        99: "雷雨（ひょうを伴う、強い）",
    }
    return weather_codes.get(code, f"不明な天気コード: {code}")

@mcp.tool()
def get_current_weather(latitude: float, longitude: float, location_name: str = "指定地点") -> dict:
    """指定された座標の現在の天気を取得する

    Args:
        latitude: 緯度（例: 東京 35.6762）
        longitude: 経度（例: 東京 139.6503）
        location_name: 地点名（表示用）
    """
    data = fetch_weather_data(latitude, longitude)
    print(json.dumps(data, ensure_ascii=False, indent=2))

    if "error" in data:
        return data

    current = data.get("current", {})

    return {
        "location": location_name,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "current_time": current.get("time", ""),
        "temperature": f"{current.get('temperature_2m', 'N/A')}°C",
        "humidity": f"{current.get('relative_humidity_2m', 'N/A')}%",
        "wind_speed": f"{current.get('wind_speed_10m', 'N/A')} km/h",
        "weather": weather_code_to_description(current.get("weather_code", 0)),
        "weather_code": current.get("weather_code", 0)
    }

@mcp.tool()
def get_weekly_forecast(latitude: float, longitude: float, location_name: str = "指定地点") -> dict:
    """指定された座標の7日間天気予報を取得する

    Args:
        latitude: 緯度（例: 東京 35.6762）
        longitude: 経度（例: 東京 139.6503）
        location_name: 地点名（表示用）
    """
    data = fetch_weather_data(latitude, longitude)

    if "error" in data:
        return data

    daily = data.get("daily", {})
    times = daily.get("time", [])
    weather_codes = daily.get("weather_code", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    precipitation = daily.get("precipitation_sum", [])

    forecast = []
    for i in range(len(times)):
        day_data = {
            "date": times[i],
            "weather": weather_code_to_description(weather_codes[i]) if i < len(weather_codes) else "不明",
            "temperature_max": f"{temp_max[i]}°C" if i < len(temp_max) else "N/A",
            "temperature_min": f"{temp_min[i]}°C" if i < len(temp_min) else "N/A",
            "precipitation": f"{precipitation[i]}mm" if i < len(precipitation) else "N/A"
        }
        forecast.append(day_data)

    return {
        "location": location_name,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "forecast_period": "7日間",
        "forecast": forecast
    }

@mcp.tool()
def get_today_hourly_weather(latitude: float, longitude: float, location_name: str = "指定地点") -> dict:
    """指定された座標の本日の1時間ごとの天気を取得する

    Args:
        latitude: 緯度（例: 東京 35.6762）
        longitude: 経度（例: 東京 139.6503）
        location_name: 地点名（表示用）
    """
    data = fetch_weather_data(latitude, longitude)

    if "error" in data:
        return data

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    codes = hourly.get("weather_code", [])
    precs = hourly.get("precipitation", [])

    if not times:
        return {"error": "時間別データが見つかりません。"}

    # APIレスポンスのタイムゾーン（例: Asia/Tokyo）を使用
    tz_name = data.get("timezone", "Asia/Tokyo")
    try:
        today_str = datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d")
    except Exception:
        # ゾーン情報の取得に失敗した場合はシステムローカル時間で代替
        today_str = datetime.now().strftime("%Y-%m-%d")

    def build_hours_for(day_prefix: str):
        hours: list[dict[str, Any]] = []
        for i, t in enumerate(times):
            if isinstance(t, str) and t.startswith(day_prefix):
                item = {
                    "time": t,
                    "temperature": f"{temps[i]}°C" if i < len(temps) else "N/A",
                    "weather": weather_code_to_description(codes[i]) if i < len(codes) else "不明",
                    "weather_code": codes[i] if i < len(codes) else None,
                    "precipitation": f"{precs[i]}mm" if i < len(precs) else "N/A",
                }
                hours.append(item)
        return hours

    hours = build_hours_for(today_str)

    # 念のため、current.timeの日付でフォールバック
    if not hours:
        current_time = data.get("current", {}).get("time")
        if isinstance(current_time, str) and len(current_time) >= 10:
            hours = build_hours_for(current_time[:10])

    return {
        "location": location_name,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "date": today_str,
        "hours": hours,
    }

if __name__ == "__main__":
    # MCPサーバーを起動（Streamable HTTP transport、ポート8000）
    print("Starting MCP server...")
    mcp.run(transport="streamable-http")
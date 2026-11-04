/**
 * Weather Service — uses Open-Meteo (FREE, no API key needed)
 * Geocoding via Nominatim (OpenStreetMap, FREE)
 */
const axios     = require('axios');
const NodeCache = require('node-cache');

const cache = new NodeCache({ stdTTL: parseInt(process.env.CACHE_TTL_WEATHER) || 1800 });

const WEATHER_CODES = {
  0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
  45: 'Foggy', 48: 'Icy fog', 51: 'Light drizzle', 53: 'Moderate drizzle',
  55: 'Dense drizzle', 61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
  71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow', 77: 'Snow grains',
  80: 'Light showers', 81: 'Moderate showers', 82: 'Violent showers',
  85: 'Slight snow showers', 86: 'Heavy snow showers',
  95: 'Thunderstorm', 96: 'Thunderstorm with hail', 99: 'Thunderstorm with heavy hail'
};

/**
 * Geocode a city name to lat/lon using Nominatim (OpenStreetMap).
 */
async function geocodeCity(cityName) {
  const cacheKey = `geo_${cityName.toLowerCase()}`;
  if (cache.has(cacheKey)) return cache.get(cacheKey);

  const url    = `${process.env.GEOCODING_API_BASE_URL || 'https://nominatim.openstreetmap.org'}/search`;
  const params = { q: cityName, format: 'json', limit: 1 };
  const headers = { 'User-Agent': 'TravelPlannerAgent/1.0' };

  const response = await axios.get(url, { params, headers });
  if (!response.data || response.data.length === 0) {
    throw new Error(`City not found: ${cityName}`);
  }

  const result = {
    name     : response.data[0].display_name,
    lat      : parseFloat(response.data[0].lat),
    lon      : parseFloat(response.data[0].lon),
    country  : response.data[0].address?.country || 'Unknown'
  };

  cache.set(cacheKey, result, 86400); // 24h cache for geocoding
  return result;
}

/**
 * Get current weather + 7-day forecast for a city.
 */
async function getWeather(cityName) {
  const cacheKey = `weather_${cityName.toLowerCase()}`;
  if (cache.has(cacheKey)) return cache.get(cacheKey);

  const { lat, lon, name } = await geocodeCity(cityName);

  const url    = `${process.env.WEATHER_API_BASE_URL || 'https://api.open-meteo.com/v1'}/forecast`;
  const params = {
    latitude              : lat,
    longitude             : lon,
    current               : 'temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weathercode,is_day',
    daily                 : 'temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,wind_speed_10m_max',
    timezone              : 'auto',
    forecast_days         : 7
  };

  const response = await axios.get(url, { params });
  const { current, daily } = response.data;

  const weather = {
    location : name,
    current  : {
      temperature       : current.temperature_2m,
      feelsLike         : current.apparent_temperature,
      humidity          : current.relative_humidity_2m,
      windSpeed         : current.wind_speed_10m,
      condition         : WEATHER_CODES[current.weathercode] || 'Unknown',
      isDay             : current.is_day === 1
    },
    forecast : daily.time.map((date, i) => ({
      date      : date,
      maxTemp   : daily.temperature_2m_max[i],
      minTemp   : daily.temperature_2m_min[i],
      condition : WEATHER_CODES[daily.weathercode[i]] || 'Unknown',
      precipitation: daily.precipitation_sum[i],
      maxWind   : daily.wind_speed_10m_max[i]
    }))
  };

  cache.set(cacheKey, weather);
  return weather;
}

/**
 * Get best travel months for a destination based on historical climate patterns.
 * Returns a simple AI-consumable summary string.
 */
function getBestTravelMonths(weatherData) {
  const forecast = weatherData.forecast || [];
  const avgMax = forecast.reduce((s, d) => s + d.maxTemp, 0) / (forecast.length || 1);
  const rainy  = forecast.filter(d => d.precipitation > 5).length;

  let summary = `Current average high: ${avgMax.toFixed(1)}°C. `;
  summary += rainy > 3
    ? 'Rainy conditions expected — pack an umbrella.'
    : 'Mostly dry conditions — good time to travel!';

  return summary;
}

module.exports = { getWeather, geocodeCity, getBestTravelMonths };

/**
 * Weather Routes — real-time weather and geocoding endpoints
 */
const express        = require('express');
const router         = express.Router();
const weatherService = require('../services/weatherService');
const placesService  = require('../services/placesService');

// ── Current weather + 7-day forecast ─────────────────────────
router.get('/:city', async (req, res) => {
  try {
    const weather = await weatherService.getWeather(req.params.city);
    res.json(weather);
  } catch (err) {
    console.error('[/weather/:city]', err.message);
    res.status(404).json({ error: err.message });
  }
});

// ── Geocode a city ────────────────────────────────────────────
router.get('/geocode/:city', async (req, res) => {
  try {
    const geo = await weatherService.geocodeCity(req.params.city);
    res.json(geo);
  } catch (err) {
    res.status(404).json({ error: err.message });
  }
});

// ── Places near a city ────────────────────────────────────────
router.get('/places/:city', async (req, res) => {
  try {
    const { category = 'attractions', radius = 5000, limit = 10 } = req.query;
    const geo    = await weatherService.geocodeCity(req.params.city);
    const places = await placesService.getPlacesNearby(geo.lat, geo.lon, category, parseInt(radius), parseInt(limit));
    res.json({ city: req.params.city, geo, places });
  } catch (err) {
    console.error('[/weather/places/:city]', err.message);
    res.status(404).json({ error: err.message });
  }
});

module.exports = router;

/**
 * Travel Routes — itinerary, transport, accommodation, booking endpoints
 */
const express        = require('express');
const router         = express.Router();
const agent          = require('../agent/travelAgent');
const bookingService = require('../services/bookingService');
const exchangeService= require('../services/exchangeService');

// ── Itinerary ─────────────────────────────────────────────────
router.post('/itinerary', async (req, res) => {
  try {
    const result = await agent.buildItinerary(req.body);
    res.json(result);
  } catch (err) {
    console.error('[/travel/itinerary]', err.message);
    res.status(500).json({ error: err.message });
  }
});

router.get('/itinerary/:id', (req, res) => {
  try {
    const it = bookingService.getItinerary(req.params.id);
    res.json(it);
  } catch (err) {
    res.status(404).json({ error: err.message });
  }
});

router.get('/itineraries', (req, res) => {
  res.json(bookingService.listItineraries());
});

// ── Transport ─────────────────────────────────────────────────
router.post('/transport', async (req, res) => {
  try {
    const result = await agent.getTransportOptions(req.body);
    res.json({ transport: result });
  } catch (err) {
    console.error('[/travel/transport]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── Accommodation ─────────────────────────────────────────────
router.post('/accommodation', async (req, res) => {
  try {
    const result = await agent.getAccommodationOptions(req.body);
    res.json({ accommodation: result });
  } catch (err) {
    console.error('[/travel/accommodation]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── Bookings ──────────────────────────────────────────────────
router.post('/booking', (req, res) => {
  try {
    const booking = bookingService.createBooking(req.body);
    res.status(201).json(booking);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get('/booking/:id', (req, res) => {
  try {
    res.json(bookingService.getBooking(req.params.id));
  } catch (err) {
    res.status(404).json({ error: err.message });
  }
});

router.get('/bookings', (req, res) => {
  res.json(bookingService.listBookings());
});

router.patch('/booking/:id', (req, res) => {
  try {
    res.json(bookingService.updateBooking(req.params.id, req.body));
  } catch (err) {
    res.status(404).json({ error: err.message });
  }
});

router.delete('/booking/:id', (req, res) => {
  try {
    res.json(bookingService.cancelBooking(req.params.id));
  } catch (err) {
    res.status(404).json({ error: err.message });
  }
});

router.post('/booking/:id/alert', (req, res) => {
  try {
    const { message, type } = req.body;
    res.json(bookingService.addAlert(req.params.id, message, type));
  } catch (err) {
    res.status(404).json({ error: err.message });
  }
});

// ── Currency conversion ───────────────────────────────────────
router.get('/currency/:from/:to/:amount', async (req, res) => {
  try {
    const { from, to, amount } = req.params;
    const result = await exchangeService.convert(parseFloat(amount), from, to);
    res.json(result);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

router.get('/currency/rates/:base', async (req, res) => {
  try {
    const rates = await exchangeService.getRates(req.params.base);
    res.json(rates);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

module.exports = router;

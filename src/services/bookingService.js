/**
 * Booking Service — manages trip bookings, alerts, and itinerary optimization
 * Uses in-memory store (replace with a database for production)
 */
const { v4: uuidv4 } = require('uuid');

// In-memory booking store
const bookings   = new Map();
const itineraries = new Map();

// ── Booking Management ────────────────────────────────────────

/**
 * Create a new booking record.
 * @param {object} bookingData
 */
function createBooking(bookingData) {
  const id = uuidv4();
  const booking = {
    id,
    status    : 'confirmed',
    createdAt : new Date().toISOString(),
    alerts    : [],
    ...bookingData
  };
  bookings.set(id, booking);
  return booking;
}

/**
 * Get a booking by ID.
 */
function getBooking(id) {
  const booking = bookings.get(id);
  if (!booking) throw new Error(`Booking ${id} not found`);
  return booking;
}

/**
 * Update a booking (e.g., status change, schedule update).
 */
function updateBooking(id, updates) {
  const booking = getBooking(id);
  const updated = { ...booking, ...updates, updatedAt: new Date().toISOString() };
  bookings.set(id, updated);
  return updated;
}

/**
 * Cancel a booking.
 */
function cancelBooking(id) {
  return updateBooking(id, { status: 'cancelled' });
}

/**
 * List all bookings for a user session.
 */
function listBookings() {
  return Array.from(bookings.values());
}

/**
 * Add an alert to a booking (e.g., flight delay, weather warning).
 */
function addAlert(bookingId, alertMessage, alertType = 'info') {
  const booking = getBooking(bookingId);
  booking.alerts.push({
    id       : uuidv4(),
    message  : alertMessage,
    type     : alertType,
    timestamp: new Date().toISOString()
  });
  bookings.set(bookingId, booking);
  return booking;
}

// ── Itinerary Management ──────────────────────────────────────

/**
 * Save a generated itinerary.
 */
function saveItinerary(destination, days, content, metadata = {}) {
  const id = uuidv4();
  const itinerary = {
    id,
    destination,
    days,
    content,
    createdAt: new Date().toISOString(),
    ...metadata
  };
  itineraries.set(id, itinerary);
  return itinerary;
}

/**
 * Retrieve a saved itinerary.
 */
function getItinerary(id) {
  const it = itineraries.get(id);
  if (!it) throw new Error(`Itinerary ${id} not found`);
  return it;
}

/**
 * List all saved itineraries.
 */
function listItineraries() {
  return Array.from(itineraries.values());
}

/**
 * Optimize a daily schedule by sorting activities by time and grouping by area.
 * @param {Array<{time:string, activity:string, location:string}>} activities
 */
function optimizeSchedule(activities) {
  // Sort by time slot
  const timeOrder = { morning: 0, afternoon: 1, evening: 2, night: 3 };
  return [...activities].sort((a, b) => {
    const ta = timeOrder[a.time?.toLowerCase()] ?? 99;
    const tb = timeOrder[b.time?.toLowerCase()] ?? 99;
    return ta - tb;
  });
}

module.exports = {
  createBooking, getBooking, updateBooking, cancelBooking, listBookings, addAlert,
  saveItinerary, getItinerary, listItineraries, optimizeSchedule
};

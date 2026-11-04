/**
 * Travel Planner Agent — Core AI Brain
 * Orchestrates IBM Granite + all services to fulfill travel planning tasks
 */
const granite        = require('../services/graniteClient');
const weatherService = require('../services/weatherService');
const placesService  = require('../services/placesService');
const exchangeService= require('../services/exchangeService');
const bookingService = require('../services/bookingService');

// ── System Prompt ─────────────────────────────────────────────
const SYSTEM_PROMPT = `You are an expert AI Travel Planner Assistant powered by IBM Granite. 
Your role is to help users plan trips with personalized, intelligent, and practical advice.

You provide:
- Destination recommendations based on user preferences, budget, and travel dates
- Detailed day-by-day itineraries with timing and logistics
- Transport options (flights, trains, buses, car rentals) with estimated costs
- Accommodation suggestions (hotels, hostels, Airbnb) across budget ranges
- Local dining, attractions, and cultural experiences
- Packing lists and travel tips
- Visa and entry requirements
- Currency and budget breakdown
- Safety and health advisories

Always be concise, practical, and culturally sensitive. Use markdown formatting for clarity.
When given weather, places, or exchange rate data, incorporate it naturally into your advice.`;

// ── Agent Actions ─────────────────────────────────────────────

/**
 * Suggest destinations based on user preferences.
 */
async function suggestDestinations({ preferences, budget, duration, travelMonth, from }) {
  const prompt = `User wants to travel ${from ? `from ${from}` : ''} for ${duration || '7-10'} days in ${travelMonth || 'any month'}.
Budget: ${budget || 'moderate'}.
Preferences: ${preferences || 'cultural experiences, nature, good food'}.

Suggest 5 diverse destination options. For each, provide:
1. Destination name & country
2. Why it matches their preferences
3. Estimated total budget range
4. Best time to visit
5. Top 3 must-do experiences
6. Getting there (flights/transport from their origin if specified)

Format as a clear, well-structured list.`;

  return await granite.generate(SYSTEM_PROMPT, prompt);
}

/**
 * Build a detailed day-by-day itinerary.
 */
async function buildItinerary({ destination, days, budget, interests, accommodation }) {
  // Fetch real weather and places data to enrich the itinerary
  let contextData = '';

  try {
    const weather = await weatherService.getWeather(destination);
    contextData += `\nCurrent weather in ${destination}: ${weather.current.condition}, ${weather.current.temperature}°C. `;
    contextData += `7-day forecast: ${weather.forecast.slice(0, 3).map(d => `${d.date}: ${d.condition}, ${d.maxTemp}°C high`).join('; ')}.`;
  } catch (e) {
    // Weather fetch failed — continue without it
  }

  try {
    const geo        = await weatherService.geocodeCity(destination);
    const places     = await placesService.getPlacesNearby(geo.lat, geo.lon, 'attractions', 10000, 8);
    const restaurants= await placesService.getPlacesNearby(geo.lat, geo.lon, 'restaurants', 5000, 5);
    if (places.length)      contextData += `\nTop attractions: ${places.slice(0, 5).map(p => p.name).join(', ')}.`;
    if (restaurants.length) contextData += `\nRecommended dining areas: ${restaurants.slice(0, 3).map(r => r.name).join(', ')}.`;
  } catch (e) {
    // Places fetch failed — continue without it
  }

  const prompt = `Create a detailed ${days || 5}-day itinerary for ${destination}.
Budget level: ${budget || 'moderate'}.
Interests: ${interests || 'sightseeing, local cuisine, culture'}.
Accommodation preference: ${accommodation || 'mid-range hotel'}.
${contextData ? `\nReal-time data context: ${contextData}` : ''}

For each day provide:
- Morning, Afternoon, Evening activities with estimated durations
- Recommended restaurants for meals with cuisine type
- Transport between locations
- Estimated daily spend
- Pro tips for that day

End with a total trip cost estimate and packing essentials.`;

  const content = await granite.generate(SYSTEM_PROMPT, prompt, { max_new_tokens: 1500 });

  // Auto-save the itinerary
  const saved = bookingService.saveItinerary(destination, days || 5, content, { budget, interests });

  return { itinerary: content, id: saved.id };
}

/**
 * Get transport options between two locations.
 */
async function getTransportOptions({ from, to, date, passengers, budget }) {
  const prompt = `Provide comprehensive transport options from ${from} to ${to} for ${passengers || 1} passenger(s).
${date ? `Travel date: ${date}.` : ''}
Budget preference: ${budget || 'any'}.

Cover all realistic options:
1. Flights (airlines, estimated price range, duration, booking tips)
2. Train/Rail (if applicable, routes, duration, cost)
3. Bus/Coach services (duration, comfort, cost)
4. Car rental / drive (distance, tolls, estimated fuel cost)
5. Combination routes (e.g., flight + train)

For each option provide: estimated cost, travel time, comfort level, booking platforms, and best-value tips.
Also recommend the best option for this specific trip.`;

  return await granite.generate(SYSTEM_PROMPT, prompt);
}

/**
 * Suggest accommodation options.
 */
async function getAccommodationOptions({ destination, checkIn, checkOut, guests, budget, style }) {
  const prompt = `Suggest accommodation options in ${destination} for ${guests || 2} guest(s).
Check-in: ${checkIn || 'flexible'}, Check-out: ${checkOut || 'flexible'}.
Budget per night: ${budget || 'moderate ($50-$150/night)'}.
Travel style: ${style || 'comfort and convenience'}.

Provide 5 accommodation recommendations across different styles:
1. Budget option (hostel/guesthouse)
2. Mid-range hotel
3. Boutique/Unique stay
4. Apartment/Airbnb style
5. Luxury option (if budget allows)

For each: location/neighborhood, price range per night, pros/cons, nearby attractions, booking platforms, and special tips.`;

  return await granite.generate(SYSTEM_PROMPT, prompt);
}

/**
 * Full trip planning — combines all steps.
 */
async function planFullTrip({ from, destination, startDate, endDate, budget, travelers, interests, accommodation, currency }) {
  // Calculate trip duration
  let days = 7;
  if (startDate && endDate) {
    const diff = Math.ceil((new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24));
    if (diff > 0) days = diff;
  }

  // Get exchange rate for budget planning
  let exchangeInfo = '';
  try {
    const targetCurrency = currency || 'USD';
    const rates = await exchangeService.getRates(targetCurrency);
    exchangeInfo = `\nExchange rate context (${targetCurrency} base): USD=${rates.rates['USD']?.toFixed(2)}, EUR=${rates.rates['EUR']?.toFixed(2)}.`;
  } catch (e) {
    // Exchange fetch failed — continue
  }

  const prompt = `Create a COMPLETE travel plan for this trip:
- From: ${from || 'Origin not specified'}
- To: ${destination}
- Dates: ${startDate || 'flexible'} to ${endDate || 'flexible'} (${days} days)
- Travelers: ${travelers || 1} person(s)
- Total budget: ${budget || 'moderate'}
- Interests: ${interests || 'culture, food, sightseeing'}
- Accommodation: ${accommodation || 'mid-range hotel'}
${exchangeInfo}

Provide a COMPLETE trip plan with these sections:
## 🗺️ Trip Overview
## ✈️ Getting There & Back (flights/transport options)
## 🏨 Where to Stay (3 accommodation options)
## 📅 Day-by-Day Itinerary (all ${days} days)
## 🍽️ Food & Dining Guide
## 💰 Budget Breakdown (itemized)
## 🌤️ Weather & What to Pack
## 📋 Practical Tips (visa, safety, health, sim card, etc.)
## 🆘 Emergency Information`;

  const content = await granite.generate(SYSTEM_PROMPT, prompt, { max_new_tokens: 2000 });

  // Save as itinerary
  const saved = bookingService.saveItinerary(destination, days, content, {
    from, budget, travelers, interests, startDate, endDate
  });

  return { plan: content, id: saved.id, days };
}

/**
 * Chat with the travel agent (multi-turn conversation).
 */
async function chat(messages) {
  return await granite.chat(SYSTEM_PROMPT, messages);
}

/**
 * Get travel tips and local guide for a destination.
 */
async function getLocalGuide({ destination, aspects }) {
  const requestedAspects = aspects || 'culture, etiquette, safety, transport, food, shopping, nightlife, hidden gems';

  const prompt = `You are a local expert guide for ${destination}. Provide a comprehensive local guide covering:
${requestedAspects}.

Include:
- Cultural customs and etiquette (do's and don'ts)
- Safety tips and areas to avoid
- Getting around locally (metro, taxis, apps)
- Best local food experiences (dishes to try, best markets)
- Shopping (local crafts, souvenirs, markets)
- Hidden gems tourists often miss
- Useful local phrases (if non-English speaking)
- Local apps & websites to download/bookmark
- Emergency numbers and important contacts`;

  return await granite.generate(SYSTEM_PROMPT, prompt);
}

/**
 * Budget planner — break down trip costs.
 */
async function planBudget({ destination, days, travelers, totalBudget, currency }) {
  let exchangeContext = '';
  try {
    if (currency && currency !== 'USD') {
      const conv = await exchangeService.convert(totalBudget || 1000, currency, 'USD');
      exchangeContext = `\nBudget in USD equivalent: $${conv.converted}.`;
    }
  } catch (e) {}

  const prompt = `Create a detailed budget breakdown for a ${days || 7}-day trip to ${destination} for ${travelers || 1} traveler(s).
Total budget: ${totalBudget || '1000'} ${currency || 'USD'}.${exchangeContext}

Provide:
1. Budget allocation table (flights, accommodation, food, transport, activities, misc)
2. Daily spending target
3. Money-saving tips specific to ${destination}
4. Free activities and attractions
5. Budget vs mid-range vs splurge options comparison
6. What NOT to spend money on (tourist traps)
7. Recommended travel insurance cost
8. Emergency fund recommendation`;

  return await granite.generate(SYSTEM_PROMPT, prompt);
}

module.exports = {
  suggestDestinations,
  buildItinerary,
  getTransportOptions,
  getAccommodationOptions,
  planFullTrip,
  chat,
  getLocalGuide,
  planBudget
};

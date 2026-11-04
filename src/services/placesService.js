/**
 * Places Service — attractions, restaurants, and points of interest
 * Uses OpenTripMap API (Free tier: 5000 requests/day)
 */
const axios     = require('axios');
const NodeCache = require('node-cache');

const cache = new NodeCache({ stdTTL: parseInt(process.env.CACHE_TTL_PLACES) || 86400 });

const BASE_URL = process.env.OPENTRIPMAP_BASE_URL || 'https://api.opentripmap.com/0.1/en';
const API_KEY  = process.env.OPENTRIPMAP_API_KEY  || '';

const CATEGORY_MAP = {
  attractions   : 'interesting_places',
  restaurants   : 'foods',
  museums       : 'cultural',
  nature        : 'natural',
  architecture  : 'architecture',
  entertainment : 'amusements',
  shopping      : 'shops'
};

/**
 * Get places near a lat/lon within a radius.
 */
async function getPlacesNearby(lat, lon, category = 'attractions', radius = 5000, limit = 10) {
  const kind     = CATEGORY_MAP[category] || category;
  const cacheKey = `places_${lat}_${lon}_${kind}_${radius}`;
  if (cache.has(cacheKey)) return cache.get(cacheKey);

  // If no API key, return curated fallback data
  if (!API_KEY || API_KEY === 'your_opentripmap_api_key_here') {
    return getFallbackPlaces(category);
  }

  const url    = `${BASE_URL}/places/radius`;
  const params = {
    radius,
    lon,
    lat,
    kinds    : kind,
    limit,
    apikey   : API_KEY,
    format   : 'json',
    rate     : 3
  };

  const response = await axios.get(url, { params });
  const places   = (response.data || []).map(p => ({
    name     : p.name || 'Unnamed Place',
    xid      : p.xid,
    kinds    : p.kinds,
    dist     : Math.round(p.dist),
    lat      : p.point?.lat,
    lon      : p.point?.lon
  })).filter(p => p.name !== 'Unnamed Place');

  cache.set(cacheKey, places);
  return places;
}

/**
 * Get place details by OpenTripMap xid.
 */
async function getPlaceDetails(xid) {
  if (!API_KEY || API_KEY === 'your_opentripmap_api_key_here') return null;

  const url    = `${BASE_URL}/places/xid/${xid}`;
  const params = { apikey: API_KEY };

  const response = await axios.get(url, { params });
  return response.data;
}

/**
 * Fallback curated places for common categories when API key is not set.
 */
function getFallbackPlaces(category) {
  const fallbacks = {
    attractions: [
      { name: 'Local City Center',      kinds: 'interesting_places', dist: 500  },
      { name: 'Historical Old Town',    kinds: 'historic',            dist: 1200 },
      { name: 'Riverside Promenade',    kinds: 'natural',             dist: 800  },
      { name: 'Main Cathedral/Mosque',  kinds: 'religion',            dist: 600  },
      { name: 'Central Park/Gardens',   kinds: 'natural',             dist: 1000 }
    ],
    restaurants: [
      { name: 'Local Street Food Market', kinds: 'foods', dist: 300  },
      { name: 'Fine Dining Restaurant',   kinds: 'foods', dist: 700  },
      { name: 'Traditional Cuisine Spot', kinds: 'foods', dist: 1100 }
    ],
    museums: [
      { name: 'National History Museum',  kinds: 'cultural', dist: 900  },
      { name: 'Art Gallery',              kinds: 'cultural', dist: 1500 },
      { name: 'Science & Tech Museum',    kinds: 'cultural', dist: 2000 }
    ],
    nature: [
      { name: 'National Park Entrance',   kinds: 'natural', dist: 5000  },
      { name: 'Botanical Gardens',        kinds: 'natural', dist: 2000  },
      { name: 'Scenic Viewpoint',         kinds: 'natural', dist: 3000  }
    ]
  };
  return fallbacks[category] || fallbacks.attractions;
}

module.exports = { getPlacesNearby, getPlaceDetails };

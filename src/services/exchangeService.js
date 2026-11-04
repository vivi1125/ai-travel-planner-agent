/**
 * Exchange Rate Service — currency conversion for trip budgeting
 * Uses ExchangeRate-API (Free tier: 1500 requests/month)
 */
const axios     = require('axios');
const NodeCache = require('node-cache');

const cache    = new NodeCache({ stdTTL: parseInt(process.env.CACHE_TTL_EXCHANGE) || 3600 });
const BASE_URL = process.env.EXCHANGE_RATE_BASE_URL || 'https://v6.exchangerate-api.com/v6';
const API_KEY  = process.env.EXCHANGE_RATE_API_KEY  || '';

/**
 * Get exchange rates for a base currency.
 * Falls back to static rates if no API key is configured.
 */
async function getRates(baseCurrency = 'USD') {
  const cacheKey = `rates_${baseCurrency.toUpperCase()}`;
  if (cache.has(cacheKey)) return cache.get(cacheKey);

  if (!API_KEY || API_KEY === 'your_exchange_rate_api_key_here') {
    return getStaticRates(baseCurrency);
  }

  const url      = `${BASE_URL}/${API_KEY}/latest/${baseCurrency.toUpperCase()}`;
  const response = await axios.get(url);

  if (response.data?.result !== 'success') {
    throw new Error(`Exchange rate API error: ${response.data?.['error-type']}`);
  }

  const rates = {
    base      : response.data.base_code,
    rates     : response.data.conversion_rates,
    updatedAt : response.data.time_last_update_utc
  };

  cache.set(cacheKey, rates);
  return rates;
}

/**
 * Convert an amount from one currency to another.
 */
async function convert(amount, from = 'USD', to = 'EUR') {
  const ratesData = await getRates(from.toUpperCase());
  const rate      = ratesData.rates[to.toUpperCase()];

  if (!rate) throw new Error(`Unsupported currency: ${to}`);

  return {
    from      : from.toUpperCase(),
    to        : to.toUpperCase(),
    amount    : parseFloat(amount),
    converted : parseFloat((amount * rate).toFixed(2)),
    rate      : rate
  };
}

/**
 * Static fallback rates (approximate) when no API key is set.
 */
function getStaticRates(base) {
  const USD_RATES = {
    USD: 1, EUR: 0.92, GBP: 0.79, JPY: 149.5, AUD: 1.53,
    CAD: 1.36, CHF: 0.88, INR: 83.2, SGD: 1.34, AED: 3.67,
    MXN: 17.1, BRL: 4.97, CNY: 7.24, KRW: 1325, THB: 35.1,
    MYR: 4.72, IDR: 15600, PHP: 56.4, VND: 24500, TRY: 32.0
  };

  if (base === 'USD') return { base: 'USD', rates: USD_RATES, updatedAt: 'static' };

  // Compute cross rates
  const baseRate = USD_RATES[base] || 1;
  const crossed  = {};
  for (const [cur, rate] of Object.entries(USD_RATES)) {
    crossed[cur] = parseFloat((rate / baseRate).toFixed(6));
  }
  return { base: base.toUpperCase(), rates: crossed, updatedAt: 'static' };
}

module.exports = { getRates, convert };

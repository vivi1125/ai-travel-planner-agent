/**
 * IBM Travel Planner Agent — Main Express Server
 * Uses IBM watsonx.ai with IBM Granite LLM (Lite tier)
 */
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');

const agentRouter   = require('./src/routes/agentRoutes');
const travelRouter  = require('./src/routes/travelRoutes');
const weatherRouter = require('./src/routes/weatherRoutes');

const app  = express();
const PORT = process.env.PORT || 3000;

// ── Middleware ────────────────────────────────────────────────
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// ── Routes ────────────────────────────────────────────────────
app.use('/api/agent',   agentRouter);
app.use('/api/travel',  travelRouter);
app.use('/api/weather', weatherRouter);

// ── Health check ─────────────────────────────────────────────
app.get('/api/health', (req, res) => {
  res.json({
    status : 'ok',
    service: process.env.APP_NAME || 'Travel Planner Agent',
    model  : process.env.GRANITE_CHAT_MODEL_ID,
    time   : new Date().toISOString()
  });
});

// ── Serve frontend SPA ────────────────────────────────────────
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ── Global error handler ─────────────────────────────────────
app.use((err, req, res, _next) => {
  console.error('[Server Error]', err.message);
  res.status(err.status || 500).json({ error: err.message || 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`\n🌍 Travel Planner Agent running on http://localhost:${PORT}`);
  console.log(`   Model : ${process.env.GRANITE_CHAT_MODEL_ID}`);
  console.log(`   Env   : ${process.env.NODE_ENV || 'development'}\n`);
});

module.exports = app;

/**
 * Agent Routes — main AI chat and planning endpoints
 */
const express = require('express');
const router  = express.Router();
const agent   = require('../agent/travelAgent');

// ── Chat endpoint (multi-turn) ────────────────────────────────
router.post('/chat', async (req, res) => {
  try {
    const { messages } = req.body;
    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return res.status(400).json({ error: 'messages array is required' });
    }
    const reply = await agent.chat(messages);
    res.json({ reply });
  } catch (err) {
    console.error('[/agent/chat]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── Suggest destinations ──────────────────────────────────────
router.post('/suggest', async (req, res) => {
  try {
    const result = await agent.suggestDestinations(req.body);
    res.json({ suggestions: result });
  } catch (err) {
    console.error('[/agent/suggest]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── Full trip plan ────────────────────────────────────────────
router.post('/plan', async (req, res) => {
  try {
    const result = await agent.planFullTrip(req.body);
    res.json(result);
  } catch (err) {
    console.error('[/agent/plan]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── Local guide ───────────────────────────────────────────────
router.post('/guide', async (req, res) => {
  try {
    const result = await agent.getLocalGuide(req.body);
    res.json({ guide: result });
  } catch (err) {
    console.error('[/agent/guide]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── Budget planner ────────────────────────────────────────────
router.post('/budget', async (req, res) => {
  try {
    const result = await agent.planBudget(req.body);
    res.json({ budget: result });
  } catch (err) {
    console.error('[/agent/budget]', err.message);
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;

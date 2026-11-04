/**
 * IBM Granite Client — wraps IBM watsonx.ai SDK for the Lite tier
 * Supports text generation via granite-3-8b-instruct
 */
const { WatsonXAI } = require('@ibm-cloud/watsonx-ai');

class GraniteClient {
  constructor() {
    this.client = WatsonXAI.newInstance({
      version         : '2024-05-31',
      serviceUrl      : process.env.WATSONX_URL || 'https://us-south.ml.cloud.ibm.com',
      authenticator   : {
        apikey: process.env.IBM_CLOUD_API_KEY
      }
    });
    this.projectId = process.env.WATSONX_PROJECT_ID;
    this.modelId   = process.env.GRANITE_CHAT_MODEL_ID || 'ibm/granite-3-8b-instruct';
  }

  /**
   * Generate a response from IBM Granite given a system prompt + user message.
   * @param {string} systemPrompt
   * @param {string} userMessage
   * @param {object} [overrides] — optional parameter overrides
   * @returns {Promise<string>}
   */
  async generate(systemPrompt, userMessage, overrides = {}) {
    const prompt = this._buildPrompt(systemPrompt, userMessage);

    const params = {
      modelId   : this.modelId,
      projectId : this.projectId,
      input     : prompt,
      parameters: {
        max_new_tokens     : parseInt(process.env.GRANITE_MAX_NEW_TOKENS)  || 1024,
        temperature        : parseFloat(process.env.GRANITE_TEMPERATURE)   || 0.7,
        top_p              : parseFloat(process.env.GRANITE_TOP_P)         || 0.9,
        top_k              : parseInt(process.env.GRANITE_TOP_K)           || 50,
        repetition_penalty : parseFloat(process.env.GRANITE_REPETITION_PENALTY) || 1.1,
        stop_sequences     : ['<|user|>', '<|endoftext|>'],
        ...overrides
      }
    };

    const response = await this.client.generateText(params);
    const result   = response.result;

    if (result?.results?.[0]?.generated_text) {
      return result.results[0].generated_text.trim();
    }
    throw new Error('No generated text received from IBM Granite.');
  }

  /**
   * Build a Granite-compatible prompt using the <|system|>/<|user|>/<|assistant|> format.
   */
  _buildPrompt(systemPrompt, userMessage) {
    return `<|system|>\n${systemPrompt}\n<|user|>\n${userMessage}\n<|assistant|>\n`;
  }

  /**
   * Chat-style generation supporting multi-turn conversation history.
   * @param {string} systemPrompt
   * @param {Array<{role:'user'|'assistant', content:string}>} messages
   * @param {object} [overrides]
   */
  async chat(systemPrompt, messages, overrides = {}) {
    let prompt = `<|system|>\n${systemPrompt}\n`;
    for (const msg of messages) {
      if (msg.role === 'user') {
        prompt += `<|user|>\n${msg.content}\n`;
      } else {
        prompt += `<|assistant|>\n${msg.content}\n`;
      }
    }
    prompt += '<|assistant|>\n';

    const params = {
      modelId   : this.modelId,
      projectId : this.projectId,
      input     : prompt,
      parameters: {
        max_new_tokens     : parseInt(process.env.GRANITE_MAX_NEW_TOKENS)  || 1024,
        temperature        : parseFloat(process.env.GRANITE_TEMPERATURE)   || 0.7,
        top_p              : parseFloat(process.env.GRANITE_TOP_P)         || 0.9,
        top_k              : parseInt(process.env.GRANITE_TOP_K)           || 50,
        repetition_penalty : parseFloat(process.env.GRANITE_REPETITION_PENALTY) || 1.1,
        stop_sequences     : ['<|user|>', '<|endoftext|>'],
        ...overrides
      }
    };

    const response = await this.client.generateText(params);
    const result   = response.result;

    if (result?.results?.[0]?.generated_text) {
      return result.results[0].generated_text.trim();
    }
    throw new Error('No generated text received from IBM Granite.');
  }
}

module.exports = new GraniteClient();

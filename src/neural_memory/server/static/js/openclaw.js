/**
 * NeuralMemory Dashboard — OpenClaw config module
 * API keys, functions, security, channel setup UI.
 */

const NM_OPENCLAW = {
  config: null,

  async init() {
    await this.loadConfig();
    this.renderConfig();
    this.renderChannels();
  },

  async loadConfig() {
    try {
      const resp = await fetch('/api/openclaw/config');
      if (resp.ok) {
        this.config = await resp.json();
      }
    } catch {
      this.config = { api_keys: [], functions: [], security: {}, telegram: {}, discord: {} };
    }
  },

  // ── Main Config Tab (OpenClaw) ───────────────────────────

  renderConfig() {
    const container = document.getElementById('openclaw-config');
    if (!container || !this.config) return;

    container.innerHTML = `
      <!-- Sub-tabs -->
      <div class="flex gap-2 mb-6 border-b border-nm-border pb-3">
        <button onclick="NM_OPENCLAW.showSubTab('apikeys')" id="subtab-apikeys"
                class="px-4 py-2 rounded-t-lg font-code text-sm bg-nm-cta/10 text-nm-cta cursor-pointer transition-colors duration-200">${NM_I18N.t('api_keys')}</button>
        <button onclick="NM_OPENCLAW.showSubTab('functions')" id="subtab-functions"
                class="px-4 py-2 rounded-t-lg font-code text-sm text-nm-muted hover:text-nm-text cursor-pointer transition-colors duration-200">${NM_I18N.t('functions')}</button>
        <button onclick="NM_OPENCLAW.showSubTab('security')" id="subtab-security"
                class="px-4 py-2 rounded-t-lg font-code text-sm text-nm-muted hover:text-nm-text cursor-pointer transition-colors duration-200">${NM_I18N.t('security')}</button>
      </div>

      <!-- API Keys -->
      <div id="panel-apikeys">
        ${this._renderApiKeys()}
      </div>

      <!-- Functions -->
      <div id="panel-functions" class="hidden">
        ${this._renderFunctions()}
      </div>

      <!-- Security -->
      <div id="panel-security" class="hidden">
        ${this._renderSecurity()}
      </div>
    `;

    if (window.lucide) lucide.createIcons();
  },

  showSubTab(tab) {
    ['apikeys', 'functions', 'security'].forEach(t => {
      const panel = document.getElementById('panel-' + t);
      const btn = document.getElementById('subtab-' + t);
      if (panel) panel.classList.toggle('hidden', t !== tab);
      if (btn) {
        btn.className = t === tab
          ? 'px-4 py-2 rounded-t-lg font-code text-sm bg-nm-cta/10 text-nm-cta cursor-pointer transition-colors duration-200'
          : 'px-4 py-2 rounded-t-lg font-code text-sm text-nm-muted hover:text-nm-text cursor-pointer transition-colors duration-200';
      }
    });
  },

  // ── API Keys ─────────────────────────────────────────────

  _renderApiKeys() {
    const keys = this.config.api_keys || [];
    const providers = ['claude', 'gemini', 'openai', 'qwen', 'iflow', 'antigravity'];

    return `
      <div class="space-y-4 max-w-2xl">
        ${providers.map(p => {
          const existing = keys.find(k => k.provider === p);
          return `
            <div class="bg-nm-primary border border-nm-border rounded-xl p-4">
              <div class="flex items-center justify-between mb-3">
                <span class="font-code font-semibold text-sm capitalize">${this._escapeHtml(p)}</span>
                ${existing && existing.enabled ? '<span class="w-2 h-2 rounded-full bg-nm-cta"></span>' : ''}
              </div>
              <div class="flex gap-2">
                <input type="password" id="apikey-${p}" placeholder="${NM_I18N.t('enter_api_key')}"
                       value="${existing ? this._escapeHtml(existing.key) : ''}"
                       class="flex-1 bg-nm-secondary border border-nm-border rounded-lg px-3 py-2 text-sm font-code text-nm-text placeholder-nm-muted focus:outline-none focus:border-nm-cta">
                <button onclick="NM_OPENCLAW.saveApiKey('${p}')"
                        class="bg-nm-cta hover:bg-nm-cta-hover text-nm-bg px-4 py-2 rounded-lg font-code text-sm transition-colors duration-200 cursor-pointer">${NM_I18N.t('save')}</button>
                ${existing ? `<button onclick="NM_OPENCLAW.deleteApiKey('${p}')"
                        class="bg-nm-danger/10 hover:bg-nm-danger/20 text-nm-danger px-3 py-2 rounded-lg text-sm transition-colors duration-200 cursor-pointer">
                        <i data-lucide="trash-2" class="w-4 h-4"></i></button>` : ''}
              </div>
            </div>`;
        }).join('')}
      </div>`;
  },

  async saveApiKey(provider) {
    const input = document.getElementById('apikey-' + provider);
    if (!input || !input.value.trim()) return;

    try {
      const resp = await fetch('/api/openclaw/apikeys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, key: input.value.trim() }),
      });
      if (resp.ok) {
        await this.loadConfig();
        this.renderConfig();
      }
    } catch (err) {
      alert('Save failed: ' + err.message);
    }
  },

  async deleteApiKey(provider) {
    try {
      const resp = await fetch(`/api/openclaw/apikeys/${provider}`, { method: 'DELETE' });
      if (resp.ok) {
        await this.loadConfig();
        this.renderConfig();
      }
    } catch (err) {
      alert('Delete failed: ' + err.message);
    }
  },

  // ── Functions ────────────────────────────────────────────

  _renderFunctions() {
    const fns = this.config.functions || [];
    return `
      <div class="space-y-3 max-w-2xl">
        ${fns.map(fn => `
          <div class="bg-nm-primary border border-nm-border rounded-xl p-4 flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="font-code font-semibold text-sm">${this._escapeHtml(fn.name)}</span>
                ${fn.restricted ? '<span class="text-[10px] bg-nm-danger/10 text-nm-danger px-1.5 py-0.5 rounded font-code">RESTRICTED</span>' : ''}
              </div>
              <div class="text-xs text-nm-muted mt-1">${this._escapeHtml(fn.description || '')}</div>
              <div class="text-xs text-nm-muted mt-1">Timeout: ${fn.timeout_ms}ms</div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" ${fn.enabled ? 'checked' : ''}
                     onchange="NM_OPENCLAW.toggleFunction('${fn.name}', this.checked)"
                     class="sr-only peer">
              <div class="w-11 h-6 bg-nm-secondary rounded-full peer peer-checked:bg-nm-cta peer-focus:outline-none transition-colors duration-200 after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-nm-text after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
            </label>
          </div>
        `).join('')}
      </div>`;
  },

  async toggleFunction(name, enabled) {
    try {
      await fetch(`/api/openclaw/functions/${name}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
    } catch (err) {
      alert('Toggle failed: ' + err.message);
    }
  },

  // ── Security ─────────────────────────────────────────────

  _renderSecurity() {
    const sec = this.config.security || {};
    return `
      <div class="space-y-4 max-w-2xl">
        <div class="bg-nm-primary border border-nm-border rounded-xl p-5">
          <div class="flex items-center justify-between mb-4">
            <span class="font-code font-semibold text-sm">${NM_I18N.t('sandbox_mode')}</span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" id="sec-sandbox" ${sec.sandbox_mode !== false ? 'checked' : ''}
                     class="sr-only peer">
              <div class="w-11 h-6 bg-nm-secondary rounded-full peer peer-checked:bg-nm-cta transition-colors duration-200 after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-nm-text after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
            </label>
          </div>

          <div class="space-y-3">
            <div>
              <label class="text-xs text-nm-muted block mb-1">${NM_I18N.t('allowed_domains')}</label>
              <input type="text" id="sec-domains" value="${(sec.allowed_domains || []).join(', ')}"
                     placeholder="example.com, api.example.com"
                     class="w-full bg-nm-secondary border border-nm-border rounded-lg px-3 py-2 text-sm font-code text-nm-text placeholder-nm-muted focus:outline-none focus:border-nm-cta">
            </div>
            <div>
              <label class="text-xs text-nm-muted block mb-1">${NM_I18N.t('blocked_commands')}</label>
              <input type="text" id="sec-blocked" value="${(sec.blocked_commands || []).join(', ')}"
                     placeholder="rm, shutdown, format"
                     class="w-full bg-nm-secondary border border-nm-border rounded-lg px-3 py-2 text-sm font-code text-nm-text placeholder-nm-muted focus:outline-none focus:border-nm-cta">
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="text-xs text-nm-muted block mb-1">${NM_I18N.t('max_tokens')}</label>
                <input type="number" id="sec-tokens" value="${sec.max_tokens_per_request || 100000}"
                       class="w-full bg-nm-secondary border border-nm-border rounded-lg px-3 py-2 text-sm font-code text-nm-text focus:outline-none focus:border-nm-cta">
              </div>
              <div>
                <label class="text-xs text-nm-muted block mb-1">${NM_I18N.t('rate_limit')}</label>
                <input type="number" id="sec-rate" value="${sec.rate_limit_rpm || 60}"
                       class="w-full bg-nm-secondary border border-nm-border rounded-lg px-3 py-2 text-sm font-code text-nm-text focus:outline-none focus:border-nm-cta">
              </div>
            </div>
          </div>

          <button onclick="NM_OPENCLAW.saveSecurity()"
                  class="mt-4 bg-nm-cta hover:bg-nm-cta-hover text-nm-bg px-4 py-2 rounded-lg font-code text-sm transition-colors duration-200 cursor-pointer">${NM_I18N.t('save')}</button>
        </div>
      </div>`;
  },

  async saveSecurity() {
    const sandbox = document.getElementById('sec-sandbox')?.checked ?? true;
    const domains = (document.getElementById('sec-domains')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
    const blocked = (document.getElementById('sec-blocked')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
    const tokens = parseInt(document.getElementById('sec-tokens')?.value || '100000', 10);
    const rate = parseInt(document.getElementById('sec-rate')?.value || '60', 10);

    try {
      await fetch('/api/openclaw/security', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sandbox_mode: sandbox,
          allowed_domains: domains,
          blocked_commands: blocked,
          max_tokens_per_request: tokens,
          rate_limit_rpm: rate,
        }),
      });
    } catch (err) {
      alert('Save failed: ' + err.message);
    }
  },

  // ── Channels ─────────────────────────────────────────────

  renderChannels() {
    const container = document.getElementById('channels-config');
    if (!container || !this.config) return;

    const tg = this.config.telegram || {};
    const dc = this.config.discord || {};

    container.innerHTML = `
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Telegram -->
        <div class="bg-nm-primary border border-nm-border rounded-xl p-5">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 bg-[#0088cc]/10 rounded-lg flex items-center justify-center">
              <i data-lucide="send" class="w-5 h-5 text-[#0088cc]"></i>
            </div>
            <div>
              <div class="font-code font-semibold">Telegram</div>
              <div class="text-xs text-nm-muted">${tg.enabled ? NM_I18N.t('connected') : NM_I18N.t('not_connected')}</div>
            </div>
          </div>
          <div class="space-y-3">
            <div>
              <label class="text-xs text-nm-muted block mb-1">${NM_I18N.t('bot_token')}</label>
              <input type="password" id="tg-token" value="${this._escapeHtml(tg.bot_token || '')}"
                     placeholder="123456:ABC-DEF..."
                     class="w-full bg-nm-secondary border border-nm-border rounded-lg px-3 py-2 text-sm font-code text-nm-text placeholder-nm-muted focus:outline-none focus:border-nm-cta">
            </div>
            <div>
              <label class="text-xs text-nm-muted block mb-1">${NM_I18N.t('chat_ids')}</label>
              <input type="text" id="tg-chats" value="${(tg.chat_ids || []).join(', ')}"
                     placeholder="-1001234567890, 987654321"
                     class="w-full bg-nm-secondary border border-nm-border rounded-lg px-3 py-2 text-sm font-code text-nm-text placeholder-nm-muted focus:outline-none focus:border-nm-cta">
            </div>
            <div class="flex items-center justify-between">
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" id="tg-enabled" ${tg.enabled ? 'checked' : ''} class="sr-only peer">
                <div class="w-11 h-6 bg-nm-secondary rounded-full peer peer-checked:bg-nm-cta transition-colors duration-200 after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-nm-text after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
                <span class="ml-2 text-sm text-nm-muted">${NM_I18N.t('enabled')}</span>
              </label>
              <button onclick="NM_OPENCLAW.saveTelegram()"
                      class="bg-nm-cta hover:bg-nm-cta-hover text-nm-bg px-4 py-2 rounded-lg font-code text-sm transition-colors duration-200 cursor-pointer">${NM_I18N.t('save')}</button>
            </div>
          </div>
        </div>

        <!-- Discord -->
        <div class="bg-nm-primary border border-nm-border rounded-xl p-5">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 bg-[#5865F2]/10 rounded-lg flex items-center justify-center">
              <i data-lucide="hash" class="w-5 h-5 text-[#5865F2]"></i>
            </div>
            <div>
              <div class="font-code font-semibold">Discord</div>
              <div class="text-xs text-nm-muted">${dc.enabled ? NM_I18N.t('connected') : NM_I18N.t('not_connected')}</div>
            </div>
          </div>
          <div class="space-y-3">
            <div>
              <label class="text-xs text-nm-muted block mb-1">${NM_I18N.t('bot_token')}</label>
              <input type="password" id="dc-token" value="${this._escapeHtml(dc.bot_token || '')}"
                     placeholder="MTIz..."
                     class="w-full bg-nm-secondary border border-nm-border rounded-lg px-3 py-2 text-sm font-code text-nm-text placeholder-nm-muted focus:outline-none focus:border-nm-cta">
            </div>
            <div>
              <label class="text-xs text-nm-muted block mb-1">${NM_I18N.t('guild_id')}</label>
              <input type="text" id="dc-guild" value="${this._escapeHtml(dc.guild_id || '')}"
                     placeholder="123456789012345678"
                     class="w-full bg-nm-secondary border border-nm-border rounded-lg px-3 py-2 text-sm font-code text-nm-text placeholder-nm-muted focus:outline-none focus:border-nm-cta">
            </div>
            <div>
              <label class="text-xs text-nm-muted block mb-1">${NM_I18N.t('channel_ids')}</label>
              <input type="text" id="dc-channels" value="${(dc.channel_ids || []).join(', ')}"
                     placeholder="123456789012345678"
                     class="w-full bg-nm-secondary border border-nm-border rounded-lg px-3 py-2 text-sm font-code text-nm-text placeholder-nm-muted focus:outline-none focus:border-nm-cta">
            </div>
            <div class="flex items-center justify-between">
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" id="dc-enabled" ${dc.enabled ? 'checked' : ''} class="sr-only peer">
                <div class="w-11 h-6 bg-nm-secondary rounded-full peer peer-checked:bg-nm-cta transition-colors duration-200 after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-nm-text after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
                <span class="ml-2 text-sm text-nm-muted">${NM_I18N.t('enabled')}</span>
              </label>
              <button onclick="NM_OPENCLAW.saveDiscord()"
                      class="bg-nm-cta hover:bg-nm-cta-hover text-nm-bg px-4 py-2 rounded-lg font-code text-sm transition-colors duration-200 cursor-pointer">${NM_I18N.t('save')}</button>
            </div>
          </div>
        </div>
      </div>`;

    if (window.lucide) lucide.createIcons();
  },

  async saveTelegram() {
    const token = document.getElementById('tg-token')?.value || '';
    const chats = (document.getElementById('tg-chats')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
    const enabled = document.getElementById('tg-enabled')?.checked ?? false;

    try {
      await fetch('/api/openclaw/telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bot_token: token, chat_ids: chats, enabled, parse_mode: 'Markdown' }),
      });
      await this.loadConfig();
      this.renderChannels();
    } catch (err) {
      alert('Save failed: ' + err.message);
    }
  },

  async saveDiscord() {
    const token = document.getElementById('dc-token')?.value || '';
    const guild = document.getElementById('dc-guild')?.value || '';
    const channels = (document.getElementById('dc-channels')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
    const enabled = document.getElementById('dc-enabled')?.checked ?? false;

    try {
      await fetch('/api/openclaw/discord', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bot_token: token, guild_id: guild, channel_ids: channels, enabled }),
      });
      await this.loadConfig();
      this.renderChannels();
    } catch (err) {
      alert('Save failed: ' + err.message);
    }
  },

  _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
  }
};

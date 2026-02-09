/**
 * NeuralMemory Dashboard — OAuth module
 * Provider cards, OAuth flow initiation, status polling.
 */

const NM_OAUTH = {
  providers: [],

  ICONS: {
    claude: 'brain',
    gemini: 'sparkles',
    codex: 'code',
    qwen: 'message-square',
    iflow: 'workflow',
    antigravity: 'rocket',
  },

  COLORS: {
    claude: '#D97757',
    gemini: '#4285F4',
    codex: '#10A37F',
    qwen: '#6366F1',
    iflow: '#F59E0B',
    antigravity: '#22C55E',
  },

  async init() {
    await this.loadProviders();
    this.render();
  },

  async loadProviders() {
    try {
      const resp = await fetch('/api/oauth/providers');
      if (resp.ok) {
        this.providers = await resp.json();
      }
    } catch {
      this.providers = [];
      nmToast(NM_I18N.t('connection_failed'), 'error');
    }
  },

  render() {
    const container = document.getElementById('int-oauth');
    if (!container) return;

    if (this.providers.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <i data-lucide="key"></i>
          <p class="text-nm-muted">No OAuth providers available.</p>
        </div>`;
      if (window.lucide) lucide.createIcons();
      return;
    }

    container.innerHTML = `<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">` +
      this.providers.map(p => `
      <div class="bg-nm-primary border border-nm-border rounded-xl p-5 hover:border-nm-border transition-colors duration-200"
           style="border-left: 3px solid ${this.COLORS[p.id] || '#475569'}">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center" style="background: ${this.COLORS[p.id] || '#475569'}20">
              <i data-lucide="${this.ICONS[p.id] || 'key'}" class="w-5 h-5" style="color: ${this.COLORS[p.id] || '#475569'}"></i>
            </div>
            <div>
              <div class="font-code font-semibold">${this.escapeHtml(p.name)}</div>
              <div class="text-xs text-nm-muted">${this.escapeHtml(p.description || '')}</div>
            </div>
          </div>
          <span class="w-3 h-3 rounded-full ${p.authenticated ? 'bg-nm-cta pulse-dot' : 'bg-nm-secondary'}"></span>
        </div>
        <div class="flex items-center gap-2">
          ${p.authenticated
            ? `<span class="text-xs text-nm-cta font-code bg-nm-cta/10 px-2 py-1 rounded">${NM_I18N.t('connected')}</span>
               <button onclick="NM_OAUTH.revokeProvider('${p.id}')"
                       aria-label="Revoke ${this.escapeHtml(p.name)}"
                       class="text-xs text-nm-danger hover:text-nm-danger/80 font-code px-2 py-1 cursor-pointer">${NM_I18N.t('revoke')}</button>`
            : `<button onclick="NM_OAUTH.connectProvider('${p.id}')"
                       aria-label="Connect ${this.escapeHtml(p.name)}"
                       class="bg-nm-secondary hover:bg-nm-border text-sm font-code px-4 py-1.5 rounded-lg transition-colors duration-200 cursor-pointer">${NM_I18N.t('connect')}</button>`
          }
        </div>
      </div>
    `).join('') + `</div>`;

    if (window.lucide) lucide.createIcons();
  },

  async connectProvider(providerId) {
    try {
      const resp = await fetch('/api/oauth/initiate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: providerId }),
      });

      if (!resp.ok) {
        const err = await resp.json();
        nmToast(err.detail || 'Failed to initiate OAuth', 'error');
        return;
      }

      const data = await resp.json();
      if (data.auth_url) {
        const popup = window.open(data.auth_url, 'oauth', 'width=600,height=700');
        this._pollAuth(providerId, popup);
      }
    } catch (err) {
      nmToast('OAuth error: ' + err.message, 'error');
    }
  },

  _pollAuth(providerId, popup) {
    const interval = setInterval(async () => {
      if (popup && popup.closed) {
        clearInterval(interval);
        await this.loadProviders();
        this.render();
        return;
      }

      try {
        const resp = await fetch(`/api/oauth/status/${providerId}`);
        if (resp.ok) {
          const data = await resp.json();
          if (data.authenticated) {
            clearInterval(interval);
            if (popup) popup.close();
            await this.loadProviders();
            this.render();
            nmToast(`${providerId} connected!`, 'success');
          }
        }
      } catch {
        // ignore polling errors
      }
    }, 2000);

    setTimeout(() => clearInterval(interval), 600000);
  },

  async revokeProvider(providerId) {
    await this.loadProviders();
    this.render();
  },

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
};

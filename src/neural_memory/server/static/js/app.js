/**
 * NeuralMemory Dashboard — Core Alpine.js application
 * Orchestrates tabs, stats, health, brain management, i18n.
 */

function dashboardApp() {
  return {
    // State
    version: '',
    locale: 'en',
    activeTab: 'overview',
    activeBrain: null,
    brains: [],
    stats: { total_brains: 0, total_neurons: 0, total_synapses: 0, total_fibers: 0 },
    healthGrade: 'F',
    purityScore: 0,
    healthWarnings: [],
    healthRecommendations: [],
    selectedNode: null,
    _radarChart: null,
    _graphLoaded: false,

    // Tab definitions
    tabs: [
      { id: 'overview', label: 'overview', icon: 'layout-dashboard' },
      { id: 'graph', label: 'neural_graph', icon: 'share-2' },
      { id: 'oauth', label: 'oauth_providers', icon: 'key' },
      { id: 'openclaw', label: 'openclaw_config', icon: 'settings' },
      { id: 'channels', label: 'channels', icon: 'message-circle' },
      { id: 'health', label: 'brain_health', icon: 'heart-pulse' },
      { id: 'settings', label: 'settings', icon: 'sliders-horizontal' },
    ],

    // Initialize
    async init() {
      await NM_I18N.init();
      this.locale = NM_I18N.locale;

      // Fetch version from API
      try {
        const resp = await fetch('/');
        if (resp.ok) {
          const data = await resp.json();
          this.version = data.version || '';
        }
      } catch {}

      await this.loadStats();
      await this.loadHealth();

      // Watch tab changes for lazy loading
      this.$watch('activeTab', (tab) => this.onTabChange(tab));

      // Init Lucide icons
      this.$nextTick(() => { if (window.lucide) lucide.createIcons(); });
    },

    // Tab change handler
    async onTabChange(tab) {
      this.$nextTick(() => { if (window.lucide) lucide.createIcons(); });

      if (tab === 'graph' && !this._graphLoaded) {
        this._graphLoaded = true;
        await this.$nextTick();
        const cy = await NM_GRAPH.init('cy-graph');
        if (cy) {
          NM_GRAPH.onNodeClick((node) => { this.selectedNode = node; });
        }
      }

      if (tab === 'oauth') {
        await NM_OAUTH.init();
      }

      if (tab === 'openclaw') {
        await NM_OPENCLAW.init();
      }

      if (tab === 'channels') {
        await NM_OPENCLAW.init();
      }

      if (tab === 'health') {
        this.$nextTick(() => this.renderRadar());
      }
    },

    // i18n helper
    t(key) {
      return NM_I18N.t(key);
    },

    toggleLocale() {
      const next = this.locale === 'en' ? 'vi' : 'en';
      this.setLocale(next);
    },

    async setLocale(locale) {
      await NM_I18N.setLocale(locale);
      this.locale = locale;
      // Force re-render of dynamic modules
      if (this.activeTab === 'oauth') NM_OAUTH.render();
      if (this.activeTab === 'openclaw') NM_OPENCLAW.renderConfig();
      if (this.activeTab === 'channels') NM_OPENCLAW.renderChannels();
    },

    // Data loading
    async loadStats() {
      try {
        const resp = await fetch('/api/dashboard/stats');
        if (resp.ok) {
          const data = await resp.json();
          this.stats = data;
          this.activeBrain = data.active_brain;
          this.brains = data.brains || [];
          this.healthGrade = data.health_grade || 'F';
          this.purityScore = data.purity_score || 0;
        }
      } catch {}
    },

    async loadHealth() {
      try {
        const resp = await fetch('/api/dashboard/health');
        if (resp.ok) {
          const data = await resp.json();
          this.healthGrade = data.grade || 'F';
          this.purityScore = data.purity_score || 0;
          this.healthWarnings = data.warnings || [];
          this.healthRecommendations = data.recommendations || [];
          this._healthData = data;
        }
      } catch {}
    },

    // Brain management
    async switchBrain(name) {
      try {
        const resp = await fetch('/api/dashboard/brains/switch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ brain_name: name }),
        });
        if (resp.ok) {
          this.activeBrain = name;
          await this.loadStats();
          await this.loadHealth();
        }
      } catch {}
    },

    async exportBrain() {
      if (!this.activeBrain) return;
      try {
        const resp = await fetch(`/brain/${this.activeBrain}/export`);
        if (resp.ok) {
          const data = await resp.json();
          const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${this.activeBrain}-brain-export.json`;
          a.click();
          URL.revokeObjectURL(url);
        }
      } catch (err) {
        alert('Export failed: ' + err.message);
      }
    },

    async importBrain(event) {
      const file = event.target.files?.[0];
      if (!file || !this.activeBrain) return;

      try {
        const text = await file.text();
        const snapshot = JSON.parse(text);
        const resp = await fetch(`/brain/${this.activeBrain}/import`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(snapshot),
        });
        if (resp.ok) {
          await this.loadStats();
          await this.loadHealth();
          alert(NM_I18N.t('import_success'));
        }
      } catch (err) {
        alert('Import failed: ' + err.message);
      }
      // Reset file input
      event.target.value = '';
    },

    // Graph
    async reloadGraph() {
      const cy = await NM_GRAPH.reload();
      if (cy) {
        NM_GRAPH.onNodeClick((node) => { this.selectedNode = node; });
      }
    },

    // Health radar chart
    renderRadar() {
      const canvas = document.getElementById('health-radar');
      if (!canvas || !this._healthData) return;

      if (this._radarChart) {
        this._radarChart.destroy();
      }

      const d = this._healthData;
      this._radarChart = new Chart(canvas, {
        type: 'radar',
        data: {
          labels: [
            this.t('connectivity'),
            this.t('diversity'),
            this.t('freshness'),
            this.t('consolidation'),
            this.t('activation'),
            this.t('recall'),
            '1 - ' + this.t('orphan_rate'),
          ],
          datasets: [{
            label: this.t('brain_health'),
            data: [
              d.connectivity || 0,
              d.diversity || 0,
              d.freshness || 0,
              d.consolidation_ratio || 0,
              d.activation_efficiency || 0,
              d.recall_confidence || 0,
              1.0 - (d.orphan_rate || 0),
            ],
            backgroundColor: 'rgba(34, 197, 94, 0.15)',
            borderColor: '#22C55E',
            pointBackgroundColor: '#22C55E',
            pointBorderColor: '#F8FAFC',
            pointBorderWidth: 1,
            borderWidth: 2,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            r: {
              beginAtZero: true,
              max: 1,
              ticks: {
                stepSize: 0.25,
                color: '#94A3B8',
                backdropColor: 'transparent',
                font: { family: 'Fira Code', size: 10 },
              },
              grid: { color: '#334155' },
              angleLines: { color: '#334155' },
              pointLabels: {
                color: '#F8FAFC',
                font: { family: 'Fira Sans', size: 11 },
              },
            },
          },
          plugins: {
            legend: { display: false },
          },
        },
      });
    },

    // Utility
    gradeColor(grade) {
      const map = {
        A: 'text-nm-cta',
        B: 'text-nm-info',
        C: 'text-nm-warning',
        D: 'text-orange-500',
        F: 'text-nm-danger',
      };
      return map[grade] || 'text-nm-muted';
    },
  };
}

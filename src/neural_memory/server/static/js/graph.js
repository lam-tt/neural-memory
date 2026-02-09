/**
 * NeuralMemory Dashboard — Cytoscape.js graph module
 * Neural graph visualization with COSE layout.
 */

const NM_GRAPH = {
  _cy: null,

  TYPE_COLORS: {
    concept: '#e94560',
    entity: '#4ecdc4',
    time: '#ffe66d',
    action: '#95e1d3',
    state: '#f38181',
    spatial: '#45b7d1',
    sensory: '#96ceb4',
    intent: '#dda0dd',
    default: '#aa96da',
  },

  async init(containerId) {
    const data = await this.fetchData();
    if (!data) return null;

    const elements = this.buildElements(data);

    this._cy = cytoscape({
      container: document.getElementById(containerId),
      elements: elements,
      minZoom: 0.1,
      maxZoom: 5,
      wheelSensitivity: 0.3,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'width': 'data(size)',
            'height': 'data(size)',
            'font-size': '10px',
            'font-family': 'Fira Code, monospace',
            'color': '#F8FAFC',
            'text-outline-color': '#0F172A',
            'text-outline-width': 2,
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 6,
            'text-max-width': '80px',
            'text-wrap': 'ellipsis',
            'border-width': 2,
            'border-color': 'data(borderColor)',
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 3,
            'border-color': '#F8FAFC',
            'overlay-opacity': 0.1,
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 'data(weight)',
            'line-color': '#475569',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'data(arrowShape)',
            'curve-style': 'bezier',
            'opacity': 0.6,
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#22C55E',
            'target-arrow-color': '#22C55E',
            'opacity': 1,
          }
        }
      ],
      layout: {
        name: 'cose',
        animate: false,
        nodeOverlap: 20,
        idealEdgeLength: 80,
        edgeElasticity: 100,
        nestingFactor: 1.2,
        gravity: 0.25,
        numIter: 1000,
        randomize: true,
        componentSpacing: 100,
        nodeDimensionsIncludeLabels: true,
      }
    });

    return this._cy;
  },

  async fetchData() {
    try {
      const resp = await fetch('/api/graph');
      if (!resp.ok) return null;
      return await resp.json();
    } catch {
      return null;
    }
  },

  buildElements(data) {
    const nodes = (data.neurons || []).map(n => {
      const color = this.TYPE_COLORS[n.type] || this.TYPE_COLORS.default;
      return {
        data: {
          id: n.id,
          label: this.truncate(n.content, 30),
          color: color,
          borderColor: color,
          size: 20,
          type: n.type,
          content: n.content,
          metadata: n.metadata,
        }
      };
    });

    const edges = (data.synapses || []).map(s => {
      const weight = Math.min(6, Math.max(1, (s.weight || 0.5) * 3));
      const arrowShape = s.direction === 'bidirectional' ? 'none' : 'triangle';
      return {
        data: {
          id: s.id,
          source: s.source_id,
          target: s.target_id,
          weight: weight,
          arrowShape: arrowShape,
          type: s.type,
        }
      };
    });

    return [...nodes, ...edges];
  },

  truncate(text, max) {
    if (!text) return '';
    return text.length > max ? text.slice(0, max) + '...' : text;
  },

  async reload() {
    if (this._cy) {
      this._cy.destroy();
      this._cy = null;
    }
    return await this.init('cy-graph');
  },

  onNodeClick(callback) {
    if (!this._cy) return;
    this._cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      callback({
        id: node.data('id'),
        type: node.data('type'),
        content: node.data('content'),
        metadata: node.data('metadata'),
      });
    });
  }
};

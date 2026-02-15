const BASE = '/api';

async function request(path, options = {}) {
  const headers = { ...options.headers };
  // Only add JSON content type if it's not FormData and not already set
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 204) return null;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const message = typeof err.detail === 'string'
      ? err.detail
      : JSON.stringify(err.detail) || 'Request failed';
    throw new Error(message);
  }
  return res.json();
}

const api = {
  // Generic
  get: (url) => request(url),
  post: (url, data) => request(url, { method: 'POST', body: JSON.stringify(data) }),

  // Resources
  getResources: () => request('/resources/'),
  createResource: (data) => request('/resources/', { method: 'POST', body: JSON.stringify(data) }),
  updateResource: (id, data) => request(`/resources/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteResource: (id) => request(`/resources/${id}`, { method: 'DELETE' }),
  deleteAllResources: () => request('/resources/', { method: 'DELETE' }),
  generateTimeSlots: (id, data) => request(`/resources/${id}/timeslots/generate`, { method: 'POST', body: JSON.stringify(data) }),
  getTimeSlots: (id, status) => request(`/resources/${id}/timeslots${status ? `?status=${status}` : ''}`),

  // Agents
  getAgents: () => request('/agents/'),
  getAgent: (id) => request(`/agents/${id}`),
  createAgent: (data) => request('/agents/', { method: 'POST', body: JSON.stringify(data) }),
  getAgentBookings: (id) => request(`/agents/${id}/bookings`),
  getAgentTransactions: (id) => request(`/agents/${id}/transactions`),
  getAgentLimitOrders: (id) => request(`/agents/${id}/limit-orders`),
  updateAgent: (id, data) => request(`/agents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Auctions
  getAuctions: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/auctions/${qs ? `?${qs}` : ''}`);
  },
  getAuction: (id) => request(`/auctions/${id}`),
  createAuction: (data) => request('/auctions/', { method: 'POST', body: JSON.stringify(data) }),
  startAuction: (id) => request(`/auctions/${id}/start`, { method: 'POST' }),
  tickAuction: (id) => request(`/auctions/${id}/tick`, { method: 'POST' }),
  placeBid: (id, data) => request(`/auctions/${id}/bid`, { method: 'POST', body: JSON.stringify(data) }),
  getPriceHistory: (id) => request(`/auctions/${id}/price-history`),

  // Limit Orders
  createLimitOrder: (auctionId, data) => request(`/auctions/${auctionId}/limit-order`, { method: 'POST', body: JSON.stringify(data) }),
  cancelLimitOrder: (id) => request(`/auctions/limit-orders/${id}`, { method: 'DELETE' }),

  // Market
  getMarketState: () => request('/market/state'),
  getMarketPriceHistory: (limit = 100) => request(`/market/price-history?limit=${limit}`),
  getResourceSchedule: (id) => request(`/market/resources/${id}/schedule`),
  getResourcePriceHistory: (id) => request(`/resources/${id}/price-history`),

  // Admin
  getConfig: () => request('/admin/config'),
  updateConfig: (data) => request('/admin/config', { method: 'PUT', body: JSON.stringify(data) }),

  // Simulation
  runRound: () => request('/simulation/round', { method: 'POST' }),
  allocateTokens: () => request('/simulation/allocate-tokens', { method: 'POST' }),
  resetSimulation: () => request('/simulation/reset', { method: 'POST' }),
  getSimulationResults: () => request('/simulation/results'),

  // History & Analysis
  analyzeHistory: (formData) => request('/history/analyze', { method: 'POST', body: formData }), // let browser set content-type for multipart
  runMarketSimulation: (config) => request('/history/simulate', { method: 'POST', body: JSON.stringify(config) }),
  optimizePrice: (config) => request('/history/optimize', { method: 'POST', body: JSON.stringify(config) }),

  // Time Controls
  advanceDay: () => request('/simulation/time/advance-day', { method: 'POST' }),
  advanceHour: () => request('/simulation/time/advance-hour', { method: 'POST' }),
  resetTime: () => request('/simulation/time/reset', { method: 'POST' }),

  // Admin Resources
  importResources: (formData) => request('/admin/import-resources', { method: 'POST', body: formData }),
  resetAndLoadDefaults: () => request('/admin/reset-and-load-defaults', { method: 'POST' }),

  // God Mode (ML Models)
  autoPopulateMarket: (data) => request('/god/auto-populate', { method: 'POST', body: JSON.stringify(data) }),

  // PettingZoo Simulation
  runPZGridSearch: (data) => request('/pz-simulation/run', { method: 'POST', body: JSON.stringify(data) }),
  getPZStatus: (jobId) => request(`/pz-simulation/status/${jobId}`),
  runPZSingle: (data) => request('/pz-simulation/single', { method: 'POST', body: JSON.stringify(data) }),
  applyPZBest: (data) => request('/pz-simulation/apply-best', { method: 'POST', body: JSON.stringify(data) }),
};

export default api;

const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (res.status === 204) return null;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

const api = {
  // Resources
  getResources: () => request('/resources/'),
  createResource: (data) => request('/resources/', { method: 'POST', body: JSON.stringify(data) }),
  updateResource: (id, data) => request(`/resources/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteResource: (id) => request(`/resources/${id}`, { method: 'DELETE' }),
  generateTimeSlots: (id, data) => request(`/resources/${id}/timeslots/generate`, { method: 'POST', body: JSON.stringify(data) }),
  getTimeSlots: (id, status) => request(`/resources/${id}/timeslots${status ? `?status=${status}` : ''}`),

  // Agents
  getAgents: () => request('/agents/'),
  getAgent: (id) => request(`/agents/${id}`),
  createAgent: (data) => request('/agents/', { method: 'POST', body: JSON.stringify(data) }),
  getAgentBookings: (id) => request(`/agents/${id}/bookings`),
  getAgentTransactions: (id) => request(`/agents/${id}/transactions`),
  getAgentLimitOrders: (id) => request(`/agents/${id}/limit-orders`),

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

  // Admin
  getConfig: () => request('/admin/config'),
  updateConfig: (data) => request('/admin/config', { method: 'PUT', body: JSON.stringify(data) }),

  // Simulation
  runRound: () => request('/simulation/round', { method: 'POST' }),
  allocateTokens: () => request('/simulation/allocate-tokens', { method: 'POST' }),
  resetSimulation: () => request('/simulation/reset', { method: 'POST' }),
  getSimulationResults: () => request('/simulation/results'),
};

export default api;

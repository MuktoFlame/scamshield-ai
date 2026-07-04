const BASE = import.meta.env.VITE_API_URL || ''

export function getToken() {
  return localStorage.getItem('token')
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (auth && token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  let data = null
  try {
    data = await res.json()
  } catch {
    /* non-JSON error body */
  }
  if (!res.ok) {
    const message = data?.detail || `Request failed (${res.status})`
    throw new Error(typeof message === 'string' ? message : 'Request failed')
  }
  return data
}

export const api = {
  register: (body) => request('/api/auth/register', { method: 'POST', body, auth: false }),
  login: (body) => request('/api/auth/login', { method: 'POST', body, auth: false }),
  scan: (body) => request('/api/scan', { method: 'POST', body }),
  scanImage: (body) => request('/api/scan/image', { method: 'POST', body }),
  checkUrl: (body) => request('/api/check/url', { method: 'POST', body }),
  checkNews: (body) => request('/api/check/news', { method: 'POST', body }),
  checkProduct: (body) => request('/api/check/product', { method: 'POST', body }),
  history: () => request('/api/history'),
  linkedHistory: (seniorId) => request(`/api/history/${seniorId}`),
  createLinkCode: () => request('/api/caregiver/code', { method: 'POST' }),
  redeemLinkCode: (code) => request('/api/caregiver/link', { method: 'POST', body: { code } }),
  myLinks: () => request('/api/caregiver/links'),
  unlink: (otherId) => request(`/api/caregiver/link/${otherId}`, { method: 'DELETE' }),
  patterns: () => request('/api/patterns', { auth: false }),
  modelInfo: () => request('/api/model/info', { auth: false }),
}

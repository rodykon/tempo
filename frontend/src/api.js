const BASE = '/api';

export function getToken() {
  return localStorage.getItem('access_token');
}

export function setToken(token) {
  localStorage.setItem('access_token', token);
}

export function clearToken() {
  localStorage.removeItem('access_token');
}

async function request(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body != null ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    clearToken();
    window.location.href = '/login';
    return null;
  }

  if (res.status === 204) return null;

  const data = await res.json();
  if (!res.ok) throw data;
  return data;
}

export const api = {
  login:         (username, password) => request('POST', '/auth/token/', { username, password }),
  getHabits:     ()         => request('GET',    '/habits/'),
  createHabit:   (data)     => request('POST',   '/habits/', data),
  updateHabit:   (id, data) => request('PATCH',  `/habits/${id}/`, data),
  deleteHabit:   (id)       => request('DELETE', `/habits/${id}/`),
  getTimings:    ()         => request('GET',    '/timing/'),
  getTiming:     (id)       => request('GET',    `/timing/${id}/`),
  updateTiming:  (id, data) => request('PUT',    `/timing/${id}/`, data),
};

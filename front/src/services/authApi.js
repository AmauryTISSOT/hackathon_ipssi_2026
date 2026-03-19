const API_URL = import.meta.env.VITE_API_URL;
const TOKEN_KEY = "auth_token";
const CURRENT_USER_KEY = "auth_user";

function normalizeUser(payload) {
  if (!payload) return null;

  const id = payload.id;
  const fullName = payload.fullName;
  const email = payload.email;
  const role = payload.role;

  return {
    id,
    fullName,
    email,
    role
  };
}

function setSession({ token, user }) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
}

async function request(path, { method = "GET", body, token } = {}) {
  const headers = {
    "Content-Type": "application/json"
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const options = {
    method,
    headers
  };

  if (body !== undefined) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_URL}${path}`, options);

  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.message);
  }

  return data;
}

export async function register({ fullName, email, password, role }) {
  return request("/api/auth/register", {
    method: "POST",
    body: {
      fullName,
      email,
      password,
      role
    }
  });
}

export async function login({ email, password }) {
  const response = await request("/api/auth/login", {
    method: "POST",
    body: { email, password }
  });

  const token = response.token;
  const userPayload = response.user;
  const user = normalizeUser(userPayload);

  if (token && user) {
    setSession({ token, user });
  }

  response.user = user;
  return response;
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(CURRENT_USER_KEY);
}

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function isAuthenticated() {
  const token = getAuthToken();
  const user = getCurrentUser();
  return Boolean(token && user && user.role);
}

export function getCurrentUser() {
  const rawUser = localStorage.getItem(CURRENT_USER_KEY);
  if (!rawUser) {
    return null;
  }

  try {
    return JSON.parse(rawUser);
  } catch {
    return null;
  }
}

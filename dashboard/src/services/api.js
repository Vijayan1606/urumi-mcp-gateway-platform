const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, apiKey, options = {}) {
  if (!apiKey) {
    throw new Error("Enter your gateway API key first.");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.detail || `Request failed with status ${response.status}`,
    );
  }

  return data;
}

export function getServers(apiKey) {
  return request("/servers", apiKey);
}

export function getUpstreamHealth(apiKey) {
  return request("/admin/upstream-health", apiKey);
}

export function getTools(apiKey) {
  return request("/tools", apiKey);
}

export function getAuditLogs(apiKey) {
  return request("/admin/audit-logs", apiKey);
}

export function updateServerStatus(apiKey, serverName, enabled) {
  return request(
    `/admin/upstreams/${encodeURIComponent(serverName)}/enabled`,
    apiKey,
    {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    },
  );
}

export function getUsers(apiKey) {
  return request("/admin/users", apiKey);
}

export function createUser(apiKey, email) {
  return request("/admin/users", apiKey, {
    method: "POST",
    body: JSON.stringify({ email, role: "member" }),
  });
}

export function getApiKeys(apiKey) {
  return request("/keys", apiKey);
}

export function createApiKey(apiKey, name, userId) {
  const body = { name };

  if (userId !== undefined && userId !== null) {
    body.user_id = Number(userId);
  }

  return request("/keys", apiKey, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function revokeApiKey(apiKey, keyId) {
  return request(`/keys/${encodeURIComponent(keyId)}/revoke`, apiKey, {
    method: "POST",
  });
}
export async function sendChatMessage(apiKey, message) {
  return request("/chat", apiKey, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

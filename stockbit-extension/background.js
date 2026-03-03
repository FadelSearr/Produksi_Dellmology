// The backend endpoint where the token will be sent.
const UPDATE_TOKEN_ENDPOINT = 'http://localhost:3000/api/update-token';
const TOKEN_STATE_KEY = 'dellmology_token_state';
const HEARTBEAT_ALARM = 'dellmology_token_heartbeat';
const HEARTBEAT_INTERVAL_MINUTES = 5;
const HEARTBEAT_MIN_INTERVAL_MS = 60 * 1000;
const PRE_EXPIRY_WINDOW_MS = 15 * 60 * 1000;

console.log('Dellmology Auth Helper: Service worker starting...');
console.log('Target API URL:', UPDATE_TOKEN_ENDPOINT);

let lastSyncedToken = null;
let lastSyncAtMs = 0;
let latestToken = null;
let latestExpiryMs = 0;

/**
 * Decodes a JWT token to extract its payload, including the expiration time.
 * @param {string} token The JWT token.
 * @returns {object|null} The decoded payload or null if decoding fails.
 */
function decodeJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error('Dellmology Auth Helper: Failed to decode JWT', e);
    return null;
  }
}

function persistTokenState(token, expiresAtSeconds) {
  const expiresAtMs = expiresAtSeconds ? expiresAtSeconds * 1000 : 0;
  latestToken = token;
  latestExpiryMs = expiresAtMs;

  chrome.storage.local.set(
    {
      [TOKEN_STATE_KEY]: {
        token,
        expires_at_ms: expiresAtMs,
        last_sync_at_ms: lastSyncAtMs,
      },
    },
    () => {
      if (chrome.runtime.lastError) {
        console.error('Dellmology Auth Helper: Failed to persist token state', chrome.runtime.lastError);
      }
    }
  );
}

function loadTokenState() {
  return new Promise((resolve) => {
    chrome.storage.local.get([TOKEN_STATE_KEY], (result) => {
      if (chrome.runtime.lastError) {
        console.error('Dellmology Auth Helper: Failed to read token state', chrome.runtime.lastError);
        resolve(null);
        return;
      }

      const state = result[TOKEN_STATE_KEY] || null;
      resolve(state);
    });
  });
}

function isTokenUsable(token, expiryMs) {
  if (!token || !expiryMs) {
    return false;
  }

  return Date.now() < expiryMs;
}

function shouldHeartbeat(token, expiryMs) {
  if (!isTokenUsable(token, expiryMs)) {
    return false;
  }

  if (token !== lastSyncedToken) {
    return true;
  }

  return Date.now() - lastSyncAtMs >= HEARTBEAT_MIN_INTERVAL_MS;
}

function scheduleHeartbeatAlarm() {
  chrome.alarms.create(HEARTBEAT_ALARM, {
    periodInMinutes: HEARTBEAT_INTERVAL_MINUTES,
    delayInMinutes: 0.2,
  });
}

/**
 * Sends the captured token to the Dellmology backend.
 * @param {string} token The bearer token.
 * @param {number} expiresAt The expiration timestamp (seconds).
 */
function sendTokenToBackend(token, expiresAt) {
  const expires_at = expiresAt ? new Date(expiresAt * 1000).toISOString() : null;

  const payload = {
    token: token,
    expires_at: expires_at,
  };

  fetch(UPDATE_TOKEN_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
    .then((response) => {
      if (response.ok) {
        console.log('Dellmology Auth Helper: Token successfully synced to backend.');
        lastSyncedToken = token; // Update cache on success
        lastSyncAtMs = Date.now();
        persistTokenState(token, expiresAt);
      } else {
        console.error('Dellmology Auth Helper: Failed to sync token. Status:', response.status);
      }
    })
    .catch((error) => {
      console.error('Dellmology Auth Helper: Error syncing token:', error);
    });
}

async function heartbeatTokenSync() {
  const state = await loadTokenState();
  if (!state || !state.token) {
    return;
  }

  latestToken = state.token;
  latestExpiryMs = state.expires_at_ms || 0;
  lastSyncAtMs = state.last_sync_at_ms || lastSyncAtMs;

  if (!isTokenUsable(latestToken, latestExpiryMs)) {
    console.warn('Dellmology Auth Helper: Stored token is expired. Waiting for a fresh token capture.');
    return;
  }

  const msToExpiry = latestExpiryMs - Date.now();
  if (msToExpiry <= PRE_EXPIRY_WINDOW_MS) {
    console.warn('Dellmology Auth Helper: Token nearing expiry. Keep Stockbit active to allow automatic refresh capture.');
  }

  if (!shouldHeartbeat(latestToken, latestExpiryMs)) {
    return;
  }

  sendTokenToBackend(latestToken, Math.floor(latestExpiryMs / 1000));
}

chrome.runtime.onInstalled.addListener(() => {
  scheduleHeartbeatAlarm();
});

chrome.runtime.onStartup.addListener(async () => {
  scheduleHeartbeatAlarm();
  await heartbeatTokenSync();
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === HEARTBEAT_ALARM) {
    heartbeatTokenSync();
  }
});

console.log('Registering webRequest listener...');

chrome.webRequest.onBeforeSendHeaders.addListener(
  (details) => {
    console.log('Dellmology Auth Helper: Checking request:', details.url);

    // Find the 'Authorization' header in the request.
    const authHeader = details.requestHeaders.find(
      (header) => header.name.toLowerCase() === 'authorization'
    );

    if (authHeader && authHeader.value && authHeader.value.startsWith('Bearer ')) {
      // Extract the token string by removing "Bearer ".
      const token = authHeader.value.substring(7);

      // Only sync if the token has changed to avoid spamming the API
      if (token !== lastSyncedToken) {
        console.log('Dellmology Auth Helper: New token candidate detected...');

        const decoded = decodeJwt(token);

        // Only sync if it's a valid JWT (must have a payload with an expiry)
        if (!decoded || !decoded.exp) {
          console.log('Dellmology Auth Helper: Skipping non-JWT or invalid token.');
          return;
        }

        console.log('Dellmology Auth Helper: Valid JWT detected from:', details.url);
        console.log('Dellmology Auth Helper: Token expiry:', new Date(decoded.exp * 1000));
        persistTokenState(token, decoded.exp);
        sendTokenToBackend(token, decoded.exp);
      }
    }
  },
  // Filter for requests to Stockbit API endpoints.
  { urls: ['https://*.stockbit.com/*'] },
  // We need 'requestHeaders' and 'extraHeaders' to read the headers.
  ['requestHeaders', 'extraHeaders']
);

scheduleHeartbeatAlarm();
heartbeatTokenSync();

console.log('Dellmology Auth Helper: Service worker started.');

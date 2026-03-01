console.log("Stockbit Token Syncer: Background script starting...");

// Configuration: This URL should point to your backend endpoint for updating the token.
const APP_API_URL = "http://localhost:3000/api/update-token";

console.log("Target API URL:", APP_API_URL);

let lastSyncedToken = null;

// Helper to decode JWT payload
function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
  } catch (e) {
    console.warn("Failed to parse JWT. It might be an opaque token.", e);
    return null;
  }
}

chrome.webRequest.onBeforeSendHeaders.addListener(
  (details) => {
    // Look for the Authorization header
    const authHeader = details.requestHeaders.find(
      (header) => header.name.toLowerCase() === "authorization"
    );

    if (authHeader && authHeader.value && authHeader.value.startsWith("Bearer ")) {
      const token = authHeader.value.substring(7); // Remove "Bearer " prefix

      // Only sync if the token has changed to avoid spamming the API
      if (token !== lastSyncedToken) {
        console.log("New token candidate detected from:", details.url);
        
        const decoded = parseJwt(token);
        
        // Ensure it's a valid JWT with an expiry date before syncing
        if (!decoded || !decoded.exp) {
          console.log("Skipping non-JWT or invalid token.");
          return;
        }

        const expiresAt = decoded.exp;
        
        console.log("Valid JWT detected. Expiry:", new Date(expiresAt * 1000));
        
        syncToken(token, expiresAt);
      }
    }
  },
  { urls: ["https://*.stockbit.com/*"] },
  ["requestHeaders"]
);

function syncToken(token, expiresAt) {
  const payload = {
    token: token,
    expires_at: expiresAt
  };

  fetch(APP_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })
    .then((response) => {
      if (response.ok) {
        console.log("Token successfully synced to API.");
        lastSyncedToken = token; // Update cache only on success
      } else {
        response.text().then(text => {
          console.error("Failed to sync token. Status:", response.status, "Response:", text);
        });
      }
    })
    .catch((error) => {
      console.error("Error syncing token:", error);
    });
}

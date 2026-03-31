/**
 * Authentication utility functions for token management.
 *
 * This module provides functions for storing, retrieving, and refreshing
 * JWT access and refresh tokens.
 */

const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

/**
 * Get the stored access token.
 */
export function getAccessToken(): string {
  return localStorage.getItem(ACCESS_TOKEN_KEY) || "";
}

/**
 * Get the stored refresh token.
 */
export function getRefreshToken(): string {
  return localStorage.getItem(REFRESH_TOKEN_KEY) || "";
}

/**
 * Store both access and refresh tokens.
 */
export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

/**
 * Clear all stored tokens (used during logout).
 */
export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Check if the user has an access token stored.
 */
export function hasAccessToken(): boolean {
  return localStorage.getItem(ACCESS_TOKEN_KEY) !== null;
}

/**
 * Check if the user has a refresh token stored.
 */
export function hasRefreshToken(): boolean {
  return localStorage.getItem(REFRESH_TOKEN_KEY) !== null;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * Attempt to refresh the access token using the stored refresh token.
 *
 * This function makes a direct fetch call to the refresh endpoint to avoid
 * triggering the axios interceptor recursively.
 *
 * @returns The new access token if successful, null if refresh failed
 */
export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    return null;
  }

  try {
    const baseUrl = import.meta.env.VITE_API_URL || "";
    const response = await fetch(`${baseUrl}/api/v1/login/refresh-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      // Refresh token is invalid or expired
      clearTokens();
      return null;
    }

    const data: TokenResponse = await response.json();
    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch (error) {
    console.error("Failed to refresh access token:", error);
    clearTokens();
    return null;
  }
}

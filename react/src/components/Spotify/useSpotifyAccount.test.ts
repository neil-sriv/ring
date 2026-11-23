import { AxiosError, type AxiosResponse } from "axios"
import { describe, expect, it } from "vitest"

import { isAxiosTimeout, spotifyErrorMessage } from "./useSpotifyAccount"

describe("spotifyErrorMessage", () => {
  it("names axios timeouts", () => {
    const err = new AxiosError(
      "timeout of 20000ms exceeded",
      AxiosError.ECONNABORTED,
    )
    expect(isAxiosTimeout(err)).toBe(true)
    expect(spotifyErrorMessage(err)).toBe(
      "Spotify request timed out. Please try again.",
    )
  })

  it("formats API detail strings", () => {
    const err = new AxiosError("Request failed with status code 500")
    err.response = {
      data: { detail: "spotify down" },
      status: 500,
      statusText: "Internal Server Error",
      headers: {},
      config: {},
    } as AxiosResponse
    expect(isAxiosTimeout(err)).toBe(false)
    expect(spotifyErrorMessage(err)).toBe("spotify down")
  })

  it("falls back when there is no response body", () => {
    const err = new AxiosError("Network Error", AxiosError.ERR_NETWORK)
    expect(spotifyErrorMessage(err)).toBe(
      "Something went wrong. Please try again.",
    )
  })
})

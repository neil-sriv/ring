import { Button } from "@/components/ui/button"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { ExternalLink } from "lucide-react"
import { useEffect, useRef } from "react"

import type { SpotifyPlaylistResponse } from "@/client"
import {
  ensureGroupSpotifyPlaylistSpotifyGroupsGroupApiIdPlaylistPostMutation,
  readGroupSpotifyPlaylistSpotifyGroupsGroupApiIdPlaylistGetOptions,
  readGroupSpotifyPlaylistSpotifyGroupsGroupApiIdPlaylistGetQueryKey,
} from "@/client/@tanstack/react-query.gen"
import useCustomToast from "@/hooks/useCustomToast"
import { formatApiErrorDetail } from "@/util/misc"
import {
  axiosDetail,
  axiosStatus,
  useSpotifyAccount,
} from "./useSpotifyAccount"

interface GroupSpotifyPlaylistProps {
  groupId: string
  groupName: string
  offset?: number
  limit?: number
  spotify?: string
  spotifyAction?: string
  spotifyError?: string
}

function unavailableMessage() {
  return (
    <p className="text-sm text-muted-foreground">
      Spotify linking is unavailable. This server has no Spotify app configured.
    </p>
  )
}

export function GroupSpotifyPlaylist({
  groupId,
  groupName,
  offset,
  limit,
  spotify,
  spotifyAction,
  spotifyError,
}: GroupSpotifyPlaylistProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const showToast = useCustomToast()
  const { statusQuery, startLink, isStartingLink } = useSpotifyAccount()
  const handledReturn = useRef(false)
  const linked = Boolean(statusQuery.data?.linked)
  const configured = Boolean(statusQuery.data?.configured)
  const playlistQuery = useQuery({
    ...readGroupSpotifyPlaylistSpotifyGroupsGroupApiIdPlaylistGetOptions({
      path: { group_api_id: groupId },
    }),
    enabled: configured && linked,
    retry: false,
  })
  const ensure = useMutation({
    ...ensureGroupSpotifyPlaylistSpotifyGroupsGroupApiIdPlaylistPostMutation(),
    onSuccess: (data) => {
      queryClient.setQueryData(
        readGroupSpotifyPlaylistSpotifyGroupsGroupApiIdPlaylistGetQueryKey({
          path: { group_api_id: groupId },
        }),
        data,
      )
      showToast(
        "Spotify",
        "Playlist updated in your Spotify account.",
        "success",
      )
    },
    onError: (err) => {
      if (
        axiosStatus(err) === 409 &&
        axiosDetail(err) === "spotify_not_linked"
      ) {
        void startLink(returnTo(groupId))
        return
      }
      showToast("Spotify", formatApiErrorDetail(axiosDetail(err)), "error")
    },
  })

  useEffect(() => {
    if (handledReturn.current || !spotify) {
      return
    }
    handledReturn.current = true
    void navigate({
      to: "/groups/$groupId/loops",
      params: { groupId },
      search: { offset, limit },
      replace: true,
    })
    if (spotify === "error") {
      showToast(
        "Spotify",
        spotifyError === "access_denied"
          ? "Spotify linking was canceled."
          : "Spotify linking failed.",
        "error",
      )
      return
    }
    if (spotify === "linked" && spotifyAction === "playlist") {
      ensure.mutate({ path: { group_api_id: groupId } })
    }
  }, [
    ensure,
    groupId,
    limit,
    navigate,
    offset,
    showToast,
    spotify,
    spotifyAction,
    spotifyError,
  ])

  if (statusQuery.isLoading) {
    return null
  }
  if (!configured) {
    return unavailableMessage()
  }

  const playlist =
    ensure.data ?? (playlistQuery.data as SpotifyPlaylistResponse | undefined)
  const missingPlaylist =
    axiosStatus(playlistQuery.error) === 404 ||
    axiosDetail(playlistQuery.error) === "no_spotify_playlist"
  const pending = isStartingLink || ensure.isPending

  function syncOrLink() {
    if (!linked) {
      void startLink(returnTo(groupId))
      return
    }
    ensure.mutate({ path: { group_api_id: groupId } })
  }

  return (
    <div className="mt-3 flex flex-col items-start gap-2">
      {playlist ? (
        <a
          href={playlist.playlist_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-sm font-medium text-primary underline-offset-4 hover:underline"
        >
          {groupName} on Spotify
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      ) : null}
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={pending}
        onClick={syncOrLink}
      >
        {playlist
          ? "Update Spotify playlist"
          : "Add this group's songs to your Spotify"}
      </Button>
      {playlistQuery.isError && !missingPlaylist && !playlist ? (
        <p className="text-sm text-destructive">
          Couldn't load the Spotify playlist.
        </p>
      ) : null}
    </div>
  )
}

function returnTo(groupId: string) {
  return `/groups/${groupId}/loops?spotify_action=playlist`
}

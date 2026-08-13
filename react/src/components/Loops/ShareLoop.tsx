import { useMutation } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { Check, Copy, Loader2 } from "lucide-react"
import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import type {
  CreateShortLinkLinksShortLinkPostError,
  ShortLink,
} from "../../client"
import { createShortLinkLinksShortLinkPostMutation } from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

interface ShareLoopProps {
  isOpen: boolean
  onClose: () => void
  loopApiId: string
  isDraft: boolean
}

function shareUrlFor(shortLink: ShortLink): string {
  return `${window.location.origin}${shortLink.path}`
}

const ShareLoop = ({ isOpen, onClose, loopApiId, isDraft }: ShareLoopProps) => {
  const showToast = useCustomToast()
  const [shortLink, setShortLink] = useState<ShortLink | null>(null)
  const [hasCopied, setHasCopied] = useState(false)

  const { mutate: createShortLink } = useMutation({
    ...createShortLinkLinksShortLinkPostMutation(),
    onSuccess: (data) => {
      setShortLink(data)
    },
    onError: (err: AxiosError<CreateShortLinkLinksShortLinkPostError>) => {
      showToast(
        "Could not create a share link.",
        formatApiErrorDetail(err.response?.data?.detail),
        "error",
      )
      onClose()
    },
  })

  // Minting is idempotent per loop, so opening the dialog repeatedly returns the
  // same link rather than creating a new one.
  useEffect(() => {
    if (!isOpen) {
      setShortLink(null)
      setHasCopied(false)
      return
    }
    createShortLink({ body: { target_api_id: loopApiId } })
  }, [isOpen, loopApiId, createShortLink])

  const handleCopy = async () => {
    if (!shortLink) {
      return
    }
    const url = shareUrlFor(shortLink)
    try {
      await navigator.clipboard.writeText(url)
      setHasCopied(true)
      showToast(
        "Link copied.",
        "The share link is on your clipboard.",
        "success",
      )
    } catch {
      showToast(
        "Could not copy automatically.",
        "Select the link and copy it manually.",
        "error",
      )
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="backdrop-blur-md bg-white/80 border border-white/20 dark:bg-gray-900/80 dark:border-gray-700/50 sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-foreground">Share this loop</DialogTitle>
          <DialogDescription>
            {isDraft
              ? "Anyone in this group can open the draft with this link."
              : "Anyone in this group can open this issue with this link."}
          </DialogDescription>
        </DialogHeader>

        <div className="pb-6 pt-4">
          {shortLink ? (
            <div className="flex items-center gap-2">
              <Input
                readOnly
                value={shareUrlFor(shortLink)}
                onFocus={(event) => event.currentTarget.select()}
                className="bg-white/50 border-white/20 dark:bg-gray-900/50 dark:border-gray-700/50"
              />
              <Button type="button" onClick={handleCopy} className="shrink-0">
                {hasCopied ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
                {hasCopied ? "Copied" : "Copy"}
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Creating link...
            </div>
          )}
        </div>

        <DialogFooter>
          <Button type="button" onClick={onClose} variant="outline">
            Done
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ShareLoop

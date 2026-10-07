/**
 * Preview copy for the app paths people paste into chat.
 *
 * Slack, iMessage, Facebook, and Twitter build a preview from the Open Graph
 * tags in the first HTML response and never run JavaScript. The copy is
 * static on purpose: a preview renders for everyone who can see the channel
 * the link was pasted into, so a card never names a group, letter, notebook,
 * or person, and it never includes a letter body.
 */

export interface UnfurlCard {
  title: string
  description: string
}

export const SITE_NAME = "Ring"
export const OG_IMAGE_PATH = "/assets/images/og-card.png"
export const OG_IMAGE_WIDTH = 1200
export const OG_IMAGE_HEIGHT = 630
export const OG_IMAGE_ALT = "The Ring logo"

export const SITE_CARD: UnfurlCard = {
  title: "Ring",
  description:
    "Ring asks your group the same few questions on a cadence, then collects everyone's answers into one newsletter.",
}

interface PrefixedCard {
  prefix: string
  card: UnfurlCard
}

// First matching prefix wins. These prefixes do not overlap.
const CARDS_BY_PREFIX: readonly PrefixedCard[] = [
  {
    prefix: "loops",
    card: {
      title: "A newsletter on Ring",
      description:
        "Sign in to read this newsletter and everyone else's answers.",
    },
  },
  {
    prefix: "register",
    card: {
      title: "Your invitation to Ring",
      description:
        "Open this invitation to join the group and answer its first questions.",
    },
  },
  {
    prefix: "documents",
    card: {
      title: "A notebook on Ring",
      description: "Sign in to write in this notebook with your group.",
    },
  },
  {
    prefix: "groups",
    card: {
      title: "A group on Ring",
      description:
        "Sign in to see this group's questions, answers, and newsletters.",
    },
  },
]

export function cardForPath(pathname: string): UnfurlCard {
  const normalized = decodePath(pathname)
    .replace(/^\/+|\/+$/g, "")
    .toLowerCase()
  for (const { prefix, card } of CARDS_BY_PREFIX) {
    if (normalized === prefix || normalized.startsWith(`${prefix}/`)) {
      return card
    }
  }
  return SITE_CARD
}

function decodePath(pathname: string): string {
  try {
    return decodeURIComponent(pathname)
  } catch {
    return pathname
  }
}

export function inboxDestination(href: string) {
  const loop = /^\/loops\/([^/]+)$/.exec(href)
  if (loop) {
    return {
      to: "/loops/$loopId" as const,
      params: { loopId: loop[1] },
    }
  }
  const group = /^\/groups\/([^/]+)\/loops$/.exec(href)
  if (group) {
    return {
      to: "/groups/$groupId/loops" as const,
      params: { groupId: group[1] },
    }
  }
  const document = /^\/documents\/([^/]+)$/.exec(href)
  if (document) {
    return {
      to: "/documents/$documentId" as const,
      params: { documentId: document[1] },
    }
  }
  return { to: "/" as const }
}

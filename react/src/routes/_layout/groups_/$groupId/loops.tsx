import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { Suspense, useEffect, useState } from "react"
import {
  listLettersLettersLettersGetOptions,
  readGroupPartiesGroupGroupApiIdGetOptions,
} from "../../../../client/@tanstack/react-query.gen"
import { DocumentsGrid } from "../../../../components/Document/DocumentsGrid"
import { GroupKeyValuesTable } from "../../../../components/GroupKeyValues/GroupKeyValuesTable"
import { LLMPlayground } from "../../../../components/LLMPlayground/LLMPlayground"
import { AdhocLoopsTab } from "../../../../components/Loops/AdhocLoopsTab"
import { LoopsTab } from "../../../../components/Loops/LoopsTab"
import { useGroupKeyValues } from "../../../../hooks/useGroupKeyValues"

type LoopsSearchParams = {
  offset?: number
  limit?: number
}

export const Route = createFileRoute("/_layout/groups/$groupId/loops")({
  validateSearch: (search: Record<string, string>): LoopsSearchParams => {
    return {
      offset: Number.parseInt(search.offset) || undefined,
      limit: Number.parseInt(search.limit) || undefined,
    }
  },
  component: LoopsContent,
})

function LoopsContentLoader() {
  const groupId = Route.useParams().groupId
  const { offset, limit } = Route.useSearch()

  const { data: loops } = useSuspenseQuery({
    ...listLettersLettersLettersGetOptions({
      query: {
        group_api_id: groupId,
        skip: offset,
        limit: limit,
      },
    }),
  })

  const { data: group } = useSuspenseQuery({
    ...readGroupPartiesGroupGroupApiIdGetOptions({
      path: { group_api_id: groupId },
    }),
  })

  const { data: keyValues } = useGroupKeyValues(groupId)

  const tabsConfig = [
    {
      title: "Loops",
      hash: "loops",
      component: () => (
        <LoopsTab
          loops={loops.filter((loop) => loop.letter_type === "CYCLIC")}
          group={group}
        />
      ),
    },
    {
      title: "Adhoc Loops",
      hash: "adhoc-loops",
      component: () => (
        <AdhocLoopsTab
          loops={loops.filter((loop) => loop.letter_type === "ADHOC")}
          group={group}
        />
      ),
    },
    {
      title: "Key Values",
      hash: "key-values",
      component: () => (
        <GroupKeyValuesTable
          keyValues={{
            key_values: keyValues?.key_values || {},
          }}
          groupApiId={groupId}
        />
      ),
    },
    {
      title: "LLM Playground",
      hash: "llm-playground",
      component: () => <LLMPlayground />,
    },
    {
      title: "Documents",
      hash: "documents",
      component: () => <DocumentsGrid groupApiId={groupId} />,
    },
  ]

  const getInitialTab = (): string => {
    if (typeof window !== "undefined") {
      const hash = window.location.hash.slice(1)
      if (tabsConfig.some((tab) => tab.hash === hash)) {
        return hash
      }
    }
    return "loops"
  }

  const [activeTab, setActiveTab] = useState(getInitialTab)

  const handleTabChange = (value: string) => {
    setActiveTab(value)
    window.location.hash = value
  }

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1)
      if (tabsConfig.some((tab) => tab.hash === hash)) {
        setActiveTab(hash)
      }
    }

    window.addEventListener("hashchange", handleHashChange)
    handleHashChange()

    return () => {
      window.removeEventListener("hashchange", handleHashChange)
    }
  }, [tabsConfig])

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 md:px-8">
      <h1 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">
        {group!.name}
      </h1>
      <div className="mt-6">
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="w-full">
            {tabsConfig.map((tab) => (
              <TabsTrigger key={tab.hash} value={tab.hash}>
                {tab.title}
              </TabsTrigger>
            ))}
          </TabsList>
          {tabsConfig.map((tab) => (
            <TabsContent key={tab.hash} value={tab.hash}>
              {tab.component()}
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  )
}

function LoopsContent() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <LoopsContentLoader />
    </Suspense>
  )
}

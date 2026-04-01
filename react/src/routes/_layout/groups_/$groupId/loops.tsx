import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { Suspense, useEffect, useMemo, useState } from "react"
import type { MinimalLetter } from "../../../../client"
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

type LoopsLoaderProps = {
  loops: MinimalLetter[]
}

export const Route = createFileRoute("/_layout/groups/$groupId/loops")({
  validateSearch: (search: Record<string, string>): LoopsSearchParams => {
    return {
      offset: Number.parseInt(search.offset) || undefined,
      limit: Number.parseInt(search.limit) || undefined,
    }
  },
  loaderDeps: ({ search: { offset, limit } }) => ({ offset, limit }),
  loader: async ({
    params,
    context,
    deps: { offset, limit },
  }): Promise<LoopsLoaderProps> => {
    const loops = await context.queryClient.ensureQueryData({
      ...listLettersLettersLettersGetOptions({
        query: {
          group_api_id: params.groupId,
          skip: offset,
          limit: limit,
        },
      }),
    })

    return {
      loops,
    }
  },
  component: LoopsContent,
})

function LoopsContentLoader() {
  const groupId = Route.useParams().groupId
  const props = Route.useLoaderData()

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
          loops={props.loops.filter((loop) => loop.letter_type === "CYCLIC")}
          group={group}
        />
      ),
    },
    {
      title: "Adhoc Loops",
      hash: "adhoc-loops",
      component: () => (
        <AdhocLoopsTab
          loops={props.loops.filter((loop) => loop.letter_type === "ADHOC")}
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

  void useMemo

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
    <div className="w-full">
      <div className="mb-6 rounded-xl border border-border/50 bg-background/80 p-6 shadow-md backdrop-blur-sm dark:border-border/30 dark:bg-background/60">
        <h2 className="text-center text-2xl font-semibold text-foreground md:text-left">
          {group!.name}
        </h2>
      </div>
      <div className="rounded-xl border border-border/50 bg-background/80 p-6 shadow-md backdrop-blur-sm dark:border-border/30 dark:bg-background/60">
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="flex-nowrap overflow-x-auto overflow-y-hidden">
            {tabsConfig.map((tab) => (
              <TabsTrigger
                key={tab.hash}
                value={tab.hash}
                className="shrink-0 transition-all duration-200 hover:-translate-y-0.5"
              >
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
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      }
    >
      <LoopsContentLoader />
    </Suspense>
  )
}

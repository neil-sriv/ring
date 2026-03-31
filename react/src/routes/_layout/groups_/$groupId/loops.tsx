import {
  Box,
  Container,
  Heading,
  Spinner,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  useColorModeValue,
} from "@chakra-ui/react"
import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
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
  const textColor = useColorModeValue("ui.dark", "ui.light")

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

  // Map hash fragments to tab indices (memoized for stability)
  const hashToIndex = useMemo(
    () => new Map(tabsConfig.map((tab, index) => [tab.hash, index])),
    [tabsConfig.length], // Only recreate if number of tabs changes
  )

  // Get initial tab index from hash fragment
  const getInitialTabIndex = (): number => {
    if (typeof window !== "undefined") {
      const hash = window.location.hash.slice(1) // Remove the '#' character
      const index = hashToIndex.get(hash)
      return index !== undefined ? index : 0
    }
    return 0
  }

  const [tabIndex, setTabIndex] = useState(getInitialTabIndex)

  // Update hash when tab changes
  const handleTabChange = (index: number) => {
    setTabIndex(index)
    const hash = tabsConfig[index]?.hash
    if (hash) {
      window.location.hash = hash
    }
  }

  // Listen for hash changes (e.g., browser back/forward)
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1)
      const index = hashToIndex.get(hash)
      if (index !== undefined) {
        setTabIndex(index)
      }
    }

    window.addEventListener("hashchange", handleHashChange)

    // Also check hash on mount in case it was set before component mounted
    handleHashChange()

    return () => {
      window.removeEventListener("hashchange", handleHashChange)
    }
  }, [hashToIndex])

  return (
    <Container maxW="full">
      <Box
        bg="ui.glass.light.background"
        backdropFilter="blur(10px)"
        border="1px solid"
        borderColor="ui.glass.light.border"
        _dark={{
          bg: "ui.glass.dark.background",
          borderColor: "ui.glass.dark.border",
        }}
        p={6}
        borderRadius="xl"
        boxShadow="md"
        mb={6}
      >
        <Heading
          size="lg"
          textAlign={{ base: "center", md: "left" }}
          color={textColor}
        >
          {group!.name}
        </Heading>
      </Box>
      <Box
        bg="ui.glass.light.background"
        backdropFilter="blur(10px)"
        border="1px solid"
        borderColor="ui.glass.light.border"
        _dark={{
          bg: "ui.glass.dark.background",
          borderColor: "ui.glass.dark.border",
        }}
        p={6}
        borderRadius="xl"
        boxShadow="md"
      >
        <Tabs variant="enclosed" index={tabIndex} onChange={handleTabChange}>
          <TabList overflowX="auto" overflowY="hidden" flexWrap="nowrap">
            {tabsConfig.map((tab, index) => (
              <Tab
                key={index}
                _hover={{ transform: "translateY(-2px)" }}
                transition="all 0.2s"
                flexShrink={0}
              >
                {tab.title}
              </Tab>
            ))}
          </TabList>
          <TabPanels>
            {tabsConfig.map((tab, index) => (
              <TabPanel key={index}>{tab.component()}</TabPanel>
            ))}
          </TabPanels>
        </Tabs>
      </Box>
    </Container>
  )
}

function LoopsContent() {
  return (
    <Suspense fallback={<Spinner size="xl" />}>
      <LoopsContentLoader />
    </Suspense>
  )
}

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
} from "@chakra-ui/react";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Suspense } from "react";
import { MinimalLetter, UserUnlinked } from "../../../../client";
import {
  listLettersLettersLettersGetOptions,
  readGroupPartiesGroupGroupApiIdGetOptions,
  readUserMePartiesMeGetQueryKey,
} from "../../../../client/@tanstack/react-query.gen";
import { CollabEditor } from "../../../../components/Document/Editor";
import { GroupKeyValuesTable } from "../../../../components/GroupKeyValues/GroupKeyValuesTable";
import { LLMPlayground } from "../../../../components/LLMPlayground/LLMPlayground";
import { AdhocLoopsTab } from "../../../../components/Loops/AdhocLoopsTab";
import { LoopsTab } from "../../../../components/Loops/LoopsTab";
import { useGroupKeyValues } from "../../../../hooks/useGroupKeyValues";

type LoopsSearchParams = {
  offset?: number;
  limit?: number;
};

type LoopsLoaderProps = {
  loops: MinimalLetter[];
};

export const Route = createFileRoute("/_layout/groups/$groupId/loops")({
  validateSearch: (search: Record<string, string>): LoopsSearchParams => {
    return {
      offset: parseInt(search.offset) || undefined,
      limit: parseInt(search.limit) || undefined,
    };
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
    });

    return {
      loops,
    };
  },
  component: LoopsContent,
});

function LoopsContentLoader() {
  const groupId = Route.useParams().groupId;
  const props = Route.useLoaderData();
  const textColor = useColorModeValue("ui.dark", "ui.light");

  const { data: group } = useSuspenseQuery({
    ...readGroupPartiesGroupGroupApiIdGetOptions({
      path: { group_api_id: groupId },
    }),
  });
  const currentUser = useQueryClient().getQueryData<UserUnlinked>(
    readUserMePartiesMeGetQueryKey()
  );

  const { data: keyValues } = useGroupKeyValues(groupId);

  const tabsConfig = [
    {
      title: "Loops",
      component: () => <LoopsTab loops={props.loops.filter(loop => loop.letter_type === "CYCLIC")} group={group} />
    },
    {
      title: "Adhoc Loops",
      component: () => <AdhocLoopsTab loops={props.loops.filter(loop => loop.letter_type === "ADHOC")} group={group} />
    },
    {
      title: "Key Values",
      component: () => (
        <GroupKeyValuesTable
          keyValues={{
            key_values: keyValues?.key_values || {}
          }}
          groupApiId={groupId}
        />
      )
    },
    {
      title: "LLM Playground",
      component: () => <LLMPlayground />
    },
    {
      title: "Collaborative Editor",
      component: () => (
        <Box p={4}>
          <Heading size="md" mb={4}>Group Collaborative Document</Heading>
          <CollabEditor
            docId="dcmnt_fdd95a02-7f6e-4952-a6e1-3c57b7627de1"
            user={currentUser!}
          />
        </Box>
      )
    }
  ];

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
        <Heading size="lg" textAlign={{ base: "center", md: "left" }} color={textColor}>
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
        <Tabs variant="enclosed">
          <TabList>
            {tabsConfig.map((tab, index) => (
              <Tab
                key={index}
                _hover={{ transform: "translateY(-2px)" }}
                transition="all 0.2s"
              >
                {tab.title}
              </Tab>
            ))}
          </TabList>
          <TabPanels>
            {tabsConfig.map((tab, index) => (
              <TabPanel key={index}>
                {tab.component()}
              </TabPanel>
            ))}
          </TabPanels>
        </Tabs>
      </Box>
    </Container>
  );
}

function LoopsContent() {
  return (
    <Suspense fallback={<Spinner size="xl" />}>
      <LoopsContentLoader />
    </Suspense>
  );
}

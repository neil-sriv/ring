import {
  Box,
  Container,
  Heading,
  HStack,
  Spinner,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useRef, useState } from "react";
import { MinimalLetter } from "../../../../client";
import {
  listLettersLettersLettersGetOptions,
  readGroupPartiesGroupGroupApiIdGetOptions
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
      component: () => {
        const [isSaving, setIsSaving] = useState(false);
        const [isEditing, setIsEditing] = useState(false);
        const savingStartTimeRef = useRef<number | null>(null);

        const handleSavingChange = (saving: boolean) => {
          if (saving) {
            savingStartTimeRef.current = Date.now();
            setIsSaving(true);
          } else {
            const elapsed = Date.now() - (savingStartTimeRef.current || 0);
            const remainingTime = Math.max(0, 1000 - elapsed);

            setTimeout(() => {
              setIsSaving(false);
            }, remainingTime);
          }
        };

        return (
          <Box p={4}>
            <HStack spacing={3} mb={4} align="center">
              <Heading size="md">Group Collaborative Document</Heading>
              <HStack
                spacing={2}
                bg="whiteAlpha.200"
                px={3}
                py={1}
                borderRadius="md"
                borderWidth="1px"
                borderColor="whiteAlpha.300"
                _dark={{
                  bg: "whiteAlpha.100",
                  borderColor: "whiteAlpha.200"
                }}
              >
                {isSaving ? (
                  <>
                    <Spinner size="sm" color="blue.400" />
                    <Text fontSize="sm" color="gray.700" _dark={{ color: "gray.300" }}>
                      Syncing...
                    </Text>
                  </>
                ) : isEditing ? (
                  <Text fontSize="sm" color="orange.600" _dark={{ color: "orange.400" }}>
                    Editing...
                  </Text>
                ) : (
                  <Text fontSize="sm" color="green.600" _dark={{ color: "green.400" }}>
                    Saved
                  </Text>
                )}
              </HStack>
            </HStack>
            <CollabEditor
              docId="dcmnt_fdd95a02-7f6e-4952-a6e1-3c57b7627de1"
              onSavingChange={handleSavingChange}
              onEditingChange={setIsEditing}
            />
          </Box>
        );
      }
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

import {
  Container,
  Heading,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Spinner
} from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { PublicLetter } from "../../../../client";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  listLettersLettersLettersGetOptions,
  readGroupPartiesGroupGroupApiIdGetOptions,
} from "../../../../client/@tanstack/react-query.gen";
import { useGroupKeyValues } from "../../../../hooks/useGroupKeyValues";
import { GroupKeyValuesTable } from "../../../../components/GroupKeyValues/GroupKeyValuesTable";
import { LoopsTab } from "../../../../components/Loops/LoopsTab";
import { Suspense } from "react";

type LoopsSearchParams = {
  offset?: number;
  limit?: number;
};

type LoopsLoaderProps = {
  loops: PublicLetter[];
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
        query: { group_api_id: params.groupId, skip: offset, limit: limit },
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

  const { data: group } = useSuspenseQuery({
    ...readGroupPartiesGroupGroupApiIdGetOptions({
      path: { group_api_id: groupId },
    }),
  });

  const { data: keyValues } = useGroupKeyValues(groupId);

  const tabsConfig = [
    {
      title: "Loops",
      component: () => <LoopsTab loops={props.loops} group={group} />
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
    }
  ];

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
        {group!.name}
      </Heading>
      <Tabs variant="enclosed">
        <TabList>
          {tabsConfig.map((tab, index) => (
            <Tab key={index}>{tab.title}</Tab>
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

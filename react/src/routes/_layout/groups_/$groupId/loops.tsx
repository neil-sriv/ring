import {
  Box,
  Card,
  CardHeader,
  Container,
  Flex,
  Heading,
  LinkBox,
  LinkOverlay,
  Grid,
  Text,
  Highlight,
  VStack
} from "@chakra-ui/react";
import { Link, createFileRoute } from "@tanstack/react-router";
import { PublicLetter } from "../../../../client";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import LoopNav from "../../../../components/Loops/LoopNav";
import {
  listLettersLettersLettersGetOptions,
  readGroupPartiesGroupGroupApiIdGetOptions,
} from "../../../../client/@tanstack/react-query.gen";

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
  component: Loops,
});

type LoopCardProps = {
  loop: PublicLetter;
  includeGroupName?: boolean;
};

function LoopCard(props: LoopCardProps): JSX.Element {
  const sendDate = new Date(props.loop.send_at);
  return (
    <LinkBox height="100%">
      <Card
        border="1px solid"
        boxShadow="lg"
        bgColor={props.loop.status === "SENT" ? "ui.dim" : "ui.main"}
        height="100%"
      >
        <CardHeader>
          <LinkOverlay
            as={Link}
            to="/loops/$loopId"
            params={{ loopId: props.loop.api_identifier }}
          >
            <VStack align="stretch" spacing={2}>
              {props.includeGroupName && (
                <Heading size="md">
                  <Highlight
                    query={props.loop.group.name}
                    styles={{
                      px: "0.5",
                      bg: "orange.200",
                      color: "orange.fg",
                    }}
                  >
                    {props.loop.group.name}
                  </Highlight>
                </Heading>
              )}
              <Heading size="md">Issue #{props.loop.number}</Heading>
              {props.loop.status === "SENT" ? (
                <Text>Published {sendDate.toLocaleDateString()}</Text>
              ) : (
                <>
                  <Text>Due {sendDate.toLocaleString()}</Text>
                  {props.loop.status === "IN_PROGRESS" && (
                    <Text fontSize="sm" color="gray.600">
                      {props.loop.responders.length} responders / {props.loop.participants.length} participants
                    </Text>
                  )}
                </>
              )}
            </VStack>
          </LinkOverlay>
        </CardHeader>
      </Card>
    </LinkBox>
  );
}

export function LoopsGrid({
  loops,
  heading,
  subheading,
  includeGroupName = false,
}: {
  loops: PublicLetter[];
  heading: string;
  subheading?: string;
  includeGroupName?: boolean;
}): JSX.Element {
  return (
    <VStack w="100%" spacing={4} align="center">
      <Box textAlign="center" w="100%">
        <Heading size="md">{heading}</Heading>
        {subheading && <Heading size="sm">{subheading}</Heading>}
      </Box>
      <Grid
        templateColumns="repeat(auto-fill, minmax(200px, 1fr))"
        gap={4}
        alignItems="stretch"
        w="100%"
      >
        {loops.map((loop) => (
          <LoopCard
            key={loop.api_identifier}
            loop={loop}
            includeGroupName={includeGroupName}
          />
        ))}
      </Grid>
    </VStack>
  );
}

function LoopsContent() {
  const props = Route.useLoaderData();
  const groupId = Route.useParams().groupId;
  const { data: group } = useSuspenseQuery({
    ...readGroupPartiesGroupGroupApiIdGetOptions({
      path: { group_api_id: groupId },
    }),
  });
  if (!group) {
    return <Box>Loading...</Box>;
  }
  const publishedLoops = new Array<PublicLetter>();
  const inProgressLoops = new Array<PublicLetter>();
  const upcomingLoops = new Array<PublicLetter>();
  props.loops.forEach((loop) => {
    if (loop.status === "SENT") {
      publishedLoops.push(loop);
    } else if (loop.status === "IN_PROGRESS") {
      inProgressLoops.push(loop);
    } else {
      upcomingLoops.push(loop);
    }
  });
  return (
    <Flex justify="center" w="100%">
      <Box maxW="1200px" w="100%" px={4}>
        <VStack spacing={8} align="center" w="100%">
          <Heading as="h1" textAlign="center">
            {group!.name}
          </Heading>
          <Box w="100%">
            <LoopNav loops={props.loops} group={group} />
          </Box>

          {inProgressLoops.length > 0 && (
            <LoopsGrid
              loops={inProgressLoops}
              heading="In Progress"
              subheading="Add your response now!"
            />
          )}

          {upcomingLoops.length > 0 && (
            <LoopsGrid
              loops={upcomingLoops}
              heading="Upcoming Issues"
              subheading="You can add questions to the upcoming issues before they are available for responses."
            />
          )}

          {publishedLoops.length > 0 && (
            <LoopsGrid
              loops={publishedLoops.sort((a, b) => a.number - b.number)}
              heading="Published Issues"
            />
          )}
        </VStack>
      </Box>
    </Flex>
  );
}

function Loops() {
  return (
    <Container maxW="full">
      <Box pt={12} m={4}>
        <ErrorBoundary
          fallbackRender={({ error }) => (
            <Box>
              <Heading>Error</Heading>
              <Text>{error.message}</Text>
            </Box>
          )}
        >
          <Suspense fallback={<Box>Loading...</Box>}>
            <LoopsContent />
          </Suspense>
        </ErrorBoundary>
      </Box >
    </Container >
  );
}

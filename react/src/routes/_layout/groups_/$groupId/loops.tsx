import {
  Box,
  Card,
  CardHeader,
  Container,
  Heading,
  LinkBox,
  LinkOverlay,
  SimpleGrid,
  Text,
  Highlight,
} from "@chakra-ui/react";
import { Link, createFileRoute } from "@tanstack/react-router";
import {
  LettersService,
  PartiesService,
  PublicLetter,
} from "../../../../client";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import LoopNav from "../../../../components/Loops/LoopNav";

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
      queryKey: ["loops", params.groupId],
      queryFn: async () => {
        return await LettersService.listLettersLettersLettersGet({
          groupApiId: params.groupId,
          skip: offset,
          limit: limit,
        });
      },
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
    <LinkBox as="div">
      <Card
        w="150px"
        h="150px"
        flexGrow="1"
        border="1px solid"
        boxShadow="lg"
        bgColor={props.loop.status === "SENT" ? "ui.dim" : "ui.main"}
      >
        <CardHeader>
          <LinkOverlay
            as={Link}
            to="/loops/$loopId"
            params={{ loopId: props.loop.api_identifier }}
          >
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
              </>
            )}
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
    <Box paddingBottom="15px">
      <Heading size="md">{heading}</Heading>
      {subheading && <Heading size="sm">{subheading}</Heading>}
      <SimpleGrid columns={[1, 4, 6]} gap={4}>
        {loops.map((loop) => (
          <LoopCard
            key={loop.api_identifier}
            loop={loop}
            includeGroupName={includeGroupName}
          />
        ))}
      </SimpleGrid>
    </Box>
  );
}

function LoopsContent() {
  const props = Route.useLoaderData();
  const groupId = Route.useParams().groupId;
  const { data: group } = useSuspenseQuery({
    queryKey: ["groups", groupId],
    queryFn: () =>
      PartiesService.readGroupPartiesGroupGroupApiIdGet({
        groupApiId: groupId,
      }),
  });
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
    <Container maxW="container.lg" py={4}>
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        {group!.name}
      </Heading>
      <LoopNav loops={props.loops} group={group} />
      <Container maxW="container.lg" py={4}>
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
      </Container>
    </Container>
  );
}

function Loops() {
  return (
    <Box>
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
    </Box>
  );
}

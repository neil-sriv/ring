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
};

function LoopCard(props: LoopCardProps): JSX.Element {
  return (
    <LinkBox as="div">
      <Card w="150px" h="150px" flexGrow="1" border="1px solid" boxShadow="lg">
        <CardHeader>
          <LinkOverlay
            as={Link}
            to="/loops/$loopId"
            params={{ loopId: props.loop.api_identifier }}
          >
            <Heading size="md">Issue #{props.loop.number}</Heading>
          </LinkOverlay>
        </CardHeader>
      </Card>
    </LinkBox>
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
  return (
    <Container maxW="container.lg" py={4}>
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        {group!.name}
      </Heading>
      <LoopNav loops={props.loops} groupId={groupId} />
      <Container maxW="container.lg" py={4}>
        <SimpleGrid columns={4} gap={4}>
          {props.loops.map((loop) => (
            <LoopCard key={loop.api_identifier} loop={loop} />
          ))}
        </SimpleGrid>
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

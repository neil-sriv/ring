import { Box, Container, Heading, Text } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";

import { useQueryClient } from "@tanstack/react-query";
import { UserLinked } from "../../client/models";
import { ErrorBoundary } from "react-error-boundary";
import { Suspense } from "react";
import { HomeDashboard } from "../../components/Home/HomeDashboard";

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
});

function Dashboard() {
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(["currentUser"]);

  return (
    <>
      <Container maxW="full">
        <Box pt={12} m={4}>
          <ErrorBoundary
            fallbackRender={({ error }) => (
              <Box>
                <Heading>Error</Heading>
                <Text>{error.message}</Text>
                <Text fontSize="2xl">
                  Hi, {currentUser?.name || currentUser?.email} 👋🏼
                </Text>
                <Text>Welcome back, nice to see you again!</Text>
              </Box>
            )}
          >
            <Suspense fallback={<Box>Loading...</Box>}>
              <HomeDashboard />
            </Suspense>
          </ErrorBoundary>
        </Box>
      </Container>
    </>
  );
}

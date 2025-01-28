import { Box, Container } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";

import { Suspense } from "react";
import { HomeDashboard } from "../../components/Home/HomeDashboard";

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
});

function Dashboard() {
  return (
    <>
      <Container maxW="full">
        <Box pt={12} m={4}>
          <Suspense fallback={<Box>Loading...</Box>}>
            <HomeDashboard />
          </Suspense>
        </Box>
      </Container>
    </>
  );
}

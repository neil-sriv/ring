import { Box, Flex, Heading, VStack } from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { LoopsGrid } from "../Loops/LoopsGrid";
import { listDashboardLettersLettersLettersDashboardGetOptions } from "../../client/@tanstack/react-query.gen";

export function HomeDashboard() {
  const dashboardLoops = useSuspenseQuery({
    ...listDashboardLettersLettersLettersDashboardGetOptions(),
  });
  const recently_completed = dashboardLoops.data.recently_completed;
  const in_progress = dashboardLoops.data.in_progress;
  const upcoming = dashboardLoops.data.upcoming;
  return (
    <Flex justify="center" w="100%">
      <Box maxW="1200px" w="100%" px={4}>
        <VStack spacing={8} align="center" w="100%">
          <Heading as="h1" textAlign="center">
            Dashboard
          </Heading>
          {recently_completed.length > 0 && (
            <LoopsGrid
              loops={recently_completed.sort((a, b) => a.number - b.number)}
              heading="Published Issues"
              includeGroupName={true}
            />
          )}
          {in_progress.length > 0 && (
            <LoopsGrid
              loops={in_progress}
              heading="In Progress"
              subheading="Add your response now!"
              includeGroupName={true}
            />
          )}
          {upcoming.length > 0 && (
            <LoopsGrid
              loops={upcoming}
              heading="Upcoming Issues"
              subheading="You can add questions to the upcoming issues before they are available for responses."
              includeGroupName={true}
            />
          )}
        </VStack>
      </Box>
    </Flex>
  );
}

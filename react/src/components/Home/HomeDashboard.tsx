import { Box, Heading } from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { LettersService } from "../../client";
import { LoopsGrid } from "../../routes/_layout/groups_/$groupId/loops";
// import { fetchPublishedIssues, fetchActionItems } from "../../api/issues";

export function HomeDashboard() {
  const { data } = useSuspenseQuery({
    queryKey: ["dashboardIssues"],
    queryFn: async () => {
      return await LettersService.listDashboardLettersLettersLettersDashboardGet();
    },
  });
  return (
    <Box p={4}>
      <Heading as="h1" mb={4}>
        Dashboard
      </Heading>
      {/* <Container maxW="container.lg" py={4}> */}
      {data.recently_completed.length > 0 && (
        <LoopsGrid
          loops={data.recently_completed.sort((a, b) => a.number - b.number)}
          heading="Published Issues"
          includeGroupName={true}
        />
      )}
      {data.in_progress.length > 0 && (
        <LoopsGrid
          loops={data.in_progress}
          heading="In Progress"
          subheading="Add your response now!"
          includeGroupName={true}
        />
      )}

      {data.upcoming.length > 0 && (
        <LoopsGrid
          loops={data.upcoming}
          heading="Upcoming Issues"
          subheading="You can add questions to the upcoming issues before they are available for responses."
          includeGroupName={true}
        />
      )}
      {/* </Container> */}
    </Box>
  );
}

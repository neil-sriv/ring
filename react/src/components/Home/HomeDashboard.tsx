import { Box, Heading } from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { LoopsGrid } from "../../routes/_layout/groups_/$groupId/loops";
import { listDashboardLettersLettersLettersDashboardGetOptions } from "../../client/@tanstack/react-query.gen";

export function HomeDashboard() {
  const dashboardLoops = useSuspenseQuery({
    ...listDashboardLettersLettersLettersDashboardGetOptions(),
  });
  const recently_completed = dashboardLoops.data.recently_completed;
  const in_progress = dashboardLoops.data.in_progress;
  const upcoming = dashboardLoops.data.upcoming;
  return (
    <Box p={4}>
      <Heading as="h1" mb={4}>
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
    </Box>
  );
}

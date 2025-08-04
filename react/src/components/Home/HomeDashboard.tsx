import { Box, Flex, Heading, VStack, useColorModeValue } from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { listDashboardLettersLettersLettersDashboardGetOptions } from "../../client/@tanstack/react-query.gen";
import { LoopsGrid } from "../Loops/LoopsGrid";

export function HomeDashboard() {
  const dashboardLoops = useSuspenseQuery({
    ...listDashboardLettersLettersLettersDashboardGetOptions(),
  });
  const recently_completed = dashboardLoops.data?.recently_completed || [];
  const in_progress = dashboardLoops.data?.in_progress || [];
  const upcoming = dashboardLoops.data?.upcoming || [];

  const textColor = useColorModeValue("ui.dark", "ui.light");
  const bgColor = useColorModeValue("ui.glass.light.background", "ui.glass.dark.background");
  const borderColor = useColorModeValue("ui.glass.light.border", "ui.glass.dark.border");

  return (
    <Flex justify="center" w="100%" bg={bgColor} backdropFilter="blur(10px)">
      <Box maxW="1200px" w="100%" px={4} py={8}>
        <VStack spacing={8} align="stretch" w="100%">
          <Heading
            as="h1"
            textAlign="center"
            color={textColor}
            size="xl"
            fontWeight="bold"
            letterSpacing="tight"
            py={4}
            borderBottom="1px solid"
            borderColor={borderColor}
          >
            Dashboard
          </Heading>
          {recently_completed.length > 0 && (
            <LoopsGrid
              loops={recently_completed.sort((a, b) => new Date(a.send_at).getTime() - new Date(b.send_at).getTime())}
              heading="Published Issues"
              includeGroupName={true}
              showLoopTypeLabel={true}
            />
          )}
          {in_progress.length > 0 && (
            <LoopsGrid
              loops={in_progress.sort((a, b) => new Date(a.send_at).getTime() - new Date(b.send_at).getTime())}
              heading="In Progress"
              subheading="Add your response now!"
              includeGroupName={true}
              showLoopTypeLabel={true}
              showResponderCount={true}
            />
          )}
          {upcoming.length > 0 && (
            <LoopsGrid
              loops={upcoming.sort((a, b) => new Date(a.send_at).getTime() - new Date(b.send_at).getTime())}
              heading="Upcoming Issues"
              subheading="You can add questions to the upcoming issues before they are available"
              includeGroupName={true}
              showLoopTypeLabel={true}
            />
          )}
        </VStack>
      </Box>
    </Flex>
  );
}

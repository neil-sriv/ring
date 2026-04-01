import { Box, Heading, Text, VStack, useColorModeValue } from "@chakra-ui/react"
import type { GroupLinked, MinimalLetter } from "../../client"
import AdhocLoopNav from "./AdhocLoopNav"
import { LoopsGrid } from "./LoopsGrid"

export function AdhocLoopsTab({
  loops,
  group,
}: { loops: MinimalLetter[]; group: GroupLinked }) {
  const textColor = useColorModeValue("ui.dark", "ui.light")
  const subtextColor = useColorModeValue("ui.dim", "ui.dim")

  const inProgressLoops = loops.filter((loop) => loop.status === "IN_PROGRESS")
  const upcomingLoops = loops.filter(
    (loop) => loop.status !== "SENT" && loop.status !== "IN_PROGRESS",
  )
  const publishedLoops = loops.filter((loop) => loop.status === "SENT")

  return (
    <VStack spacing={8} w="100%">
      <Box w="100%">
        <AdhocLoopNav loops={loops} group={group} />
      </Box>

      <Box w="100%">
        <VStack spacing={4} align="center">
          <Heading size="md" color={textColor}>
            Adhoc Loops
          </Heading>
          <Text color={subtextColor} textAlign="center" maxW="600px">
            Adhoc loops are one-time loops that can be created outside of the
            regular cycle.
          </Text>
        </VStack>
      </Box>

      {loops.length > 0 ? (
        <VStack spacing={6} w="100%">
          <Box w="100%">
            <Text color={subtextColor} textAlign="center" fontSize="sm" mb={4}>
              Currently showing all adhoc loops.
            </Text>
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
              loops={publishedLoops.sort(
                (a, b) =>
                  new Date(a.send_at).getTime() - new Date(b.send_at).getTime(),
              )}
              heading="Published Issues"
            />
          )}
        </VStack>
      ) : (
        <Box w="100%" textAlign="center">
          <Text color={subtextColor}>
            No adhoc loops found. Create your first adhoc loop to get started!
          </Text>
        </Box>
      )}
    </VStack>
  )
}

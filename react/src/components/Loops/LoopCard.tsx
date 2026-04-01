import {
  Badge,
  Box,
  Heading,
  LinkBox,
  LinkOverlay,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import { useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import type { MinimalLetter, PublicLetter, UserLinked } from "../../client"
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen"

export function LoopCard(props: {
  loop: MinimalLetter | PublicLetter
  includeGroupName?: boolean
  showLoopTypeLabel?: boolean
  showResponderCount?: boolean
}): JSX.Element {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )

  const sendDate = new Date(props.loop.send_at)
  const textColor = useColorModeValue("ui.dark", "ui.light")
  const subtextColor = useColorModeValue("ui.dim", "ui.dim")

  // Determine the main heading text
  const getHeadingText = () => {
    if (props.loop.title) {
      return props.loop.title
    }
    if (props.loop.number) {
      return `Issue #${props.loop.number}`
    }
    return "Untitled Loop"
  }

  // Get loop type label
  const getLoopTypeLabel = () => {
    if (!props.showLoopTypeLabel) return null

    const loopType = props.loop.letter_type
    if (loopType === "ADHOC") {
      return (
        <Badge
          colorScheme="purple"
          variant="subtle"
          fontSize="xs"
          position="absolute"
          top={2}
          right={2}
        >
          One-off
        </Badge>
      )
    }
    if (loopType === "CYCLIC") {
      return (
        <Badge
          colorScheme="blue"
          variant="subtle"
          fontSize="xs"
          position="absolute"
          top={2}
          right={2}
        >
          Recurring
        </Badge>
      )
    }
    return null
  }

  // Check if responders attribute exists and get responder count
  const getResponderCount = () => {
    if (
      props.showResponderCount &&
      "responders" in props.loop &&
      props.loop.responders
    ) {
      return props.loop.responders.length
    }
    return null
  }

  // Check if user has unanswered questions in this published loop
  const getUnansweredQuestionsCount = () => {
    if (
      props.loop.status === "SENT" &&
      currentUser &&
      "questions" in props.loop &&
      props.loop.questions
    ) {
      const unansweredQuestions = props.loop.questions.filter((question) => {
        return !question.responses.some(
          (response) =>
            response.participant.api_identifier === currentUser.api_identifier,
        )
      })
      return unansweredQuestions.length
    }
    return 0
  }

  const responderCount = getResponderCount()
  const unansweredCount = getUnansweredQuestionsCount()

  return (
    <LinkBox height="100%">
      <Box
        h="100%"
        bg="ui.glass.light.background"
        backdropFilter="blur(10px)"
        border="1px solid"
        borderColor="ui.glass.light.border"
        _dark={{
          bg: "ui.glass.dark.background",
          borderColor: "ui.glass.dark.border",
        }}
        p={6}
        borderRadius="xl"
        boxShadow="md"
        transition="all 0.2s"
        _hover={{
          transform: "translateY(-4px)",
          boxShadow: "xl",
          borderColor: "ui.main",
        }}
        position="relative"
      >
        {getLoopTypeLabel()}
        <LinkOverlay
          as={Link}
          to={`/loops/${props.loop.api_identifier}`}
          _hover={{ textDecoration: "none" }}
        >
          <VStack align="start" spacing={2}>
            <Heading size="md" color={textColor}>
              {getHeadingText()}
            </Heading>
            {props.includeGroupName && (
              <Text color={subtextColor} fontSize="sm">
                {props.loop.group.name}
              </Text>
            )}
            <Text color={subtextColor} fontSize="sm">
              {sendDate.toLocaleDateString()}
            </Text>
            {responderCount !== null && (
              <Text color={subtextColor} fontSize="sm">
                {responderCount} responder{responderCount !== 1 ? "s" : ""}
              </Text>
            )}
            {unansweredCount > 0 && (
              <Text color="orange.500" fontSize="sm" fontWeight="medium">
                You have {unansweredCount} unanswered question
                {unansweredCount !== 1 ? "s" : ""}
              </Text>
            )}
          </VStack>
        </LinkOverlay>
      </Box>
    </LinkBox>
  )
}

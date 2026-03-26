import { Badge, Box, Button, Container, Flex, Heading, Icon, Text, Tooltip, Wrap, WrapItem, useColorModeValue, useDisclosure, VStack } from "@chakra-ui/react";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { FaPlus } from "react-icons/fa";
import { PublicLetter, UserLinked } from "../../../client";
import {
  readGroupPartiesGroupGroupApiIdGetOptions,
  readLetterLettersLetterLetterApiIdGetOptions,
  readUserMePartiesMeGetQueryKey,
} from "../../../client/@tanstack/react-query.gen";
import DraftLoop from "../../../components/Loops/DraftLoop";
import EditLetter from "../../../components/Loops/EditLoop";
import LoopRespondersModal from "../../../components/Loops/LoopRespondersModal";
import PublishedLoop from "../../../components/Loops/PublishedLoop";
import AddQuestion from "../../../components/Question/AddQuestion";
import GenerateQuestion from "../../../components/Question/GenerateQuestion";

type IssueLoaderProps = {
  loop: PublicLetter;
};

export const Route = createFileRoute("/_layout/loops/$loopId")({
  loader: async ({ params, context }): Promise<IssueLoaderProps> => {
    const loop = await context.queryClient.ensureQueryData({
      ...readLetterLettersLetterLetterApiIdGetOptions({
        path: { letter_api_id: params.loopId },
      }),
    });
    return {
      loop,
    };
  },
  component: Issue,
});

function IssueContent() {
  const routeParams = Route.useParams();
  const { data: loop } = useSuspenseQuery({
    ...readLetterLettersLetterLetterApiIdGetOptions({
      path: { letter_api_id: routeParams.loopId },
    }),
  });
  const { data: group } = useSuspenseQuery({
    ...readGroupPartiesGroupGroupApiIdGetOptions({
      path: { group_api_id: loop.group.api_identifier },
    }),
  });
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey()
  );
  const localDueDate = new Date(loop.send_at);
  const textColor = useColorModeValue("ui.dark", "ui.light");
  const subtextColor = useColorModeValue("ui.dim", "ui.dim");
  const editLoopModal = useDisclosure();
  const addQuestionModal = useDisclosure();
  const generateQuestionModal = useDisclosure();
  const respondersModal = useDisclosure();

  const hasDesignatedResponders = loop.designated_responders.length > 0;

  return (
    <Flex justify="center" w="100%">
      <Box maxW="1200px" w="100%" px={[2, 4]}>
        <VStack spacing={[4, 6, 8]} align="center" w="100%">
          <Box
            w="100%"
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
          >
            <VStack spacing={4} align="center">
              <Box position="relative" w="100%">
                <Heading size={["md", "lg"]} textAlign="center" color={textColor}>
                  <Link
                    to="/groups/$groupId/loops"
                    params={{ groupId: group!.api_identifier }}
                    style={{ textDecoration: "underline" }}
                  >
                    {group!.name}
                  </Link>
                </Heading>
                {group.admin.api_identifier === currentUser?.api_identifier && loop.status !== "SENT" && (
                  <Button
                    variant="primary"
                    onClick={editLoopModal.onOpen}
                    _hover={{
                      opacity: 0.9,
                      bg: "ui.primary",
                    }}
                    transition="all 0.2s ease-in-out"
                    position="absolute"
                    right="0"
                    top="50%"
                    transform="translateY(-50%)"
                  >
                    Edit Loop
                  </Button>
                )}
              </Box>
              {loop.title && (
                <Heading size={["md", "lg"]} color={textColor}>
                  {loop.title}
                </Heading>
              )}
              {!loop.title && loop.number && (
                <Heading size={["md", "lg"]} color={textColor}>
                  Issue #{loop.number}
                </Heading>
              )}
              {loop.status === "IN_PROGRESS" && (
                <Heading
                  size="md"
                  textAlign={{ base: "center", md: "left" }}
                  pt={2}
                  color={subtextColor}
                >
                  Due {localDueDate.toLocaleString()}
                </Heading>
              )}
              {hasDesignatedResponders && (
                <Box pt={2}>
                  <Tooltip label="Only designated responders can submit answers">
                    <Text fontSize="sm" color={subtextColor} textAlign="center">
                      Responders:{" "}
                      <Wrap display="inline-flex" spacing={1}>
                        {loop.designated_responders.map((r) => (
                          <WrapItem key={r.api_identifier}>
                            <Badge colorScheme="teal" variant="subtle" fontSize="xs">
                              {r.name}
                            </Badge>
                          </WrapItem>
                        ))}
                      </Wrap>
                    </Text>
                  </Tooltip>
                </Box>
              )}
              {loop.status !== "SENT" && (
                <Button
                  size="xs"
                  variant="ghost"
                  onClick={respondersModal.onOpen}
                  mt={1}
                >
                  {hasDesignatedResponders ? "Edit Responders" : "Set Responders"}
                </Button>
              )}
            </VStack>
          </Box>

          {loop.status === "UPCOMING" && (
            <Flex gap={4} wrap="wrap" w="100%">
              <Button
                variant="primary"
                gap={1}
                fontSize={{ base: "sm", md: "inherit" }}
                onClick={() => addQuestionModal.onOpen()}
                whiteSpace="normal"
                textAlign="left"
                height="auto"
                py={2}
                _hover={{ transform: "translateY(-2px)" }}
                transition="all 0.2s"
              >
                <Icon as={FaPlus} />{" "}
                Add new question
              </Button>
              <Button
                variant="primary"
                gap={1}
                fontSize={{ base: "sm", md: "inherit" }}
                onClick={() => generateQuestionModal.onOpen()}
                whiteSpace="normal"
                textAlign="left"
                height="auto"
                py={2}
                _hover={{ transform: "translateY(-2px)" }}
                transition="all 0.2s"
              >
                <Icon as={FaPlus} />{" "}
                Ask ChatGPT to generate a question.
              </Button>
            </Flex>
          )}

          <Box
            w="100%"
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
          >
            {loop.status === "SENT" ? (
              <PublishedLoop loop={loop} />
            ) : (
              <DraftLoop loop={loop} isGroupAdmin={group.admin.api_identifier === currentUser?.api_identifier} />
            )}
          </Box>
        </VStack>
      </Box>
      <EditLetter
        isOpen={editLoopModal.isOpen}
        onClose={editLoopModal.onClose}
        loop={loop}
      />
      <AddQuestion
        isOpen={addQuestionModal.isOpen}
        onClose={addQuestionModal.onClose}
        loopApiId={loop.api_identifier}
      />
      <GenerateQuestion
        isOpen={generateQuestionModal.isOpen}
        onClose={generateQuestionModal.onClose}
        loopApiId={loop.api_identifier}
      />
      {group && (
        <LoopRespondersModal
          isOpen={respondersModal.isOpen}
          onClose={respondersModal.onClose}
          loop={loop}
          group={group}
        />
      )}
    </Flex>
  );
}

function Issue() {
  return (
    <Container maxW="full">
      <Box pt={[4, 8, 12]} mx={[2, 4]}>
        <ErrorBoundary
          fallbackRender={({ error }) => (
            <Box>
              <Heading>Error</Heading>
              <Text>{error.message}</Text>
            </Box>
          )}
        >
          <Suspense fallback={<Box>Loading...</Box>}>
            <IssueContent />
          </Suspense>
        </ErrorBoundary>
      </Box>
    </Container>
  );
}

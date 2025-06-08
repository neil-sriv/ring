import {
  Box,
  Heading,
  LinkBox,
  LinkOverlay,
  Text,
  useColorModeValue,
  VStack
} from "@chakra-ui/react";
import { Link } from "@tanstack/react-router";
import { PublicLetter } from "../../client";

export function LoopCard(props: {
  loop: PublicLetter;
  includeGroupName?: boolean
}): JSX.Element {
  const sendDate = new Date(props.loop.send_at);
  const textColor = useColorModeValue("ui.dark", "ui.light");
  const subtextColor = useColorModeValue("ui.dim", "ui.dim");

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
      >
        <LinkOverlay
          as={Link}
          to={`/loops/${props.loop.api_identifier}`}
          _hover={{ textDecoration: "none" }}
        >
          <VStack align="start" spacing={2}>
            <Heading size="md" color={textColor}>
              Issue #{props.loop.number}
            </Heading>
            {props.includeGroupName && (
              <Text color={subtextColor} fontSize="sm">
                {props.loop.group.name}
              </Text>
            )}
            <Text color={subtextColor} fontSize="sm">
              {sendDate.toLocaleDateString()}
            </Text>
          </VStack>
        </LinkOverlay>
      </Box>
    </LinkBox>
  );
}

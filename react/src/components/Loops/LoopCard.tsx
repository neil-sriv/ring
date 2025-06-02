import {
  Card,
  CardHeader,
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
      <Card
        h="100%"
        transition="all 0.2s"
        _hover={{
          transform: "translateY(-4px)",
          boxShadow: "xl",
          borderColor: "ui.main",
        }}
      >
        <CardHeader p={4}>
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
        </CardHeader>
      </Card>
    </LinkBox>
  );
}

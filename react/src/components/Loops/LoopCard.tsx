import {
  Box,
  Card,
  CardHeader,
  Heading,
  LinkBox,
  LinkOverlay,
  VStack
} from "@chakra-ui/react";
import { PublicLetter } from "../../client";
import { Link } from "@tanstack/react-router";

export function LoopCard(props: {
  loop: PublicLetter;
  includeGroupName?: boolean
}): JSX.Element {
  const sendDate = new Date(props.loop.send_at);
  return (
    <LinkBox height="100%">
      <Card
        // border="1px solid"
        // boxShadow="lg"
        // bgColor={props.loop.status === "SENT" ? "ui.dim" : "ui.main"}
        // height="100%"
        border="1px solid"
        borderColor="gray.200"
        borderRadius="md"
        p={4}
        h="100%"
      >
        <CardHeader>
          <LinkOverlay
            as={Link}
            to="/loops/$loopId"
            params={{ loopId: props.loop.api_identifier }}
          >
            <VStack align="stretch" spacing={2}>
              {props.includeGroupName && (
                <Heading size="sm" color="gray.600">
                  {props.loop.group.name}
                </Heading>
              )}
              <Heading size="md">Issue #{props.loop.number}</Heading>
              {props.loop.status === "SENT" ? (
                <Box>Published {sendDate.toLocaleDateString()}</Box>
              ) : (
                <>
                  <Box>Due {sendDate.toLocaleString()}</Box>
                  {props.loop.status === "IN_PROGRESS" && (
                    <Box fontSize="sm" color="gray.600">
                      {props.loop.responders.length} responders / {props.loop.participants.length} participants
                    </Box>
                  )}
                </>
              )}
            </VStack>
          </LinkOverlay>
        </CardHeader>
      </Card>
    </LinkBox>
  );
}

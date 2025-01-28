import {
  Box,
  Container,
  Flex,
  Heading,
  Skeleton,
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  Text,
  Tr,
} from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { Link as ChakraLink } from "@chakra-ui/react";

import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { UserLinked } from "../../client";
import Navbar from "../../components/Common/Navbar";
import ActionsMenu from "../../components/Common/ActionsMenu";
import { listGroupsPartiesGroupsGetOptions } from "../../client/@tanstack/react-query.gen";

export const Route = createFileRoute("/_layout/groups")({
  component: Groups,
  loader: async ({ context }) => {
    if (!context.auth.user) {
      throw new Error("User not authenticated");
    }
    return context.auth.user;
  },
});

function GroupTableBody() {
  const currentUser = Route.useLoaderData<UserLinked>();
  const { data: groups } = useSuspenseQuery({
    ...listGroupsPartiesGroupsGetOptions({
      query: { user_api_id: currentUser?.api_identifier },
    }),
  });

  if (!groups) {
    return null;
  }

  return (
    <Tbody>
      {groups.map((group) => (
        <Tr key={group.api_identifier}>
          {/* <Td>{group.name}</Td> */}
          <Td>
            <ChakraLink
              as={Link}
              to="/groups/$groupId/loops"
              params={{ groupId: group.api_identifier }}
              textDecoration={"underline"}
            >
              {group.name}
            </ChakraLink>
          </Td>
          <Td whiteSpace="normal">
            <Box>
              <Text>
                {group.members
                  .map((member) => {
                    return member.name;
                  })
                  .sort()
                  .join(", ")}
              </Text>
            </Box>
          </Td>
          {/* <Td>
            {group.letters
              .map((letter) => {
                return letter.number;
              })
              .sort()
              .join(", ")}
          </Td> */}
          <Td>
            <ActionsMenu type={"Group"} value={group} />
          </Td>
        </Tr>
      ))}
    </Tbody>
  );
}

function GroupTable() {
  return (
    <TableContainer>
      <Table size={{ base: "sm", md: "md" }} maxW="100%">
        <Thead>
          <Tr>
            <Th>Name</Th>
            <Th>Members</Th>
            {/* <Th>Letters</Th> */}
            <Th>Actions</Th>
          </Tr>
        </Thead>
        <ErrorBoundary
          fallbackRender={({ error }) => (
            <Tbody>
              <Tr>
                <Td colSpan={4}>Something went wrong: {error.message}</Td>
              </Tr>
            </Tbody>
          )}
        >
          <Suspense
            fallback={
              <Tbody>
                {new Array(5).fill(null).map((_, index) => (
                  <Tr key={index}>
                    {new Array(4).fill(null).map((_, index) => (
                      <Td key={index}>
                        <Flex>
                          <Skeleton height="20px" width="20px" />
                        </Flex>
                      </Td>
                    ))}
                  </Tr>
                ))}
              </Tbody>
            }
          >
            <GroupTableBody />
          </Suspense>
        </ErrorBoundary>
      </Table>
    </TableContainer>
  );
}

function Groups() {
  return (
    <Container maxW="container.xl">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        Groups
      </Heading>

      <Navbar type={"Group"} />
      <GroupTable />
    </Container>
  );
}

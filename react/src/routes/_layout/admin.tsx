import {
  Badge,
  Box,
  Container,
  Flex,
  Heading,
  SkeletonText,
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { Suspense } from "react";
import { type UserLinked } from "../../client";
import ActionsMenu from "../../components/Common/ActionsMenu";
import Navbar from "../../components/Common/Navbar";
import { readUsersPartiesUsersGetOptions } from "../../client/@tanstack/react-query.gen";

export const Route = createFileRoute("/_layout/admin")({
  component: Admin,
  loader: async ({ context }) => {
    if (!context.auth.user) {
      throw new Error("User not authenticated");
    }
    return context.auth.user;
  },
});

const MembersTableBody = () => {
  const currentUser = Route.useLoaderData<UserLinked>();

  const { data: users } = useSuspenseQuery({
    ...readUsersPartiesUsersGetOptions(),
  });

  return (
    <Tbody>
      {users.map((user) => (
        <Tr key={user.api_identifier}>
          <Td color={!user.name ? "ui.dim" : "inherit"}>
            {user.name || "N/A"}
            {currentUser?.api_identifier === user.api_identifier && (
              <Badge ml="1" colorScheme="teal">
                You
              </Badge>
            )}
          </Td>
          <Td>{user.email}</Td>
          {/* <Td>{user.is_superuser ? "Superuser" : "User"}</Td> */}
          <Td>{false ? "Superuser" : "User"}</Td>
          <Td>
            <Flex gap={2}>
              <Box
                w="2"
                h="2"
                borderRadius="50%"
                // bg={user.is_active ? "ui.success" : "ui.danger"}
                bg={true ? "ui.success" : "ui.danger"}
                alignSelf="center"
              />
              {/* {user.is_active ? "Active" : "Inactive"} */}
              {true ? "Active" : "Inactive"}
            </Flex>
          </Td>
          <Td>
            <ActionsMenu
              type="User"
              value={user}
              disabled={
                currentUser?.api_identifier === user.api_identifier
                  ? true
                  : false
              }
            />
          </Td>
        </Tr>
      ))}
    </Tbody>
  );
};

const MembersBodySkeleton = () => {
  return (
    <Tbody>
      <Tr>
        {new Array(5).fill(null).map((_, index) => (
          <Td key={index}>
            <SkeletonText noOfLines={1} paddingBlock="16px" />
          </Td>
        ))}
      </Tr>
    </Tbody>
  );
};

function Admin() {
  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        User Management
      </Heading>
      <Navbar type={"User"} />
      <TableContainer>
        <Table fontSize="md" size={{ base: "sm", md: "md" }}>
          <Thead>
            <Tr>
              <Th width="20%">Full name</Th>
              <Th width="50%">Email</Th>
              <Th width="10%">Role</Th>
              <Th width="10%">Status</Th>
              <Th width="10%">Actions</Th>
            </Tr>
          </Thead>
          <Suspense fallback={<MembersBodySkeleton />}>
            <MembersTableBody />
          </Suspense>
        </Table>
      </TableContainer>
    </Container>
  );
}

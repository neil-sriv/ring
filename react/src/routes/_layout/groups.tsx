import {
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
  Tr,
} from "@chakra-ui/react";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { PartiesService, UserLinked } from "../../client";
// import ActionsMenu from "../../components/Common/ActionsMenu";
import Navbar from "../../components/Common/Navbar";
import ActionsMenu from "../../components/Common/ActionsMenu";

export const Route = createFileRoute("/_layout/groups")({
  component: Groups,
});

function GroupTableBody() {
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(["currentUser"]);
  const { data: groups } = useSuspenseQuery({
    queryKey: ["groups"],
    queryFn: () =>
      PartiesService.listGroupsPartiesGroupsGet({
        userApiId: currentUser!.api_identifier,
      }),
  });

  return (
    <Tbody>
      {groups.map((group) => (
        <Tr key={group.api_identifier}>
          <Td>{group.name}</Td>
          {/* <Td>{item.title}</Td> */}
          {/* <Td color={!item.description ? "ui.dim" : "inherit"}>
            {item.description || "N/A"}
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
      <Table size={{ base: "sm", md: "md" }}>
        <Thead>
          <Tr>
            <Th>ID</Th>
            <Th>Title</Th>
            <Th>Description</Th>
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
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        Groups
      </Heading>

      <Navbar type={"Group"} />
      <GroupTable />
    </Container>
  );
}

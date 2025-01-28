import {
  Container,
  Heading,
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react";
import { useQueryClient } from "@tanstack/react-query";

import { GroupLinked } from "../../client";
import { readGroupPartiesGroupGroupApiIdGetQueryKey } from "../../client/@tanstack/react-query.gen";

function GroupMembershipSettings({ groupId }: { groupId: string }) {
  const queryClient = useQueryClient();
  const group = queryClient.getQueryData<GroupLinked>(
    readGroupPartiesGroupGroupApiIdGetQueryKey({
      path: { group_api_id: groupId },
    })
  );

  if (group === undefined) {
    return null;
  }
  return (
    <>
      <Container maxW="full">
        <Heading size="sm" py={4}>
          Group Membership
        </Heading>
        <TableContainer>
          <Table variant="striped" colorScheme="teal">
            <Thead>
              <Tr>
                <Th>Name</Th>
                <Th>Email</Th>
                <Th>Role</Th>
              </Tr>
            </Thead>
            <Tbody>
              {group.members.map((member) => {
                return (
                  <Tr key={member.email}>
                    <Td>{member.name}</Td>
                    <Td>{member.email}</Td>
                    <Td>Member</Td>
                  </Tr>
                );
              })}
            </Tbody>
          </Table>
        </TableContainer>
      </Container>
    </>
  );
}

export default GroupMembershipSettings;

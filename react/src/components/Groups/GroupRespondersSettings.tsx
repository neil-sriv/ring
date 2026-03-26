import {
  Box,
  Button,
  Checkbox,
  Container,
  Flex,
  Heading,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { GroupLinked } from "../../client";
import { SetGroupDesignatedRespondersPartiesGroupGroupApiIdSetDesignatedRespondersPostError } from "../../client/types.gen";
import useCustomToast from "../../hooks/useCustomToast";
import { useRouter } from "@tanstack/react-router";
import {
  readGroupPartiesGroupGroupApiIdGetQueryKey,
  setGroupDesignatedRespondersPartiesGroupGroupApiIdSetDesignatedRespondersPostMutation,
} from "../../client/@tanstack/react-query.gen";
import { AxiosError } from "axios";

function GroupRespondersSettings({ groupId }: { groupId: string }) {
  const queryClient = useQueryClient();
  const color = useColorModeValue("inherit", "ui.light");
  const showToast = useCustomToast();
  const router = useRouter();
  const [editMode, setEditMode] = useState(false);

  const group = queryClient.getQueryData<GroupLinked>(
    readGroupPartiesGroupGroupApiIdGetQueryKey({
      path: { group_api_id: groupId },
    })
  );

  const hasDesignatedResponders = group !== undefined && group.designated_responders.length > 0;

  const [selectedResponders, setSelectedResponders] = useState<Set<string>>(
    () => {
      if (!group) {
        return new Set<string>();
      }
      if (hasDesignatedResponders) {
        return new Set(group.designated_responders.map((r) => r.api_identifier));
      }
      return new Set(group.members.map((m) => m.api_identifier));
    }
  );

  if (group === undefined) {
    return null;
  }

  const isAllMembers = selectedResponders.size === group.members.length;

  const mutation = useMutation({
    ...setGroupDesignatedRespondersPartiesGroupGroupApiIdSetDesignatedRespondersPostMutation(),
    onSuccess: () => {
      showToast("Success!", "Designated responders updated successfully.", "success");
    },
    onError: (
      err: AxiosError<SetGroupDesignatedRespondersPartiesGroupGroupApiIdSetDesignatedRespondersPostError>
    ) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support";
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
    onSettled: async () => {
      queryClient.invalidateQueries({
        queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
          path: { group_api_id: groupId },
        }),
      });
      router.invalidate();
      await queryClient.refetchQueries({
        queryKey: readGroupPartiesGroupGroupApiIdGetQueryKey({
          path: { group_api_id: groupId },
        }),
      });
    },
  });

  function handleToggle(apiIdentifier: string): void {
    setSelectedResponders((prev) => {
      const next = new Set(prev);
      if (next.has(apiIdentifier)) {
        if (next.size <= 1) {
          return next;
        }
        next.delete(apiIdentifier);
      } else {
        next.add(apiIdentifier);
      }
      return next;
    });
  }

  function handleSelectAll(): void {
    if (isAllMembers) {
      return;
    }
    setSelectedResponders(new Set(group.members.map((m) => m.api_identifier)));
  }

  function handleSave(): void {
    const responderIds = isAllMembers ? [] : Array.from(selectedResponders);
    mutation.mutate({
      body: { responder_api_identifiers: responderIds },
      path: { group_api_id: groupId },
    });
    setEditMode(false);
  }

  function handleCancel(): void {
    if (hasDesignatedResponders) {
      setSelectedResponders(new Set(group.designated_responders.map((r) => r.api_identifier)));
    } else {
      setSelectedResponders(new Set(group.members.map((m) => m.api_identifier)));
    }
    setEditMode(false);
  }

  return (
    <Container maxW="full">
      <Heading size="sm" py={4}>
        Designated Responders
      </Heading>
      <Text fontSize="sm" color="gray.500" mb={4}>
        Configure which members can respond to cyclic loops.
        When set, only designated responders can submit answers. Everyone else
        in the group will still receive the loop emails and can ask questions.
      </Text>
      <Text fontSize="sm" color="gray.500" mb={4} fontWeight="bold">
        {hasDesignatedResponders
          ? `${group.designated_responders.length} of ${group.members.length} members are designated responders.`
          : "All members can respond (default)."}
      </Text>
      <Box w={{ sm: "full", md: "50%" }}>
        {editMode ? (
          <VStack align="stretch" spacing={2}>
            <Button size="xs" variant="ghost" onClick={handleSelectAll} mb={2}>
              Select All
            </Button>
            {group.members.map((member) => (
              <Checkbox
                key={member.api_identifier}
                isChecked={selectedResponders.has(member.api_identifier)}
                onChange={() => handleToggle(member.api_identifier)}
                color={color}
              >
                {member.name} ({member.email})
              </Checkbox>
            ))}
          </VStack>
        ) : (
          <VStack align="stretch" spacing={1}>
            {(hasDesignatedResponders ? group.designated_responders : group.members).map(
              (user) => (
                <Text key={user.api_identifier} color={color} fontSize="sm">
                  {user.name} ({user.email})
                </Text>
              )
            )}
          </VStack>
        )}
        <Flex mt={4} gap={3}>
          <Button
            variant="primary"
            onClick={editMode ? handleSave : () => setEditMode(true)}
            isLoading={mutation.isPending}
          >
            {editMode ? "Save" : "Edit"}
          </Button>
          {editMode && (
            <Button onClick={handleCancel} isDisabled={mutation.isPending}>
              Cancel
            </Button>
          )}
        </Flex>
      </Box>
    </Container>
  );
}

export default GroupRespondersSettings;

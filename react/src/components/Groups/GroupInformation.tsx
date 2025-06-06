import {
    Box,
    Button,
    Flex,
    Heading,
    Input,
    Text,
    useColorModeValue
} from "@chakra-ui/react";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { GroupLinked } from "../../client";
import {
    readGroupPartiesGroupGroupApiIdGetQueryKey,
} from "../../client/@tanstack/react-query.gen";

function GroupInformation({ groupId }: { groupId: string }) {
  const queryClient = useQueryClient();
  const [editMode, setEditMode] = useState(false);
  const group = queryClient.getQueryData<GroupLinked>(
    readGroupPartiesGroupGroupApiIdGetQueryKey({
      path: { group_api_id: groupId },
    })
  );
  if (group === undefined) {
    return null;
  }
  const {
    register,
  } = useForm<GroupLinked>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: group.name,
    },
  });

  const toggleEditMode = () => {
    setEditMode(!editMode);
  };

  const textColor = useColorModeValue("ui.dark", "ui.light");
  const bgColor = useColorModeValue("ui.glass.light.background", "ui.glass.dark.background");
  const borderColor = useColorModeValue("ui.glass.light.border", "ui.glass.dark.border");

  return (
    <Box
      p={6}
      bg={bgColor}
      backdropFilter="blur(10px)"
      border="1px solid"
      borderColor={borderColor}
      borderRadius="lg"
      boxShadow="sm"
    >
      <Flex justify="space-between" align="center" mb={4}>
        <Heading size="md" color={textColor}>Group Information</Heading>
        <Button
          variant="glass"
          onClick={toggleEditMode}
          _hover={{ 
            opacity: 0.9,
            bg: "ui.primary",
          }}
          transition="all 0.2s ease-in-out"
        >
          Edit
        </Button>
      </Flex>
      
      <Box>
        <Text color={textColor} fontWeight="medium" mb={2}>Name</Text>
        {editMode ? (
          <Input
            id="name"
            {...register("name", { maxLength: 30 })}
            type="text"
            size="md"
          />
        ) : (
          <Text color={textColor} mb={4}>{group.name || "N/A"}</Text>
        )}
        
        <Text color={textColor} fontWeight="medium" mb={2}>Created At</Text>
        <Text color={textColor}>{new Date(group.created_at).toLocaleDateString()}</Text>
      </Box>
    </Box>
  );
}

export default GroupInformation;

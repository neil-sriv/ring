import { 
  Box, 
  VStack, 
  Heading,
  Button,
  Flex
} from "@chakra-ui/react";
import { useState } from "react";
import ReactJson from "react-json-view";
import { GroupKeyValueResponse } from "../../client";

export function GroupKeyValuesTable({ 
  keyValues 
}: { 
  keyValues: GroupKeyValueResponse 
}) {
  const [editableData, setEditableData] = useState(keyValues.key_values);
  const [isEditing, setIsEditing] = useState(false);

  const handleEdit = ({ updated_src }: { updated_src: any }) => {
    setEditableData(updated_src);
  };

  const handleSave = () => {
    // TODO: Implement actual save logic to backend
    console.log('Saving:', editableData);
    setIsEditing(false);
  };

  return (
    <VStack w="100%" spacing={4} align="stretch">
      <Flex justifyContent="space-between" alignItems="center">
        <Heading size="md">Group Key Values</Heading>
        {!isEditing ? (
          <Button 
            size="sm" 
            colorScheme="blue" 
            onClick={() => setIsEditing(true)}
          >
            Edit
          </Button>
        ) : (
          <Button 
            size="sm" 
            colorScheme="green" 
            onClick={handleSave}
          >
            Save
          </Button>
        )}
      </Flex>

      {Object.keys(editableData).length === 0 ? (
        <Box>No key-value pairs found</Box>
      ) : (
        <Box 
          border="1px solid" 
          borderColor="gray.200" 
          borderRadius="md" 
          p={4}
        >
          <ReactJson 
            src={editableData}
            onEdit={handleEdit}
            onAdd={handleEdit}
            onDelete={handleEdit}
            theme="monokai"
            enableClipboard={false}
            displayDataTypes={false}
            collapsed={false}
            editable={isEditing}
          />
        </Box>
      )}
    </VStack>
  );
}

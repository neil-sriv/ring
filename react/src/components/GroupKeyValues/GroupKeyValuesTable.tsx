import { 
  Table, 
  Thead, 
  Tbody, 
  Tr, 
  Th, 
  Td, 
  TableContainer,
  VStack,
  Heading,
  Box 
} from "@chakra-ui/react";
import { GroupKeyValueResponse } from "../../client";

// Utility function to flatten nested objects
function flattenObject(obj: any, parentKey = ''): { key: string, value: string }[] {
  const result: { key: string, value: string }[] = [];

  const processValue = (value: any, currentKey: string) => {
    // Convert null or undefined to string
    if (value === null || value === undefined) {
      result.push({ key: currentKey, value: 'null' });
      return;
    }

    // Handle primitive types
    if (typeof value === 'string' || 
        typeof value === 'number' || 
        typeof value === 'boolean') {
      result.push({ key: currentKey, value: String(value) });
      return;
    }

    // Handle arrays
    if (Array.isArray(value)) {
      result.push({ key: currentKey, value: JSON.stringify(value) });
      return;
    }

    // Handle nested objects
    if (typeof value === 'object') {
      Object.entries(value).forEach(([nestedKey, nestedValue]) => {
        const newKey = parentKey 
          ? `${parentKey}.${currentKey}.${nestedKey}` 
          : `${currentKey}.${nestedKey}`;
        processValue(nestedValue, newKey);
      });
    }
  };

  Object.entries(obj).forEach(([key, value]) => {
    processValue(value, key);
  });

  return result;
}

export function GroupKeyValuesTable({ 
  keyValues 
}: { 
  keyValues: GroupKeyValueResponse 
}) {
  // Flatten the key-value pairs, handling nested objects
  const keyValuePairs = Array.isArray(keyValues.key_values) 
    ? keyValues.key_values 
    : flattenObject(keyValues.key_values);

  return (
    <VStack w="100%" spacing={4} align="center">
      <Box textAlign="center" w="100%">
        <Heading size="md">Group Key Values</Heading>
      </Box>
      {keyValuePairs.length === 0 ? (
        <Box>No key-value pairs found</Box>
      ) : (
        <TableContainer w="100%">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Key</Th>
                <Th>Value</Th>
              </Tr>
            </Thead>
            <Tbody>
              {keyValuePairs.map((kv) => (
                <Tr key={kv.key}>
                  <Td>{kv.key}</Td>
                  <Td>{kv.value}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </TableContainer>
      )}
    </VStack>
  );
}

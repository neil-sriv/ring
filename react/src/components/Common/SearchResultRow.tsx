import { Badge, Flex, Td, Text, Tr } from "@chakra-ui/react";
import { type SearchResult } from "../../client";

interface SearchResultRowProps {
    result: SearchResult;
}

export function SearchResultRow({ result }: SearchResultRowProps) {
    return (
        <Tr _hover={{ bg: "gray.50" }} cursor="pointer">
            <Td>
                <Flex direction="column" gap={1}>
                    <Text fontWeight="medium">{result.model.api_identifier}</Text>
                    <Badge colorScheme="blue" width="fit-content">
                        {result.type.replace('Linked', '')}
                    </Badge>
                </Flex>
            </Td>
        </Tr>
    );
} 
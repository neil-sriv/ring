import { Badge, Flex, Td, Text, Tr } from "@chakra-ui/react";
import { type ResponseLinked, type SearchResult } from "../../client";

interface SearchResultRowProps {
    result: SearchResult;
}

function ResponseSearchResultRow({ result }: { result: SearchResult }) {
    const model = result.model as ResponseLinked;

    return (
        <Tr _hover={{ bg: "gray.200" }} cursor="pointer">
            <Td>
                <Flex direction="column" gap={2}>
                    <Flex gap={2} align="center">
                        <Badge colorScheme="blue">Response</Badge>
                        <Text fontWeight="medium">
                            Group A - Letter 1
                        </Text>
                    </Flex>
                    <Flex gap={2} align="center">
                        <Text fontWeight="medium">Q: {model.question.question_text}</Text>
                    </Flex>
                    <Flex gap={2} align="center">
                        <Text fontWeight="medium">by {model.participant.name}</Text>
                    </Flex>
                    <Text fontSize="sm" color="gray.600" noOfLines={2}>
                        {model.response_text}
                    </Text>
                </Flex>
            </Td>
        </Tr>
    );
}

function DefaultSearchResultRow({ result }: { result: SearchResult }) {
    return (
        <Tr _hover={{ bg: "gray.200" }} cursor="pointer">
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

export function SearchResultRow({ result }: SearchResultRowProps) {
    switch (result.type) {
        case 'ResponseLinked':
            return <ResponseSearchResultRow result={result} />;
        case 'QuestionLinked':
        case 'UserLinked':
        case 'GroupLinked':
        case 'LetterLinked':
        default:
            return <DefaultSearchResultRow result={result} />;
    }
} 
import { Badge, Flex, Td, Text, Tr } from "@chakra-ui/react";
import { Link } from "@tanstack/react-router";
import { type GroupLinked, type PublicLetter, type QuestionLinked, type ResponseLinked, type SearchResult, type UserLinked } from "../../client";

interface SearchResultRowProps {
    result: SearchResult;
}

function ResponseSearchResultRow({ result }: { result: SearchResult }) {
    const model = result.model as ResponseLinked;

    return (
        <Tr _hover={{ bg: "gray.200" }} cursor="pointer">
            <Td>
                <Link
                    to="/loops/$loopId"
                    params={{ loopId: model.letter?.api_identifier ?? "" }}
                    style={{ textDecoration: "none" }}
                >
                    <Flex direction="column" gap={2}>
                        <Flex gap={2} align="center">
                            <Badge colorScheme="blue">Response</Badge>
                            <Text fontWeight="medium">
                                {model.group?.name} - Letter {model.letter?.number}
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
                </Link>
            </Td>
        </Tr>
    );
}

function UserSearchResultRow({ result }: { result: SearchResult }) {
    const model = result.model as UserLinked;

    return (
        <Tr _hover={{ bg: "gray.200" }} cursor="pointer">
            <Td>
                <Flex direction="column" gap={2}>
                    <Flex gap={2} align="center">
                        <Badge colorScheme="green">User</Badge>
                        <Text fontWeight="medium">{model.name}</Text>
                    </Flex>
                    <Text fontSize="sm" color="gray.600">
                        Member of {model.groups.length} groups
                    </Text>
                </Flex>
            </Td>
        </Tr>
    );
}

function GroupSearchResultRow({ result }: { result: SearchResult }) {
    const model = result.model as GroupLinked;

    return (
        <Tr _hover={{ bg: "gray.200" }} cursor="pointer">
            <Td>
                <Link
                    to="/groups/$groupId/loops"
                    params={{ groupId: model.api_identifier }}
                    style={{ textDecoration: "none" }}
                >
                    <Flex direction="column" gap={2}>
                        <Flex gap={2} align="center">
                            <Badge colorScheme="purple">Group</Badge>
                            <Text fontWeight="medium">{model.name}</Text>
                        </Flex>
                        <Text fontSize="sm" color="gray.600">
                            {model.members.length} members • {model.letters.length} letters
                        </Text>
                    </Flex>
                </Link>
            </Td>
        </Tr>
    );
}

function QuestionSearchResultRow({ result }: { result: SearchResult }) {
    const model = result.model as QuestionLinked;
    const letter = model.letter as PublicLetter;

    return (
        <Tr _hover={{ bg: "gray.200" }} cursor="pointer">
            <Td>
                <Link
                    to="/loops/$loopId"
                    params={{ loopId: letter.api_identifier }}
                    style={{ textDecoration: "none" }}
                >
                    <Flex direction="column" gap={2}>
                        <Flex gap={2} align="center">
                            <Badge colorScheme="orange">Question</Badge>
                            <Text fontWeight="medium">
                                {letter.group.name} - Letter {letter.number}
                            </Text>
                        </Flex>
                        <Text fontSize="sm" color="gray.600" noOfLines={2}>
                            {model.question_text}
                        </Text>
                        <Text fontSize="sm" color="gray.500">
                            {model.responses.length} responses
                        </Text>
                    </Flex>
                </Link>
            </Td>
        </Tr>
    );
}

function LetterSearchResultRow({ result }: { result: SearchResult }) {
    const model = result.model as PublicLetter;

    return (
        <Tr _hover={{ bg: "gray.200" }} cursor="pointer">
            <Td>
                <Link
                    to="/loops/$loopId"
                    params={{ loopId: model.api_identifier }}
                    style={{ textDecoration: "none" }}
                >
                    <Flex direction="column" gap={2}>
                        <Flex gap={2} align="center">
                            <Badge colorScheme="teal">Letter</Badge>
                            <Text fontWeight="medium">
                                {model.group.name} - Letter {model.number}
                            </Text>
                        </Flex>
                        <Text fontSize="sm" color="gray.600">
                            {model.participants.length} participants • {model.questions.length} questions
                        </Text>
                    </Flex>
                </Link>
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
        case 'UserLinked':
            return <UserSearchResultRow result={result} />;
        case 'GroupLinked':
            return <GroupSearchResultRow result={result} />;
        case 'QuestionLinked':
            return <QuestionSearchResultRow result={result} />;
        case 'PublicLetter':
            return <LetterSearchResultRow result={result} />;
        default:
            return <DefaultSearchResultRow result={result} />;
    }
} 
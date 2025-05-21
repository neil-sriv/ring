import {
    Button,
    Container,
    Flex,
    Heading,
    Input,
    InputGroup,
    InputRightElement,
    Spinner,
    Table,
    TableContainer,
    Tbody,
    Td,
    Th,
    Thead,
    Tr
} from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { FaSearch } from "react-icons/fa";

import { useQuery } from "@tanstack/react-query";
import { type SearchResult } from "../../client";
import { performSearchSearchSearchSearchGetOptions } from "../../client/@tanstack/react-query.gen";

export const Route = createFileRoute("/_layout/search")({
    component: Search,
});

function SearchContent() {
    const [searchQuery, setSearchQuery] = useState("");
    const [isSearching, setIsSearching] = useState(false);

    const { data: searchResults, refetch } = useQuery({
        ...performSearchSearchSearchSearchGetOptions({
            query: {
                query: searchQuery,
            },
        }),
        enabled: false,
    });

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        setIsSearching(true);
        await refetch();
    };

    const getApiIdentifier = (result: SearchResult) => {
        if ('api_identifier' in result.model) {
            return result.model.api_identifier;
        }
        return 'Unknown';
    };

    return (
        <Container maxW="full" px={0}>
            <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12} px={4}>
                Search
            </Heading>
            <Flex py={8} px={4}>
                <InputGroup size="lg">
                    <Input
                        type="text"
                        placeholder="Search..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyPress={(e) => {
                            if (e.key === "Enter") {
                                handleSearch();
                            }
                        }}
                    />
                    <InputRightElement>
                        <Button
                            variant="ghost"
                            onClick={handleSearch}
                            _hover={{ bg: "transparent" }}
                            size="lg"
                        >
                            <FaSearch />
                        </Button>
                    </InputRightElement>
                </InputGroup>
            </Flex>

            {isSearching && searchResults && (
                <TableContainer px={4}>
                    <Table fontSize="md" size={{ base: "sm", md: "md" }}>
                        <Thead>
                            <Tr>
                                <Th>API Identifier</Th>
                            </Tr>
                        </Thead>
                        <Tbody>
                            {searchResults.results.map((result: SearchResult) => (
                                <Tr key={getApiIdentifier(result)}>
                                    <Td>{getApiIdentifier(result)}</Td>
                                </Tr>
                            ))}
                        </Tbody>
                    </Table>
                </TableContainer>
            )}
        </Container>
    );
}

function Search() {
    return (
        <Suspense fallback={<Spinner size="xl" />}>
            <SearchContent />
        </Suspense>
    );
} 
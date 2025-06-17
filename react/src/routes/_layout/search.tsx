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
    Th,
    Thead,
    Tr
} from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { FaSearch } from "react-icons/fa";

import { useQuery } from "@tanstack/react-query";
import { type SearchResult } from "../../client";
import { performSearchSearchSearchGetOptions } from "../../client/@tanstack/react-query.gen";
import { SearchResultRow } from "../../components/Common/SearchResultRow";

export const Route = createFileRoute("/_layout/search")({
    component: Search,
});

function SearchContent() {
    const [searchQuery, setSearchQuery] = useState("");
    const [isSearching, setIsSearching] = useState(false);

    const { data: searchResults, refetch } = useQuery({
        ...performSearchSearchSearchGetOptions({
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
                                <Th>Result</Th>
                            </Tr>
                        </Thead>
                        <Tbody>
                            {searchResults.results
                                .map((result: SearchResult) => (
                                    <SearchResultRow key={result.model.api_identifier} result={result} />
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
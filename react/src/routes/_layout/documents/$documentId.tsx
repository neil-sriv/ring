import {
    Box,
    Container,
    Heading,
    HStack,
    Spinner,
    Text,
    useColorModeValue,
} from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useRef, useState } from "react";
import { DocumentResponse } from "../../../client";
import { getDocumentEndpointNotebookDocumentsDocumentApiIdGetOptions } from "../../../client/@tanstack/react-query.gen";
import { CollabEditor } from "../../../components/Document/Editor";

type DocumentLoaderProps = {
    document: DocumentResponse;
};

export const Route = createFileRoute("/_layout/documents/$documentId")({
    loader: async ({
        params,
        context,
    }): Promise<DocumentLoaderProps> => {
        const document = await context.queryClient.ensureQueryData({
            ...getDocumentEndpointNotebookDocumentsDocumentApiIdGetOptions({
                path: {
                    document_api_id: params.documentId,
                },
            }),
        });

        return {
            document,
        };
    },
    component: DocumentContent,
});

function DocumentContentLoader() {
    const documentId = Route.useParams().documentId;
    const props = Route.useLoaderData();
    const textColor = useColorModeValue("ui.dark", "ui.light");
    const [isSaving, setIsSaving] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const savingStartTimeRef = useRef<number | null>(null);

    const handleSavingChange = (saving: boolean) => {
        if (saving) {
            savingStartTimeRef.current = Date.now();
            setIsSaving(true);
        } else {
            const elapsed = Date.now() - (savingStartTimeRef.current || 0);
            const remainingTime = Math.max(0, 1000 - elapsed);

            setTimeout(() => {
                setIsSaving(false);
            }, remainingTime);
        }
    };

    return (
        <Container maxW="full" mt={8}>
            <Box
                bg="ui.glass.light.background"
                backdropFilter="blur(10px)"
                border="1px solid"
                borderColor="ui.glass.light.border"
                _dark={{
                    bg: "ui.glass.dark.background",
                    borderColor: "ui.glass.dark.border",
                }}
                p={6}
                borderRadius="xl"
                boxShadow="md"
                mb={6}
            >
                <HStack justify="space-between" align="center">
                    <Heading size="lg" textAlign={{ base: "center", md: "left" }} color={textColor}>
                        {props.document.name}
                    </Heading>
                    <HStack
                        spacing={2}
                        bg="whiteAlpha.200"
                        px={3}
                        py={1}
                        borderRadius="md"
                        borderWidth="1px"
                        borderColor="whiteAlpha.300"
                        _dark={{
                            bg: "whiteAlpha.100",
                            borderColor: "whiteAlpha.200"
                        }}
                    >
                        {isSaving ? (
                            <>
                                <Spinner size="sm" color="blue.400" />
                                <Text fontSize="sm" color="gray.700" _dark={{ color: "gray.300" }}>
                                    Syncing...
                                </Text>
                            </>
                        ) : isEditing ? (
                            <Text fontSize="sm" color="orange.600" _dark={{ color: "orange.400" }}>
                                Editing...
                            </Text>
                        ) : (
                            <Text fontSize="sm" color="green.600" _dark={{ color: "green.400" }}>
                                Saved
                            </Text>
                        )}
                    </HStack>
                </HStack>
            </Box>
            <Box
                bg="ui.glass.light.background"
                backdropFilter="blur(10px)"
                border="1px solid"
                borderColor="ui.glass.light.border"
                _dark={{
                    bg: "ui.glass.dark.background",
                    borderColor: "ui.glass.dark.border",
                }}
                p={6}
                borderRadius="xl"
                boxShadow="md"
            >
                <CollabEditor
                    docId={documentId}
                    onSavingChange={handleSavingChange}
                    onEditingChange={setIsEditing}
                />
            </Box>
        </Container>
    );
}

function DocumentContent() {
    return (
        <Suspense fallback={<Spinner size="xl" />}>
            <DocumentContentLoader />
        </Suspense>
    );
}

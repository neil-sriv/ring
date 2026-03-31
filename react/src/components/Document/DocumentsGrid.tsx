import {
  Box,
  Button,
  Grid,
  HStack,
  Heading,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import type { DocumentResponse } from "../../client"
import {
  createDocumentEndpointNotebookDocumentsPostMutation,
  listDocumentsNotebookDocumentsGetOptions,
  listDocumentsNotebookDocumentsGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import { DocumentCard } from "./DocumentCard"

export function DocumentsGrid(props: {
  groupApiId: string
}): JSX.Element {
  const textColor = useColorModeValue("ui.dark", "ui.light")

  const { data: documents } = useSuspenseQuery({
    ...listDocumentsNotebookDocumentsGetOptions({
      query: {
        group_api_id: props.groupApiId,
      },
    }),
  })

  const queryClient = useQueryClient()

  const createDocumentMutation = useMutation({
    ...createDocumentEndpointNotebookDocumentsPostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listDocumentsNotebookDocumentsGetQueryKey({
          query: { group_api_id: props.groupApiId },
        }),
      })
    },
  })

  return (
    <Box p={4}>
      <VStack align="start" spacing={6}>
        <HStack justify="space-between" w="full">
          <Heading size="lg" color={textColor}>
            Documents
          </Heading>
          <HStack spacing={3}>
            <Button
              colorScheme="blue"
              size="sm"
              isLoading={createDocumentMutation.isPending}
              onClick={() => {
                createDocumentMutation.mutate({
                  body: {
                    group_api_id: props.groupApiId,
                    name: "Untitled Document",
                    content: "",
                  },
                })
              }}
            >
              New Document
            </Button>
          </HStack>
        </HStack>

        {documents.length === 0 ? (
          <Box
            textAlign="center"
            py={12}
            w="full"
            bg="ui.glass.light.background"
            backdropFilter="blur(10px)"
            border="1px solid"
            borderColor="ui.glass.light.border"
            _dark={{
              bg: "ui.glass.dark.background",
              borderColor: "ui.glass.dark.border",
            }}
            borderRadius="xl"
          >
            <VStack spacing={4}>
              <Text color={textColor} fontSize="lg">
                No documents yet
              </Text>
              <Text color="ui.dim" fontSize="sm">
                Create your first collaborative document to get started
              </Text>
              <Button
                colorScheme="blue"
                onClick={() => {
                  createDocumentMutation.mutate({
                    body: {
                      group_api_id: props.groupApiId,
                      name: "My First Document",
                      content: "",
                    },
                  })
                }}
              >
                Create Document
              </Button>
            </VStack>
          </Box>
        ) : (
          <Grid
            templateColumns={{
              base: "1fr",
              md: "repeat(2, 1fr)",
              lg: "repeat(3, 1fr)",
            }}
            gap={6}
            w="full"
          >
            {documents.map((document: DocumentResponse) => (
              <DocumentCard key={document.api_identifier} document={document} />
            ))}
          </Grid>
        )}
      </VStack>
    </Box>
  )
}

import {
  Badge,
  Box,
  Heading,
  LinkBox,
  LinkOverlay,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import type { DocumentResponse } from "../../client"

export function DocumentCard(props: {
  document: DocumentResponse
}): JSX.Element {
  const textColor = useColorModeValue("ui.dark", "ui.light")
  const subtextColor = useColorModeValue("ui.dim", "ui.dim")

  const createdDate = new Date(props.document.created_at)
  const updatedDate = props.document.updated_at
    ? new Date(props.document.updated_at)
    : null

  // Get content preview (first 100 characters)
  const getContentPreview = () => {
    if (!props.document.content) return "No content yet"
    const plainText = props.document.content.replace(/<[^>]*>/g, "") // Strip HTML tags
    return plainText.length > 50
      ? `${plainText.substring(0, 50)}...`
      : plainText
  }

  return (
    <LinkBox height="100%">
      <Box
        h="100%"
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
        transition="all 0.2s"
        _hover={{
          transform: "translateY(-4px)",
          boxShadow: "xl",
          borderColor: "ui.main",
        }}
        position="relative"
      >
        <Badge
          colorScheme="blue"
          variant="subtle"
          fontSize="xs"
          position="absolute"
          top={2}
          right={2}
        >
          v{props.document.latest_snapshot_version}
        </Badge>

        <LinkOverlay
          as={Link}
          to={`/documents/${props.document.api_identifier}`}
          _hover={{ textDecoration: "none" }}
        >
          <VStack align="start" spacing={3}>
            <Heading size="md" color={textColor}>
              {props.document.name}
            </Heading>

            <Text color={subtextColor} fontSize="sm" noOfLines={3}>
              {getContentPreview()}
            </Text>

            <VStack align="start" spacing={1} w="full">
              <Text color={subtextColor} fontSize="xs">
                Created: {createdDate.toLocaleDateString()}
              </Text>
              {updatedDate && (
                <Text color={subtextColor} fontSize="xs">
                  Updated: {updatedDate.toLocaleDateString()}
                </Text>
              )}
            </VStack>
          </VStack>
        </LinkOverlay>
      </Box>
    </LinkBox>
  )
}

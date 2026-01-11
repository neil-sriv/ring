import { Container, Heading, Text, VStack } from "@chakra-ui/react"

export default function MaintenanceMode() {
  return (
    <Container maxW="container.md" py={20}>
      <VStack spacing={8} textAlign="center">
        <Heading size="2xl">🛠️ Maintenance Mode</Heading>
        <Text fontSize="xl">
          We're currently performing scheduled maintenance to improve our
          infrastructure. Please check back later.
        </Text>
      </VStack>
    </Container>
  )
}

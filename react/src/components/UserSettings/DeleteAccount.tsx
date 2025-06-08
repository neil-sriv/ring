import {
    Box,
    Button,
    Container,
    Heading,
    Text,
    useColorModeValue,
    useDisclosure,
    VStack,
} from "@chakra-ui/react";

import DeleteConfirmation from "./DeleteConfirmation";

const DeleteAccount = () => {
  const confirmationModal = useDisclosure()
  const textColor = useColorModeValue("ui.dark", "ui.light");

  return (
    <Container maxW="full">
      <VStack spacing={6} align="stretch">
        <Heading size="sm" color={textColor}>
          Delete Account
        </Heading>
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
          <VStack spacing={4} align="stretch">
            <Text color={textColor}>
              Permanently delete your data and everything associated with your
              account.
            </Text>
            <Button 
              variant="danger" 
              onClick={confirmationModal.onOpen}
              _hover={{ transform: "translateY(-2px)" }}
              transition="all 0.2s"
            >
              Delete
            </Button>
          </VStack>
        </Box>
        <DeleteConfirmation
          isOpen={confirmationModal.isOpen}
          onClose={confirmationModal.onClose}
        />
      </VStack>
    </Container>
  )
}

export default DeleteAccount

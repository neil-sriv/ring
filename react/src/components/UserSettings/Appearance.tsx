import {
  Badge,
    Box,
  Container,
  Heading,
  Radio,
  RadioGroup,
  Stack,
  useColorMode,
    useColorModeValue,
    VStack,
} from "@chakra-ui/react";

const Appearance = () => {
  const { colorMode, toggleColorMode } = useColorMode()
  const textColor = useColorModeValue("ui.dark", "ui.light");

  return (
      <Container maxW="full">
      <VStack spacing={6} align="stretch">
        <Heading size="sm" color={textColor}>
          Appearance
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
        <RadioGroup onChange={toggleColorMode} value={colorMode}>
            <Stack spacing={4}>
              <Radio 
                value="light" 
                colorScheme="teal"
                _hover={{ transform: "translateX(4px)" }}
                transition="all 0.2s"
              >
              Light Mode
                <Badge ml="2" colorScheme="teal">
                Default
              </Badge>
            </Radio>
              <Radio 
                value="dark" 
                colorScheme="teal"
                _hover={{ transform: "translateX(4px)" }}
                transition="all 0.2s"
              >
              Dark Mode
            </Radio>
          </Stack>
        </RadioGroup>
        </Box>
      </VStack>
      </Container>
  )
}

export default Appearance

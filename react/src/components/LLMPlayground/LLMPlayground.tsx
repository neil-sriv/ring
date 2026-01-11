import {
  Box,
  Button,
  Container,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  Text,
  Textarea,
  VStack,
  useToast,
} from "@chakra-ui/react"
import { useMutation } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { useState } from "react"
import type {
  GenerateCompletionLlmCompletionPostError,
  GenerateCompletionLlmCompletionPostResponse,
} from "../../client"
import { generateCompletionLlmCompletionPostMutation } from "../../client/@tanstack/react-query.gen"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export function LLMPlayground(): JSX.Element {
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const toast = useToast()

  const { mutate: sendMessage, isPending } = useMutation({
    ...generateCompletionLlmCompletionPostMutation({
      body: {
        prompt: message,
      },
    }),
    onSuccess: (data: GenerateCompletionLlmCompletionPostResponse) => {
      // Add user message to history
      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: message,
          timestamp: new Date(),
        },
      ])

      // Add assistant response to history
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.text,
          timestamp: new Date(),
        },
      ])

      setMessage("")
    },
    onError: (error: AxiosError<GenerateCompletionLlmCompletionPostError>) => {
      toast({
        title: "Error",
        description:
          error.response?.data.detail?.[0].msg || "Failed to send message",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    sendMessage({
      body: {
        prompt: message,
      },
    })
  }

  return (
    <Container maxW="container.md" py={8}>
      <VStack spacing={6} align="stretch">
        <Heading size="lg">LLM Playground</Heading>
        <Text>
          This is a playground for talking to LLMs. I don't have chat history or
          memory, so it's not very useful yet.
        </Text>

        {/* Message History */}
        <Box
          flex="1"
          overflowY="auto"
          maxH="60vh"
          borderWidth="1px"
          borderRadius="md"
          p={4}
        >
          <VStack spacing={4} align="stretch">
            {messages.map((msg, index) => (
              <Flex
                key={index}
                justify={msg.role === "user" ? "flex-end" : "flex-start"}
              >
                <Box
                  maxW="70%"
                  bg={msg.role === "user" ? "blue.500" : "gray.100"}
                  color={msg.role === "user" ? "white" : "black"}
                  p={3}
                  borderRadius="lg"
                >
                  <Text>{msg.content}</Text>
                  <Text
                    fontSize="xs"
                    color={msg.role === "user" ? "whiteAlpha.700" : "gray.500"}
                  >
                    {msg.timestamp.toLocaleTimeString()}
                  </Text>
                </Box>
              </Flex>
            ))}
          </VStack>
        </Box>

        {/* Message Input */}
        <Box as="form" onSubmit={handleSubmit}>
          <FormControl isRequired>
            <FormLabel>Message</FormLabel>
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your message here..."
              size="lg"
              rows={3}
            />
          </FormControl>

          <Button
            mt={4}
            type="submit"
            colorScheme="blue"
            isLoading={isPending}
            loadingText="Sending..."
          >
            Send Message
          </Button>
        </Box>
      </VStack>
    </Container>
  )
}

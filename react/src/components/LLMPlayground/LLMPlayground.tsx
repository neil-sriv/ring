import {
    Box,
    Button,
    Container,
    FormControl,
    FormLabel,
    Heading,
    Textarea,
    useToast,
    VStack,
} from "@chakra-ui/react";
import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { useState } from "react";
import { GenerateCompletionLlmCompletionPostError, GenerateCompletionLlmCompletionPostResponse } from "../../client";
import { generateCompletionLlmCompletionPostMutation } from "../../client/@tanstack/react-query.gen";

export function LLMPlayground(): JSX.Element {
    const [message, setMessage] = useState("");
    const toast = useToast();

    const { mutate: sendMessage, isPending } = useMutation({
        ...generateCompletionLlmCompletionPostMutation({
            body: {
                prompt: message,
            },
        }),
        onSuccess: (data: GenerateCompletionLlmCompletionPostResponse) => {
            // toast({
            //     title: "Success",
            //     description: "Message sent successfully",
            //     status: "success",
            //     duration: 3000,
            //     isClosable: true,
            // });
            setMessage(data.text);
        },
        onError: (error: AxiosError<GenerateCompletionLlmCompletionPostError>) => {
            toast({
                title: "Error",
                description: error instanceof Error ? error.message : "Failed to send message",
                status: "error",
                duration: 3000,
                isClosable: true,
            });
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!message.trim()) return;

        sendMessage({
            body: {
                prompt: message,
            },
        });
    };

    return (
        <Container maxW="container.md" py={8}>
            <VStack spacing={6} align="stretch">
                <Heading size="lg">LLM Playground</Heading>

                <Box as="form" onSubmit={handleSubmit}>
                    <FormControl isRequired>
                        <FormLabel>Message</FormLabel>
                        <Textarea
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="Type your message here..."
                            size="lg"
                            rows={4}
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
    );
}

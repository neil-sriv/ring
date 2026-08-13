import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useMutation } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { Loader2 } from "lucide-react"
import { useState } from "react"
import type {
  GenerateCompletionLlmCompletionPostError,
  GenerateCompletionLlmCompletionPostResponse,
} from "../../client"
import { generateCompletionLlmCompletionPostMutation } from "../../client/@tanstack/react-query.gen"
import useCustomToast from "../../hooks/useCustomToast"
import { formatApiErrorDetail } from "../../util/misc"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export function LLMPlayground(): JSX.Element {
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const showToast = useCustomToast()

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
      showToast(
        "Error",
        formatApiErrorDetail(
          error.response?.data?.detail,
          "Failed to send message",
        ),
        "error",
      )
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
    <div className="max-w-2xl mx-auto py-8 px-4">
      <div className="flex flex-col gap-6">
        <h2 className="text-2xl font-bold">LLM Playground</h2>
        <p>
          This is a playground for talking to LLMs. I don't have chat history or
          memory, so it's not very useful yet.
        </p>

        {/* Message History */}
        <div className="flex-1 overflow-y-auto max-h-[60vh] border rounded-md p-4">
          <div className="flex flex-col gap-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[70%] p-3 rounded-lg ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground"
                  }`}
                >
                  <p>{msg.content}</p>
                  <p
                    className={`text-xs ${
                      msg.role === "user"
                        ? "text-primary-foreground/70"
                        : "text-muted-foreground"
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Message Input */}
        <form onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="message">Message</Label>
            <Textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your message here..."
              rows={3}
              required
            />
          </div>

          <Button className="mt-4" type="submit" disabled={isPending}>
            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isPending ? "Sending..." : "Send Message"}
          </Button>
        </form>
      </div>
    </div>
  )
}

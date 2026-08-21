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
    <div className="w-full max-w-2xl">
      <h3 className="text-base font-semibold">LLM playground</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        This is a playground for talking to LLMs. I don't have chat history or
        memory, so it's not very useful yet.
      </p>

      {messages.length > 0 && (
        <div className="mt-6 flex max-h-[60vh] flex-col gap-4 overflow-y-auto">
          {messages.map((msg, index) =>
            msg.role === "user" ? (
              <div key={index} className="flex flex-col gap-1">
                <p className="text-xs text-muted-foreground">
                  You · {msg.timestamp.toLocaleTimeString()}
                </p>
                <p className="text-sm leading-relaxed text-foreground">
                  {msg.content}
                </p>
              </div>
            ) : (
              <div key={index} className="rounded-lg border bg-muted/50 px-4 py-3">
                <p className="font-display text-base leading-relaxed text-foreground">
                  {msg.content}
                </p>
                <p className="mt-1.5 text-xs text-muted-foreground">
                  {msg.timestamp.toLocaleTimeString()}
                </p>
              </div>
            ),
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6">
        <div className="flex flex-col gap-1.5">
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
          {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          {isPending ? "Sending…" : "Send message"}
        </Button>
      </form>
    </div>
  )
}

import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { apiUrl, wsUrl } from "@/lib/apiUrl"
import { cn } from "@/lib/utils"
import Placeholder from "@tiptap/extension-placeholder"
import { TextStyleKit } from "@tiptap/extension-text-style"
import type { Editor } from "@tiptap/react"
import { EditorContent, useEditor, useEditorState } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import {
  Bold,
  Code,
  Heading1,
  Heading2,
  Heading3,
  Italic,
  List,
  ListOrdered,
  Minus,
  Pilcrow,
  Quote,
  Redo,
  Strikethrough,
  Undo,
} from "lucide-react"
import type React from "react"
import { useEffect, useRef } from "react"

export type NotebookWsStatus = "connecting" | "connected" | "reconnecting"

function toolbarButtonClass(isActive = false) {
  return cn(
    "h-8 w-8 px-0 text-muted-foreground hover:bg-accent hover:text-foreground",
    isActive && "bg-accent text-foreground",
  )
}

function MenuBar({ editor }: { editor: Editor }) {
  const editorState = useEditorState({
    editor,
    selector: (ctx) => {
      return {
        isBold: ctx.editor.isActive("bold") ?? false,
        canBold: ctx.editor.can().chain().toggleBold().run() ?? false,
        isItalic: ctx.editor.isActive("italic") ?? false,
        canItalic: ctx.editor.can().chain().toggleItalic().run() ?? false,
        isStrike: ctx.editor.isActive("strike") ?? false,
        canStrike: ctx.editor.can().chain().toggleStrike().run() ?? false,
        isCode: ctx.editor.isActive("code") ?? false,
        canCode: ctx.editor.can().chain().toggleCode().run() ?? false,
        isParagraph: ctx.editor.isActive("paragraph") ?? false,
        isHeading1: ctx.editor.isActive("heading", { level: 1 }) ?? false,
        isHeading2: ctx.editor.isActive("heading", { level: 2 }) ?? false,
        isHeading3: ctx.editor.isActive("heading", { level: 3 }) ?? false,
        isBulletList: ctx.editor.isActive("bulletList") ?? false,
        isOrderedList: ctx.editor.isActive("orderedList") ?? false,
        isCodeBlock: ctx.editor.isActive("codeBlock") ?? false,
        isBlockquote: ctx.editor.isActive("blockquote") ?? false,
        canUndo: ctx.editor.can().chain().undo().run() ?? false,
        canRedo: ctx.editor.can().chain().redo().run() ?? false,
      }
    },
  })

  return (
    <div className="rounded-lg border bg-card p-1">
      <TooltipProvider>
        <div className="flex flex-wrap items-center gap-0.5">
          {/* Text Formatting */}
          <div className="flex gap-0.5">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isBold)}
                  onClick={() => editor.chain().focus().toggleBold().run()}
                  disabled={!editorState.canBold}
                >
                  <Bold className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Bold</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isItalic)}
                  onClick={() => editor.chain().focus().toggleItalic().run()}
                  disabled={!editorState.canItalic}
                >
                  <Italic className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Italic</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isStrike)}
                  onClick={() => editor.chain().focus().toggleStrike().run()}
                  disabled={!editorState.canStrike}
                >
                  <Strikethrough className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Strikethrough</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isCode)}
                  onClick={() => editor.chain().focus().toggleCode().run()}
                  disabled={!editorState.canCode}
                >
                  <Code className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Code</TooltipContent>
            </Tooltip>
          </div>

          <div className="mx-1 h-5 w-px bg-border" />

          {/* Headings */}
          <div className="flex gap-0.5">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isParagraph)}
                  onClick={() => editor.chain().focus().setParagraph().run()}
                >
                  <Pilcrow className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Paragraph</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isHeading1)}
                  onClick={() =>
                    editor.chain().focus().toggleHeading({ level: 1 }).run()
                  }
                >
                  <Heading1 className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Heading 1</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isHeading2)}
                  onClick={() =>
                    editor.chain().focus().toggleHeading({ level: 2 }).run()
                  }
                >
                  <Heading2 className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Heading 2</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isHeading3)}
                  onClick={() =>
                    editor.chain().focus().toggleHeading({ level: 3 }).run()
                  }
                >
                  <Heading3 className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Heading 3</TooltipContent>
            </Tooltip>
          </div>

          <div className="mx-1 h-5 w-px bg-border" />

          {/* Lists and Blocks */}
          <div className="flex gap-0.5">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isBulletList)}
                  onClick={() =>
                    editor.chain().focus().toggleBulletList().run()
                  }
                >
                  <List className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Bullet List</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isOrderedList)}
                  onClick={() =>
                    editor.chain().focus().toggleOrderedList().run()
                  }
                >
                  <ListOrdered className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Ordered List</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isCodeBlock)}
                  onClick={() => editor.chain().focus().toggleCodeBlock().run()}
                >
                  <Code className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Code Block</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass(editorState.isBlockquote)}
                  onClick={() =>
                    editor.chain().focus().toggleBlockquote().run()
                  }
                >
                  <Quote className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Blockquote</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass()}
                  onClick={() =>
                    editor.chain().focus().setHorizontalRule().run()
                  }
                >
                  <Minus className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Horizontal Rule</TooltipContent>
            </Tooltip>
          </div>

          <div className="mx-1 h-5 w-px bg-border" />

          {/* History */}
          <div className="flex gap-0.5">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass()}
                  onClick={() => editor.chain().focus().undo().run()}
                  disabled={!editorState.canUndo}
                >
                  <Undo className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Undo</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className={toolbarButtonClass()}
                  onClick={() => editor.chain().focus().redo().run()}
                  disabled={!editorState.canRedo}
                >
                  <Redo className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Redo</TooltipContent>
            </Tooltip>
          </div>
        </div>
      </TooltipProvider>
    </div>
  )
}

export const CollabEditor: React.FC<{
  docId: string
  onSavingChange?: (isSaving: boolean) => void
  onEditingChange?: (isEditing: boolean) => void
  onConnectionChange?: (status: NotebookWsStatus) => void
}> = ({ docId, onSavingChange, onEditingChange, onConnectionChange }) => {
  const editorRef = useRef<any>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const lastContentRef = useRef<string>("")
  const editingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const lastSentMessageIdRef = useRef<string>("")
  const isUpdatingFromWebSocketRef = useRef<boolean>(false)
  const wsSendTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const wsReconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  )
  const pendingContentRef = useRef<string>("")
  const onConnectionChangeRef = useRef(onConnectionChange)
  onConnectionChangeRef.current = onConnectionChange
  const hasConnectedOnceRef = useRef(false)

  useEffect(() => {
    const accessToken = localStorage.getItem("access_token") ?? ""
    const documentUrl = apiUrl(`/api/v1/notebook/documents/${docId}`)
    const notebookWsUrl = wsUrl(
      `/api/v1/ws/notebook/${docId}?token=${encodeURIComponent(accessToken)}`,
    )
    let cancelled = false
    hasConnectedOnceRef.current = false

    // Load existing content
    const loadContent = async () => {
      try {
        const response = await fetch(documentUrl, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        })
        if (response.ok) {
          const data = await response.json()
          if (data.content && editorRef.current) {
            editorRef.current.commands.setContent(data.content)
            lastContentRef.current = data.content
          }
        }
      } catch (error) {
        console.error("Failed to load content:", error)
      }
    }

    // Setup WebSocket for real-time collaboration
    const setupWebSocket = () => {
      if (cancelled) {
        return
      }
      if (wsReconnectTimeoutRef.current) {
        clearTimeout(wsReconnectTimeoutRef.current)
        wsReconnectTimeoutRef.current = null
      }

      onConnectionChangeRef.current?.(
        hasConnectedOnceRef.current ? "reconnecting" : "connecting",
      )
      wsRef.current = new WebSocket(notebookWsUrl)

      wsRef.current.onopen = () => {
        if (cancelled) {
          return
        }
        hasConnectedOnceRef.current = true
        onConnectionChangeRef.current?.("connected")
      }

      wsRef.current.onmessage = (event) => {
        try {
          // Handle both text and binary data
          let messageData: {
            type?: unknown
            content?: unknown
            messageId?: unknown
          }
          if (typeof event.data === "string") {
            messageData = JSON.parse(event.data)
          } else if (event.data instanceof ArrayBuffer) {
            // Convert ArrayBuffer to string
            const decoder = new TextDecoder()
            const text = decoder.decode(event.data)
            messageData = JSON.parse(text)
          } else if (event.data instanceof Blob) {
            // Handle Blob data
            event.data.text().then((text: string) => {
              try {
                const data = JSON.parse(text)
                if (
                  data.type === "content_update" &&
                  data.content !== lastContentRef.current
                ) {
                  // Skip if this is our own message to prevent infinite loop
                  if (
                    data.messageId &&
                    data.messageId === lastSentMessageIdRef.current
                  ) {
                    return
                  }

                  if (editorRef.current) {
                    // Set flag to prevent onUpdate from firing
                    isUpdatingFromWebSocketRef.current = true
                    editorRef.current.commands.setContent(data.content)
                    lastContentRef.current = data.content
                    // Reset flag after a brief delay
                    setTimeout(() => {
                      isUpdatingFromWebSocketRef.current = false
                    }, 50)
                  }
                }
              } catch (error) {
                // Leave parse errors quiet; connection status covers outages.
                console.debug("Failed to parse WebSocket Blob message:", error)
              }
            })
            return // Exit early for async Blob handling
          } else {
            console.debug("Unknown WebSocket message type:", typeof event.data)
            return
          }

          if (
            messageData.type === "content_update" &&
            typeof messageData.content === "string" &&
            messageData.content !== lastContentRef.current
          ) {
            // Skip if this is our own message to prevent infinite loop
            if (
              typeof messageData.messageId === "string" &&
              messageData.messageId === lastSentMessageIdRef.current
            ) {
              return
            }

            if (editorRef.current) {
              // Set flag to prevent onUpdate from firing
              isUpdatingFromWebSocketRef.current = true
              editorRef.current.commands.setContent(messageData.content)
              lastContentRef.current = messageData.content
              // Reset flag after a brief delay
              setTimeout(() => {
                isUpdatingFromWebSocketRef.current = false
              }, 100)
            }
          }
        } catch (error) {
          // Leave parse errors quiet; connection status covers outages.
          console.debug("Failed to parse WebSocket message:", error)
        }
      }

      wsRef.current.onclose = () => {
        if (cancelled) {
          return
        }
        onConnectionChangeRef.current?.(
          hasConnectedOnceRef.current ? "reconnecting" : "connecting",
        )
        wsReconnectTimeoutRef.current = setTimeout(setupWebSocket, 1000)
      }

      wsRef.current.onerror = () => {
        // Browsers often fire error then close; surface via reconnecting status.
        if (!cancelled) {
          onConnectionChangeRef.current?.(
            hasConnectedOnceRef.current ? "reconnecting" : "connecting",
          )
        }
      }
    }

    loadContent()
    setupWebSocket()

    return () => {
      cancelled = true
      if (wsReconnectTimeoutRef.current) {
        clearTimeout(wsReconnectTimeoutRef.current)
        wsReconnectTimeoutRef.current = null
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
      // Clean up timeouts
      if (wsSendTimeoutRef.current) {
        clearTimeout(wsSendTimeoutRef.current)
      }
    }
  }, [docId])

  const editor = useEditor({
    extensions: [
      TextStyleKit,
      StarterKit,
      Placeholder.configure({ placeholder: "Start typing here…" }),
    ],
    editable: true,
    editorProps: { attributes: { class: "prosemirror-editor outline-none" } },
    onCreate: ({ editor }) => {
      editorRef.current = editor
    },
    onUpdate: ({ editor }) => {
      // Skip if we're updating from WebSocket to prevent infinite loop
      if (isUpdatingFromWebSocketRef.current) {
        return
      }

      const content = editor.getHTML()
      if (content !== lastContentRef.current) {
        lastContentRef.current = content

        // Set editing state immediately when user types
        onEditingChange?.(true)

        // Clear any existing editing timeout
        if (editingTimeoutRef.current) {
          clearTimeout(editingTimeoutRef.current)
        }

        // Set editing timeout to clear editing state after 1 second of inactivity
        editingTimeoutRef.current = setTimeout(() => {
          onEditingChange?.(false)
        }, 1000)

        // Debounced WebSocket send to prevent rapid-fire messages
        pendingContentRef.current = content

        // Clear any existing WebSocket send timeout
        if (wsSendTimeoutRef.current) {
          clearTimeout(wsSendTimeoutRef.current)
        }

        // Send to WebSocket with minimal debouncing
        wsSendTimeoutRef.current = setTimeout(() => {
          if (
            wsRef.current &&
            wsRef.current.readyState === WebSocket.OPEN &&
            pendingContentRef.current === content
          ) {
            const messageId = `${Date.now()}-${Math.random()
              .toString(36)
              .substr(2, 9)}`
            lastSentMessageIdRef.current = messageId
            wsRef.current.send(
              JSON.stringify({
                type: "content_update",
                content: content,
                docId: docId,
                messageId: messageId,
              }),
            )
          }
        }, 10) // Minimal debounce - just enough to batch rapid changes

        // Debounced sync to backend
        clearTimeout((window as any).syncTimeout)
        ;(window as any).syncTimeout = setTimeout(async () => {
          onSavingChange?.(true)
          try {
            const accessToken = localStorage.getItem("access_token") ?? ""

            await fetch(apiUrl(`/api/v1/notebook/documents/${docId}`), {
              method: "PUT",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
              },
              body: JSON.stringify({ content: content }),
            })
          } catch (error) {
            console.error("Failed to sync to backend:", error)
          } finally {
            onSavingChange?.(false)
          }
        }, 1000)
      }
    },
  })

  if (!editor) {
    return (
      <div className="py-8 text-center text-sm text-muted-foreground">
        Initializing editor...
      </div>
    )
  }

  return (
    <div>
      <MenuBar editor={editor} />
      <EditorContent
        editor={editor}
        style={{
          minHeight: "400px",
          fontSize: "16px",
          lineHeight: "1.6",
          outline: "none",
        }}
      />
      <style
        // biome-ignore lint/security/noDangerouslySetInnerHtml: Required to style ProseMirror document content reliably.
        dangerouslySetInnerHTML={{
          __html: `
                        .prosemirror-editor {
                            min-height: 400px;
                            padding: 1rem 0.5rem;
                            color: var(--color-foreground);
                        }

                        .prosemirror-editor ::selection {
                            background-color: color-mix(in oklab, var(--color-primary) 20%, transparent);
                        }

                        .prosemirror-editor p.is-editor-empty:first-child::before {
                            content: attr(data-placeholder);
                            float: left;
                            height: 0;
                            pointer-events: none;
                            color: var(--color-muted-foreground);
                        }

                        .prosemirror-editor h1,
                        .prosemirror-editor h2,
                        .prosemirror-editor h3,
                        .prosemirror-editor h4,
                        .prosemirror-editor h5,
                        .prosemirror-editor h6 {
                            line-height: 1.1;
                            margin-top: 2rem;
                            margin-bottom: 1rem;
                            font-weight: 600;
                        }

                        .prosemirror-editor h1,
                        .prosemirror-editor h2 {
                            font-family: var(--font-display);
                            letter-spacing: -0.025em;
                        }

                        .prosemirror-editor h1 {
                            font-size: 1.8rem;
                            margin-top: 2.5rem;
                        }

                        .prosemirror-editor h2 {
                            font-size: 1.5rem;
                            margin-top: 2rem;
                        }

                        .prosemirror-editor h3 {
                            font-size: 1.3rem;
                        }

                        .prosemirror-editor h4 {
                            font-size: 1.2rem;
                        }

                        .prosemirror-editor h5 {
                            font-size: 1.1rem;
                        }

                        .prosemirror-editor h6 {
                            font-size: 1rem;
                        }

                        .prosemirror-editor ul,
                        .prosemirror-editor ol {
                            padding-left: 1.5rem;
                            margin: 1rem 0;
                        }

                        .prosemirror-editor li {
                            margin: 0.25rem 0;
                        }

                        .prosemirror-editor code {
                            background-color: var(--color-muted);
                            border-radius: 0.25rem;
                            padding: 0.125rem 0.25rem;
                            font-family: var(--font-mono);
                            font-size: 0.9em;
                        }

                        .prosemirror-editor pre {
                            background-color: var(--color-muted);
                            border-radius: 0.5rem;
                            padding: 1rem;
                            margin: 1rem 0;
                            overflow-x: auto;
                        }

                        .prosemirror-editor pre code {
                            background: none;
                            padding: 0;
                        }

                        .prosemirror-editor blockquote {
                            border-left: 3px solid var(--color-border);
                            margin: 1rem 0;
                            padding-left: 1rem;
                            font-style: italic;
                            color: var(--color-muted-foreground);
                        }

                        .prosemirror-editor hr {
                            border: none;
                            border-top: 1px solid var(--color-border);
                            margin: 2rem 0;
                        }

                        .prosemirror-editor p {
                            margin: 0.5rem 0;
                        }

                        .prosemirror-editor strong {
                            font-weight: bold;
                        }

                        .prosemirror-editor em {
                            font-style: italic;
                        }

                        .prosemirror-editor s {
                            text-decoration: line-through;
                        }
                    `,
        }}
      />
    </div>
  )
}

import { readUserMePartiesMeGetOptions } from "@/client/@tanstack/react-query.gen"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { apiUrl, wsUrl } from "@/lib/apiUrl"
import { cn } from "@/lib/utils"
import { useQuery } from "@tanstack/react-query"
import Collaboration from "@tiptap/extension-collaboration"
import CollaborationCaret from "@tiptap/extension-collaboration-caret"
import Placeholder from "@tiptap/extension-placeholder"
import { TextStyleKit } from "@tiptap/extension-text-style"
import type { Transaction } from "@tiptap/pm/state"
import type { Editor } from "@tiptap/react"
import { EditorContent, useEditor, useEditorState } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import { ySyncPluginKey } from "@tiptap/y-tiptap"
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
import { useEffect, useRef, useState } from "react"
import { WebsocketProvider } from "y-websocket"
import * as Y from "yjs"

export type NotebookWsStatus = "connecting" | "connected" | "reconnecting"

const CARET_COLORS = [
  "#b45309", // amber
  "#0e7490", // cyan
  "#15803d", // green
  "#7c3aed", // violet
  "#be185d", // pink
  "#b91c1c", // red
  "#1d4ed8", // blue
  "#4d7c0f", // lime
]

function caretColorFor(seed: string): string {
  let hash = 0
  for (const char of seed) {
    hash = (hash * 31 + char.charCodeAt(0)) | 0
  }
  return CARET_COLORS[Math.abs(hash) % CARET_COLORS.length]
}

function isRemoteTransaction(transaction: Transaction): boolean {
  const meta = transaction.getMeta(ySyncPluginKey) as
    | { isChangeOrigin?: boolean }
    | undefined
  return Boolean(meta?.isChangeOrigin)
}

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

type CollabSession = {
  ydoc: Y.Doc
  provider: WebsocketProvider
}

/** Create one Y.Doc + WebSocket provider per document (StrictMode-safe). */
function useCollabSession(
  docId: string,
  onConnectionChange?: (status: NotebookWsStatus) => void,
): CollabSession | null {
  const [session, setSession] = useState<CollabSession | null>(null)
  const onConnectionChangeRef = useRef(onConnectionChange)
  onConnectionChangeRef.current = onConnectionChange

  useEffect(() => {
    const accessToken = localStorage.getItem("access_token") ?? ""
    const ydoc = new Y.Doc()
    const provider = new WebsocketProvider(
      wsUrl("/api/v1/ws/notebook"),
      docId,
      ydoc,
      { params: { token: accessToken } },
    )

    let hasConnectedOnce = false
    onConnectionChangeRef.current?.("connecting")
    provider.on("status", ({ status }: { status: string }) => {
      if (status === "connected") {
        hasConnectedOnce = true
        onConnectionChangeRef.current?.("connected")
      } else {
        onConnectionChangeRef.current?.(
          hasConnectedOnce ? "reconnecting" : "connecting",
        )
      }
    })

    setSession({ ydoc, provider })
    return () => {
      setSession(null)
      provider.destroy()
      ydoc.destroy()
    }
  }, [docId])

  return session
}

export const CollabEditor: React.FC<{
  docId: string
  legacyContent?: string
  onSavingChange?: (isSaving: boolean) => void
  onEditingChange?: (isEditing: boolean) => void
  onConnectionChange?: (status: NotebookWsStatus) => void
}> = ({
  docId,
  legacyContent,
  onSavingChange,
  onEditingChange,
  onConnectionChange,
}) => {
  const session = useCollabSession(docId, onConnectionChange)

  if (!session) {
    return (
      <div className="py-8 text-center text-sm text-muted-foreground">
        Initializing editor...
      </div>
    )
  }

  return (
    <CollabEditorInner
      key={docId}
      docId={docId}
      session={session}
      legacyContent={legacyContent}
      onSavingChange={onSavingChange}
      onEditingChange={onEditingChange}
    />
  )
}

const CollabEditorInner: React.FC<{
  docId: string
  session: CollabSession
  legacyContent?: string
  onSavingChange?: (isSaving: boolean) => void
  onEditingChange?: (isEditing: boolean) => void
}> = ({ docId, session, legacyContent, onSavingChange, onEditingChange }) => {
  const { data: me } = useQuery({ ...readUserMePartiesMeGetOptions({}) })
  const editingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const hasSeededRef = useRef(false)

  const editor = useEditor(
    {
      extensions: [
        TextStyleKit,
        // Collaboration provides its own CRDT-aware undo/redo history.
        StarterKit.configure({ undoRedo: false }),
        Placeholder.configure({ placeholder: "Start typing here…" }),
        Collaboration.configure({ document: session.ydoc }),
        CollaborationCaret.configure({
          provider: session.provider,
          user: {
            name: me?.name ?? "Anonymous",
            color: caretColorFor(me?.api_identifier ?? "anonymous"),
          },
        }),
      ],
      editable: true,
      editorProps: {
        attributes: { class: "prosemirror-editor outline-none" },
      },
      onUpdate: ({ editor, transaction }) => {
        // Remote peers' changes arrive through the same update pipeline;
        // only local edits should drive the editing indicator and autosave.
        if (isRemoteTransaction(transaction)) {
          return
        }

        onEditingChange?.(true)
        if (editingTimeoutRef.current) {
          clearTimeout(editingTimeoutRef.current)
        }
        editingTimeoutRef.current = setTimeout(() => {
          onEditingChange?.(false)
        }, 1000)

        // Debounced write of the rendered-HTML projection. The CRDT state on
        // the WebSocket is the source of truth; this keeps REST reads,
        // letters, and search working off documents.content.
        if (saveTimeoutRef.current) {
          clearTimeout(saveTimeoutRef.current)
        }
        const content = editor.getHTML()
        saveTimeoutRef.current = setTimeout(async () => {
          onSavingChange?.(true)
          try {
            const accessToken = localStorage.getItem("access_token") ?? ""
            await fetch(apiUrl(`/api/v1/notebook/documents/${docId}`), {
              method: "PUT",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
              },
              body: JSON.stringify({ content }),
            })
          } catch (error) {
            console.error("Failed to sync content projection:", error)
          } finally {
            onSavingChange?.(false)
          }
        }, 1000)
      },
    },
    [session],
  )

  // Keep the caret identity in sync once the profile loads.
  useEffect(() => {
    if (editor && me) {
      editor.commands.updateUser({
        name: me.name,
        color: caretColorFor(me.api_identifier),
      })
    }
  }, [editor, me])

  // Seed documents created before the CRDT rewrite: their content exists only
  // as stored HTML. Once synced, if the shared doc is still empty and we are
  // the only connected client, populate it from the HTML projection. When
  // other clients are present, don't latch the seeded flag — retry on
  // awareness changes so whichever client ends up alone performs the seed.
  useEffect(() => {
    if (!editor) {
      return
    }
    const { provider, ydoc } = session

    const seedIfNeeded = () => {
      if (!provider.synced || hasSeededRef.current) {
        return
      }
      const fragment = ydoc.getXmlFragment("default")
      if (fragment.length > 0) {
        hasSeededRef.current = true
        return
      }
      const hasLegacyContent =
        legacyContent && legacyContent !== "" && legacyContent !== "<p></p>"
      if (!hasLegacyContent) {
        hasSeededRef.current = true
        return
      }
      const aloneInRoom = provider.awareness.getStates().size <= 1
      if (!aloneInRoom) {
        return
      }
      hasSeededRef.current = true
      editor.commands.setContent(legacyContent)
    }

    provider.on("sync", seedIfNeeded)
    provider.awareness.on("change", seedIfNeeded)
    seedIfNeeded()
    return () => {
      provider.off("sync", seedIfNeeded)
      provider.awareness.off("change", seedIfNeeded)
    }
  }, [editor, session, legacyContent])

  useEffect(() => {
    return () => {
      if (editingTimeoutRef.current) {
        clearTimeout(editingTimeoutRef.current)
      }
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
    }
  }, [])

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
          __html: editorStyles,
        }}
      />
    </div>
  )
}

const editorStyles = `
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

    /* Tailwind preflight resets list-style to none;
       restore markers inside the editor. */
    .prosemirror-editor ul,
    .prosemirror-editor ol {
        padding-left: 1.5rem;
        margin: 1rem 0;
    }

    .prosemirror-editor ul {
        list-style-type: disc;
    }

    .prosemirror-editor ul ul {
        list-style-type: circle;
    }

    .prosemirror-editor ol {
        list-style-type: decimal;
    }

    .prosemirror-editor li {
        margin: 0.25rem 0;
    }

    .prosemirror-editor li::marker {
        color: var(--color-muted-foreground);
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

    /* Remote collaborator carets (CollaborationCaret awareness) */
    .prosemirror-editor .collaboration-carets__caret {
        border-left: 1px solid;
        border-right: 1px solid;
        margin-left: -1px;
        margin-right: -1px;
        pointer-events: none;
        position: relative;
        word-break: normal;
    }

    .prosemirror-editor .collaboration-carets__label {
        border-radius: 3px 3px 3px 0;
        color: #fff;
        font-size: 0.7rem;
        font-weight: 600;
        left: -1px;
        line-height: normal;
        padding: 0.1rem 0.3rem;
        position: absolute;
        top: -1.4em;
        user-select: none;
        white-space: nowrap;
    }

    /* Remote collaborator text selections */
    .prosemirror-editor .ProseMirror-yjs-selection {
        border-radius: 2px;
    }
`

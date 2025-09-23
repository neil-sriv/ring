import { Box, Button, ButtonGroup, HStack, Icon, Tooltip } from '@chakra-ui/react';
import Placeholder from '@tiptap/extension-placeholder';
import { TextStyleKit } from '@tiptap/extension-text-style';
import type { Editor } from '@tiptap/react';
import { EditorContent, useEditor, useEditorState } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import React, { useEffect, useRef } from 'react';
import { FaBold, FaCode, FaItalic, FaListOl, FaListUl, FaMinus, FaQuoteLeft, FaRedo, FaStrikethrough, FaUndo } from 'react-icons/fa';

function MenuBar({ editor }: { editor: Editor }) {
    const editorState = useEditorState({
        editor,
        selector: ctx => {
            return {
                isBold: ctx.editor.isActive('bold') ?? false,
                canBold: ctx.editor.can().chain().toggleBold().run() ?? false,
                isItalic: ctx.editor.isActive('italic') ?? false,
                canItalic: ctx.editor.can().chain().toggleItalic().run() ?? false,
                isStrike: ctx.editor.isActive('strike') ?? false,
                canStrike: ctx.editor.can().chain().toggleStrike().run() ?? false,
                isCode: ctx.editor.isActive('code') ?? false,
                canCode: ctx.editor.can().chain().toggleCode().run() ?? false,
                isParagraph: ctx.editor.isActive('paragraph') ?? false,
                isHeading1: ctx.editor.isActive('heading', { level: 1 }) ?? false,
                isHeading2: ctx.editor.isActive('heading', { level: 2 }) ?? false,
                isHeading3: ctx.editor.isActive('heading', { level: 3 }) ?? false,
                isBulletList: ctx.editor.isActive('bulletList') ?? false,
                isOrderedList: ctx.editor.isActive('orderedList') ?? false,
                isCodeBlock: ctx.editor.isActive('codeBlock') ?? false,
                isBlockquote: ctx.editor.isActive('blockquote') ?? false,
                canUndo: ctx.editor.can().chain().undo().run() ?? false,
                canRedo: ctx.editor.can().chain().redo().run() ?? false,
            }
        },
    });

    return (
        <Box
            p={3}
            borderBottom="1px solid"
            borderColor="gray.200"
            bg="gray.50"
            _dark={{
                bg: "gray.700",
                borderColor: "gray.600"
            }}
        >
            <HStack spacing={2} wrap="wrap">
                {/* Text Formatting */}
                <ButtonGroup size="sm" variant="outline" spacing={1}>
                    <Tooltip label="Bold">
                        <Button
                            onClick={() => editor.chain().focus().toggleBold().run()}
                            isDisabled={!editorState.canBold}
                            colorScheme={editorState.isBold ? "blue" : "gray"}
                            variant={editorState.isBold ? "solid" : "outline"}
                        >
                            <Icon as={FaBold} />
                        </Button>
                    </Tooltip>
                    <Tooltip label="Italic">
                        <Button
                            onClick={() => editor.chain().focus().toggleItalic().run()}
                            isDisabled={!editorState.canItalic}
                            colorScheme={editorState.isItalic ? "blue" : "gray"}
                            variant={editorState.isItalic ? "solid" : "outline"}
                        >
                            <Icon as={FaItalic} />
                        </Button>
                    </Tooltip>
                    <Tooltip label="Strikethrough">
                        <Button
                            onClick={() => editor.chain().focus().toggleStrike().run()}
                            isDisabled={!editorState.canStrike}
                            colorScheme={editorState.isStrike ? "blue" : "gray"}
                            variant={editorState.isStrike ? "solid" : "outline"}
                        >
                            <Icon as={FaStrikethrough} />
                        </Button>
                    </Tooltip>
                    <Tooltip label="Code">
                        <Button
                            onClick={() => editor.chain().focus().toggleCode().run()}
                            isDisabled={!editorState.canCode}
                            colorScheme={editorState.isCode ? "blue" : "gray"}
                            variant={editorState.isCode ? "solid" : "outline"}
                        >
                            <Icon as={FaCode} />
                        </Button>
                    </Tooltip>
                </ButtonGroup>

                {/* Headings */}
                <ButtonGroup size="sm" variant="outline" spacing={1}>
                    <Tooltip label="Paragraph">
                        <Button
                            onClick={() => editor.chain().focus().setParagraph().run()}
                            colorScheme={editorState.isParagraph ? "blue" : "gray"}
                            variant={editorState.isParagraph ? "solid" : "outline"}
                        >
                            P
                        </Button>
                    </Tooltip>
                    <Tooltip label="Heading 1">
                        <Button
                            onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
                            colorScheme={editorState.isHeading1 ? "blue" : "gray"}
                            variant={editorState.isHeading1 ? "solid" : "outline"}
                        >
                            H1
                        </Button>
                    </Tooltip>
                    <Tooltip label="Heading 2">
                        <Button
                            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                            colorScheme={editorState.isHeading2 ? "blue" : "gray"}
                            variant={editorState.isHeading2 ? "solid" : "outline"}
                        >
                            H2
                        </Button>
                    </Tooltip>
                    <Tooltip label="Heading 3">
                        <Button
                            onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
                            colorScheme={editorState.isHeading3 ? "blue" : "gray"}
                            variant={editorState.isHeading3 ? "solid" : "outline"}
                        >
                            H3
                        </Button>
                    </Tooltip>
                </ButtonGroup>

                {/* Lists and Blocks */}
                <ButtonGroup size="sm" variant="outline" spacing={1}>
                    <Tooltip label="Bullet List">
                        <Button
                            onClick={() => editor.chain().focus().toggleBulletList().run()}
                            colorScheme={editorState.isBulletList ? "blue" : "gray"}
                            variant={editorState.isBulletList ? "solid" : "outline"}
                        >
                            <Icon as={FaListUl} />
                        </Button>
                    </Tooltip>
                    <Tooltip label="Ordered List">
                        <Button
                            onClick={() => editor.chain().focus().toggleOrderedList().run()}
                            colorScheme={editorState.isOrderedList ? "blue" : "gray"}
                            variant={editorState.isOrderedList ? "solid" : "outline"}
                        >
                            <Icon as={FaListOl} />
                        </Button>
                    </Tooltip>
                    <Tooltip label="Code Block">
                        <Button
                            onClick={() => editor.chain().focus().toggleCodeBlock().run()}
                            colorScheme={editorState.isCodeBlock ? "blue" : "gray"}
                            variant={editorState.isCodeBlock ? "solid" : "outline"}
                        >
                            <Icon as={FaCode} />
                        </Button>
                    </Tooltip>
                    <Tooltip label="Blockquote">
                        <Button
                            onClick={() => editor.chain().focus().toggleBlockquote().run()}
                            colorScheme={editorState.isBlockquote ? "blue" : "gray"}
                            variant={editorState.isBlockquote ? "solid" : "outline"}
                        >
                            <Icon as={FaQuoteLeft} />
                        </Button>
                    </Tooltip>
                    <Tooltip label="Horizontal Rule">
                        <Button
                            onClick={() => editor.chain().focus().setHorizontalRule().run()}
                        >
                            <Icon as={FaMinus} />
                        </Button>
                    </Tooltip>
                </ButtonGroup>

                {/* History */}
                <ButtonGroup size="sm" variant="outline" spacing={1}>
                    <Tooltip label="Undo">
                        <Button
                            onClick={() => editor.chain().focus().undo().run()}
                            isDisabled={!editorState.canUndo}
                        >
                            <Icon as={FaUndo} />
                        </Button>
                    </Tooltip>
                    <Tooltip label="Redo">
                        <Button
                            onClick={() => editor.chain().focus().redo().run()}
                            isDisabled={!editorState.canRedo}
                        >
                            <Icon as={FaRedo} />
                        </Button>
                    </Tooltip>
                </ButtonGroup>
            </HStack>
        </Box>
    );
}

export const CollabEditor: React.FC<{ docId: string; onSavingChange?: (isSaving: boolean) => void; onEditingChange?: (isEditing: boolean) => void }> = ({ docId, onSavingChange, onEditingChange }) => {
    const editorRef = useRef<any>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const lastContentRef = useRef<string>('');
    const editingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const lastSentMessageIdRef = useRef<string>('');
    const isUpdatingFromWebSocketRef = useRef<boolean>(false);
    const wsSendTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const pendingContentRef = useRef<string>('');

    useEffect(() => {
        const accessToken = localStorage.getItem('access_token') ?? '';
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const wsUrl = `${baseUrl.replace('http', 'ws')}/api/v1/ws/notebook/${docId}?token=${encodeURIComponent(accessToken)}`;

        // Load existing content
        const loadContent = async () => {
            try {
                const response = await fetch(`${baseUrl}/api/v1/notebook/documents/${docId}`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                    },
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data.content && editorRef.current) {
                        editorRef.current.commands.setContent(data.content);
                        lastContentRef.current = data.content;
                    }
                }
            } catch (error) {
                console.error('Failed to load content:', error);
            }
        };

        // Setup WebSocket for real-time collaboration
        const setupWebSocket = () => {
            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onopen = () => {
                console.log('WebSocket connected');
            };

            wsRef.current.onmessage = (event) => {
                try {
                    // Handle both text and binary data
                    let messageData;
                    if (typeof event.data === 'string') {
                        messageData = JSON.parse(event.data);
                    } else if (event.data instanceof ArrayBuffer) {
                        // Convert ArrayBuffer to string
                        const decoder = new TextDecoder();
                        const text = decoder.decode(event.data);
                        messageData = JSON.parse(text);
                    } else if (event.data instanceof Blob) {
                        // Handle Blob data
                        event.data.text().then((text: string) => {
                            try {
                                const data = JSON.parse(text);
                                if (data.type === 'content_update' && data.content !== lastContentRef.current) {
                                    // Skip if this is our own message to prevent infinite loop
                                    if (data.messageId && data.messageId === lastSentMessageIdRef.current) {
                                        return;
                                    }

                                    if (editorRef.current) {
                                        // Set flag to prevent onUpdate from firing
                                        isUpdatingFromWebSocketRef.current = true;
                                        editorRef.current.commands.setContent(data.content);
                                        lastContentRef.current = data.content;
                                        // Reset flag after a brief delay
                                        setTimeout(() => {
                                            isUpdatingFromWebSocketRef.current = false;
                                        }, 50);
                                    }
                                }
                            } catch (error) {
                                console.error('Failed to parse WebSocket Blob message:', error);
                            }
                        });
                        return; // Exit early for async Blob handling
                    } else {
                        console.warn('Unknown WebSocket message type:', typeof event.data);
                        return;
                    }

                    if (messageData.type === 'content_update' && messageData.content !== lastContentRef.current) {
                        // Skip if this is our own message to prevent infinite loop
                        if (messageData.messageId && messageData.messageId === lastSentMessageIdRef.current) {
                            return;
                        }

                        if (editorRef.current) {
                            // Set flag to prevent onUpdate from firing
                            isUpdatingFromWebSocketRef.current = true;
                            editorRef.current.commands.setContent(messageData.content);
                            lastContentRef.current = messageData.content;
                            // Reset flag after a brief delay
                            setTimeout(() => {
                                isUpdatingFromWebSocketRef.current = false;
                            }, 100);
                        }
                    }
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            wsRef.current.onclose = () => {
                console.log('WebSocket disconnected, reconnecting...');
                setTimeout(setupWebSocket, 1000);
            };

            wsRef.current.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        };

        loadContent();
        setupWebSocket();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            // Clean up timeouts
            if (wsSendTimeoutRef.current) {
                clearTimeout(wsSendTimeoutRef.current);
            }
        };
    }, [docId]);

    const editor = useEditor({
        extensions: [
            TextStyleKit,
            StarterKit,
            Placeholder.configure({ placeholder: 'Start typing here…' }),
        ],
        editable: true,
        editorProps: { attributes: { class: 'prosemirror-editor outline-none' } },
        onCreate: ({ editor }) => {
            editorRef.current = editor;
        },
        onUpdate: ({ editor }) => {
            // Skip if we're updating from WebSocket to prevent infinite loop
            if (isUpdatingFromWebSocketRef.current) {
                return;
            }

            const content = editor.getHTML();
            if (content !== lastContentRef.current) {
                lastContentRef.current = content;

                // Set editing state immediately when user types
                onEditingChange?.(true);

                // Clear any existing editing timeout
                if (editingTimeoutRef.current) {
                    clearTimeout(editingTimeoutRef.current);
                }

                // Set editing timeout to clear editing state after 1 second of inactivity
                editingTimeoutRef.current = setTimeout(() => {
                    onEditingChange?.(false);
                }, 1000);

                // Debounced WebSocket send to prevent rapid-fire messages
                pendingContentRef.current = content;

                // Clear any existing WebSocket send timeout
                if (wsSendTimeoutRef.current) {
                    clearTimeout(wsSendTimeoutRef.current);
                }

                // Send to WebSocket with minimal debouncing
                wsSendTimeoutRef.current = setTimeout(() => {
                    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && pendingContentRef.current === content) {
                        const messageId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                        lastSentMessageIdRef.current = messageId;
                        wsRef.current.send(JSON.stringify({
                            type: 'content_update',
                            content: content,
                            docId: docId,
                            messageId: messageId
                        }));
                    }
                }, 10); // Minimal debounce - just enough to batch rapid changes

                // Debounced sync to backend
                clearTimeout((window as any).syncTimeout);
                (window as any).syncTimeout = setTimeout(async () => {
                    onSavingChange?.(true);
                    try {
                        const accessToken = localStorage.getItem('access_token') ?? '';
                        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

                        await fetch(`${baseUrl}/api/v1/notebook/documents/${docId}`, {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${accessToken}`,
                            },
                            body: JSON.stringify({ content: content }),
                        });
                    } catch (error) {
                        console.error('Failed to sync to backend:', error);
                    } finally {
                        onSavingChange?.(false);
                    }
                }, 1000);
            }
        },
    });

    if (!editor) {
        return (
            <Box textAlign="center" py={8}>
                Initializing editor...
            </Box>
        );
    }

    return (
        <Box minH="100vh">
            <Box
                bg="gray.50"
                borderRadius="lg"
                p={6}
                border="1px solid"
                borderColor="gray.200"
                boxShadow="sm"
                transition="all 0.2s"
                _dark={{
                    bg: "gray.800",
                    borderColor: "gray.600"
                }}
                _focusWithin={{
                    borderColor: "blue.400",
                    boxShadow: "0 0 0 1px var(--chakra-colors-blue-400)"
                }}
            >
                <MenuBar editor={editor} />
                <EditorContent
                    editor={editor}
                    style={{
                        minHeight: "400px",
                        fontSize: "16px",
                        lineHeight: "1.6",
                        outline: "none"
                    }}
                />
                <style dangerouslySetInnerHTML={{
                    __html: `
                        .prosemirror-editor {
                            min-height: 400px;
                            padding: 1rem;
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
                            font-weight: bold;
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
                            background-color: rgba(0, 0, 0, 0.1);
                            border-radius: 0.25rem;
                            padding: 0.125rem 0.25rem;
                            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                            font-size: 0.9em;
                        }
                        
                        .prosemirror-editor pre {
                            background-color: rgba(0, 0, 0, 0.05);
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
                            border-left: 3px solid #e2e8f0;
                            margin: 1rem 0;
                            padding-left: 1rem;
                            font-style: italic;
                        }
                        
                        .prosemirror-editor hr {
                            border: none;
                            border-top: 1px solid #e2e8f0;
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
                    `
                }} />
            </Box>
        </Box>
    );
};
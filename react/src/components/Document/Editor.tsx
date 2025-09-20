import { Box } from '@chakra-ui/react';
import Placeholder from '@tiptap/extension-placeholder';
import { EditorContent, useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import React, { useEffect, useRef } from 'react';

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
                                        }, 100);
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
            <Box borderWidth="1px" borderRadius="md" p={4} minH="100vh">
                <Box textAlign="center" py={8}>
                    Initializing editor...
                </Box>
            </Box>
        );
    }

    return (
        <Box borderWidth="1px" borderRadius="md" p={4} minH="100vh">
            <EditorContent editor={editor} />
        </Box>
    );
};
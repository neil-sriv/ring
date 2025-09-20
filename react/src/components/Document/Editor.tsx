import { Box } from '@chakra-ui/react';
import Placeholder from '@tiptap/extension-placeholder';
import { EditorContent, useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import React, { useEffect, useRef } from 'react';

export const CollabEditor: React.FC<{ docId: string }> = ({ docId }) => {
    const editorRef = useRef<any>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const lastContentRef = useRef<string>('');

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
                    const data = JSON.parse(event.data);
                    if (data.type === 'content_update' && data.content !== lastContentRef.current) {
                        if (editorRef.current) {
                            editorRef.current.commands.setContent(data.content);
                            lastContentRef.current = data.content;
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
            const content = editor.getHTML();
            if (content !== lastContentRef.current) {
                lastContentRef.current = content;

                // Send to WebSocket
                if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                    wsRef.current.send(JSON.stringify({
                        type: 'content_update',
                        content: content,
                        docId: docId
                    }));
                }

                // Debounced sync to backend
                clearTimeout((window as any).syncTimeout);
                (window as any).syncTimeout = setTimeout(async () => {
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
                    }
                }, 2000);
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
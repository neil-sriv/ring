// Editor.tsx
import { Box } from '@chakra-ui/react';
import CodeBlock from '@tiptap/extension-code-block';
import Collaboration from '@tiptap/extension-collaboration';
import CollaborationCursor from '@tiptap/extension-collaboration-cursor';
import Placeholder from '@tiptap/extension-placeholder';
import { EditorContent, useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import React, { useEffect, useState } from 'react';
import { WebsocketProvider } from 'y-websocket';
import * as Y from 'yjs';
import { UserUnlinked } from '../../client';

interface Props {
    docId: string;
    user: UserUnlinked
}

export const CollabEditor: React.FC<Props> = ({ docId, user }) => {
    const [provider, setProvider] = useState<WebsocketProvider | null>(null);
    const [ydoc] = useState(new Y.Doc());

    useEffect(() => {
        // Get the access token from localStorage
        const accessToken = localStorage.getItem('access_token');

        if (!accessToken) {
            console.error('No access token found');
            return;
        }

        const wsUrl = `wss://localhost/api/v1/ws/notebook/`;
        const p = new WebsocketProvider(wsUrl, docId, ydoc, {
            params: {
                token: accessToken,
            },
        });
        setProvider(p);

        return () => {
            p.destroy();
            ydoc.destroy();
        };
    }, [docId, ydoc]);

    const editor = useEditor({
        extensions: [
            StarterKit,
            CodeBlock,
            Placeholder.configure({ placeholder: 'Start typing here...' }),
            Collaboration.configure({ document: ydoc }),
            ...(provider ? [CollaborationCursor.configure({
                provider,
                user: {
                    name: user.name,
                    color: "#f87171"
                },
            })] : []),
        ],
        editable: true,
    });

    // Update editor extensions when provider becomes available
    useEffect(() => {
        if (editor && provider) {
            editor.extensionManager.extensions.forEach(ext => {
                if (ext.name === 'collaborationCursor') {
                    ext.options.provider = provider;
                }
            });
        }
    }, [editor, provider]);

    return (
        <Box borderWidth="1px" borderRadius="md" p={4} minH="100vh">
            <EditorContent editor={editor} />
        </Box>
    );
};

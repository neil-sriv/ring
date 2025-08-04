# Letter Comments & Discussion Feature Design Document

## Overview
This document outlines the design for adding a question-level commenting feature to Ring. Users will be able to comment on questions (viewing all responses collectively) to create group discussions around each question topic.

## ✅ Backend Implementation Status: COMPLETED

## Requirements Summary

### Core Features
- **Comments are at the question level** - users comment on the question and can see all responses together
- **All group members can comment** (not limited to letter participants)
- **Flat comment structure** (no threading/replies in v1)
- **Users can comment anytime** on past or current letters
- **Timestamps on all comments**
- **Group admins can delete comments**
- **No notifications in v1**

### Example User Flow
1. User views a letter and clicks on a question (e.g., "What is your favorite color?")
2. They see all responses from participants grouped together
3. Below the responses, they see a comment section where group members discuss the responses
4. Any group member can add a comment about the collective responses

## Technical Design

### Data Model

```sql
-- New table for comments
CREATE TABLE comment (
    id SERIAL PRIMARY KEY,
    api_identifier VARCHAR(255) UNIQUE NOT NULL, -- Format: com_xxxxxx
    question_id INTEGER NOT NULL REFERENCES question(id),
    author_id INTEGER NOT NULL REFERENCES user(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    deleted_by_id INTEGER REFERENCES user(id), -- Track who deleted
    
    INDEX idx_comment_question (question_id),
    INDEX idx_comment_author (author_id),
    INDEX idx_comment_created (created_at DESC)
);
```

### API Endpoints (✅ Implemented)

#### Create Comment
```
POST /letters/questions/{question_api_id}/comments
Body: {
    "content": "Great responses! I'm surprised so many people chose blue."
}
Response: CommentLinked object
```

#### Get Comments for a Question
```
GET /letters/questions/{question_api_id}/comments
Query params:
  - skip (default: 0)
  - limit (default: 50, max: 100)
  - include_deleted (default: false, admin only)
Response: {
    "comments": [...],
    "total": 145,
    "skip": 0,
    "limit": 50,
    "has_more": true
}
```

#### Update Comment (Author only)
```
PATCH /letters/comments/{comment_api_id}
Body: {
    "content": "Updated comment text"
}
Response: CommentLinked object
```

#### Delete Comment (Admin only)
```
DELETE /letters/comments/{comment_api_id}
Response: {"message": "Comment deleted successfully"}
```

### Backend Implementation (✅ Completed)

#### Models (`ring/letters/models/comment_model.py`) - ✅ Implemented
- Comment model with soft delete functionality
- Relationships to Question and User models
- API identifier prefix: `com_`
- Includes updated_at field for edit tracking

#### Schemas (`ring/letters/schemas/comment.py`) - ✅ Implemented
- `CommentCreate`: For creating new comments
- `CommentUpdate`: For updating existing comments
- `CommentUnlinked`: Basic comment data without relationships
- `CommentLinked`: Full comment data with author and question relationships

#### CRUD Operations (`ring/letters/crud/comment.py`) - ✅ Implemented
- `create_comment()`: Create new comment
- `get_comments_for_question()`: Get paginated comments with optional deleted
- `update_comment()`: Update comment content
- `soft_delete_comment()`: Soft delete with deleted_by tracking
- `can_user_edit_comment()`: Check edit permissions
- `can_user_delete_comment()`: Check delete permissions

#### Authorization Updates - ✅ Implemented
- Comments integrated into Casbin resource hierarchy
- Comments inherit permissions from parent questions
- Group membership automatically grants comment access
- Permission rules:
  - **Create**: Any group member can comment
  - **Read**: Any group member can read (admins see deleted)
  - **Update**: Only comment author can edit
  - **Delete**: Only system admins can soft delete

### Frontend Implementation - 🚧 Partially Complete

#### New Components (✅ Created)

1. **CommentSection** (`react/src/components/Comments/CommentSection.tsx`) - ✅ Created
   - Displays all comments for a question
   - Add comment form with real-time submission
   - Shows comment count
   - Pagination support (load more button)

2. **CommentItem** (`react/src/components/Comments/CommentItem.tsx`) - ✅ Created
   - Individual comment display with author info
   - Edit functionality for comment authors
   - Delete button (admin only)
   - Timestamp formatting with date-fns
   - Visual indication for deleted comments

3. **Integration with PublishedQuestion** - ✅ Completed
   - CommentSection integrated into existing question view
   - Comments appear below all responses

#### UI/UX Flow
```
┌─────────────────────────────────────────┐
│ Question: What is your favorite color?  │
├─────────────────────────────────────────┤
│ Responses (5 participants)              │
│                                         │
│ • John: "Blue - reminds me of ocean"   │
│ • Sarah: "Green - nature!"             │
│ • Mike: "Red - bold and energetic"     │
│ • Lisa: "Purple - royal and creative"  │
│ • Tom: "Blue - calming effect"         │
├─────────────────────────────────────────┤
│ Discussion (12 comments)                │
│                                         │
│ Jane (2 hours ago):                    │
│ "Interesting that blue is so popular!" │
│                                         │
│ Admin Bob (1 hour ago):                │
│ "Great responses everyone!"            │
│                                         │
│ [Add comment input box]                │
└─────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Backend MVP - ✅ COMPLETED
- [x] Database migration for comment table
- [x] Backend models, schemas, and CRUD operations
- [x] API endpoints with authorization
- [x] Comprehensive test suite
- [x] Integration with existing permission system

### Phase 2: Frontend Implementation - 🚧 IN PROGRESS
- [x] Basic frontend components (CommentSection, CommentItem)
- [x] Integration with existing question view
- [x] Comment display and creation UI
- [x] Admin moderation tools (delete functionality)
- [ ] API client regeneration to include comment types
- [ ] Fix TypeScript types after API client update
- [ ] Add proper error handling for network failures
- [ ] Add loading states for comment operations

### Phase 3: Enhancements
- [x] Comment pagination (backend ready)
- [ ] Real-time comment count updates
- [ ] Improved UI/UX
- [ ] Comment search/filter

### Phase 3: Future Features
- [ ] Rich text/markdown support
- [ ] Comment editing
- [ ] Notification system
- [ ] Reactions/likes
- [ ] Threading/replies
- [ ] @mentions

## Security Considerations
- Sanitize comment content to prevent XSS
- Rate limiting on comment creation
- Audit trail for deleted comments
- Group membership validation

## Performance Considerations
- Index on question_id for fast retrieval
- Pagination to handle many comments
- Consider caching comment counts
- Lazy load comments (don't load by default with question)

## Testing Strategy - ✅ Backend Tests Completed
- ✅ Unit tests for CRUD operations (`test_comment_crud.py`)
- ✅ API endpoint tests with various permissions (`test_comment_api.py`)
- ✅ Model tests (`test_comment_model.py`)
- ✅ Factory for test data creation (`CommentFactory`)
- ⏳ Frontend component tests (pending)
- ⏳ Integration tests for full flow (pending)

### Running Tests
```bash
# Run comment tests
ring test run ring/tests/unit/letters/test_comment_model.py
ring test run ring/tests/unit/letters/test_comment_crud.py
ring test run ring/tests/unit/letters/test_comment_api.py
```
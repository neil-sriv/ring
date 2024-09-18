export const $AddMembers = {
	properties: {
		member_emails: {
	type: 'array',
	contains: {
	type: 'string',
},
	isRequired: true,
},
	},
} as const;

export const $Body_login_access_token_login_access_token_post = {
	properties: {
		grant_type: {
	type: 'any-of',
	contains: [{
	type: 'string',
	pattern: 'password',
}, {
	type: 'null',
}],
},
		username: {
	type: 'string',
	isRequired: true,
},
		password: {
	type: 'string',
	isRequired: true,
},
		scope: {
	type: 'string',
	default: '',
},
		client_id: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		client_secret: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $Body_upload_image_questions_question__question_api_id__upload_image_post = {
	properties: {
		response_image: {
	type: 'binary',
	isRequired: true,
	format: 'binary',
},
	},
} as const;

export const $Body_upload_image_responses_response__response_api_id__upload_image_post = {
	properties: {
		response_images: {
	type: 'array',
	contains: {
	type: 'binary',
	format: 'binary',
},
	isRequired: true,
},
	},
} as const;

export const $GroupCreate = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		admin_api_identifier: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $GroupLinked = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		created_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		members: {
	type: 'array',
	contains: {
		type: 'UserUnlinked',
	},
	isRequired: true,
},
		letters: {
	type: 'array',
	contains: {
		type: 'LetterUnlinked',
	},
	isRequired: true,
},
		schedule: {
	type: 'any-of',
	contains: [{
	type: 'ScheduleUnlinked',
}, {
	type: 'null',
}],
	isRequired: true,
},
		admin: {
	type: 'UserUnlinked',
	isRequired: true,
},
	},
} as const;

export const $GroupUnlinked = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		created_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
	},
} as const;

export const $GroupUpdate = {
	properties: {
		name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $HTTPValidationError = {
	properties: {
		detail: {
	type: 'array',
	contains: {
		type: 'ValidationError',
	},
},
	},
} as const;

export const $Image = {
	properties: {
		s3_url: {
	type: 'string',
	isRequired: true,
},
		media_type: {
	type: 'MediaType',
	isRequired: true,
},
	},
} as const;

export const $InviteCreate = {
	properties: {
		email: {
	type: 'string',
	isRequired: true,
},
		group_api_id: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $InviteLinked = {
	properties: {
		email: {
	type: 'string',
	isRequired: true,
},
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		created_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		is_expired: {
	type: 'boolean',
	isRequired: true,
},
		token: {
	type: 'string',
	isRequired: true,
},
		inviter: {
	type: 'UserUnlinked',
	isRequired: true,
},
		group: {
	type: 'GroupUnlinked',
	isRequired: true,
},
	},
} as const;

export const $LetterCreate = {
	properties: {
		group_api_identifier: {
	type: 'string',
	isRequired: true,
},
		send_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
	},
} as const;

export const $LetterStatus = {
	type: 'Enum',
	enum: ['UPCOMING','IN_PROGRESS','SENT',],
} as const;

export const $LetterUnlinked = {
	properties: {
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		number: {
	type: 'number',
	isRequired: true,
},
		status: {
	type: 'LetterStatus',
	isRequired: true,
},
		send_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		created_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
	},
} as const;

export const $LetterUpdate = {
	properties: {
		send_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
	},
} as const;

export const $MediaType = {
	type: 'Enum',
	enum: ['image','video',],
} as const;

export const $NewPassword = {
	properties: {
		new_password: {
	type: 'string',
	isRequired: true,
},
		token: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $PublicLetter = {
	properties: {
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		number: {
	type: 'number',
	isRequired: true,
},
		status: {
	type: 'LetterStatus',
	isRequired: true,
},
		send_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		created_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		group: {
	type: 'GroupUnlinked',
	isRequired: true,
},
		questions: {
	type: 'array',
	contains: {
		type: 'PublicQuestion',
	},
	isRequired: true,
},
	},
} as const;

export const $PublicQuestion = {
	properties: {
		question_text: {
	type: 'string',
	isRequired: true,
},
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		created_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		responses: {
	type: 'array',
	contains: {
		type: 'ResponseWithParticipant',
	},
	isRequired: true,
},
		author: {
	type: 'any-of',
	contains: [{
	type: 'UserUnlinked',
}, {
	type: 'null',
}],
	isRequired: true,
},
	},
} as const;

export const $QuestionCreate = {
	properties: {
		question_text: {
	type: 'string',
	isRequired: true,
},
		author_api_id: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
	isRequired: true,
},
	},
} as const;

export const $QuestionLinked = {
	properties: {
		question_text: {
	type: 'string',
	isRequired: true,
},
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		created_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		letter: {
	type: 'LetterUnlinked',
	isRequired: true,
},
		responses: {
	type: 'array',
	contains: {
		type: 'ResponseUnlinked',
	},
	isRequired: true,
},
	},
} as const;

export const $QuestionUnlinked = {
	properties: {
		question_text: {
	type: 'string',
	isRequired: true,
},
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		created_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
	},
} as const;

export const $ResponseCreateBase = {
	properties: {
		response_text: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $ResponseLinked = {
	properties: {
		response_text: {
	type: 'string',
	isRequired: true,
},
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		created_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		question: {
	type: 'QuestionUnlinked',
	isRequired: true,
},
		participant: {
	type: 'UserUnlinked',
	isRequired: true,
},
		images: {
	type: 'array',
	contains: {
		type: 'Image',
	},
	isReadOnly: true,
	isRequired: true,
},
	},
} as const;

export const $ResponseMessage = {
	properties: {
		message: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $ResponseUnlinked = {
	properties: {
		response_text: {
	type: 'string',
	isRequired: true,
},
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		created_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
	},
} as const;

export const $ResponseUpsert = {
	properties: {
		response_text: {
	type: 'string',
	isRequired: true,
},
		participant_api_identifier: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		api_identifier: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $ResponseWithParticipant = {
	properties: {
		response_text: {
	type: 'string',
	isRequired: true,
},
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		created_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		participant: {
	type: 'UserUnlinked',
	isRequired: true,
},
		images: {
	type: 'array',
	contains: {
		type: 'Image',
	},
	isReadOnly: true,
	isRequired: true,
},
	},
} as const;

export const $ScheduleLinked = {
	properties: {
		group: {
	type: 'GroupUnlinked',
	isRequired: true,
},
		tasks: {
	type: 'array',
	contains: {
		type: 'TaskUnlinked',
	},
	isRequired: true,
},
	},
} as const;

export const $ScheduleSendParam = {
	properties: {
		letter_api_id: {
	type: 'string',
	isRequired: true,
},
		send_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
	},
} as const;

export const $ScheduleUnlinked = {
	properties: {
		tasks: {
	type: 'array',
	contains: {
		type: 'TaskUnlinked',
	},
	isRequired: true,
},
	},
} as const;

export const $TaskUnlinked = {
	properties: {
		type: {
	type: 'string',
	isRequired: true,
},
		status: {
	type: 'string',
	isRequired: true,
},
		execute_at: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		arguments: {
	type: 'dictionary',
	contains: {
	type: 'string',
},
	isRequired: true,
},
	},
} as const;

export const $Token = {
	properties: {
		access_token: {
	type: 'string',
	isRequired: true,
},
		token_type: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $UserCreate = {
	properties: {
		email: {
	type: 'string',
	isRequired: true,
},
		name: {
	type: 'string',
	isRequired: true,
},
		password: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $UserLinked = {
	properties: {
		email: {
	type: 'string',
	isRequired: true,
},
		name: {
	type: 'string',
	isRequired: true,
},
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		groups: {
	type: 'array',
	contains: {
		type: 'GroupUnlinked',
	},
	isRequired: true,
},
		responses: {
	type: 'array',
	contains: {
		type: 'ResponseUnlinked',
	},
	isRequired: true,
},
	},
} as const;

export const $UserUnlinked = {
	properties: {
		email: {
	type: 'string',
	isRequired: true,
},
		name: {
	type: 'string',
	isRequired: true,
},
		api_identifier: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $UserUpdate = {
	properties: {
		email: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $UserUpdatePassword = {
	properties: {
		current_password: {
	type: 'string',
	isRequired: true,
},
		new_password: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $ValidationError = {
	properties: {
		loc: {
	type: 'array',
	contains: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'number',
}],
},
	isRequired: true,
},
		msg: {
	type: 'string',
	isRequired: true,
},
		type: {
	type: 'string',
	isRequired: true,
},
	},
} as const;
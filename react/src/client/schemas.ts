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

export const $LetterCreate = {
	properties: {
		group_api_identifier: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $LetterLinked = {
	properties: {
		api_identifier: {
	type: 'string',
	isRequired: true,
},
		number: {
	type: 'number',
	isRequired: true,
},
		participants: {
	type: 'array',
	contains: {
		type: 'UserUnlinked',
	},
	isRequired: true,
},
		group: {
	type: 'GroupUnlinked',
	isRequired: true,
},
		questions: {
	type: 'array',
	contains: {
		type: 'QuestionUnlinked',
	},
	isRequired: true,
},
	},
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
	},
} as const;

export const $QuestionCreate = {
	properties: {
		question_text: {
	type: 'string',
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
		responses: {
	type: 'array',
	contains: {
		type: 'ResponseUnlinked',
	},
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
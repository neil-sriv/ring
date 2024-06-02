export type Body_login_access_token_login_access_token_post = {
	grant_type?: string | null;
	username: string;
	password: string;
	scope?: string;
	client_id?: string | null;
	client_secret?: string | null;
};



export type GroupCreate = {
	name: string;
	admin_api_identifier: string;
};



export type GroupLinked = {
	name: string;
	api_identifier: string;
	members: Array<UserUnlinked>;
	letters: Array<LetterUnlinked>;
	schedule: ScheduleUnlinked | null;
};



export type GroupUnlinked = {
	name: string;
	api_identifier: string;
};



export type HTTPValidationError = {
	detail?: Array<ValidationError>;
};



export type LetterCreate = {
	group_api_identifier: string;
};



export type LetterLinked = {
	api_identifier: string;
	number: number;
	participants: Array<UserUnlinked>;
	group: GroupUnlinked;
	questions: Array<QuestionUnlinked>;
};



export type LetterUnlinked = {
	api_identifier: string;
	number: number;
};



export type QuestionCreate = {
	question_text: string;
};



export type QuestionUnlinked = {
	question_text: string;
	api_identifier: string;
	responses: Array<ResponseUnlinked>;
};



export type ResponseUnlinked = {
	response_text: string;
	api_identifier: string;
};



export type ScheduleLinked = {
	group: GroupUnlinked;
	tasks: Array<TaskUnlinked>;
};



export type ScheduleSendParam = {
	letter_api_id: string;
	send_at: string;
};



export type ScheduleUnlinked = {
	tasks: Array<TaskUnlinked>;
};



export type TaskUnlinked = {
	type: string;
	status: string;
	execute_at: string;
	arguments: Record<string, string>;
};



export type Token = {
	access_token: string;
	token_type: string;
};



export type UserCreate = {
	email: string;
	name: string;
	password: string;
};



export type UserLinked = {
	email: string;
	name: string;
	api_identifier: string;
	groups: Array<GroupUnlinked>;
	responses: Array<ResponseUnlinked>;
};



export type UserUnlinked = {
	email: string;
	name: string;
	api_identifier: string;
};



export type UserUpdate = {
	email?: string | null;
	name?: string | null;
	password?: string | null;
};



export type ValidationError = {
	loc: Array<string | number>;
	msg: string;
	type: string;
};


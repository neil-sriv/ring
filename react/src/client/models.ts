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



export type GroupUpdate = {
	name?: string | null;
};



export type HTTPValidationError = {
	detail?: Array<ValidationError>;
};



export type LetterCreate = {
	group_api_identifier: string;
};



export type LetterStatus = 'IN_PROGRESS' | 'SENT';



export type LetterUnlinked = {
	api_identifier: string;
	number: number;
	status: LetterStatus;
};



export type NewPassword = {
	new_password: string;
	token: string;
};



export type PublicLetter = {
	api_identifier: string;
	number: number;
	status: LetterStatus;
	group: GroupUnlinked;
	questions: Array<PublicQuestion>;
};



export type PublicQuestion = {
	question_text: string;
	api_identifier: string;
	responses: Array<ResponseWithParticipant>;
};



export type QuestionCreate = {
	question_text: string;
};



export type QuestionLinked = {
	question_text: string;
	api_identifier: string;
	letter: LetterUnlinked;
	responses: Array<ResponseUnlinked>;
};



export type QuestionUnlinked = {
	question_text: string;
	api_identifier: string;
};



export type ResponseCreateBase = {
	response_text: string;
};



export type ResponseLinked = {
	response_text: string;
	api_identifier: string;
	question: QuestionUnlinked;
	participant: UserUnlinked;
};



export type ResponseMessage = {
	message: string;
};



export type ResponseUnlinked = {
	response_text: string;
	api_identifier: string;
};



export type ResponseUpsert = {
	response_text: string;
	participant_api_identifier?: string | null;
	api_identifier?: string | null;
};



export type ResponseWithParticipant = {
	response_text: string;
	api_identifier: string;
	participant: UserUnlinked;
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
};



export type UserUpdatePassword = {
	current_password: string;
	new_password: string;
};



export type ValidationError = {
	loc: Array<string | number>;
	msg: string;
	type: string;
};


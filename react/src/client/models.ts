export type AddMembers = {
	member_emails: Array<string>;
};



export type Body_login_access_token_login_access_token_post = {
	grant_type?: string | null;
	username: string;
	password: string;
	scope?: string;
	client_id?: string | null;
	client_secret?: string | null;
};



export type Body_upload_image_questions_question__question_api_id__upload_image_post = {
	response_image: Blob | File;
};



export type Body_upload_image_responses_response__response_api_id__upload_image_post = {
	response_images: Array<Blob | File>;
};



export type GroupCreate = {
	name: string;
	admin_api_identifier: string;
};



export type GroupLinked = {
	name: string;
	api_identifier: string;
	created_at: string;
	members: Array<UserUnlinked>;
	letters: Array<LetterUnlinked>;
	schedule: ScheduleUnlinked | null;
	admin: UserUnlinked;
};



export type GroupUnlinked = {
	name: string;
	api_identifier: string;
	created_at: string;
};



export type GroupUpdate = {
	name?: string | null;
};



export type HTTPValidationError = {
	detail?: Array<ValidationError>;
};



export type LetterCreate = {
	group_api_identifier: string;
	send_at: string;
};



export type LetterStatus = 'UPCOMING' | 'IN_PROGRESS' | 'SENT';



export type LetterUnlinked = {
	api_identifier: string;
	number: number;
	status: LetterStatus;
	send_at: string;
	created_at: string;
};



export type LetterUpdate = {
	send_at: string;
};



export type NewPassword = {
	new_password: string;
	token: string;
};



export type PublicLetter = {
	api_identifier: string;
	number: number;
	status: LetterStatus;
	send_at: string;
	created_at: string;
	group: GroupUnlinked;
	questions: Array<PublicQuestion>;
};



export type PublicQuestion = {
	question_text: string;
	api_identifier: string;
	created_at: string;
	responses: Array<ResponseWithParticipant>;
	author: UserUnlinked | null;
};



export type QuestionCreate = {
	question_text: string;
	author_api_id: string | null;
};



export type QuestionLinked = {
	question_text: string;
	api_identifier: string;
	created_at: string;
	letter: LetterUnlinked;
	responses: Array<ResponseUnlinked>;
};



export type QuestionUnlinked = {
	question_text: string;
	api_identifier: string;
	created_at: string;
};



export type ResponseCreateBase = {
	response_text: string;
};



export type ResponseLinked = {
	response_text: string;
	api_identifier: string;
	created_at: string;
	question: QuestionUnlinked;
	participant: UserUnlinked;
	readonly image_urls: Array<string>;
};



export type ResponseMessage = {
	message: string;
};



export type ResponseUnlinked = {
	response_text: string;
	api_identifier: string;
	created_at: string;
};



export type ResponseUpsert = {
	response_text: string;
	participant_api_identifier?: string | null;
	api_identifier?: string | null;
};



export type ResponseWithParticipant = {
	response_text: string;
	api_identifier: string;
	created_at: string;
	participant: UserUnlinked;
	readonly image_urls: Array<string>;
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


import type { CancelablePromise } from './core/CancelablePromise';
import { OpenAPI } from './core/OpenAPI';
import { request as __request } from './core/request';

import type { Body_login_access_token_login_access_token_post,NewPassword,Token,AddMembers,GroupCreate,GroupLinked,GroupUpdate,ResponseMessage,ScheduleSendParam,UserCreate,UserLinked,UserUpdate,UserUpdatePassword,LetterCreate,LetterUpdate,PublicLetter,QuestionCreate,ResponseUnlinked,ScheduleLinked,Body_upload_image_questions_question__question_api_id__upload_image_post,QuestionLinked,ResponseUpsert,Body_upload_image_responses_response__response_api_id__upload_image_post,ResponseCreateBase,ResponseLinked,InviteCreate,InviteLinked } from './models';

export type LoginData = {
        LoginAccessTokenLoginAccessTokenPost: {
                    formData: Body_login_access_token_login_access_token_post
                    
                };
RecoverPasswordPasswordRecoveryEmailPost: {
                    email: string
                    
                };
ResetPasswordResetPasswordPost: {
                    requestBody: NewPassword
                    
                };
RecoverPasswordHtmlContentPasswordRecoveryHtmlContentEmailPost: {
                    email: string
                    
                };
    }

export type PartiesData = {
        UpdateUserMePartiesMePatch: {
                    requestBody: UserUpdate
                    
                };
CreateUserPartiesUserPost: {
                    requestBody: UserCreate
                    
                };
RegisterUserPartiesRegisterTokenPost: {
                    requestBody: UserCreate
token: string
                    
                };
ReadUsersPartiesUsersGet: {
                    limit?: number
skip?: number
                    
                };
ReadUserByIdPartiesUserUserApiIdGet: {
                    userApiId: string
                    
                };
UpdatePasswordMePartiesMePasswordPatch: {
                    requestBody: UserUpdatePassword
                    
                };
CreateGroupPartiesGroupPost: {
                    requestBody: GroupCreate
                    
                };
ListGroupsPartiesGroupsGet: {
                    limit?: number
skip?: number
userApiId: string
                    
                };
ReadGroupPartiesGroupGroupApiIdGet: {
                    groupApiId: string
                    
                };
UpdateGroupPartiesGroupGroupApiIdPatch: {
                    groupApiId: string
requestBody: GroupUpdate
                    
                };
AddUserToGroupPartiesGroupGroupApiIdAddMemberUserApiIdPost: {
                    groupApiId: string
userApiId: string
                    
                };
RemoveUserFromGroupPartiesGroupGroupApiIdRemoveMemberUserApiIdPost: {
                    groupApiId: string
userApiId: string
                    
                };
ScheduleSendPartiesGroupGroupApiIdScheduleSendPost: {
                    groupApiId: string
requestBody: ScheduleSendParam
                    
                };
AddMembersPartiesGroupGroupApiIdAddMembersPost: {
                    groupApiId: string
requestBody: AddMembers
                    
                };
    }

export type LettersData = {
        AddNextLetterLettersLetterPost: {
                    requestBody: LetterCreate
                    
                };
ListLettersLettersLettersGet: {
                    groupApiId: string
limit?: number
skip?: number
                    
                };
ReadLetterLettersLetterLetterApiIdGet: {
                    letterApiId: string
                    
                };
EditLetterLettersLetterLetterApiIdEditLetterPost: {
                    letterApiId: string
requestBody: LetterUpdate
                    
                };
AddQuestionLettersLetterLetterApiIdAddQuestionPost: {
                    letterApiId: string
requestBody: QuestionCreate
                    
                };
BulkEditResponsesLettersLetterLetterApiIdBulkEditResponsesPatch: {
                    letterApiId: string
requestBody: Array<ResponseUnlinked>
                    
                };
    }

export type ScheduleData = {
        GetScheduleForGroupScheduleScheduleGroupApiIdGet: {
                    groupApiId: string
                    
                };
    }

export type QuestionsData = {
        UpsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost: {
                    questionApiId: string
requestBody: ResponseUpsert
                    
                };
UploadImageQuestionsQuestionQuestionApiIdUploadImagePost: {
                    formData: Body_upload_image_questions_question__question_api_id__upload_image_post
questionApiId: string
                    
                };
    }

export type ResponsesData = {
        EditResponseResponsesResponseResponseApiIdEditResponsePost: {
                    requestBody: ResponseCreateBase
responseApiId: string
                    
                };
UploadImageResponsesResponseResponseApiIdUploadImagePost: {
                    formData: Body_upload_image_responses_response__response_api_id__upload_image_post
responseApiId: string
                    
                };
    }

export type InvitesData = {
        CreateInviteInvitesPost: {
                    requestBody: InviteCreate
                    
                };
ValidateTokenInvitesTokenTokenGet: {
                    token: string
                    
                };
    }

export type DefaultData = {
        
    }

export class LoginService {

	/**
	 * Login Access Token
	 * @returns Token Successful Response
	 * @throws ApiError
	 */
	public static loginAccessTokenLoginAccessTokenPost(data: LoginData['LoginAccessTokenLoginAccessTokenPost']): CancelablePromise<Token> {
		const {
formData,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/login/access-token',
			formData: formData,
			mediaType: 'application/x-www-form-urlencoded',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * @deprecated
	 * Test Token
	 * Test access token
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static testTokenLoginTestTokenPost(): CancelablePromise<null> {
				return __request(OpenAPI, {
			method: 'POST',
			url: '/login/test-token',
		});
	}

	/**
	 * @deprecated
	 * Recover Password
	 * Password Recovery
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static recoverPasswordPasswordRecoveryEmailPost(data: LoginData['RecoverPasswordPasswordRecoveryEmailPost']): CancelablePromise<null> {
		const {
email,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/password-recovery/{email}',
			path: {
				email
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * @deprecated
	 * Reset Password
	 * Reset password
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static resetPasswordResetPasswordPost(data: LoginData['ResetPasswordResetPasswordPost']): CancelablePromise<null> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/reset-password/',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * @deprecated
	 * Recover Password Html Content
	 * HTML Content for Password Recovery
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static recoverPasswordHtmlContentPasswordRecoveryHtmlContentEmailPost(data: LoginData['RecoverPasswordHtmlContentPasswordRecoveryHtmlContentEmailPost']): CancelablePromise<null> {
		const {
email,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/password-recovery-html-content/{email}',
			path: {
				email
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class PartiesService {

	/**
	 * Read User Me
	 * @returns UserLinked Successful Response
	 * @throws ApiError
	 */
	public static readUserMePartiesMeGet(): CancelablePromise<UserLinked> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/parties/me',
		});
	}

	/**
	 * @deprecated
	 * Delete User Me
	 * Delete own user.
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static deleteUserMePartiesMeDelete(): CancelablePromise<null> {
				return __request(OpenAPI, {
			method: 'DELETE',
			url: '/parties/me',
		});
	}

	/**
	 * Update User Me
	 * Update own user.
	 * @returns UserLinked Successful Response
	 * @throws ApiError
	 */
	public static updateUserMePartiesMePatch(data: PartiesData['UpdateUserMePartiesMePatch']): CancelablePromise<UserLinked> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'PATCH',
			url: '/parties/me',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Create User
	 * @returns UserLinked Successful Response
	 * @throws ApiError
	 */
	public static createUserPartiesUserPost(data: PartiesData['CreateUserPartiesUserPost']): CancelablePromise<UserLinked> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/parties/user',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Register User
	 * @returns UserLinked Successful Response
	 * @throws ApiError
	 */
	public static registerUserPartiesRegisterTokenPost(data: PartiesData['RegisterUserPartiesRegisterTokenPost']): CancelablePromise<UserLinked> {
		const {
token,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/parties/register/{token}',
			path: {
				token
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Read Users
	 * @returns UserLinked Successful Response
	 * @throws ApiError
	 */
	public static readUsersPartiesUsersGet(data: PartiesData['ReadUsersPartiesUsersGet'] = {}): CancelablePromise<Array<UserLinked>> {
		const {
skip = 0,
limit = 100,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/parties/users',
			query: {
				skip, limit
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Read User By Id
	 * @returns UserLinked Successful Response
	 * @throws ApiError
	 */
	public static readUserByIdPartiesUserUserApiIdGet(data: PartiesData['ReadUserByIdPartiesUserUserApiIdGet']): CancelablePromise<UserLinked> {
		const {
userApiId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/parties/user/{user_api_id}',
			path: {
				user_api_id: userApiId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Update Password Me
	 * Update own password.
	 * @returns ResponseMessage Successful Response
	 * @throws ApiError
	 */
	public static updatePasswordMePartiesMePasswordPatch(data: PartiesData['UpdatePasswordMePartiesMePasswordPatch']): CancelablePromise<ResponseMessage> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'PATCH',
			url: '/parties/me/password',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * @deprecated
	 * Signup
	 * Create new user without the need to be logged in.
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static signupPartiesSignupPost(): CancelablePromise<null> {
				return __request(OpenAPI, {
			method: 'POST',
			url: '/parties/signup',
		});
	}

	/**
	 * @deprecated
	 * Delete User
	 * Delete a user.
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static deleteUserPartiesUserIdDelete(): CancelablePromise<null> {
				return __request(OpenAPI, {
			method: 'DELETE',
			url: '/parties/{user_id}',
		});
	}

	/**
	 * @deprecated
	 * Update User
	 * Update a user.
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static updateUserPartiesUserIdPatch(): CancelablePromise<null> {
				return __request(OpenAPI, {
			method: 'PATCH',
			url: '/parties/{user_id}',
		});
	}

	/**
	 * Create Group
	 * @returns GroupLinked Successful Response
	 * @throws ApiError
	 */
	public static createGroupPartiesGroupPost(data: PartiesData['CreateGroupPartiesGroupPost']): CancelablePromise<GroupLinked> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/parties/group',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * List Groups
	 * @returns GroupLinked Successful Response
	 * @throws ApiError
	 */
	public static listGroupsPartiesGroupsGet(data: PartiesData['ListGroupsPartiesGroupsGet']): CancelablePromise<Array<GroupLinked>> {
		const {
userApiId,
skip = 0,
limit = 100,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/parties/groups/',
			query: {
				user_api_id: userApiId, skip, limit
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Read Group
	 * @returns GroupLinked Successful Response
	 * @throws ApiError
	 */
	public static readGroupPartiesGroupGroupApiIdGet(data: PartiesData['ReadGroupPartiesGroupGroupApiIdGet']): CancelablePromise<GroupLinked> {
		const {
groupApiId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/parties/group/{group_api_id}',
			path: {
				group_api_id: groupApiId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * @deprecated
	 * Update Group
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static updateGroupPartiesGroupGroupApiIdPatch(data: PartiesData['UpdateGroupPartiesGroupGroupApiIdPatch']): CancelablePromise<null> {
		const {
groupApiId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'PATCH',
			url: '/parties/group/{group_api_id}',
			path: {
				group_api_id: groupApiId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Add User To Group
	 * @returns GroupLinked Successful Response
	 * @throws ApiError
	 */
	public static addUserToGroupPartiesGroupGroupApiIdAddMemberUserApiIdPost(data: PartiesData['AddUserToGroupPartiesGroupGroupApiIdAddMemberUserApiIdPost']): CancelablePromise<GroupLinked> {
		const {
groupApiId,
userApiId,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/parties/group/{group_api_id}:add_member/{user_api_id}',
			path: {
				group_api_id: groupApiId, user_api_id: userApiId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Remove User From Group
	 * @returns GroupLinked Successful Response
	 * @throws ApiError
	 */
	public static removeUserFromGroupPartiesGroupGroupApiIdRemoveMemberUserApiIdPost(data: PartiesData['RemoveUserFromGroupPartiesGroupGroupApiIdRemoveMemberUserApiIdPost']): CancelablePromise<GroupLinked> {
		const {
groupApiId,
userApiId,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/parties/group/{group_api_id}:remove_member/{user_api_id}',
			path: {
				group_api_id: groupApiId, user_api_id: userApiId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Schedule Send
	 * @returns GroupLinked Successful Response
	 * @throws ApiError
	 */
	public static scheduleSendPartiesGroupGroupApiIdScheduleSendPost(data: PartiesData['ScheduleSendPartiesGroupGroupApiIdScheduleSendPost']): CancelablePromise<GroupLinked> {
		const {
groupApiId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/parties/group/{group_api_id}:schedule_send',
			path: {
				group_api_id: groupApiId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Add Members
	 * @returns GroupLinked Successful Response
	 * @throws ApiError
	 */
	public static addMembersPartiesGroupGroupApiIdAddMembersPost(data: PartiesData['AddMembersPartiesGroupGroupApiIdAddMembersPost']): CancelablePromise<GroupLinked> {
		const {
groupApiId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/parties/group/{group_api_id}:add_members',
			path: {
				group_api_id: groupApiId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class LettersService {

	/**
	 * Add Next Letter
	 * @returns PublicLetter Successful Response
	 * @throws ApiError
	 */
	public static addNextLetterLettersLetterPost(data: LettersData['AddNextLetterLettersLetterPost']): CancelablePromise<PublicLetter> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/letters/letter',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * List Letters
	 * @returns PublicLetter Successful Response
	 * @throws ApiError
	 */
	public static listLettersLettersLettersGet(data: LettersData['ListLettersLettersLettersGet']): CancelablePromise<Array<PublicLetter>> {
		const {
groupApiId,
skip = 0,
limit = 100,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/letters/letters/',
			query: {
				group_api_id: groupApiId, skip, limit
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Read Letter
	 * @returns PublicLetter Successful Response
	 * @throws ApiError
	 */
	public static readLetterLettersLetterLetterApiIdGet(data: LettersData['ReadLetterLettersLetterLetterApiIdGet']): CancelablePromise<PublicLetter> {
		const {
letterApiId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/letters/letter/{letter_api_id}',
			path: {
				letter_api_id: letterApiId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Edit Letter
	 * @returns PublicLetter Successful Response
	 * @throws ApiError
	 */
	public static editLetterLettersLetterLetterApiIdEditLetterPost(data: LettersData['EditLetterLettersLetterLetterApiIdEditLetterPost']): CancelablePromise<PublicLetter> {
		const {
letterApiId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/letters/letter/{letter_api_id}:edit_letter',
			path: {
				letter_api_id: letterApiId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Add Question
	 * @returns PublicLetter Successful Response
	 * @throws ApiError
	 */
	public static addQuestionLettersLetterLetterApiIdAddQuestionPost(data: LettersData['AddQuestionLettersLetterLetterApiIdAddQuestionPost']): CancelablePromise<PublicLetter> {
		const {
letterApiId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/letters/letter/{letter_api_id}:add_question',
			path: {
				letter_api_id: letterApiId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * @deprecated
	 * Bulk Edit Responses
	 * @returns PublicLetter Successful Response
	 * @throws ApiError
	 */
	public static bulkEditResponsesLettersLetterLetterApiIdBulkEditResponsesPatch(data: LettersData['BulkEditResponsesLettersLetterLetterApiIdBulkEditResponsesPatch']): CancelablePromise<PublicLetter> {
		const {
letterApiId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'PATCH',
			url: '/letters/letter/{letter_api_id}:bulk_edit_responses',
			path: {
				letter_api_id: letterApiId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class ScheduleService {

	/**
	 * Get Schedule For Group
	 * @returns ScheduleLinked Successful Response
	 * @throws ApiError
	 */
	public static getScheduleForGroupScheduleScheduleGroupApiIdGet(data: ScheduleData['GetScheduleForGroupScheduleScheduleGroupApiIdGet']): CancelablePromise<ScheduleLinked> {
		const {
groupApiId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/schedule/schedule/{group_api_id}',
			path: {
				group_api_id: groupApiId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class QuestionsService {

	/**
	 * Upsert Response
	 * @returns QuestionLinked Successful Response
	 * @throws ApiError
	 */
	public static upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost(data: QuestionsData['UpsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost']): CancelablePromise<QuestionLinked> {
		const {
questionApiId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/questions/question/{question_api_id}:upsert_response',
			path: {
				question_api_id: questionApiId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Upload Image
	 * @returns QuestionLinked Successful Response
	 * @throws ApiError
	 */
	public static uploadImageQuestionsQuestionQuestionApiIdUploadImagePost(data: QuestionsData['UploadImageQuestionsQuestionQuestionApiIdUploadImagePost']): CancelablePromise<QuestionLinked> {
		const {
questionApiId,
formData,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/questions/question/{question_api_id}:upload_image',
			path: {
				question_api_id: questionApiId
			},
			formData: formData,
			mediaType: 'multipart/form-data',
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class ResponsesService {

	/**
	 * Edit Response
	 * @returns ResponseLinked Successful Response
	 * @throws ApiError
	 */
	public static editResponseResponsesResponseResponseApiIdEditResponsePost(data: ResponsesData['EditResponseResponsesResponseResponseApiIdEditResponsePost']): CancelablePromise<ResponseLinked> {
		const {
responseApiId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/responses/response/{response_api_id}:edit_response',
			path: {
				response_api_id: responseApiId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * @deprecated
	 * Upload Image
	 * @returns ResponseLinked Successful Response
	 * @throws ApiError
	 */
	public static uploadImageResponsesResponseResponseApiIdUploadImagePost(data: ResponsesData['UploadImageResponsesResponseResponseApiIdUploadImagePost']): CancelablePromise<ResponseLinked> {
		const {
responseApiId,
formData,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/responses/response/{response_api_id}:upload_image',
			path: {
				response_api_id: responseApiId
			},
			formData: formData,
			mediaType: 'multipart/form-data',
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class InvitesService {

	/**
	 * Create Invite
	 * @returns InviteLinked Successful Response
	 * @throws ApiError
	 */
	public static createInviteInvitesPost(data: InvitesData['CreateInviteInvitesPost']): CancelablePromise<InviteLinked> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/invites/',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Validate Token
	 * @returns InviteLinked Successful Response
	 * @throws ApiError
	 */
	public static validateTokenInvitesTokenTokenGet(data: InvitesData['ValidateTokenInvitesTokenTokenGet']): CancelablePromise<InviteLinked> {
		const {
token,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/invites/token/{token}',
			path: {
				token
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class DefaultService {

	/**
	 * Root
	 * @returns unknown Successful Response
	 * @throws ApiError
	 */
	public static rootGet(): CancelablePromise<unknown> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/',
		});
	}

	/**
	 * Hello
	 * @returns unknown Successful Response
	 * @throws ApiError
	 */
	public static helloHelloGet(): CancelablePromise<unknown> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/hello',
		});
	}

}
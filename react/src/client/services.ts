import type { CancelablePromise } from './core/CancelablePromise';
import { OpenAPI } from './core/OpenAPI';
import { request as __request } from './core/request';

import type { Body_login_access_token_login_access_token_post,NewPassword,Token,GroupCreate,GroupLinked,GroupUpdate,ScheduleSendParam,UserCreate,UserLinked,UserUpdate,UserUpdatePassword,LetterCreate,LetterLinked,QuestionCreate,ScheduleLinked } from './models';

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
AddQuestionLettersLetterLetterApiIdAddQuestionPost: {
                    letterApiId: string
requestBody: QuestionCreate
                    
                };
    }

export type ScheduleData = {
        GetScheduleForGroupScheduleScheduleGroupApiIdGet: {
                    groupApiId: string
                    
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
	 * @deprecated
	 * Update User Me
	 * Update own user.
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static updateUserMePartiesMePatch(data: PartiesData['UpdateUserMePartiesMePatch']): CancelablePromise<null> {
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
	 * @deprecated
	 * Update Password Me
	 * Update own password.
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static updatePasswordMePartiesMePasswordPatch(data: PartiesData['UpdatePasswordMePartiesMePasswordPatch']): CancelablePromise<null> {
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
	 * Register User
	 * Create new user without the need to be logged in.
	 * @returns null Successful Response
	 * @throws ApiError
	 */
	public static registerUserPartiesSignupPost(): CancelablePromise<null> {
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

}

export class LettersService {

	/**
	 * Add Next Letter
	 * @returns LetterLinked Successful Response
	 * @throws ApiError
	 */
	public static addNextLetterLettersLetterPost(data: LettersData['AddNextLetterLettersLetterPost']): CancelablePromise<LetterLinked> {
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
	 * @returns LetterLinked Successful Response
	 * @throws ApiError
	 */
	public static listLettersLettersLettersGet(data: LettersData['ListLettersLettersLettersGet']): CancelablePromise<Array<LetterLinked>> {
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
	 * @returns LetterLinked Successful Response
	 * @throws ApiError
	 */
	public static readLetterLettersLetterLetterApiIdGet(data: LettersData['ReadLetterLettersLetterLetterApiIdGet']): CancelablePromise<LetterLinked> {
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
	 * Add Question
	 * @returns LetterLinked Successful Response
	 * @throws ApiError
	 */
	public static addQuestionLettersLetterLetterApiIdAddQuestionPost(data: LettersData['AddQuestionLettersLetterLetterApiIdAddQuestionPost']): CancelablePromise<LetterLinked> {
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
import { useMutation } from "@tanstack/react-query";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { useState } from "react";

import { AxiosError } from "axios";
import {
  type Body_login_access_token_login_access_token_post as AccessToken,
  type ApiError,
  LoginService,
  type UserLinked,
} from "../client";

export interface AuthContext {
  isAuthenticated?: boolean;
  user: UserLinked | null | undefined;
}

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null;
};

const useAuth = () => {
  const search = useSearch({ strict: false });
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessTokenLoginAccessTokenPost({
      formData: data,
    });
    localStorage.setItem("access_token", response.access_token);
  };

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      // @ts-expect-error
      navigate({ to: search.path || "/groups" });
    },
    onError: (err: ApiError) => {
      let errDetail = err.body.detail;

      if (err instanceof AxiosError) {
        errDetail = err.message;
      }

      if (Array.isArray(errDetail)) {
        errDetail = "Something went wrong";
      }

      setError(errDetail);
    },
  });

  const logout = () => {
    localStorage.removeItem("access_token");
    navigate({ to: "/login" });
  };

  return {
    loginMutation,
    logout,
    error,
    resetError: () => setError(null),
  };
};

export { isLoggedIn };
export default useAuth;

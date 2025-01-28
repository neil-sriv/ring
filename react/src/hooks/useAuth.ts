import { useMutation } from "@tanstack/react-query";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { useState } from "react";

// import { AxiosError } from "axios";
import {
  loginAccessTokenLoginAccessTokenPost,
  LoginAccessTokenLoginAccessTokenPostError,
  type BodyLoginAccessTokenLoginAccessTokenPost as AccessToken,
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
    const response = await loginAccessTokenLoginAccessTokenPost({
      body: data,
    });
    if (response.error) {
      throw response.error;
    }
    localStorage.setItem("access_token", response.data.access_token);
  };

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      // @ts-expect-error
      navigate({ to: search.path || "/groups" });
    },
    onError: (err: LoginAccessTokenLoginAccessTokenPostError) => {
      // const errDetail = err.detail || "no error detail, please contact support";
      // setError(errDetail);
      console.log(err);
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

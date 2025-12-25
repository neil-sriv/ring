import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";

import {
  LoginAccessTokenLoginAccessTokenPostError,
  type UserLinked,
} from "../client";
import {
  loginAccessTokenLoginAccessTokenPostMutation,
  readUserMePartiesMeGetOptions,
} from "../client/@tanstack/react-query.gen";
import { AxiosError } from "axios";

export interface AuthContext {
  isAuthenticated?: boolean;
  user: UserLinked | undefined;
}

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null;
};

const useAuth = (next?: string) => {
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const loginMutation = useMutation({
    ...loginAccessTokenLoginAccessTokenPostMutation(),
    onSuccess: (data) => {
      localStorage.setItem("access_token", data.access_token);
      queryClient.ensureQueryData({
        ...readUserMePartiesMeGetOptions({}),
      });
      // Redirect to the next parameter if provided, otherwise go to home
      // Use window.location.href to preserve hash fragments
      if (next) {
        window.location.href = next;
      } else {
        navigate({ to: "/" });
      }
    },
    onError: (err: AxiosError<LoginAccessTokenLoginAccessTokenPostError>) => {
      const errDetail =
        err.response?.data.detail || "no error detail, please contact support";
      console.log(errDetail);
    },
    onSettled: (data, error) => {
      if (error) {
        throw error;
      }
      if (data) {
        localStorage.setItem("access_token", data.access_token);
      }
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

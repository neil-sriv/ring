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
      // Use TanStack Router's hash option to preserve hash fragments
      if (next) {
        // Parse the next URL to extract pathname, search, and hash
        const url = new URL(next, window.location.origin);
        const pathname = url.pathname;
        const search = url.search;
        const hash = url.hash.slice(1); // Remove the '#' character
        
        if (hash) {
          navigate({
            to: pathname + search,
            hash: hash,
          });
        } else {
          navigate({
            to: pathname + search,
          });
        }
      } else {
        navigate({ to: "/" });
      }
      // Ensure next is a string (not an object) to avoid [object Object] in URL
      const redirectTo = typeof next === "string" && next ? next : "/";
      navigate({ to: redirectTo });
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

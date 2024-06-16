import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";

import { AxiosError } from "axios";
import {
  type Body_login_access_token_login_access_token_post as AccessToken,
  type ApiError,
  LoginService,
  type UserLinked,
  PartiesService,
} from "../client";

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null;
};

const useAuth = () => {
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { data: user, isLoading } = useQuery<UserLinked | null, Error>({
    queryKey: ["currentUser"],
    queryFn: PartiesService.readUserMePartiesMeGet,
    enabled: isLoggedIn(),
  });

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessTokenLoginAccessTokenPost({
      formData: data,
    });
    localStorage.setItem("access_token", response.access_token);
  };

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" });
    },
    onError: (err: ApiError) => {
      let errDetail = (err.body as any)?.detail;

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
    user,
    isLoading,
    error,
    resetError: () => setError(null),
  };
};

export { isLoggedIn };
export default useAuth;

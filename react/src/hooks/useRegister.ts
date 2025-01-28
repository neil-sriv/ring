import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";

import {
  registerUserPartiesRegisterTokenPost,
  RegisterUserPartiesRegisterTokenPostError,
  UserCreate,
} from "../client";

const useRegister = () => {
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const register = async (data: {
    body: UserCreate;
    path: { token: string };
  }) => {
    return await registerUserPartiesRegisterTokenPost({
      ...data,
    });
  };

  const registerMutation = useMutation({
    mutationFn: register,
    onSuccess: () => {
      navigate({ to: "/login" });
    },
    onError: (err: RegisterUserPartiesRegisterTokenPostError) => {
      // const errDetail = err.detail || "no error detail, please contact support";
      // setError(errDetail);
      console.log(err);
    },
  });

  return {
    registerMutation,
    error,
    resetError: () => setError(null),
  };
};

export default useRegister;

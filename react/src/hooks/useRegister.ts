import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";

import { RegisterUserPartiesRegisterTokenPostError } from "../client";
import { registerUserPartiesRegisterTokenPostMutation } from "../client/@tanstack/react-query.gen";
import { AxiosError } from "axios";

const useRegister = () => {
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const registerMutation = useMutation({
    ...registerUserPartiesRegisterTokenPostMutation(),
    onSuccess: () => {
      navigate({ to: "/login" });
    },
    onError: (err: AxiosError<RegisterUserPartiesRegisterTokenPostError>) => {
      const errDetail = err.response?.data.detail;
      if (errDetail === undefined) {
        return;
      }
      setError(errDetail[0].msg);
    },
  });

  return {
    registerMutation,
    error,
    resetError: () => setError(null),
  };
};

export default useRegister;

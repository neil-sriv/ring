import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";

import { AxiosError } from "axios";
import { type ApiError, PartiesData, PartiesService } from "../client";

const useRegister = () => {
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const register = async (
    data: PartiesData["RegisterUserPartiesRegisterTokenPost"]
  ) => {
    return await PartiesService.registerUserPartiesRegisterTokenPost(data);
  };

  const registerMutation = useMutation({
    mutationFn: register,
    onSuccess: () => {
      navigate({ to: "/login" });
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

  return {
    registerMutation,
    error,
    resetError: () => setError(null),
  };
};

export default useRegister;

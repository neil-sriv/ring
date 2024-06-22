import {
  Button,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type SubmitHandler, useForm } from "react-hook-form";

import {
  type ApiError,
  type LetterCreate,
  UserLinked,
  LettersService,
} from "../../client";
import useCustomToast from "../../hooks/useCustomToast";

interface AddLetterProps {
  isOpen: boolean;
  onClose: () => void;
}

const AddLetter = ({ isOpen, onClose }: AddLetterProps) => {
  const queryClient = useQueryClient();
  const showToast = useCustomToast();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<LetterCreate>({
    mode: "onBlur",
    criteriaMode: "all",
  });

  const mutation = useMutation({
    mutationFn: (data: LetterCreate) =>
      LettersService.addNextLetterLettersLetterPost({
        requestBody: {
          group_api_identifier: data.group_api_identifier,
        },
      }),
    onSuccess: () => {
      showToast("Success!", "Next letter created successfully.", "success");
      reset();
      onClose();
    },
    onError: (err: ApiError) => {
      const errDetail = (err.body as any)?.detail;
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["loops"] });
    },
  });

  const onSubmit: SubmitHandler<LetterCreate> = (data) => {
    mutation.mutate(data);
  };

  return (
    <>{/* <ModalContent as="form" onSubmit={handleSubmit(onSubmit)}> */}</>
  );
};

export default AddLetter;

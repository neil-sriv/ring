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
  type LetterUpdate,
  LettersService,
  PublicLetter,
} from "../../client";
import useCustomToast from "../../hooks/useCustomToast";
import { toISOLocal } from "../../util/misc";

type LetterFormProps = {
  sendAt: Date | string;
};

interface EditLetterProps {
  isOpen: boolean;
  onClose: () => void;
  loop: PublicLetter;
}

const EditLetter = ({ isOpen, onClose, loop }: EditLetterProps) => {
  const queryClient = useQueryClient();
  const showToast = useCustomToast();
  const previousSendAt = new Date(loop.send_at);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<LetterFormProps>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      sendAt: toISOLocal(previousSendAt).slice(0, 16),
    },
  });

  const mutation = useMutation({
    mutationFn: (data: LetterUpdate) =>
      LettersService.editLetterLettersLetterLetterApiIdEditLetterPost({
        letterApiId: loop.api_identifier,
        requestBody: {
          send_at: data.send_at,
        },
      }),
    onSuccess: () => {
      showToast("Success!", "Letter due date updated.", "success");
      reset();
      onClose();
    },
    onError: (err: ApiError) => {
      const errDetail = (err.body as any)?.detail;
      showToast("Something went wrong.", `${errDetail}`, "error");
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["loop", loop.api_identifier],
      });
    },
  });

  const onSubmit: SubmitHandler<LetterFormProps> = (data) => {
    mutation.mutate({
      send_at:
        data.sendAt instanceof Date ? toISOLocal(data.sendAt) : data.sendAt,
    });
  };

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size={{ base: "sm", md: "md" }}
        isCentered
      >
        <ModalOverlay />
        <ModalContent as="form" onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Start Next Loop</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <FormControl isRequired>
              <FormLabel htmlFor="sendAt">Send at</FormLabel>
              <Input
                id="sendAt"
                {...register("sendAt", {
                  required: "Send at is required.",
                  valueAsDate: true,
                })}
                type="datetime-local"
                min={toISOLocal(new Date()).slice(0, 16)}
              />
              {errors.sendAt && (
                <FormErrorMessage>{errors.sendAt.message}</FormErrorMessage>
              )}
            </FormControl>
          </ModalBody>

          <ModalFooter gap={3}>
            <Button variant="primary" type="submit" isLoading={isSubmitting}>
              Save
            </Button>
            <Button onClick={onClose}>Cancel</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default EditLetter;

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

import { type ApiError, type LetterCreate, LettersService } from "../../client";
import useCustomToast from "../../hooks/useCustomToast";
import { toISOLocal } from "../../util/misc";

type LetterFormProps = {
  sendAt: Date | string;
};

interface AddLetterProps {
  isOpen: boolean;
  onClose: () => void;
  groupApiId: string;
}

const AddLetter = ({ isOpen, onClose, groupApiId }: AddLetterProps) => {
  const queryClient = useQueryClient();
  const showToast = useCustomToast();
  let defaultDate = new Date();
  defaultDate.setUTCDate(defaultDate.getDate() + 14);
  defaultDate.setUTCHours(21);
  defaultDate.setUTCMinutes(0);
  defaultDate.setUTCSeconds(0);
  defaultDate.setUTCMilliseconds(0);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<LetterFormProps>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      sendAt: defaultDate.toISOString().slice(0, 16),
    },
  });

  const mutation = useMutation({
    mutationFn: (data: LetterCreate) =>
      LettersService.addNextLetterLettersLetterPost({
        requestBody: {
          group_api_identifier: data.group_api_identifier,
          send_at: data.send_at,
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
      queryClient.invalidateQueries({ queryKey: ["loops", groupApiId] });
    },
  });

  const onSubmit: SubmitHandler<LetterFormProps> = (data) => {
    mutation.mutate({
      group_api_identifier: groupApiId,
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

export default AddLetter;

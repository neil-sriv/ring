import { Box, Heading, Textarea } from "@chakra-ui/react";
import {
  PublicQuestion,
  ResponseWithParticipant,
  uploadImageQuestionsQuestionQuestionApiIdUploadImagePost,
  upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost,
  UserLinked,
} from "../../client";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import useCustomToast from "../../hooks/useCustomToast";
import {
  S3Image,
  S3Video,
  SingleUploadImage,
} from "../Common/SingleUploadImage";
import { readLetterLettersLetterLetterApiIdGetQueryKey } from "../../client/@tanstack/react-query.gen";

type ResponseBlockProps = {
  uploadFunction: (file: File) => Promise<void>;
  questionApiId: string;
  response?: ResponseWithParticipant;
  submitResponse: (responseText: string) => Promise<void>;
  readOnly?: boolean;
};

function ResponseBlock(props: ResponseBlockProps) {
  const [responseText, setResponseText] = useState(
    props.response?.response_text ?? ""
  );
  const showToast = useCustomToast();
  const handleResponseChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setResponseText(e.target.value);
  };

  return (
    <Box my="10px">
      <Textarea
        size="md"
        variant="filled"
        value={responseText}
        onChange={handleResponseChange}
        isDisabled={props.readOnly}
        onBlur={async () => {
          if ((props.response?.response_text ?? "") !== responseText) {
            await props.submitResponse(responseText);
            showToast("Success!", "Answer saved.", "success");
          }
        }}
      />
      {props.response?.images.map((image, index) => {
        return image.media_type === "image" ? (
          <S3Image s3Key={image.s3_url} alt="response" key={index} />
        ) : (
          <S3Video s3Key={image.s3_url} key={index} />
        );
      })}
      {!props.readOnly && (
        <SingleUploadImage
          onUpdateFile={props.uploadFunction}
          name={props.questionApiId}
        />
      )}
    </Box>
  );
}

function DraftQuestion({
  question,
  loopApiId,
  readOnly = false,
}: {
  question: PublicQuestion;
  loopApiId: string;
  readOnly?: boolean;
}): JSX.Element {
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(["currentUser"]);
  if (!currentUser) {
    return <Box>loading...</Box>;
  }
  const response = question.responses.find(
    (response) =>
      response.participant.api_identifier === currentUser.api_identifier
  );

  const handleUpsert = async (responseText: string) => {
    await upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost({
      path: { question_api_id: question.api_identifier },
      body: {
        response_text: responseText,
        participant_api_identifier: currentUser.api_identifier,
      },
    });
  };

  const newHandleUpload = async (file: File) => {
    await uploadImageQuestionsQuestionQuestionApiIdUploadImagePost({
      path: { question_api_id: question.api_identifier },
      body: {
        response_image: file,
      },
    });
    queryClient.invalidateQueries({
      queryKey: readLetterLettersLetterLetterApiIdGetQueryKey({
        path: { letter_api_id: loopApiId },
      }),
    });
  };

  return (
    <Box my="20px">
      {question.author == null ? (
        <Heading size="md">{question.question_text}</Heading>
      ) : (
        <Heading size="md">
          {question.author.name} asked: {question.question_text}
        </Heading>
      )}
      <ResponseBlock
        questionApiId={question.api_identifier}
        response={response}
        submitResponse={handleUpsert}
        uploadFunction={newHandleUpload}
        key={question.api_identifier}
        readOnly={readOnly}
      />
    </Box>
  );
}

export default DraftQuestion;

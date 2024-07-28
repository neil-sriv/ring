import { Box, Heading, Textarea } from "@chakra-ui/react";
import {
  PublicQuestion,
  QuestionsService,
  ResponseWithParticipant,
  UserLinked,
} from "../../client";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import useCustomToast from "../../hooks/useCustomToast";
import { S3Image, SingleUploadImage } from "../Common/SingleUploadImage";

type ResponseBlockProps = {
  uploadFunction: (file: File) => Promise<void>;
  questionApiId: string;
  response?: ResponseWithParticipant;
  submitResponse: (responseText: string) => Promise<void>;
  imageUrls?: string[];
  readOnly?: boolean;
};

function ResponseBlock(props: ResponseBlockProps) {
  const [responseText, setResponseText] = useState(
    props.response?.response_text ?? "",
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
      {props.imageUrls?.map((url, index) => {
        return <S3Image s3Key={url} alt="response" key={index} />;
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
  readOnly = false,
}: {
  question: PublicQuestion;
  readOnly?: boolean;
}): JSX.Element {
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserLinked>(["currentUser"]);
  if (!currentUser) {
    return <Box>loading...</Box>;
  }
  const response = question.responses.find(
    (response) =>
      response.participant.api_identifier === currentUser.api_identifier,
  );

  const handleUpsert = async (responseText: string) => {
    await QuestionsService.upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost(
      {
        questionApiId: question.api_identifier,
        requestBody: {
          response_text: responseText,
          participant_api_identifier: currentUser.api_identifier,
        },
      },
    );
  };

  const newHandleUpload = async (file: File) => {
    await QuestionsService.uploadImageQuestionsQuestionQuestionApiIdUploadImagePost(
      {
        questionApiId: question.api_identifier,
        formData: {
          response_image: file,
        },
      },
    );
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
        imageUrls={response?.image_urls || []}
        key={question.api_identifier}
        readOnly={readOnly}
      />
    </Box>
  );
}

export default DraftQuestion;

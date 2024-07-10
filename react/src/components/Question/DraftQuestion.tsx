import { Box, Heading, Textarea } from "@chakra-ui/react";
import {
  PublicQuestion,
  QuestionsService,
  ResponsesService,
  UserLinked,
} from "../../client";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import useCustomToast from "../../hooks/useCustomToast";
import { S3Image, SingleUploadImage } from "../Common/SingleUploadImage";

type ResponseBlockProps = {
  uploadFunction?: (file: File) => Promise<void>;
  questionApiId: string;
  responseText: string;
  submitResponse: (responseText: string) => Promise<void>;
  imageUrls?: string[];
};

function ResponseBlock(props: ResponseBlockProps) {
  const [responseText, setResponseText] = useState(props.responseText);
  const showToast = useCustomToast();
  const handleResponseChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setResponseText(e.target.value);
  };

  return (
    <Box my="10px">
      <Textarea
        // key={props.questionApiId}
        size="md"
        variant="filled"
        value={responseText}
        onChange={handleResponseChange}
        onBlur={async () => {
          if (props.responseText !== responseText) {
            await props.submitResponse(responseText);
            showToast("Success!", "Answer saved.", "success");
          }
        }}
      />
      {props.imageUrls?.map((url, index) => {
        return <S3Image s3Key={url} alt="response" key={index} />;
      })}
      {props.uploadFunction !== undefined && (
        <SingleUploadImage
          onUpdateFile={props.uploadFunction}
          // key={props.questionApiId}
        />
      )}
    </Box>
  );
}

function DraftQuestion({
  question,
}: {
  question: PublicQuestion;
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

  const handleUpdate = async (responseText: string) => {
    await QuestionsService.upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost(
      {
        questionApiId: question.api_identifier,
        requestBody: {
          response_text: responseText,
          api_identifier: response!.api_identifier,
        },
      }
    );
  };

  const handleInsert = async (responseText: string) => {
    await QuestionsService.upsertResponseQuestionsQuestionQuestionApiIdUpsertResponsePost(
      {
        questionApiId: question.api_identifier,
        requestBody: {
          response_text: responseText,
          participant_api_identifier: currentUser.api_identifier,
        },
      }
    );
  };

  const handleUpload =
    response === undefined
      ? undefined
      : async (file: File) => {
          const formData = { response_images: [file] };
          await ResponsesService.uploadImageResponsesResponseResponseApiIdUploadImagePost(
            {
              responseApiId: response?.api_identifier,
              formData,
            }
          );
        };

  return (
    <Box my="20px">
      <Heading>{question.question_text}</Heading>
      <ResponseBlock
        questionApiId={question.api_identifier}
        responseText={response?.response_text || ""}
        submitResponse={response === undefined ? handleInsert : handleUpdate}
        uploadFunction={handleUpload}
        imageUrls={response?.image_urls || []}
        key={question.api_identifier}
      />
    </Box>
  );
}

export default DraftQuestion;

import { Box, Heading, Textarea } from "@chakra-ui/react";
import { PublicQuestion, QuestionsService, UserLinked } from "../../client";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import useCustomToast from "../../hooks/useCustomToast";
import SingleUploadImage from "../Common/SingleUploadImage";

type ResponseBlockProps = {
  responseText: string;
  submitResponse: (responseText: string) => Promise<void>;
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
      <SingleUploadImage />
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
  return (
    <Box my="20px">
      <Heading>{question.question_text}</Heading>
      <ResponseBlock
        responseText={response?.response_text || ""}
        submitResponse={response === undefined ? handleInsert : handleUpdate}
      />
    </Box>
  );
}

export default DraftQuestion;

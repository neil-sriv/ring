import {
    Box,
    Flex,
    Heading,
    VStack
} from "@chakra-ui/react";
import { PublicLetter } from "../../client";
import { LoopCard } from "./LoopCard";

export function LoopsGrid({
  loops,
  heading,
  subheading,
  includeGroupName = false,
}: {
  loops: PublicLetter[];
  heading: string;
  subheading?: string;
  includeGroupName?: boolean;
}): JSX.Element {
  return (
    <VStack w="100%" spacing={4} align="center">
      <Box textAlign="center" w="100%">
        <Heading size="md">{heading}</Heading>
        {subheading && <Heading size="sm">{subheading}</Heading>}
      </Box>
      <Flex 
        flexWrap="wrap" 
        justifyContent="center" 
        gap={4} 
        w="100%"
      >
        {loops.map((loop) => (
          <Box key={loop.api_identifier} flex="0 1 calc(25% - 1rem)" minWidth="200px">
            <LoopCard 
              loop={loop} 
              includeGroupName={includeGroupName} 
            />
          </Box>
        ))}
      </Flex>
    </VStack>
  );
}

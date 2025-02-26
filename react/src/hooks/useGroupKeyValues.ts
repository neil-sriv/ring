import { useSuspenseQuery } from "@tanstack/react-query";
import { readGroupKeyValuesPartiesGroupGroupApiIdKeyValueGetOptions } from "../client/@tanstack/react-query.gen";

export function useGroupKeyValues(groupApiId: string) {
  return useSuspenseQuery({
    ...readGroupKeyValuesPartiesGroupGroupApiIdKeyValueGetOptions({
      path: { group_api_id: groupApiId },
    }),
  });
}

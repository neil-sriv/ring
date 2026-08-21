import { Button } from "@/components/ui/button"
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import { Link, createFileRoute } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import { Suspense, useState } from "react"
import { ErrorBoundary } from "react-error-boundary"
import type { PublicLetter, UserLinked } from "../../../client"
import {
  readGroupPartiesGroupGroupApiIdGetOptions,
  readLetterLettersLetterLetterApiIdGetOptions,
  readUserMePartiesMeGetQueryKey,
} from "../../../client/@tanstack/react-query.gen"
import DraftLoop from "../../../components/Loops/DraftLoop"
import EditLetter from "../../../components/Loops/EditLoop"
import { LoopReplyTracker } from "../../../components/Loops/LoopReplyTracker"
import PublishedLoop from "../../../components/Loops/PublishedLoop"
import AddQuestion from "../../../components/Question/AddQuestion"
import GenerateQuestion from "../../../components/Question/GenerateQuestion"

type IssueLoaderProps = {
  loop: PublicLetter
}

export const Route = createFileRoute("/_layout/loops/$loopId")({
  loader: async ({ params, context }): Promise<IssueLoaderProps> => {
    const loop = await context.queryClient.ensureQueryData({
      ...readLetterLettersLetterLetterApiIdGetOptions({
        path: { letter_api_id: params.loopId },
      }),
    })
    return {
      loop,
    }
  },
  component: Issue,
})

function IssueContent() {
  const routeParams = Route.useParams()
  const { data: loop } = useSuspenseQuery({
    ...readLetterLettersLetterLetterApiIdGetOptions({
      path: { letter_api_id: routeParams.loopId },
    }),
  })
  const { data: group } = useSuspenseQuery({
    ...readGroupPartiesGroupGroupApiIdGetOptions({
      path: { group_api_id: loop.group.api_identifier },
    }),
  })
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey(),
  )
  const localDueDate = new Date(loop.send_at)
  const isGroupAdmin =
    group.admin.api_identifier === currentUser?.api_identifier
  const [editLoopOpen, setEditLoopOpen] = useState(false)
  const [addQuestionOpen, setAddQuestionOpen] = useState(false)
  const [generateQuestionOpen, setGenerateQuestionOpen] = useState(false)

  return (
    <div className="flex w-full justify-center">
      <div className="w-full max-w-[1200px] px-2 sm:px-4">
        <div className="flex w-full flex-col items-center gap-4 sm:gap-6 lg:gap-8">
          <div className="w-full rounded-xl border border-border/50 bg-background/80 p-6 shadow-md backdrop-blur-sm dark:border-border/30 dark:bg-background/60">
            <div className="flex flex-col items-center gap-4">
              <div className="relative w-full">
                <h2 className="text-center text-lg font-semibold text-foreground sm:text-xl lg:text-2xl">
                  <Link
                    to="/groups/$groupId/loops"
                    params={{ groupId: group!.api_identifier }}
                    className="underline"
                  >
                    {group!.name}
                  </Link>
                </h2>
                {isGroupAdmin && loop.status !== "SENT" && (
                  <Button
                    onClick={() => setEditLoopOpen(true)}
                    className="absolute right-0 top-1/2 -translate-y-1/2"
                  >
                    Edit Loop
                  </Button>
                )}
              </div>
              {loop.title && (
                <h2 className="text-lg font-semibold text-foreground sm:text-xl lg:text-2xl">
                  {loop.title}
                </h2>
              )}
              {!loop.title && loop.number && (
                <h2 className="text-lg font-semibold text-foreground sm:text-xl lg:text-2xl">
                  Issue #{loop.number}
                </h2>
              )}
              {loop.status === "IN_PROGRESS" && (
                <h3 className="pt-2 text-center text-base font-semibold text-muted-foreground md:text-left">
                  Due {localDueDate.toLocaleString()}
                </h3>
              )}
            </div>
          </div>

          {isGroupAdmin && <LoopReplyTracker loop={loop} />}

          {loop.status === "UPCOMING" && (
            <div className="flex w-full flex-wrap gap-4">
              <Button
                onClick={() => setAddQuestionOpen(true)}
                className="h-auto whitespace-normal py-2 text-left transition-all duration-200 hover:-translate-y-0.5"
              >
                <Plus className="h-4 w-4" /> Add new question
              </Button>
              <Button
                onClick={() => setGenerateQuestionOpen(true)}
                className="h-auto whitespace-normal py-2 text-left transition-all duration-200 hover:-translate-y-0.5"
              >
                <Plus className="h-4 w-4" /> Ask ChatGPT to generate a question.
              </Button>
            </div>
          )}

          <div className="w-full rounded-xl border border-border/50 bg-background/80 p-6 shadow-md backdrop-blur-sm dark:border-border/30 dark:bg-background/60">
            {loop.status === "SENT" ? (
              <PublishedLoop loop={loop} />
            ) : (
              <DraftLoop loop={loop} isGroupAdmin={isGroupAdmin} />
            )}
          </div>
        </div>
      </div>
      <EditLetter
        isOpen={editLoopOpen}
        onClose={() => setEditLoopOpen(false)}
        loop={loop}
      />
      <AddQuestion
        isOpen={addQuestionOpen}
        onClose={() => setAddQuestionOpen(false)}
        loopApiId={loop.api_identifier}
      />
      <GenerateQuestion
        isOpen={generateQuestionOpen}
        onClose={() => setGenerateQuestionOpen(false)}
        loopApiId={loop.api_identifier}
      />
    </div>
  )
}

function Issue() {
  return (
    <div className="w-full">
      <div className="mx-2 pt-4 sm:mx-4 sm:pt-8 lg:pt-12">
        <ErrorBoundary
          fallbackRender={({ error }) => (
            <div>
              <h2 className="text-xl font-bold">Error</h2>
              <p>{error.message}</p>
            </div>
          )}
        >
          <Suspense fallback={<div>Loading...</div>}>
            <IssueContent />
          </Suspense>
        </ErrorBoundary>
      </div>
    </div>
  )
}

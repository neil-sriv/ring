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
    <div className="mx-auto w-full max-w-3xl px-4 py-8 md:px-8">
      <header className="border-b pb-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <Link
              to="/groups/$groupId/loops"
              params={{ groupId: group!.api_identifier }}
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {group!.name}
            </Link>
            {loop.title && (
              <h1 className="mt-1 font-display text-2xl font-semibold tracking-tight md:text-3xl">
                {loop.title}
              </h1>
            )}
            {!loop.title && loop.number && (
              <h1 className="mt-1 font-display text-2xl font-semibold tracking-tight md:text-3xl">
                Issue #{loop.number}
              </h1>
            )}
            {loop.status === "IN_PROGRESS" && (
              <p className="mt-2 text-sm text-muted-foreground">
                Due {localDueDate.toLocaleString()}
              </p>
            )}
          </div>
          {isGroupAdmin && loop.status !== "SENT" && (
            <Button variant="outline" onClick={() => setEditLoopOpen(true)}>
              Edit Loop
            </Button>
          )}
        </div>
      </header>

      {/* Reply tracker: everyone sees it while the loop is in progress;
          once sent, the "Didn't reply" view stays admin-only. */}
      {(loop.status === "IN_PROGRESS" || isGroupAdmin) && (
        <div className="mt-6">
          <LoopReplyTracker loop={loop} />
        </div>
      )}

      {loop.status === "UPCOMING" && (
        <div className="mt-6 flex flex-wrap gap-3">
          <Button onClick={() => setAddQuestionOpen(true)}>
            <Plus className="h-4 w-4" /> Add new question
          </Button>
          <Button
            variant="outline"
            onClick={() => setGenerateQuestionOpen(true)}
          >
            <Plus className="h-4 w-4" /> Ask ChatGPT to generate a question.
          </Button>
        </div>
      )}

      <div className="mt-8">
        {loop.status === "SENT" ? (
          <PublishedLoop loop={loop} />
        ) : (
          <DraftLoop loop={loop} isGroupAdmin={isGroupAdmin} />
        )}
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
      <ErrorBoundary
        fallbackRender={({ error }) => (
          <div className="mx-auto w-full max-w-3xl px-4 py-8 md:px-8">
            <h2 className="font-display text-lg font-medium">Error</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {error.message}
            </p>
          </div>
        )}
      >
        <Suspense
          fallback={
            <div className="mx-auto w-full max-w-3xl px-4 py-8 text-sm text-muted-foreground md:px-8">
              Loading...
            </div>
          }
        >
          <IssueContent />
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

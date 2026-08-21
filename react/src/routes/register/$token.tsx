import {
  Link as RouterLink,
  createFileRoute,
  redirect,
} from "@tanstack/react-router"
import { Eye, EyeOff, Loader2 } from "lucide-react"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useQueryClient } from "@tanstack/react-query"
import type { UserCreate } from "../../client"
import {
  validateTokenInvitesTokenTokenGetOptions,
  validateTokenInvitesTokenTokenGetQueryKey,
} from "../../client/@tanstack/react-query.gen"
import useRegister from "../../hooks/useRegister"
import { emailPattern } from "../../util/misc"

export const Route = createFileRoute("/register/$token")({
  component: Register,
  beforeLoad: async ({ context }) => {
    // Gate on a verified session, not on a leftover localStorage token, so an
    // expired session cannot swallow the invite token in the URL.
    if (context.auth.isAuthenticated) {
      throw redirect({
        to: "/groups",
      })
    }
  },
  loader: async ({ params, context }) => {
    await context.queryClient
      .ensureQueryData({
        ...validateTokenInvitesTokenTokenGetOptions({
          path: { token: params.token },
        }),
      })
      .catch(() => {
        // Invalid/expired/used tokens render the invalid-invite UI below.
      })
  },
})

function Register() {
  const { token } = Route.useParams()
  const queryClient = useQueryClient()
  const validToken =
    queryClient.getQueryData(
      validateTokenInvitesTokenTokenGetQueryKey({
        path: { token: token },
      }),
    ) ?? false
      ? true
      : false
  if (!validToken) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
        <div className="w-full max-w-sm text-center">
          <RouterLink
            to="/"
            className="font-display text-3xl font-semibold tracking-tight text-foreground"
          >
            Ring
          </RouterLink>
          <h1 className="mt-6 text-lg font-semibold">Invite link invalid</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            This invite may have expired, already been used, or the link is
            incorrect. Ask a group admin for a new invite.
          </p>
          <Button asChild className="mt-8 w-full">
            <RouterLink to="/login">Back to login</RouterLink>
          </Button>
        </div>
      </div>
    )
  }

  const [showPassword, setShowPassword] = useState(false)
  const { registerMutation, error, resetError } = useRegister()
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<UserCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      email: "",
      name: "",
      password: "",
    },
  })

  const onSubmit: SubmitHandler<UserCreate> = async (data) => {
    if (isSubmitting) return

    resetError()

    const formData = {
      body: data,
      path: { token: token },
    }

    try {
      await registerMutation.mutateAsync(formData)
    } catch {
      // error is handled by useRegister hook
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="text-center">
          <RouterLink
            to="/"
            className="font-display text-3xl font-semibold tracking-tight text-foreground"
          >
            Ring
          </RouterLink>
          <h1 className="mt-6 text-lg font-semibold">Create your account</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            You&apos;ve been invited to write letters with your group.
          </p>
        </div>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-8 flex flex-col gap-5"
        >
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              {...register("name")}
              placeholder="Name"
              type="text"
              required
              className={errors.name ? "border-destructive" : ""}
            />
            {errors.name && (
              <p className="text-xs text-destructive">{errors.name.message}</p>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              {...register("email", {
                pattern: emailPattern,
              })}
              placeholder="Email"
              type="email"
              required
              className={errors.email || error ? "border-destructive" : ""}
            />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input
                id="password"
                {...register("password")}
                type={showPassword ? "text" : "password"}
                placeholder="Password"
                required
                className={error ? "border-destructive pr-10" : "pr-10"}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>

          <Button type="submit" disabled={isSubmitting} className="w-full">
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            Register
          </Button>

          <div className="text-center">
            <RouterLink
              to="/login"
              className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
            >
              Already have an account?
            </RouterLink>
          </div>
        </form>
      </div>
    </div>
  )
}

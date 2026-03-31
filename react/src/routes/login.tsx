import {
  Link as RouterLink,
  createFileRoute,
  redirect,
} from "@tanstack/react-router"
import { Eye, EyeOff, Loader2 } from "lucide-react"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { BodyLoginAccessTokenLoginAccessTokenPost as AccessToken } from "../client"
import useAuth from "../hooks/useAuth"
import { emailPattern } from "../util/misc"

export const Route = createFileRoute("/login")({
  component: Login,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      next:
        typeof search.next === "string" && search.next
          ? search.next
          : undefined,
    }
  },
  beforeLoad: async ({ context, search }) => {
    if (
      context.auth.isAuthenticated &&
      localStorage.getItem("access_token") !== null
    ) {
      // If already authenticated and there's a next parameter, redirect there
      // Otherwise redirect to home
      // Use TanStack Router's hash option to preserve hash fragments
      if (search.next) {
        try {
          // Parse the next URL to extract pathname, search, and hash
          const baseUrl =
            typeof window !== "undefined"
              ? window.location.origin
              : "http://localhost"
          const url = new URL(search.next, baseUrl)
          const pathname = url.pathname
          const searchParams = url.search
          const hash = url.hash.slice(1)

          if (hash) {
            throw redirect({
              to: pathname + searchParams,
              hash: hash,
            })
          }
          throw redirect({
            to: pathname + searchParams,
          })
        } catch (e) {
          if (e instanceof TypeError) {
            throw redirect({
              to: search.next,
            })
          }
          throw e
        }
      }
      throw redirect({
        to: "/",
      })
    }
  },
})

function Login() {
  const [showPassword, setShowPassword] = useState(false)
  const search = Route.useSearch()
  const { loginMutation, error, resetError } = useAuth(search.next)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AccessToken>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  })

  const onSubmit: SubmitHandler<AccessToken> = async (data) => {
    if (isSubmitting) return

    resetError()

    try {
      await loginMutation.mutateAsync({
        body: data,
      })
    } catch {
      // error is handled by useAuth hook
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary/10 via-background to-muted p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold tracking-tight">
            Login
          </CardTitle>
          <CardDescription>Enter your credentials</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="flex flex-col gap-4"
          >
            <div className="space-y-2">
              <Label htmlFor="username">Email</Label>
              <Input
                id="username"
                {...register("username", {
                  pattern: emailPattern,
                })}
                placeholder="you@example.com"
                type="email"
                required
                className={errors.username || error ? "border-destructive" : ""}
              />
              {errors.username && (
                <p className="text-sm text-destructive">
                  {errors.username.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
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
              {error && <p className="text-sm text-destructive">{error}</p>}
            </div>

            <div className="text-center">
              <RouterLink
                to="/reset-password"
                className="text-sm text-primary hover:text-primary/80 transition-colors"
              >
                Forgot password?
              </RouterLink>
            </div>

            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Sign In
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

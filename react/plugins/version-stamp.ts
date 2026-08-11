import { execFileSync } from "node:child_process"
import type { Plugin } from "vite"
import { type BuildVersion, VERSION_FILE_NAME } from "../src/util/buildVersion"

export { VERSION_FILE_NAME }

export interface GitFields {
  sha: string
  short_sha: string
  branch: string | null
}

function readEnv(environ: NodeJS.ProcessEnv, name: string): string | undefined {
  const value = environ[name]?.trim()
  return value ? value : undefined
}

function readGitFromCli(): GitFields | null {
  const git = (...args: string[]): string | null => {
    try {
      return execFileSync("git", args, {
        encoding: "utf8",
        stdio: ["ignore", "pipe", "ignore"],
        timeout: 5000,
      }).trim()
    } catch {
      return null
    }
  }
  const sha = git("rev-parse", "HEAD")
  if (!sha) {
    return null
  }
  const branch = git("rev-parse", "--abbrev-ref", "HEAD")
  return {
    sha,
    short_sha: git("rev-parse", "--short", "HEAD") ?? sha.slice(0, 7),
    // Detached-HEAD CI checkouts report "HEAD", which names no branch.
    branch: branch && branch !== "HEAD" ? branch : null,
  }
}

/**
 * Identify the commit this bundle was built from.
 *
 * Cloudflare Workers Builds clones without a usable git history for our
 * purposes but injects WORKERS_CI_*, so that wins. The Docker frontend
 * image passes RING_GIT_* as build args. A laptop build falls back to the
 * git CLI.
 */
export function resolveBuildVersion(
  environ: NodeJS.ProcessEnv = process.env,
  now: Date = new Date(),
  readGit: () => GitFields | null = readGitFromCli,
): BuildVersion {
  const built_at = now.toISOString()

  const workersSha = readEnv(environ, "WORKERS_CI_COMMIT_SHA")
  if (workersSha) {
    return {
      sha: workersSha,
      short_sha: workersSha.slice(0, 7),
      branch: readEnv(environ, "WORKERS_CI_BRANCH") ?? null,
      built_at,
      source: "workers_ci",
      build_uuid: readEnv(environ, "WORKERS_CI_BUILD_UUID") ?? null,
    }
  }

  const envSha = readEnv(environ, "RING_GIT_SHA")
  if (envSha) {
    return {
      sha: envSha,
      short_sha: readEnv(environ, "RING_GIT_SHORT_SHA") ?? envSha.slice(0, 7),
      branch: readEnv(environ, "RING_GIT_BRANCH") ?? null,
      built_at,
      source: "env",
      build_uuid: null,
    }
  }

  const git = readGit()
  if (git) {
    return { ...git, built_at, source: "git", build_uuid: null }
  }

  return {
    sha: null,
    short_sha: null,
    branch: null,
    built_at,
    source: "unavailable",
    build_uuid: null,
  }
}

/**
 * Emit `version.json` next to the bundle so a deployed frontend can say
 * which commit it is and when it was built.
 *
 * Cloudflare Workers serves it as a static asset at `/version.json`; the
 * dev server serves an equivalent response from memory.
 */
export function versionStamp(): Plugin {
  let payload = ""

  return {
    name: "ring-version-stamp",
    buildStart() {
      payload = `${JSON.stringify(resolveBuildVersion(), null, 2)}\n`
    },
    generateBundle() {
      this.emitFile({
        type: "asset",
        fileName: VERSION_FILE_NAME,
        source: payload,
      })
    },
    configureServer(server) {
      server.middlewares.use(`/${VERSION_FILE_NAME}`, (_req, res) => {
        res.setHeader("Content-Type", "application/json")
        res.setHeader("Cache-Control", "no-store")
        res.end(`${JSON.stringify(resolveBuildVersion(), null, 2)}\n`)
      })
    },
  }
}

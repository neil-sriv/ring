import path from "node:path"
import { defineConfig } from "vitest/config"

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    include: [
      "src/hooks/**/*.test.ts",
      "src/hooks/**/*.test.tsx",
      "src/components/Loops/EditLoop.test.tsx",
      "src/components/Loops/AddLoop.test.tsx",
      "src/components/Loops/AddAdhocLoop.test.tsx",
      "src/components/Loops/LoopQuestionActions.test.tsx",
      "src/components/Loops/LoopReplyTracker.test.tsx",
      "src/components/Loops/SendLetterNow.test.tsx",
      "src/components/Groups/AddGroup.test.tsx",
      "src/components/Groups/AddMembers.test.tsx",
      "src/components/Groups/EditGroup.test.tsx",
      "src/components/Groups/RemoveMemberConfirmation.test.tsx",
      "src/components/Question/DraftQuestion.test.tsx",
      "src/components/Question/PublishedQuestion.test.tsx",
      "src/components/Question/AddQuestion.test.tsx",
      "src/components/Question/GenerateQuestion.test.tsx",
      "src/components/Spotify/AddSongsToSpotify.test.tsx",
      "src/components/Spotify/GroupSpotifyPlaylist.test.tsx",
      "src/components/Spotify/useSpotifyAccount.test.ts",
      "src/components/Home/HomeDashboard.test.tsx",
      "src/components/Document/Editor.test.tsx",
      "src/route-tests/GroupStoreTab.test.tsx",
      "src/route-tests/groupLoopsRoute.remount.test.tsx",
      "src/route-tests/groupSettingsRoute.remount.test.tsx",
      "src/route-tests/loopId.remount.test.tsx",
    ],
    setupFiles: ["./src/test-setup.ts"],
  },
})

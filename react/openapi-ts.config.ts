import { defaultPlugins } from "@hey-api/openapi-ts";

export default {
  input: "openapi.json",
  output: "src/client",
  plugins: [
    ...defaultPlugins,
    "@hey-api/client-axios",
    "@tanstack/react-query",
  ],
};

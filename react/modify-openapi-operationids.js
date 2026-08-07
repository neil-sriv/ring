import * as fs from "node:fs"

function modifyOpenAPIFile(filePath) {
  const data = fs.readFileSync(filePath)
  const openapiContent = JSON.parse(data)

  const paths = openapiContent.paths
  for (const pathKey of Object.keys(paths)) {
    const pathData = paths[pathKey]
    for (const method of Object.keys(pathData)) {
      const operation = pathData[method]
      if (operation.tags && operation.tags.length > 0) {
        const tag = operation.tags[0]
        const operationId = operation.operationId
        const toRemove = `${tag}-`
        if (operationId.startsWith(toRemove)) {
          const newOperationId = operationId.substring(toRemove.length)
          operation.operationId = newOperationId
        }
      }
    }
  }

  fs.writeFileSync(filePath, JSON.stringify(openapiContent, null, 2))
  console.log("File successfully modified")
}

const filePath = "./openapi.json"
try {
  modifyOpenAPIFile(filePath)
} catch (err) {
  console.error("Error:", err)
  process.exit(1)
}

import type { ApiRequestOptions } from "./ApiRequestOptions";
import type { ApiResult } from "./ApiResult";

class ErrorDetail {
  public readonly detail!: string;
}

export class ApiError extends Error {
  public readonly url: string;
  public readonly status: number;
  public readonly statusText: string;
  public readonly body: ErrorDetail;
  public readonly request: ApiRequestOptions;

  constructor(
    request: ApiRequestOptions,
    response: ApiResult,
    message: string
  ) {
    super(message);

    this.name = "ApiError";
    this.url = response.url;
    this.status = response.status;
    this.statusText = response.statusText;
    this.body = response.body;
    this.request = request;
  }
}

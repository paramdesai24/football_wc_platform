export interface PaginationQuery {
  limit?: number;
  offset?: number;
}

export interface ApiSuccess<T> {
  data: T;
  message?: string;
  timestamp: string;
}

export interface ApiFailure {
  error: string;
  message: string;
  timestamp: string;
}

export type ApiResult<T> = ApiSuccess<T> | ApiFailure;

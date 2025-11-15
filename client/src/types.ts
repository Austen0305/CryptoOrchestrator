// Re-export shared types
export * from '@shared/types';

// Additional frontend-specific types
export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
}

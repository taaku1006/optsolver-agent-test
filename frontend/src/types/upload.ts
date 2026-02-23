/**
 * Upload-related type definitions
 */

export interface FileValidationResult {
  isValid: boolean
  error?: FileValidationError
}

export interface FileValidationError {
  type: 'INVALID_TYPE' | 'FILE_TOO_LARGE' | 'UNKNOWN_ERROR'
  message: string
}

export interface FileValidationOptions {
  maxSizeInMB?: number
  allowedTypes?: string[]
}

import type { FileValidationResult, FileValidationOptions } from '../types/upload'

const DEFAULT_MAX_SIZE_MB = 50
const PDF_MIME_TYPES = ['application/pdf']
const PDF_EXTENSIONS = ['.pdf']

/**
 * Validates a file for upload
 * Checks file type (PDF only) and size limits
 */
export const validateFile = (
  file: File,
  options: FileValidationOptions = {}
): FileValidationResult => {
  const maxSizeInMB = options.maxSizeInMB ?? DEFAULT_MAX_SIZE_MB
  const allowedTypes = options.allowedTypes ?? PDF_MIME_TYPES

  // Check file type by MIME type
  if (!allowedTypes.includes(file.type)) {
    // Also check file extension as fallback
    const hasValidExtension = PDF_EXTENSIONS.some(ext =>
      file.name.toLowerCase().endsWith(ext)
    )

    if (!hasValidExtension) {
      return {
        isValid: false,
        error: {
          type: 'INVALID_TYPE',
          message: 'Please upload a PDF file. Other file types are not supported.'
        }
      }
    }
  }

  // Check file size
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024
  if (file.size > maxSizeInBytes) {
    return {
      isValid: false,
      error: {
        type: 'FILE_TOO_LARGE',
        message: `File size exceeds ${maxSizeInMB}MB limit. Please upload a smaller file.`
      }
    }
  }

  // File is valid
  return {
    isValid: true
  }
}

/**
 * Formats file size in human-readable format
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

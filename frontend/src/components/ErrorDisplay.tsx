import { FC } from 'react'
import styles from './ErrorDisplay.module.css'
import type { PDFExtractionError } from '../types/pdf'
import type { FileValidationError } from '../types/upload'

export type ErrorType =
  | PDFExtractionError['type']
  | FileValidationError['type']
  | 'NETWORK_ERROR'

interface ErrorDisplayProps {
  error: string
  errorType?: ErrorType
  onRetry?: () => void
  onDismiss?: () => void
  showRetry?: boolean
  showDismiss?: boolean
}

const ErrorDisplay: FC<ErrorDisplayProps> = ({
  error,
  errorType,
  onRetry,
  onDismiss,
  showRetry = true,
  showDismiss = false
}) => {
  // Determine error icon and color based on error type
  const getErrorIcon = () => {
    switch (errorType) {
      case 'CORRUPTED_PDF':
      case 'EXTRACTION_FAILED':
        return (
          <svg
            className={styles.icon}
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="9" y1="15" x2="15" y2="15" />
          </svg>
        )
      case 'PASSWORD_PROTECTED':
        return (
          <svg
            className={styles.icon}
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
        )
      case 'INVALID_TYPE':
        return (
          <svg
            className={styles.icon}
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        )
      case 'FILE_TOO_LARGE':
        return (
          <svg
            className={styles.icon}
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
            <polyline points="13 2 13 9 20 9" />
            <line x1="12" y1="12" x2="12" y2="18" />
            <line x1="9" y1="15" x2="15" y2="15" />
          </svg>
        )
      case 'NETWORK_ERROR':
        return (
          <svg
            className={styles.icon}
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
          </svg>
        )
      default:
        return (
          <svg
            className={styles.icon}
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        )
    }
  }

  // Get user-friendly title based on error type
  const getErrorTitle = () => {
    switch (errorType) {
      case 'CORRUPTED_PDF':
        return 'Corrupted PDF File'
      case 'PASSWORD_PROTECTED':
        return 'Password Protected PDF'
      case 'EXTRACTION_FAILED':
        return 'Extraction Failed'
      case 'INVALID_TYPE':
        return 'Invalid File Type'
      case 'FILE_TOO_LARGE':
        return 'File Too Large'
      case 'NETWORK_ERROR':
        return 'Network Error'
      case 'UNKNOWN_ERROR':
        return 'Unknown Error'
      default:
        return 'Error'
    }
  }

  // Get helpful suggestion based on error type
  const getErrorSuggestion = () => {
    switch (errorType) {
      case 'CORRUPTED_PDF':
        return 'The PDF file appears to be corrupted or damaged. Please try a different file.'
      case 'PASSWORD_PROTECTED':
        return 'This PDF is password protected. Please remove the password protection and try again.'
      case 'EXTRACTION_FAILED':
        return 'Unable to extract text from this PDF. The file may be scanned images without text layers.'
      case 'INVALID_TYPE':
        return 'Please upload a valid PDF file.'
      case 'FILE_TOO_LARGE':
        return 'Please select a smaller file and try again.'
      case 'NETWORK_ERROR':
        return 'Please check your internet connection and try again.'
      default:
        return 'Please try again or contact support if the problem persists.'
    }
  }

  return (
    <div className={styles.container} role="alert" aria-live="assertive">
      <div className={styles.iconContainer}>
        {getErrorIcon()}
      </div>

      <div className={styles.content}>
        <h3 className={styles.title}>{getErrorTitle()}</h3>
        <p className={styles.message}>{error}</p>
        <p className={styles.suggestion}>{getErrorSuggestion()}</p>
      </div>

      <div className={styles.actions}>
        {showRetry && onRetry && (
          <button
            className={`${styles.button} ${styles.retryButton}`}
            onClick={onRetry}
            type="button"
            aria-label="Retry operation"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polyline points="23 4 23 10 17 10" />
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
            </svg>
            <span>Try Again</span>
          </button>
        )}
        {showDismiss && onDismiss && (
          <button
            className={`${styles.button} ${styles.dismissButton}`}
            onClick={onDismiss}
            type="button"
            aria-label="Dismiss error"
          >
            <span>Dismiss</span>
          </button>
        )}
      </div>
    </div>
  )
}

export default ErrorDisplay

import { FC, useState } from 'react'
import DragDropZone from './DragDropZone'
import LoadingIndicator from './LoadingIndicator'
import ErrorDisplay, { ErrorType } from './ErrorDisplay'
import TextPreview from './TextPreview'
import { usePDFExtraction } from '../hooks/usePDFExtraction'
import type { FileValidationError } from '../types/upload'

interface PDFUploaderProps {
  maxSizeInMB?: number
}

const PDFUploader: FC<PDFUploaderProps> = ({ maxSizeInMB = 50 }) => {
  const { state, extractText, reset } = usePDFExtraction()
  const [validationError, setValidationError] = useState<FileValidationError | null>(null)

  // Handle file selection from DragDropZone
  const handleFileSelect = async (file: File) => {
    // Clear any previous validation errors
    setValidationError(null)

    // Start extraction process
    await extractText(file, {
      preserveFormatting: true,
      includeMetadata: true
    })
  }

  // Handle validation errors from DragDropZone
  const handleValidationError = (error: FileValidationError) => {
    setValidationError(error)
  }

  // Handle retry action from ErrorDisplay
  const handleRetry = () => {
    setValidationError(null)
    reset()
  }

  // Determine current error type and message for ErrorDisplay
  const getCurrentError = (): { type: ErrorType; message: string } | null => {
    if (validationError) {
      return {
        type: validationError.type,
        message: validationError.message
      }
    }

    if (state.error) {
      // Parse error message to determine type
      // The usePDFExtraction hook returns error messages from PDFExtractionError
      const errorMessage = state.error.toLowerCase()
      let errorType: ErrorType = 'UNKNOWN_ERROR'

      if (errorMessage.includes('scanned') || errorMessage.includes('image-only')) {
        errorType = 'SCANNED_PDF'
      } else if (errorMessage.includes('timeout') || errorMessage.includes('taking too long')) {
        errorType = 'TIMEOUT_ERROR'
      } else if (errorMessage.includes('network') || errorMessage.includes('cdn') || errorMessage.includes('internet connection')) {
        errorType = 'NETWORK_ERROR'
      } else if (errorMessage.includes('corrupted') || errorMessage.includes('damaged') || errorMessage.includes('invalid')) {
        errorType = 'CORRUPTED_PDF'
      } else if (errorMessage.includes('password') || errorMessage.includes('encrypted')) {
        errorType = 'PASSWORD_PROTECTED'
      } else if (errorMessage.includes('extract') || errorMessage.includes('memory')) {
        errorType = 'EXTRACTION_FAILED'
      }

      return {
        type: errorType,
        message: state.error
      }
    }

    return null
  }

  const currentError = getCurrentError()

  // Warning banner component for displaying warnings
  const WarningBanner: FC<{ message: string }> = ({ message }) => (
    <div
      style={{
        padding: '1rem',
        marginBottom: '1rem',
        backgroundColor: '#fef3c7',
        border: '1px solid #f59e0b',
        borderRadius: '0.5rem',
        color: '#92400e',
        fontSize: '0.875rem',
        lineHeight: '1.5'
      }}
      role="alert"
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <span>{message}</span>
      </div>
    </div>
  )

  // Render based on current state
  return (
    <div className="pdf-uploader">
      {currentError ? (
        // Show error display
        <ErrorDisplay
          error={currentError.message}
          errorType={currentError.type}
          onRetry={handleRetry}
          showRetry={true}
          showDismiss={false}
        />
      ) : state.isLoading ? (
        // Show loading indicator during extraction with optional warning
        <div>
          {state.warning && <WarningBanner message={state.warning} />}
          <LoadingIndicator progress={state.progress} />
        </div>
      ) : state.result ? (
        // Show text preview after successful extraction
        <div>
          {state.warning && <WarningBanner message={state.warning} />}
          <TextPreview result={state.result} />
          <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
            <button
              onClick={handleRetry}
              style={{
                padding: '0.75rem 1.5rem',
                fontSize: '1rem',
                fontWeight: '500',
                color: '#fff',
                backgroundColor: '#4f46e5',
                border: 'none',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#4338ca'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#4f46e5'
              }}
            >
              Upload Another PDF
            </button>
          </div>
        </div>
      ) : (
        // Show upload zone initially
        <DragDropZone
          onFileSelect={handleFileSelect}
          maxSizeInMB={maxSizeInMB}
          onValidationError={handleValidationError}
        />
      )}
    </div>
  )
}

export default PDFUploader

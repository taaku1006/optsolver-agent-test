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

      if (errorMessage.includes('corrupted') || errorMessage.includes('damaged')) {
        errorType = 'CORRUPTED_PDF'
      } else if (errorMessage.includes('password')) {
        errorType = 'PASSWORD_PROTECTED'
      } else if (errorMessage.includes('extract')) {
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
        // Show loading indicator during extraction
        <LoadingIndicator progress={state.progress} />
      ) : state.result ? (
        // Show text preview after successful extraction
        <div>
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

import { useState, useCallback } from 'react'
import { extractTextFromPDF } from '../utils/pdfParser'
import type { PDFExtractionResult, PDFExtractionOptions } from '../types/pdf'

export interface PDFExtractionState {
  isLoading: boolean
  progress: number
  result: PDFExtractionResult | null
  error: string | null
  warning: string | null
}

export interface UsePDFExtractionReturn {
  state: PDFExtractionState
  extractText: (file: File, options?: PDFExtractionOptions) => Promise<void>
  reset: () => void
}

/**
 * Custom hook for managing PDF text extraction state and progress
 *
 * @returns Object containing extraction state and methods to extract text
 */
export const usePDFExtraction = (): UsePDFExtractionReturn => {
  const [state, setState] = useState<PDFExtractionState>({
    isLoading: false,
    progress: 0,
    result: null,
    error: null,
    warning: null
  })

  /**
   * Extract text from a PDF file
   */
  const extractText = useCallback(async (
    file: File,
    options?: PDFExtractionOptions
  ): Promise<void> => {
    // Check for large file and set warning
    const fileSizeMB = file.size / (1024 * 1024)
    const LARGE_FILE_THRESHOLD_MB = 30 // Warn for files > 30MB (limit is 50MB)
    const largeFileWarning = fileSizeMB > LARGE_FILE_THRESHOLD_MB
      ? `Processing large file (${fileSizeMB.toFixed(1)}MB). This may take a moment...`
      : null

    // Reset state and start loading
    setState({
      isLoading: true,
      progress: 0,
      result: null,
      error: null,
      warning: largeFileWarning
    })

    try {
      // Simulate initial progress
      setState(prev => ({ ...prev, progress: 10 }))

      // Add delay for large files to show progress
      if (fileSizeMB > LARGE_FILE_THRESHOLD_MB) {
        await new Promise(resolve => setTimeout(resolve, 100))
        setState(prev => ({ ...prev, progress: 20 }))
      }

      // Extract text from PDF
      const result = await extractTextFromPDF(file, options)

      // Update progress to halfway during extraction
      setState(prev => ({ ...prev, progress: 50 }))

      // Check if extraction resulted in an error
      if (result.error) {
        // For scanned PDFs, show warning instead of error if text was extracted
        if (result.error.type === 'SCANNED_PDF' && result.text.trim().length > 0) {
          setState({
            isLoading: false,
            progress: 100,
            result,
            error: null,
            warning: `${result.error.message} ${result.error.details || ''}`
          })
          return
        }

        // For other errors, show error state
        const errorDetails = result.error.details ? `\n\n${result.error.details}` : ''
        setState({
          isLoading: false,
          progress: 0,
          result: null,
          error: `${result.error.message}${errorDetails}`,
          warning: null
        })
        return
      }

      // Success - update state with result
      setState({
        isLoading: false,
        progress: 100,
        result,
        error: null,
        warning: null
      })
    } catch (error) {
      // Handle unexpected errors
      const errorMessage = error instanceof Error
        ? error.message
        : 'An unexpected error occurred during PDF extraction'

      setState({
        isLoading: false,
        progress: 0,
        result: null,
        error: errorMessage,
        warning: null
      })
    }
  }, [])

  /**
   * Reset the extraction state
   */
  const reset = useCallback(() => {
    setState({
      isLoading: false,
      progress: 0,
      result: null,
      error: null,
      warning: null
    })
  }, [])

  return {
    state,
    extractText,
    reset
  }
}

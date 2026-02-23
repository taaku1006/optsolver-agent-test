import { useState, useCallback } from 'react'
import { extractTextFromPDF } from '../utils/pdfParser'
import type { PDFExtractionResult, PDFExtractionOptions } from '../types/pdf'

export interface PDFExtractionState {
  isLoading: boolean
  progress: number
  result: PDFExtractionResult | null
  error: string | null
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
    error: null
  })

  /**
   * Extract text from a PDF file
   */
  const extractText = useCallback(async (
    file: File,
    options?: PDFExtractionOptions
  ): Promise<void> => {
    // Reset state and start loading
    setState({
      isLoading: true,
      progress: 0,
      result: null,
      error: null
    })

    try {
      // Simulate initial progress
      setState(prev => ({ ...prev, progress: 10 }))

      // Extract text from PDF
      const result = await extractTextFromPDF(file, options)

      // Update progress to halfway during extraction
      setState(prev => ({ ...prev, progress: 50 }))

      // Check if extraction resulted in an error
      if (result.error) {
        setState({
          isLoading: false,
          progress: 0,
          result: null,
          error: result.error.message
        })
        return
      }

      // Success - update state with result
      setState({
        isLoading: false,
        progress: 100,
        result,
        error: null
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
        error: errorMessage
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
      error: null
    })
  }, [])

  return {
    state,
    extractText,
    reset
  }
}

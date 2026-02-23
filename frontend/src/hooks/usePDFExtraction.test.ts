import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { usePDFExtraction } from './usePDFExtraction'
import * as pdfParser from '../utils/pdfParser'
import type { PDFExtractionResult } from '../types/pdf'

// Mock the pdfParser module
vi.mock('../utils/pdfParser', () => ({
  extractTextFromPDF: vi.fn()
}))

describe('usePDFExtraction', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => usePDFExtraction())

      expect(result.current.state.isLoading).toBe(false)
      expect(result.current.state.progress).toBe(0)
      expect(result.current.state.result).toBeNull()
      expect(result.current.state.error).toBeNull()
    })

    it('should provide extractText and reset functions', () => {
      const { result } = renderHook(() => usePDFExtraction())

      expect(typeof result.current.extractText).toBe('function')
      expect(typeof result.current.reset).toBe('function')
    })
  })

  describe('extractText', () => {
    it('should successfully extract text from PDF', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const mockResult: PDFExtractionResult = {
        text: 'Sample PDF text content',
        pageCount: 3,
        metadata: {
          title: 'Test Document'
        }
      }

      vi.mocked(pdfParser.extractTextFromPDF).mockResolvedValue(mockResult)

      const { result } = renderHook(() => usePDFExtraction())

      // Start extraction
      await act(async () => {
        await result.current.extractText(mockFile)
      })

      // Wait for loading to complete
      await waitFor(() => {
        expect(result.current.state.isLoading).toBe(false)
      })

      // Verify final state
      expect(result.current.state.isLoading).toBe(false)
      expect(result.current.state.progress).toBe(100)
      expect(result.current.state.result).toEqual(mockResult)
      expect(result.current.state.error).toBeNull()
      expect(pdfParser.extractTextFromPDF).toHaveBeenCalledWith(mockFile, undefined)
    })

    it('should pass options to extractTextFromPDF', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const mockResult: PDFExtractionResult = {
        text: 'Sample PDF text',
        pageCount: 1
      }

      const options = {
        preserveFormatting: false,
        includeMetadata: false
      }

      vi.mocked(pdfParser.extractTextFromPDF).mockResolvedValue(mockResult)

      const { result } = renderHook(() => usePDFExtraction())

      await act(async () => {
        await result.current.extractText(mockFile, options)
      })

      await waitFor(() => {
        expect(result.current.state.isLoading).toBe(false)
      })

      expect(pdfParser.extractTextFromPDF).toHaveBeenCalledWith(mockFile, options)
    })

    it('should set loading state during extraction', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const mockResult: PDFExtractionResult = {
        text: 'Sample text',
        pageCount: 1
      }

      // Create a promise that we can control
      let resolveExtraction: (value: PDFExtractionResult) => void
      const extractionPromise = new Promise<PDFExtractionResult>((resolve) => {
        resolveExtraction = resolve
      })

      vi.mocked(pdfParser.extractTextFromPDF).mockReturnValue(extractionPromise)

      const { result } = renderHook(() => usePDFExtraction())

      // Start extraction
      act(() => {
        result.current.extractText(mockFile)
      })

      // Should be loading immediately
      await waitFor(() => {
        expect(result.current.state.isLoading).toBe(true)
      })
      expect(result.current.state.progress).toBeGreaterThan(0)

      // Resolve the extraction
      await act(async () => {
        resolveExtraction(mockResult)
        await extractionPromise
      })

      // Should no longer be loading
      await waitFor(() => {
        expect(result.current.state.isLoading).toBe(false)
      })
    })

    it('should update progress during extraction', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const mockResult: PDFExtractionResult = {
        text: 'Sample text',
        pageCount: 1
      }

      vi.mocked(pdfParser.extractTextFromPDF).mockResolvedValue(mockResult)

      const { result } = renderHook(() => usePDFExtraction())

      await act(async () => {
        await result.current.extractText(mockFile)
      })

      await waitFor(() => {
        expect(result.current.state.progress).toBe(100)
      })
    })

    it('should handle extraction errors from pdfParser', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const mockResult: PDFExtractionResult = {
        text: '',
        pageCount: 0,
        error: {
          type: 'CORRUPTED_PDF',
          message: 'This PDF appears to be corrupted or invalid.'
        }
      }

      vi.mocked(pdfParser.extractTextFromPDF).mockResolvedValue(mockResult)

      const { result } = renderHook(() => usePDFExtraction())

      await act(async () => {
        await result.current.extractText(mockFile)
      })

      await waitFor(() => {
        expect(result.current.state.isLoading).toBe(false)
      })

      // Verify error state
      expect(result.current.state.isLoading).toBe(false)
      expect(result.current.state.progress).toBe(0)
      expect(result.current.state.result).toBeNull()
      expect(result.current.state.error).toBe('This PDF appears to be corrupted or invalid.')
    })

    it('should handle password-protected PDF errors', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const mockResult: PDFExtractionResult = {
        text: '',
        pageCount: 0,
        error: {
          type: 'PASSWORD_PROTECTED',
          message: 'This PDF is password-protected.'
        }
      }

      vi.mocked(pdfParser.extractTextFromPDF).mockResolvedValue(mockResult)

      const { result } = renderHook(() => usePDFExtraction())

      await act(async () => {
        await result.current.extractText(mockFile)
      })

      await waitFor(() => {
        expect(result.current.state.error).toBe('This PDF is password-protected.')
      })

      expect(result.current.state.result).toBeNull()
    })

    it('should handle unexpected errors during extraction', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const errorMessage = 'Network error'
      vi.mocked(pdfParser.extractTextFromPDF).mockRejectedValue(new Error(errorMessage))

      const { result } = renderHook(() => usePDFExtraction())

      await act(async () => {
        await result.current.extractText(mockFile)
      })

      await waitFor(() => {
        expect(result.current.state.isLoading).toBe(false)
      })

      // Verify error state
      expect(result.current.state.error).toBe(errorMessage)
      expect(result.current.state.result).toBeNull()
      expect(result.current.state.progress).toBe(0)
    })

    it('should handle non-Error exceptions', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      vi.mocked(pdfParser.extractTextFromPDF).mockRejectedValue('String error')

      const { result } = renderHook(() => usePDFExtraction())

      await act(async () => {
        await result.current.extractText(mockFile)
      })

      await waitFor(() => {
        expect(result.current.state.isLoading).toBe(false)
      })

      expect(result.current.state.error).toBe('An unexpected error occurred during PDF extraction')
    })
  })

  describe('reset', () => {
    it('should reset state to initial values', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const mockResult: PDFExtractionResult = {
        text: 'Sample text',
        pageCount: 1
      }

      vi.mocked(pdfParser.extractTextFromPDF).mockResolvedValue(mockResult)

      const { result } = renderHook(() => usePDFExtraction())

      // Extract text first
      await act(async () => {
        await result.current.extractText(mockFile)
      })

      await waitFor(() => {
        expect(result.current.state.result).not.toBeNull()
      })

      // Reset state
      act(() => {
        result.current.reset()
      })

      // Verify reset to initial state
      expect(result.current.state.isLoading).toBe(false)
      expect(result.current.state.progress).toBe(0)
      expect(result.current.state.result).toBeNull()
      expect(result.current.state.error).toBeNull()
    })

    it('should reset after error state', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      vi.mocked(pdfParser.extractTextFromPDF).mockRejectedValue(new Error('Test error'))

      const { result } = renderHook(() => usePDFExtraction())

      // Trigger error
      await act(async () => {
        await result.current.extractText(mockFile)
      })

      await waitFor(() => {
        expect(result.current.state.error).toBeTruthy()
      })

      // Reset
      act(() => {
        result.current.reset()
      })

      // Verify reset
      expect(result.current.state.error).toBeNull()
      expect(result.current.state.result).toBeNull()
    })
  })

  describe('multiple extractions', () => {
    it('should reset state when starting new extraction', async () => {
      const mockFile1 = new File(['fake pdf 1'], 'test1.pdf', {
        type: 'application/pdf'
      })

      const mockFile2 = new File(['fake pdf 2'], 'test2.pdf', {
        type: 'application/pdf'
      })

      const mockResult1: PDFExtractionResult = {
        text: 'First PDF text',
        pageCount: 1
      }

      const mockResult2: PDFExtractionResult = {
        text: 'Second PDF text',
        pageCount: 2
      }

      vi.mocked(pdfParser.extractTextFromPDF)
        .mockResolvedValueOnce(mockResult1)
        .mockResolvedValueOnce(mockResult2)

      const { result } = renderHook(() => usePDFExtraction())

      // First extraction
      await act(async () => {
        await result.current.extractText(mockFile1)
      })

      await waitFor(() => {
        expect(result.current.state.result?.text).toBe('First PDF text')
      })

      // Second extraction should reset state first
      await act(async () => {
        await result.current.extractText(mockFile2)
      })

      await waitFor(() => {
        expect(result.current.state.result?.text).toBe('Second PDF text')
      })

      expect(result.current.state.result?.pageCount).toBe(2)
    })
  })
})

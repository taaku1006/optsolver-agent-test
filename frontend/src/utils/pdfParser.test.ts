import { describe, it, expect, vi, beforeEach } from 'vitest'
import { extractTextFromPDF } from './pdfParser'
import type * as pdfjsLib from 'pdfjs-dist'

// Mock pdfjs-dist
vi.mock('pdfjs-dist', () => {
  const mockGetDocument = vi.fn()

  return {
    GlobalWorkerOptions: {
      workerSrc: ''
    },
    getDocument: mockGetDocument,
    version: '5.4.624'
  }
})

describe('pdfParser', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('extractTextFromPDF', () => {
    it('should extract text from a valid PDF', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      // Mock PDF.js response
      const mockPdf = createMockPdf({
        numPages: 2,
        pages: [
          {
            pageNumber: 1,
            textItems: [
              { str: 'Hello', transform: [1, 0, 0, 1, 10, 100], width: 50, height: 12 },
              { str: 'World', transform: [1, 0, 0, 1, 70, 100], width: 50, height: 12 }
            ]
          },
          {
            pageNumber: 2,
            textItems: [
              { str: 'Page', transform: [1, 0, 0, 1, 10, 100], width: 40, height: 12 },
              { str: 'Two', transform: [1, 0, 0, 1, 60, 100], width: 40, height: 12 }
            ]
          }
        ]
      })

      const pdfjsLib = await import('pdfjs-dist')
      vi.mocked(pdfjsLib.getDocument).mockReturnValue({
        promise: Promise.resolve(mockPdf)
      } as unknown as pdfjsLib.PDFDocumentLoadingTask)

      const result = await extractTextFromPDF(mockFile)

      expect(result.text).toContain('Hello World')
      expect(result.text).toContain('Page Two')
      expect(result.pageCount).toBe(2)
      expect(result.error).toBeUndefined()
    })

    it('should extract metadata when includeMetadata is true', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const mockPdf = createMockPdf({
        numPages: 1,
        pages: [
          {
            pageNumber: 1,
            textItems: [
              { str: 'Test', transform: [1, 0, 0, 1, 10, 100], width: 40, height: 12 }
            ]
          }
        ],
        metadata: {
          Title: 'Test Document',
          Author: 'Test Author',
          Subject: 'Testing'
        }
      })

      const pdfjsLib = await import('pdfjs-dist')
      vi.mocked(pdfjsLib.getDocument).mockReturnValue({
        promise: Promise.resolve(mockPdf)
      } as unknown as pdfjsLib.PDFDocumentLoadingTask)

      const result = await extractTextFromPDF(mockFile, { includeMetadata: true })

      expect(result.metadata).toBeDefined()
      expect(result.metadata?.title).toBe('Test Document')
      expect(result.metadata?.author).toBe('Test Author')
      expect(result.metadata?.subject).toBe('Testing')
    })

    it('should handle password-protected PDFs', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const pdfjsLib = await import('pdfjs-dist')
      vi.mocked(pdfjsLib.getDocument).mockReturnValue({
        promise: Promise.reject(new Error('password required'))
      } as unknown as pdfjsLib.PDFDocumentLoadingTask)

      const result = await extractTextFromPDF(mockFile)

      expect(result.text).toBe('')
      expect(result.pageCount).toBe(0)
      expect(result.error).toBeDefined()
      expect(result.error?.type).toBe('PASSWORD_PROTECTED')
      expect(result.error?.message).toContain('password-protected')
    })

    it('should handle corrupted PDFs', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const pdfjsLib = await import('pdfjs-dist')
      vi.mocked(pdfjsLib.getDocument).mockReturnValue({
        promise: Promise.reject(new Error('Invalid PDF structure'))
      } as unknown as pdfjsLib.PDFDocumentLoadingTask)

      const result = await extractTextFromPDF(mockFile)

      expect(result.text).toBe('')
      expect(result.pageCount).toBe(0)
      expect(result.error).toBeDefined()
      expect(result.error?.type).toBe('CORRUPTED_PDF')
      expect(result.error?.message).toContain('corrupted or invalid')
    })

    it('should handle generic extraction failures', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const pdfjsLib = await import('pdfjs-dist')
      vi.mocked(pdfjsLib.getDocument).mockReturnValue({
        promise: Promise.reject(new Error('Unknown error'))
      } as unknown as pdfjsLib.PDFDocumentLoadingTask)

      const result = await extractTextFromPDF(mockFile)

      expect(result.text).toBe('')
      expect(result.pageCount).toBe(0)
      expect(result.error).toBeDefined()
      expect(result.error?.type).toBe('EXTRACTION_FAILED')
    })

    it('should preserve formatting when preserveFormatting is true', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      // Mock multi-line text with different Y positions
      const mockPdf = createMockPdf({
        numPages: 1,
        pages: [
          {
            pageNumber: 1,
            textItems: [
              { str: 'Line', transform: [1, 0, 0, 1, 10, 100], width: 40, height: 12 },
              { str: 'One', transform: [1, 0, 0, 1, 60, 100], width: 40, height: 12 },
              { str: 'Line', transform: [1, 0, 0, 1, 10, 85], width: 40, height: 12 },
              { str: 'Two', transform: [1, 0, 0, 1, 60, 85], width: 40, height: 12 }
            ]
          }
        ]
      })

      const pdfjsLib = await import('pdfjs-dist')
      vi.mocked(pdfjsLib.getDocument).mockReturnValue({
        promise: Promise.resolve(mockPdf)
      } as unknown as pdfjsLib.PDFDocumentLoadingTask)

      const result = await extractTextFromPDF(mockFile, { preserveFormatting: true })

      expect(result.text).toContain('\n') // Should have newlines
      expect(result.text).toMatch(/Line One.*Line Two/s) // Should preserve line order
    })

    it('should handle empty PDFs', async () => {
      const mockFile = new File(['fake pdf content'], 'test.pdf', {
        type: 'application/pdf'
      })

      const mockPdf = createMockPdf({
        numPages: 1,
        pages: [
          {
            pageNumber: 1,
            textItems: []
          }
        ]
      })

      const pdfjsLib = await import('pdfjs-dist')
      vi.mocked(pdfjsLib.getDocument).mockReturnValue({
        promise: Promise.resolve(mockPdf)
      } as unknown as pdfjsLib.PDFDocumentLoadingTask)

      const result = await extractTextFromPDF(mockFile)

      expect(result.text).toBe('')
      expect(result.pageCount).toBe(1)
      expect(result.error).toBeUndefined()
    })
  })
})

// Helper function to create mock PDF objects
function createMockPdf(config: {
  numPages: number
  pages: Array<{
    pageNumber: number
    textItems: Array<{
      str: string
      transform: number[]
      width: number
      height: number
    }>
  }>
  metadata?: Record<string, unknown>
}) {
  const pages = new Map()

  config.pages.forEach(pageConfig => {
    pages.set(pageConfig.pageNumber, {
      getTextContent: vi.fn().mockResolvedValue({
        items: pageConfig.textItems
      })
    })
  })

  return {
    numPages: config.numPages,
    getPage: vi.fn((pageNum: number) => {
      return Promise.resolve(pages.get(pageNum))
    }),
    getMetadata: vi.fn().mockResolvedValue({
      info: config.metadata || {}
    })
  }
}

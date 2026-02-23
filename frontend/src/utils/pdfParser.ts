import * as pdfjsLib from 'pdfjs-dist'
import type {
  PDFExtractionResult,
  PDFExtractionOptions,
  PDFMetadata,
  PDFPageText
} from '../types/pdf'

// Configure PDF.js worker
// Using CDN for worker to avoid bundling issues with Vite
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

/**
 * Extracts text content from a PDF file
 * Handles multi-column layouts by sorting text items by vertical then horizontal position
 */
export const extractTextFromPDF = async (
  file: File,
  options: PDFExtractionOptions = {}
): Promise<PDFExtractionResult> => {
  const { preserveFormatting = true, includeMetadata = true } = options

  try {
    // Read file as ArrayBuffer
    const arrayBuffer = await file.arrayBuffer()
    const typedArray = new Uint8Array(arrayBuffer)

    // Load PDF document with timeout
    const loadingTask = pdfjsLib.getDocument({
      data: typedArray,
      useSystemFonts: true,
      standardFontDataUrl: `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/standard_fonts/`
    })

    // Add timeout for very large or slow PDFs (2 minutes)
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => {
        reject(new Error('PDF extraction timeout: File is too large or processing is taking too long'))
      }, 120000)
    })

    const pdf = await Promise.race([loadingTask.promise, timeoutPromise])

    // Extract metadata if requested
    let metadata: PDFMetadata | undefined
    if (includeMetadata) {
      metadata = await extractMetadata(pdf)
    }

    // Extract text from all pages
    const pageTexts: PDFPageText[] = []
    let totalCharacters = 0

    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
      const page = await pdf.getPage(pageNum)
      const pageText = await extractPageText(page, preserveFormatting)
      pageTexts.push({
        pageNumber: pageNum,
        text: pageText
      })
      totalCharacters += pageText.length
    }

    // Combine all page texts
    const fullText = pageTexts
      .map(pt => pt.text)
      .join('\n\n--- Page Break ---\n\n')

    // Check for scanned PDF (image-only with no extractable text)
    // Use per-page average to detect scanned documents
    // Multi-page documents with very little text per page are likely scanned
    const avgCharsPerPage = pdf.numPages > 0 ? totalCharacters / pdf.numPages : 0
    const MIN_CHARS_PER_PAGE = 10 // Very low threshold - less than this suggests scanned images
    const MIN_TOTAL_CHARS_MULTIPAGE = 100 // For multi-page docs, also check total

    // Only flag as scanned if:
    // 1. Multi-page document (>2 pages) with very little text per page
    // 2. File size suggests content but extraction yielded almost nothing
    const isLikelyScanned = (
      pdf.numPages > 2 &&
      avgCharsPerPage < MIN_CHARS_PER_PAGE &&
      totalCharacters < MIN_TOTAL_CHARS_MULTIPAGE &&
      file.size > 100000 // File is >100KB but has almost no text
    )

    if (isLikelyScanned) {
      return {
        text: fullText,
        pageCount: pdf.numPages,
        metadata,
        error: {
          type: 'SCANNED_PDF',
          message: 'This PDF appears to be scanned images without text layers.',
          details: `Only ${totalCharacters} characters were extracted from ${pdf.numPages} page(s) (${avgCharsPerPage.toFixed(1)} chars/page). The document may contain only images or require OCR processing.`
        }
      }
    }

    return {
      text: fullText,
      pageCount: pdf.numPages,
      metadata
    }
  } catch (error) {
    return handleExtractionError(error, file)
  }
}

/**
 * Extracts text from a single PDF page
 * Preserves structure by sorting text items by position
 */
const extractPageText = async (
  page: pdfjsLib.PDFPageProxy,
  preserveFormatting: boolean
): Promise<string> => {
  const textContent = await page.getTextContent()
  const textItems = textContent.items as Array<{
    str: string
    transform: number[]
    width: number
    height: number
  }>

  if (!preserveFormatting) {
    // Simple extraction: just concatenate all text
    return textItems.map(item => item.str).join(' ')
  }

  // Advanced extraction: preserve layout structure
  // Sort items by Y position (top to bottom) then X position (left to right)
  // This helps handle multi-column layouts
  const sortedItems = textItems.slice().sort((a, b) => {
    const yDiff = Math.abs(b.transform[5] - a.transform[5])
    // If Y positions are close (same line), sort by X
    if (yDiff < 5) {
      return a.transform[4] - b.transform[4]
    }
    // Otherwise sort by Y (top to bottom)
    return b.transform[5] - a.transform[5]
  })

  // Group items into lines based on Y position
  const lines: string[][] = []
  let currentLine: string[] = []
  let currentY: number | null = null

  for (const item of sortedItems) {
    const y = item.transform[5]
    const text = item.str

    if (!text.trim()) continue

    if (currentY === null || Math.abs(y - currentY) < 5) {
      // Same line
      currentLine.push(text)
      currentY = y
    } else {
      // New line
      if (currentLine.length > 0) {
        lines.push(currentLine)
      }
      currentLine = [text]
      currentY = y
    }
  }

  // Add last line
  if (currentLine.length > 0) {
    lines.push(currentLine)
  }

  // Join lines with proper spacing
  return lines
    .map(line => line.join(' '))
    .join('\n')
    .trim()
}

/**
 * Extracts metadata from PDF document
 */
const extractMetadata = async (
  pdf: pdfjsLib.PDFDocumentProxy
): Promise<PDFMetadata> => {
  try {
    const metadata = await pdf.getMetadata()
    const info = metadata.info as Record<string, unknown>

    return {
      title: info.Title as string | undefined,
      author: info.Author as string | undefined,
      subject: info.Subject as string | undefined,
      keywords: info.Keywords as string | undefined,
      creator: info.Creator as string | undefined,
      producer: info.Producer as string | undefined,
      creationDate: info.CreationDate as string | undefined,
      modificationDate: info.ModDate as string | undefined
    }
  } catch {
    // Metadata extraction failed, return empty object
    return {}
  }
}

/**
 * Handles extraction errors and returns appropriate error result
 */
const handleExtractionError = (error: unknown, file?: File): PDFExtractionResult => {
  const errorMessage = error instanceof Error ? error.message : String(error)
  const errorName = error instanceof Error ? error.name : ''

  // Check for timeout errors
  if (errorMessage.includes('timeout') || errorMessage.includes('taking too long')) {
    const fileSize = file ? ` (${(file.size / (1024 * 1024)).toFixed(1)}MB)` : ''
    return {
      text: '',
      pageCount: 0,
      error: {
        type: 'TIMEOUT_ERROR',
        message: 'PDF extraction timed out. The file may be too large or complex to process.',
        details: `Processing exceeded the 2-minute timeout limit${fileSize}. Try a smaller or simpler PDF file.`
      }
    }
  }

  // Check for network/CDN errors
  if (
    errorMessage.includes('network') ||
    errorMessage.includes('fetch') ||
    errorMessage.includes('CDN') ||
    errorMessage.includes('Failed to load') ||
    errorName === 'NetworkError'
  ) {
    return {
      text: '',
      pageCount: 0,
      error: {
        type: 'NETWORK_ERROR',
        message: 'Network error while loading PDF processing resources.',
        details: 'Unable to load required PDF.js libraries from CDN. Please check your internet connection and try again.'
      }
    }
  }

  // Check for password-protected PDFs
  if (errorMessage.includes('password') || errorMessage.includes('encrypted')) {
    return {
      text: '',
      pageCount: 0,
      error: {
        type: 'PASSWORD_PROTECTED',
        message: 'This PDF is password-protected. Please provide an unprotected version.',
        details: 'The PDF file is encrypted and requires a password. Remove password protection before uploading.'
      }
    }
  }

  // Check for corrupted/invalid PDFs
  if (
    errorMessage.includes('Invalid PDF') ||
    errorMessage.includes('corrupted') ||
    errorMessage.includes('damaged') ||
    errorMessage.includes('not a PDF') ||
    errorMessage.includes('malformed')
  ) {
    return {
      text: '',
      pageCount: 0,
      error: {
        type: 'CORRUPTED_PDF',
        message: 'This PDF appears to be corrupted or invalid. Please try a different file.',
        details: errorMessage
      }
    }
  }

  // Check for memory errors (common with very large PDFs)
  if (
    errorMessage.includes('memory') ||
    errorMessage.includes('out of memory') ||
    errorName === 'RangeError'
  ) {
    const fileSize = file ? ` The file size is ${(file.size / (1024 * 1024)).toFixed(1)}MB.` : ''
    return {
      text: '',
      pageCount: 0,
      error: {
        type: 'EXTRACTION_FAILED',
        message: 'Failed to process PDF due to memory limitations.',
        details: `The PDF file is too large or complex for browser-based processing.${fileSize} Try a smaller file or one with fewer pages.`
      }
    }
  }

  // Generic extraction failure
  return {
    text: '',
    pageCount: 0,
    error: {
      type: 'EXTRACTION_FAILED',
      message: 'Failed to extract text from PDF.',
      details: errorMessage
    }
  }
}

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

    // Load PDF document
    const loadingTask = pdfjsLib.getDocument({
      data: typedArray,
      useSystemFonts: true,
      standardFontDataUrl: `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/standard_fonts/`
    })

    const pdf = await loadingTask.promise

    // Extract metadata if requested
    let metadata: PDFMetadata | undefined
    if (includeMetadata) {
      metadata = await extractMetadata(pdf)
    }

    // Extract text from all pages
    const pageTexts: PDFPageText[] = []
    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
      const page = await pdf.getPage(pageNum)
      const pageText = await extractPageText(page, preserveFormatting)
      pageTexts.push({
        pageNumber: pageNum,
        text: pageText
      })
    }

    // Combine all page texts
    const fullText = pageTexts
      .map(pt => pt.text)
      .join('\n\n--- Page Break ---\n\n')

    return {
      text: fullText,
      pageCount: pdf.numPages,
      metadata
    }
  } catch (error) {
    return handleExtractionError(error)
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
const handleExtractionError = (error: unknown): PDFExtractionResult => {
  const errorMessage = error instanceof Error ? error.message : String(error)

  // Check for specific error types
  if (errorMessage.includes('password')) {
    return {
      text: '',
      pageCount: 0,
      error: {
        type: 'PASSWORD_PROTECTED',
        message: 'This PDF is password-protected. Please provide an unprotected version.'
      }
    }
  }

  if (errorMessage.includes('Invalid PDF') || errorMessage.includes('corrupted')) {
    return {
      text: '',
      pageCount: 0,
      error: {
        type: 'CORRUPTED_PDF',
        message: 'This PDF appears to be corrupted or invalid. Please try a different file.'
      }
    }
  }

  // Generic extraction failure
  return {
    text: '',
    pageCount: 0,
    error: {
      type: 'EXTRACTION_FAILED',
      message: `Failed to extract text from PDF: ${errorMessage}`
    }
  }
}

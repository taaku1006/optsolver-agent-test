/**
 * PDF-related type definitions
 */

export interface PDFExtractionResult {
  text: string
  pageCount: number
  metadata?: PDFMetadata
  error?: PDFExtractionError
}

export interface PDFMetadata {
  title?: string
  author?: string
  subject?: string
  keywords?: string
  creator?: string
  producer?: string
  creationDate?: string
  modificationDate?: string
}

export interface PDFExtractionError {
  type: 'CORRUPTED_PDF' | 'PASSWORD_PROTECTED' | 'EXTRACTION_FAILED' | 'UNKNOWN_ERROR' | 'SCANNED_PDF' | 'NETWORK_ERROR' | 'TIMEOUT_ERROR'
  message: string
  details?: string
}

export interface PDFExtractionOptions {
  preserveFormatting?: boolean
  includeMetadata?: boolean
}

export interface PDFPageText {
  pageNumber: number
  text: string
}

/** Represents an academic paper submitted for review */
export interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  content: string;
  submittedAt: string;
  status: PaperStatus;
  metadata?: PaperMetadata;
}

export type PaperStatus =
  | "pending"
  | "analyzing"
  | "reviewed"
  | "error";

export interface PaperMetadata {
  venue?: string;
  year?: number;
  keywords?: string[];
  pageCount?: number;
  fileUrl?: string;
}

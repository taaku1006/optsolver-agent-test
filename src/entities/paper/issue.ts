/** Represents a specific issue found during paper analysis */
export interface Issue {
  id: string;
  category: IssueCategory;
  severity: IssueSeverity;
  title: string;
  description: string;
  location?: string;
  suggestion?: string;
}

export type IssueCategory =
  | "methodology"
  | "clarity"
  | "novelty"
  | "reproducibility"
  | "presentation"
  | "references"
  | "other";

export type IssueSeverity = "critical" | "major" | "minor" | "suggestion";

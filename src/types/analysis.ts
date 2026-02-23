import type { Issue } from "./issue";
import type { PaperScores } from "./scores";

/** Represents the AI-generated analysis of a paper */
export interface Analysis {
  id: string;
  paperId: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  issues: Issue[];
  scores: PaperScores;
  createdAt: string;
}

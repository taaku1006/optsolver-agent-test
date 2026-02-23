import type { Analysis } from "./analysis";
import type { Paper } from "./paper";

/** The complete review result combining paper data and analysis */
export interface ReviewResult {
  paper: Paper;
  analysis: Analysis;
  completedAt: string;
}

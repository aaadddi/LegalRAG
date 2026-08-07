export interface QuerySource {
  report_id: string | null;
  date: string | null;
  incident_type: string | null;
  excerpt: string;
}

export interface QueryResponse {
  answer: string;
  sources: QuerySource[];
  routing: {
    people_detected: string[];
    date_range_detected: [string | null, string | null];
    sql_prefiltered_report_ids: string[];
  };
}

export interface ReportSummary {
  report_id: string;
  date: string;
  location: string | null;
  incident_type: string | null;
  reporting_officer: string | null;
}

export interface ReportDetail extends ReportSummary {
  narrative: string;
  source_path: string;
  people_involved: string[];
}

export interface ReportCreateInput {
  report_id?: string;
  date: string;
  location?: string;
  incident_type?: string;
  reporting_officer?: string;
  people_involved?: string[];
  narrative: string;
}

export interface ReportUpdateInput {
  date: string;
  location?: string;
  incident_type?: string;
  reporting_officer?: string;
  people_involved?: string[];
  narrative: string;
}

export type ReportFormInput = ReportCreateInput | ReportUpdateInput;

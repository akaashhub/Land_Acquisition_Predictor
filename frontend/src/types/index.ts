export interface Project {
  project_id: string;
  project_name: string;
  project_type: string;
  state: string;
  district: string;
  latitude?: number;
  longitude?: number;
  current_stage: string;
  risk_score?: number;
  risk_category?: string;
  delay_probability?: number;
  estimated_delay_days?: number;
  bottleneck_stage?: string;
  [key: string]: any;
}

export interface Overview {
  total_projects: number;
  on_track: number;
  medium_risk: number;
  high_risk: number;
  critical_risk: number;
  average_predicted_delay: number;
  average_risk_score: number;
  delayed_count: number;
  disclaimer?: string;
}

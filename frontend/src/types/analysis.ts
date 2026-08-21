export type RiskLevel="LOW"|"MEDIUM"|"HIGH"|"CRITICAL"
export type JobStatus="queued"|"running"|"completed"|"failed"
export interface AnalysisJob{
id:string
repository_url:string
repository_name:string
base_ref:string
target_ref:string
commit_sha:string|null
status:JobStatus
progress:number
current_stage:string
overall_risk_score:number|null
overall_risk_level:RiskLevel|null
error_message:string|null
result:Record<string,unknown>|null
created_at:string
started_at:string|null
completed_at:string|null
}
export interface JobListResponse{
total:number
limit:number
offset:number
jobs:AnalysisJob[]
}
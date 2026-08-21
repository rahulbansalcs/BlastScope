import type {ReactNode} from "react"
import {useEffect,useMemo,useState} from "react"
import {Activity,AlertTriangle,ArrowRight,CheckCircle2,Clock3,GitPullRequest,LoaderCircle,ShieldAlert} from "lucide-react"
import {Link} from "react-router-dom"
import api from "../services/api"
import type {AnalysisJob,JobListResponse} from "../types/analysis"
function Dashboard(){
const [jobs,setJobs]=useState<AnalysisJob[]>([])
const [loading,setLoading]=useState(true)
const [error,setError]=useState("")
useEffect(()=>{
async function load(){
try{
const response=await api.get<JobListResponse>("/api/jobs",{params:{limit:20,offset:0}})
setJobs(response.data.jobs)
setError("")
}catch(error:any){
setError(error?.response?.data?.detail||"Unable to load dashboard data")
}finally{
setLoading(false)
}
}
load()
},[])
const completed=useMemo(()=>jobs.filter(job=>job.status==="completed"),[jobs])
const active=useMemo(()=>jobs.filter(job=>job.status==="running"||job.status==="queued"),[jobs])
const failed=useMemo(()=>jobs.filter(job=>job.status==="failed"),[jobs])
const averageRisk=useMemo(()=>{
const values=completed.map(job=>job.overall_risk_score).filter((value):value is number=>value!==null)
if(!values.length)return 0
return Math.round(values.reduce((sum,value)=>sum+value,0)/values.length)
},[completed])
const highestRisk=useMemo(()=>{
return completed.reduce<AnalysisJob|null>((highest,job)=>{
if(job.overall_risk_score===null)return highest
if(!highest||highest.overall_risk_score===null||job.overall_risk_score>highest.overall_risk_score)return job
return highest
},null)
},[completed])
return(
<div className="page">
<header className="page-header">
<div>
<p className="eyebrow">CHANGE INTELLIGENCE PLATFORM</p>
<h1>Understand the risk before you merge.</h1>
<p className="page-description">Monitor repository analyses, surface critical change risk and trace the blast radius before code reaches production.</p>
</div>
<Link to="/analysis/new" className="primary-button">Analyze repository<ArrowRight size={17}/></Link>
</header>
{loading?(
<div className="dashboard-loading">
<LoaderCircle className="spin" size={24}/>
<span>Loading BlastScope workspace</span>
</div>
):error?(
<div className="dashboard-error">
<AlertTriangle size={18}/>
<span>{error}</span>
</div>
):(
<>
<section className="dashboard-metrics">
<MetricCard label="Total analyses" value={jobs.length} icon={<Activity size={18}/>} caption="Recent repository scans"/>
<MetricCard label="Active jobs" value={active.length} icon={<Clock3 size={18}/>} caption="Queued or currently running"/>
<MetricCard label="Average risk" value={averageRisk} icon={<ShieldAlert size={18}/>} caption="Across completed analyses"/>
<MetricCard label="Failed jobs" value={failed.length} icon={<AlertTriangle size={18}/>} caption="Require investigation"/>
</section>
<section className="dashboard-main-grid">
<div className="dashboard-panel">
<div className="dashboard-panel-header">
<div>
<p className="eyebrow">RECENT ACTIVITY</p>
<h2>Latest analyses</h2>
</div>
<Link to="/history">View all<ArrowRight size={14}/></Link>
</div>
{jobs.length===0?(
<div className="dashboard-empty">
<GitPullRequest size={24}/>
<h3>No analyses yet</h3>
<p>Run your first repository analysis to populate the workspace.</p>
<Link to="/analysis/new" className="secondary-button">Start analysis</Link>
</div>
):(
<div className="dashboard-job-list">
{jobs.slice(0,6).map(job=>(
<Link to={`/analysis/${job.id}`} className="dashboard-job-row" key={job.id}>
<div className="dashboard-job-main">
<div className={`job-status-dot ${job.status}`}/>
<div>
<strong>{job.repository_name}</strong>
<span>{job.base_ref} → {job.target_ref}</span>
</div>
</div>
<div className="dashboard-job-status">
<span className={`history-status ${job.status}`}>{job.status}</span>
{job.overall_risk_score!==null&&(
<div className="dashboard-risk">
<strong>{job.overall_risk_score}</strong>
<span>{job.overall_risk_level}</span>
</div>
)}
<ArrowRight size={15}/>
</div>
</Link>
))}
</div>
)}
</div>
<div className="dashboard-side-stack">
<div className="dashboard-panel">
<div className="dashboard-panel-header compact">
<div>
<p className="eyebrow">RISK SNAPSHOT</p>
<h2>Highest observed risk</h2>
</div>
</div>
{highestRisk?(
<div className="highest-risk-card">
<div className="risk-orbit">
<strong>{highestRisk.overall_risk_score}</strong>
<span>/100</span>
</div>
<div>
<span className={`risk-level ${(highestRisk.overall_risk_level||"LOW").toLowerCase()}`}>{highestRisk.overall_risk_level}</span>
<h3>{highestRisk.repository_name}</h3>
<p>{highestRisk.base_ref} → {highestRisk.target_ref}</p>
<Link to={`/analysis/${highestRisk.id}`}>Open report<ArrowRight size={13}/></Link>
</div>
</div>
):(
<div className="dashboard-empty small">
<CheckCircle2 size={22}/>
<p>No completed risk assessments yet.</p>
</div>
)}
</div>
<div className="dashboard-panel">
<div className="dashboard-panel-header compact">
<div>
<p className="eyebrow">WORKSPACE HEALTH</p>
<h2>Current status</h2>
</div>
</div>
<div className="workspace-health-row">
<span>Completed</span>
<strong>{completed.length}</strong>
</div>
<div className="workspace-health-row">
<span>Running</span>
<strong>{active.length}</strong>
</div>
<div className="workspace-health-row">
<span>Failed</span>
<strong>{failed.length}</strong>
</div>
<div className="workspace-health-row">
<span>Total tracked</span>
<strong>{jobs.length}</strong>
</div>
</div>
</div>
</section>
</>
)}
</div>
)
}
function MetricCard({label,value,icon,caption}:{label:string,value:number,icon:ReactNode,caption:string}){
return(
<div className="dashboard-metric-card">
<div className="metric-top">
<span>{label}</span>
<div className="metric-icon">{icon}</div>
</div>
<strong>{value}</strong>
<p>{caption}</p>
</div>
)
}
export default Dashboard
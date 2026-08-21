import {useEffect,useState} from "react"
import {AlertCircle,ArrowRight,Clock3,LoaderCircle,RefreshCw,Search} from "lucide-react"
import {Link} from "react-router-dom"
import api from "../services/api"
import type {AnalysisJob,JobListResponse} from "../types/analysis"
function History(){
const [jobs,setJobs]=useState<AnalysisJob[]>([])
const [loading,setLoading]=useState(true)
const [error,setError]=useState("")
const [search,setSearch]=useState("")
const [status,setStatus]=useState("all")
async function fetchJobs(){
try{
setLoading(true)
const params:Record<string,string|number>={limit:100,offset:0}
if(status!=="all")params.status=status
const response=await api.get<JobListResponse>("/api/jobs",{params})
setJobs(response.data.jobs)
setError("")
}catch(error:any){
setError(error?.response?.data?.detail||"Unable to load analysis history")
}finally{
setLoading(false)
}
}
useEffect(()=>{
fetchJobs()
},[status])
const filteredJobs=jobs.filter(job=>{
const query=search.trim().toLowerCase()
if(!query)return true
return job.repository_name.toLowerCase().includes(query)||job.repository_url.toLowerCase().includes(query)||job.base_ref.toLowerCase().includes(query)||job.target_ref.toLowerCase().includes(query)
})
return(
<div className="page">
<header className="page-header history-header">
<div>
<p className="eyebrow">ANALYSIS HISTORY</p>
<h1>Repository analyses</h1>
<p className="page-description">Review completed scans, monitor active jobs and reopen previous BlastScope reports.</p>
</div>
<Link to="/analysis/new" className="primary-button">New analysis<ArrowRight size={17}/></Link>
</header>
<section className="history-toolbar">
<div className="history-search">
<Search size={16}/>
<input value={search} onChange={event=>setSearch(event.target.value)} placeholder="Search repositories or refs"/>
</div>
<div className="history-filters">
{["all","queued","running","completed","failed"].map(item=>(
<button key={item} onClick={()=>setStatus(item)} className={status===item?"filter-button active":"filter-button"}>{item}</button>
))}
</div>
<button onClick={fetchJobs} className="history-refresh"><RefreshCw size={15}/></button>
</section>
{loading?(
<div className="history-state">
<LoaderCircle className="spin" size={24}/>
<p>Loading analysis history</p>
</div>
):error?(
<div className="history-state error">
<AlertCircle size={24}/>
<p>{error}</p>
<button onClick={fetchJobs} className="secondary-button">Retry</button>
</div>
):filteredJobs.length===0?(
<div className="history-state">
<Clock3 size={24}/>
<h3>No analyses found</h3>
<p>Run a repository analysis to start building your BlastScope history.</p>
<Link to="/analysis/new" className="secondary-button">Start analysis</Link>
</div>
):(
<section className="history-table-card">
<div className="history-table-header">
<span>Repository</span>
<span>Comparison</span>
<span>Status</span>
<span>Risk</span>
<span>Created</span>
<span/>
</div>
{filteredJobs.map(job=>(
<HistoryRow key={job.id} job={job}/>
))}
</section>
)}
</div>
)
}
function HistoryRow({job}:{job:AnalysisJob}){
return(
<div className="history-row">
<div className="history-repository">
<strong>{job.repository_name}</strong>
<span>{job.repository_url}</span>
</div>
<div className="history-comparison">
<strong>{job.base_ref}</strong>
<span>→</span>
<strong>{job.target_ref}</strong>
</div>
<div>
<span className={`history-status ${job.status}`}>{job.status}</span>
</div>
<div className="history-risk">
{job.overall_risk_score!==null?(
<>
<strong>{job.overall_risk_score}</strong>
<span className={`risk-text ${(job.overall_risk_level||"LOW").toLowerCase()}`}>{job.overall_risk_level}</span>
</>
):<span className="history-muted">Pending</span>}
</div>
<div className="history-date">{formatDate(job.created_at)}</div>
<Link to={`/analysis/${job.id}`} className="history-open"><ArrowRight size={16}/></Link>
</div>
)
}
function formatDate(value:string){
const date=new Date(value)
return date.toLocaleString(undefined,{
month:"short",
day:"numeric",
year:"numeric",
hour:"2-digit",
minute:"2-digit"
})
}
export default History
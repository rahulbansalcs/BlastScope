import {useState} from "react"
import type {FormEvent} from "react"
import {ArrowRight,GitBranch,GitFork,LoaderCircle,ScanSearch} from "lucide-react"
import {useNavigate} from "react-router-dom"
import api from "../services/api"
import type {AnalysisJob} from "../types/analysis"
function NewAnalysis(){
const navigate=useNavigate()
const [repositoryUrl,setRepositoryUrl]=useState("")
const [baseRef,setBaseRef]=useState("main")
const [targetRef,setTargetRef]=useState("HEAD")
const [loading,setLoading]=useState(false)
const [error,setError]=useState("")
async function handleSubmit(event:FormEvent<HTMLFormElement>){
event.preventDefault()
setError("")
if(!repositoryUrl.trim()){
setError("Enter a repository URL")
return
}
try{
setLoading(true)
const response=await api.post<AnalysisJob>("/api/jobs",{
repository_url:repositoryUrl.trim(),
base_ref:baseRef.trim()||"main",
target_ref:targetRef.trim()||"HEAD"
})
navigate(`/analysis/${response.data.id}`)
}catch(error:any){
setError(error?.response?.data?.detail||"Unable to start repository analysis")
}finally{
setLoading(false)
}
}
return(
<div className="page new-analysis-page">
<header className="page-header">
<div>
<p className="eyebrow">NEW REPOSITORY ANALYSIS</p>
<h1>Analyze a code change before it reaches production.</h1>
<p className="page-description">Provide a public Git repository and the refs you want BlastScope to compare. The analysis engine will clone the repository temporarily and calculate its change risk.</p>
</div>
</header>
<div className="analysis-layout">
<section className="analysis-form-card">
<div className="section-heading">
<div className="section-icon"><ScanSearch size={19}/></div>
<div>
<h2>Repository configuration</h2>
<p>Choose the repository and Git comparison.</p>
</div>
</div>
<form onSubmit={handleSubmit}>
<div className="form-group">
<label htmlFor="repositoryUrl">Repository URL</label>
<div className="input-shell">
<GitFork size={17}/>
<input id="repositoryUrl" type="url" value={repositoryUrl} onChange={event=>setRepositoryUrl(event.target.value)} placeholder="https://github.com/owner/repository.git" autoComplete="off"/>
</div>
<span className="input-help">Public HTTPS repositories are supported in the current version.</span>
</div>
<div className="ref-grid">
<div className="form-group">
<label htmlFor="baseRef">Base ref</label>
<div className="input-shell">
<GitBranch size={16}/>
<input id="baseRef" value={baseRef} onChange={event=>setBaseRef(event.target.value)} placeholder="main"/>
</div>
</div>
<div className="form-group">
<label htmlFor="targetRef">Target ref</label>
<div className="input-shell">
<GitBranch size={16}/>
<input id="targetRef" value={targetRef} onChange={event=>setTargetRef(event.target.value)} placeholder="HEAD"/>
</div>
</div>
</div>
{error&&<div className="form-error">{error}</div>}
<button className="analysis-submit" type="submit" disabled={loading}>
{loading?<><LoaderCircle className="spin" size={17}/>Starting analysis</>:<>Run BlastScope analysis<ArrowRight size={17}/></>}
</button>
</form>
</section>
<aside className="analysis-info-card">
<p className="eyebrow">WHAT BLASTSCOPE CHECKS</p>
<h3>One analysis, multiple risk signals.</h3>
<div className="analysis-check">
<span>01</span>
<div>
<strong>Dependency blast radius</strong>
<p>Find direct and transitive callers affected by code changes.</p>
</div>
</div>
<div className="analysis-check">
<span>02</span>
<div>
<strong>Breaking changes</strong>
<p>Detect incompatible signatures, removals and unsafe renames.</p>
</div>
</div>
<div className="analysis-check">
<span>03</span>
<div>
<strong>Public API exposure</strong>
<p>Trace internal changes to FastAPI and Flask endpoints.</p>
</div>
</div>
<div className="analysis-check">
<span>04</span>
<div>
<strong>Architecture and test risk</strong>
<p>Surface cycles, violations, test gaps and historical instability.</p>
</div>
</div>
</aside>
</div>
</div>
)
}
export default NewAnalysis
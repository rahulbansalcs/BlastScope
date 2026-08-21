import {useEffect,useMemo,useState} from "react"
import type {ReactNode} from "react"
import {AlertTriangle,CheckCircle2,Clock3,LoaderCircle,RefreshCw,XCircle} from "lucide-react"
import {useParams} from "react-router-dom"
import api from "../services/api"
import DependencyGraph from "../components/DependencyGraph"
import type {AnalysisJob} from "../types/analysis"
type ReportTab="overview"|"graph"|"breaking"|"critical"|"architecture"|"tests"|"git"
function AnalysisDetail(){
const {id}=useParams()
const [job,setJob]=useState<AnalysisJob|null>(null)
const [loading,setLoading]=useState(true)
const [error,setError]=useState("")
const [activeTab,setActiveTab]=useState<ReportTab>("overview")
const [graphData,setGraphData]=useState<{nodes:any[];edges:any[]}|null>(null)
const [graphLoading,setGraphLoading]=useState(false)
const [graphError,setGraphError]=useState("")
const [graphTarget,setGraphTarget]=useState<string|null>(null)
async function fetchJob(){
if(!id)return
try{
const response=await api.get<AnalysisJob>(`/api/jobs/${id}`)
setJob(response.data)
setError("")
}catch(error:any){
setError(error?.response?.data?.detail||"Unable to load analysis")
}finally{
setLoading(false)
}
}
function loadGraph(){
if(!job?.result)return
const result=job.result as any
const graph=result?.dependency_graph
if(!graph){
setGraphError("Dependency graph data is unavailable")
return
}
setGraphLoading(true)
setGraphError("")
setGraphData(graph)
setGraphLoading(false)
}
function viewBlastRadius(symbol:string){
setGraphTarget(symbol)
if(!graphData){
loadGraph()
}
setActiveTab("graph")
}
function viewBreakingChangeImpact(symbol:string){
    setGraphTarget(symbol)
    if(!graphData){
    loadGraph()
    }
    setActiveTab("graph")
    }
useEffect(()=>{
fetchJob()
},[id])
useEffect(()=>{
if(!job)return
if(job.status==="completed"||job.status==="failed")return
const interval=setInterval(()=>{
fetchJob()
},2000)
return()=>clearInterval(interval)
},[job?.status,id])
useEffect(()=>{
if(activeTab==="graph"&&job?.status==="completed"&&!graphData&&!graphLoading){
loadGraph()
}
},[activeTab,job?.status])
const result=useMemo(()=>{
return job?.result as any
},[job])
if(loading){
return(
<div className="page analysis-status-page">
<div className="loading-state">
<LoaderCircle className="spin" size={26}/>
<h2>Loading analysis</h2>
<p>Retrieving repository analysis status.</p>
</div>
</div>
)
}
if(error){
return(
<div className="page analysis-status-page">
<div className="error-state">
<XCircle size={28}/>
<h2>Unable to load analysis</h2>
<p>{error}</p>
<button onClick={fetchJob} className="secondary-button"><RefreshCw size={16}/>Retry</button>
</div>
</div>
)
}
if(!job)return null
const completed=job.status==="completed"
const failed=job.status==="failed"
const running=job.status==="running"||job.status==="queued"
return(
<div className="page">
<header className="analysis-detail-header">
<div>
<p className="eyebrow">ANALYSIS REPORT</p>
<h1>{job.repository_name}</h1>
<p className="page-description">{job.base_ref} → {job.target_ref}</p>
</div>
<div className={`status-badge ${job.status}`}>
{completed&&<CheckCircle2 size={15}/>}
{failed&&<XCircle size={15}/>}
{running&&<Clock3 size={15}/>}
<span>{job.status.toUpperCase()}</span>
</div>
</header>
<section className="analysis-progress-card">
<div className="progress-header">
<div>
<span className="progress-label">CURRENT STAGE</span>
<h2>{formatStage(job.current_stage)}</h2>
</div>
<span className="progress-number">{job.progress}%</span>
</div>
<div className="progress-track">
<div className="progress-fill" style={{width:`${job.progress}%`}}/>
</div>
<div className="analysis-stage-grid">
<Stage label="Queued" active={job.progress>=0}/>
<Stage label="Cloning" active={job.progress>=10}/>
<Stage label="Analyzing" active={job.progress>=30}/>
<Stage label="Finalizing" active={job.progress>=85}/>
<Stage label="Completed" active={job.progress>=100}/>
</div>
</section>
{failed&&(
<section className="analysis-error-panel">
<AlertTriangle size={19}/>
<div>
<strong>Analysis failed</strong>
<p>{job.error_message||"An unexpected error occurred during repository analysis."}</p>
</div>
</section>
)}
{completed&&(
<>
<section className="summary-grid">
<SummaryCard label="OVERALL RISK" value={job.overall_risk_score??0} caption={job.overall_risk_level||"LOW"}/>
<SummaryCard label="CHANGED FILES" value={result?.summary?.changed_files??0} caption="Files in comparison"/>
<SummaryCard label="BREAKING CHANGES" value={result?.summary?.breaking_changes??0} caption="Compatibility issues"/>
<SummaryCard label="ARCHITECTURE" value={result?.summary?.architecture_violations??0} caption="Detected violations"/>
</section>
<nav className="report-tabs">
<TabButton label="Overview" active={activeTab==="overview"} onClick={()=>setActiveTab("overview")}/>
<TabButton label="Dependency Graph" active={activeTab==="graph"} onClick={()=>setActiveTab("graph")}/>
<TabButton label="Breaking Changes" active={activeTab==="breaking"} onClick={()=>setActiveTab("breaking")} count={result?.breaking_changes?.length??0}/>
<TabButton label="Critical Components" active={activeTab==="critical"} onClick={()=>setActiveTab("critical")} count={result?.critical_components?.length??0}/>
<TabButton label="Architecture" active={activeTab==="architecture"} onClick={()=>setActiveTab("architecture")} count={result?.architecture_violations?.length??0}/>
<TabButton label="Test Risk" active={activeTab==="tests"} onClick={()=>setActiveTab("tests")}/>
<TabButton label="Git Risk" active={activeTab==="git"} onClick={()=>setActiveTab("git")}/>
</nav>
<section className="report-tab-content">
{activeTab==="overview"&&<OverviewTab result={result}/>}
{activeTab==="graph"&&(
<>
{graphLoading&&(
<div className="history-state">
<LoaderCircle className="spin" size={24}/>
<p>Building dependency graph</p>
</div>
)}
{graphError&&(
<div className="history-state error">
<AlertTriangle size={24}/>
<p>{graphError}</p>
<button className="secondary-button" onClick={loadGraph}>Retry</button>
</div>
)}
{graphData&&!graphLoading&&!graphError&&(
<DependencyGraph nodes={graphData.nodes} edges={graphData.edges} initialTarget={graphTarget||result?.critical_components?.[0]?.name} maxDepth={5}/>
)}
</>
)}
{activeTab==="breaking"&&<BreakingTab result={result} onViewImpact={viewBreakingChangeImpact}/>}
{activeTab==="critical"&&<CriticalTab result={result} onViewBlastRadius={viewBlastRadius}/>}
{activeTab==="architecture"&&<ArchitectureTab result={result}/>}
{activeTab==="tests"&&<TestsTab result={result}/>}
{activeTab==="git"&&<GitTab result={result}/>}
</section>
</>
)}
</div>
)
}
function SummaryCard({label,value,caption}:{label:string,value:number,caption:string}){
return(
<div className="summary-card">
<span className="summary-label">{label}</span>
<strong className="summary-value">{value}</strong>
<span className="summary-caption">{caption}</span>
</div>
)
}
function TabButton({label,active,onClick,count}:{label:string,active:boolean,onClick:()=>void,count?:number}){
return(
<button className={active?"report-tab active":"report-tab"} onClick={onClick}>
<span>{label}</span>
{typeof count==="number"&&<strong>{count}</strong>}
</button>
)
}
function OverviewTab({result}:{result:any}){
return(
<div className="report-grid">
<ReportCard title="Repository summary">
<InfoRow label="Files" value={result?.summary?.repository?.total_files??0}/>
<InfoRow label="Python files" value={result?.summary?.repository?.python_files??0}/>
<InfoRow label="Symbols" value={result?.summary?.repository?.symbols??0}/>
<InfoRow label="Graph nodes" value={result?.summary?.repository?.graph_nodes??0}/>
<InfoRow label="Graph edges" value={result?.summary?.repository?.graph_edges??0}/>
<InfoRow label="API routes" value={result?.summary?.repository?.api_routes??0}/>
</ReportCard>
<ReportCard title="Risk signals">
<InfoRow label="Dependency cycles" value={result?.summary?.dependency_cycles??0}/>
<InfoRow label="Dead code candidates" value={result?.summary?.dead_code_candidates??0}/>
<InfoRow label="Renamed/deleted symbols" value={result?.summary?.renamed_or_deleted_symbols??0}/>
<InfoRow label="Architecture violations" value={result?.summary?.architecture_violations??0}/>
</ReportCard>
</div>
)
}
function BreakingTab({result,onViewImpact}:{result:any,onViewImpact:(symbol:string)=>void}){
    const items=result?.breaking_changes??[]
    if(!items.length)return <EmptyState text="No breaking changes detected"/>
    return(
    <div className="report-list">
    {items.map((item:any,index:number)=>(
    <div className="detail-card" key={`${item.symbol}-${index}`}>
    <div className="detail-card-top">
    <div>
    <span className="detail-label">BREAKING CHANGE</span>
    <h3>{item.symbol}</h3>
    </div>
    <div className="danger-chip">{item.change_type}</div>
    </div>
    <div className="detail-meta">
    <span>Runtime failures: {item.potential_runtime_failures}</span>
    <span>Affected callers: {item.affected_callers?.length??0}</span>
    </div>
    {item.reasons?.length>0&&(
    <div className="reason-list">
    {item.reasons.map((reason:string,reasonIndex:number)=>(
    <p key={reasonIndex}>- {reason}</p>
    ))}
    </div>
    )}
    {item.affected_callers?.length>0&&(
    <div className="affected-callers">
    <span className="affected-callers-title">AFFECTED CALLERS</span>
    <div className="affected-callers-list">
    {item.affected_callers.map((caller:string,callerIndex:number)=>(
    <button type="button" key={`${caller}-${callerIndex}`} onClick={()=>onViewImpact(caller)}>
    <span>{caller}</span>
    <span>View →</span>
    </button>
    ))}
    </div>
    </div>
    )}
    <div className="breaking-actions">
    <button type="button" className="blast-radius-button" onClick={()=>onViewImpact(item.symbol)}>View breaking change impact</button>
    </div>
    </div>
    ))}
    </div>
    )
    }
function CriticalTab({result,onViewBlastRadius}:{result:any,onViewBlastRadius:(symbol:string)=>void}){
const items=result?.critical_components??[]
if(!items.length)return <EmptyState text="No critical components detected"/>
return(
<div className="report-list">
{items.map((item:any,index:number)=>(
<div className="detail-card" key={`${item.name}-${index}`}>
<div className="detail-card-top">
<div>
<span className="detail-label">{item.node_type}</span>
<h3>{item.name}</h3>
</div>
<div className="score-chip">{item.criticality_score}/100</div>
</div>
<div className="detail-meta">
<span>Direct dependents: {item.direct_dependents}</span>
<span>Transitive dependents: {item.transitive_dependents}</span>
<span>API endpoints: {item.api_endpoints}</span>
<span>Depth: {item.dependency_depth}</span>
</div>
<div className="critical-actions">
<button type="button" className="blast-radius-button" onClick={()=>onViewBlastRadius(item.name)}>View blast radius</button>
</div>
</div>
))}
</div>
)
}
function ArchitectureTab({result}:{result:any}){
const violations=result?.architecture_violations??[]
const cycles=result?.cycles??[]
return(
<div className="report-grid">
<ReportCard title={`Architecture violations (${violations.length})`}>
{violations.length?violations.map((item:any,index:number)=>(
<div className="architecture-row" key={`${item.source}-${index}`}>
<strong>{item.source}</strong>
<span>{item.source_layer} → {item.target_layer}</span>
<p>{item.reason}</p>
</div>
)):<EmptyState text="No architecture violations detected"/>}
</ReportCard>
<ReportCard title={`Dependency cycles (${cycles.length})`}>
{cycles.length?cycles.map((item:any,index:number)=>(
<div className="architecture-row" key={index}>
<strong>Cycle #{index+1}</strong>
<span>{item.size} nodes</span>
<p>{item.nodes?.join(" → ")}</p>
</div>
)):<EmptyState text="No circular dependencies detected"/>}
</ReportCard>
</div>
)
}
function TestsTab({result}:{result:any}){
const deadCode=result?.dead_code??[]
return(
<div className="report-grid">
<ReportCard title="Potential untested or orphaned code">
{deadCode.length?deadCode.slice(0,20).map((item:any,index:number)=>(
<div className="architecture-row" key={`${item.name}-${index}`}>
<strong>{item.name}</strong>
<span>{item.confidence} confidence</span>
<p>{item.reasons?.join(" · ")}</p>
</div>
)):<EmptyState text="No dead-code candidates detected"/>}
</ReportCard>
<ReportCard title="Test intelligence">
<p className="report-copy">Detailed regression-test recommendations are calculated during symbol-level impact analysis. This repository report currently surfaces structural test-risk indicators and orphan candidates.</p>
</ReportCard>
</div>
)
}
function GitTab({result}:{result:any}){
const severity=result?.file_severity??[]
const changes=result?.symbol_changes??[]
return(
<div className="report-grid">
<ReportCard title="Change severity">
{severity.length?severity.map((item:any,index:number)=>(
<div className="architecture-row" key={`${item.file_path}-${index}`}>
<strong>{item.file_path}</strong>
<span>{item.severity_level} · {item.severity_score}/100</span>
<p>+{item.additions} / -{item.deletions} · {item.change_ratio}% changed</p>
</div>
)):<EmptyState text="No file severity data available"/>}
</ReportCard>
<ReportCard title="Symbol changes">
{changes.length?changes.slice(0,20).map((item:any,index:number)=>(
<div className="architecture-row" key={index}>
<strong>{item.old_symbol||item.new_symbol}</strong>
<span>{item.change_type} · {item.breaking?"breaking":"non-breaking"}</span>
<p>Confidence: {item.confidence}%</p>
</div>
)):<EmptyState text="No symbol changes detected"/>}
</ReportCard>
</div>
)
}
function ReportCard({title,children}:{title:string,children:ReactNode}){
return(
<div className="report-card">
<div className="report-heading">
<h3>{title}</h3>
</div>
{children}
</div>
)
}
function InfoRow({label,value}:{label:string,value:string|number}){
return(
<div className="workspace-health-row">
<span>{label}</span>
<strong>{value}</strong>
</div>
)
}
function Stage({label,active}:{label:string,active:boolean}){
return(
<div className={active?"stage-item active":"stage-item"}>
<div className="stage-dot"/>
<span>{label}</span>
</div>
)
}
function EmptyState({text}:{text:string}){
return <div className="report-empty">{text}</div>
}
function formatStage(stage:string){
return stage.split("_").map(word=>word.charAt(0).toUpperCase()+word.slice(1)).join(" ")
}
export default AnalysisDetail
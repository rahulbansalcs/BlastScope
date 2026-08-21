import {useCallback,useEffect,useMemo,useState} from "react"
import {Background,Controls,Handle,MiniMap,Position,ReactFlow,useEdgesState,useNodesState,type Edge,type Node,type NodeProps} from "@xyflow/react"
import {ChevronDown,Network,Search,Target} from "lucide-react"
import "@xyflow/react/dist/style.css"
type GraphNode={
id:string
name:string
node_type:string
file_path:string
direct_dependents:number
direct_dependencies:number
is_target?:boolean|null
}
type GraphEdge={
id:string
source:string
target:string
edge_type:string
}
type BlastNodeData={
name:string
nodeType:string
filePath:string
directDependents:number
directDependencies:number
isTarget:boolean
depth:number
}
type DependencyGraphProps={
nodes:GraphNode[]
edges:GraphEdge[]
initialTarget?:string
maxDepth?:number
}
const nodeTypes={
blastNode:BlastNode
}
function DependencyGraph({nodes,edges,initialTarget,maxDepth=5}:DependencyGraphProps){
const [targetId,setTargetId]=useState("")
const [selected,setSelected]=useState<BlastNodeData|null>(null)
const [search,setSearch]=useState("")
const [depth,setDepth]=useState(maxDepth)
const [showCalls,setShowCalls]=useState(true)
const [showImports,setShowImports]=useState(true)
const [showFunctions,setShowFunctions]=useState(true)
const [showMethods,setShowMethods]=useState(true)
const [showClasses,setShowClasses]=useState(true)
const [showEndpoints,setShowEndpoints]=useState(true)
useEffect(()=>{
if(!nodes.length)return
if(initialTarget){
const exact=nodes.find(node=>node.id===initialTarget||node.name===initialTarget)
if(exact){
setTargetId(exact.id)
return
}
}
const best=[...nodes].sort((a,b)=>b.direct_dependents-a.direct_dependents)[0]
setTargetId(best?.id||nodes[0].id)
},[nodes,initialTarget])
const filteredGraph=useMemo(()=>{
const allowedNodeTypes=new Set<string>()
if(showFunctions)allowedNodeTypes.add("function")
if(showMethods)allowedNodeTypes.add("method")
if(showClasses)allowedNodeTypes.add("class")
if(showEndpoints)allowedNodeTypes.add("api_endpoint")
const visibleNodes=nodes.filter(node=>node.id===targetId||allowedNodeTypes.has(node.node_type)||!["function","method","class","api_endpoint"].includes(node.node_type))
const visibleIds=new Set(visibleNodes.map(node=>node.id))
const visibleEdges=edges.filter(edge=>{
if(!visibleIds.has(edge.source)||!visibleIds.has(edge.target))return false
if(edge.edge_type==="calls"&&!showCalls)return false
if(edge.edge_type==="imports"&&!showImports)return false
return true
})
return{
nodes:visibleNodes,
edges:visibleEdges
}
},[nodes,edges,targetId,showCalls,showImports,showFunctions,showMethods,showClasses,showEndpoints])
const blastRadius=useMemo(()=>{
return calculateBlastRadius(filteredGraph.nodes,filteredGraph.edges,targetId,depth)
},[filteredGraph,targetId,depth])
const initialNodes=useMemo<Node<BlastNodeData>[]>(()=>{
return buildFlowNodes(blastRadius.nodes,blastRadius.depths,targetId)
},[blastRadius,targetId])
const initialEdges=useMemo<Edge[]>(()=>{
return blastRadius.edges.map(item=>({
id:item.id,
source:item.source,
target:item.target,
label:item.edge_type,
animated:item.edge_type==="calls",
type:"smoothstep"
}))
},[blastRadius])
const [flowNodes,setFlowNodes,onNodesChange]=useNodesState(initialNodes)
const [flowEdges,setFlowEdges,onEdgesChange]=useEdgesState(initialEdges)
useEffect(()=>{
setFlowNodes(initialNodes)
setFlowEdges(initialEdges)
},[initialNodes,initialEdges,setFlowNodes,setFlowEdges])
const filteredSymbols=useMemo(()=>{
const query=search.trim().toLowerCase()
return nodes.filter(node=>{
if(!["function","method","class","api_endpoint"].includes(node.node_type))return false
if(!query)return true
return node.name.toLowerCase().includes(query)||node.file_path.toLowerCase().includes(query)
}).sort((a,b)=>b.direct_dependents-a.direct_dependents).slice(0,50)
},[nodes,search])
const targetNode=nodes.find(node=>node.id===targetId)
const handleNodeClick=useCallback((_:React.MouseEvent,node:Node<BlastNodeData>)=>{
setSelected(node.data)
setTargetId(node.id)
},[])
function selectTarget(nodeId:string){
setTargetId(nodeId)
setSelected(null)
}
return(
<div className="blast-graph-wrapper">
<div className="graph-toolbar">
<div className="graph-toolbar-main">
<div className="graph-symbol-search">
<Search size={15}/>
<input value={search} onChange={event=>setSearch(event.target.value)} placeholder="Search symbol"/>
<div className="graph-symbol-results">
{search&&filteredSymbols.map(node=>(
<button type="button" key={node.id} onClick={()=>{selectTarget(node.id);setSearch("")}}>
<div>
<strong>{shortenName(node.name)}</strong>
<span>{node.node_type}</span>
</div>
<span>{node.direct_dependents}</span>
</button>
))}
</div>
</div>
<div className="graph-depth-control">
<ChevronDown size={14}/>
<select value={depth} onChange={event=>setDepth(Number(event.target.value))}>
<option value={1}>Depth 1</option>
<option value={2}>Depth 2</option>
<option value={3}>Depth 3</option>
<option value={4}>Depth 4</option>
<option value={5}>Depth 5</option>
<option value={6}>Depth 6</option>
<option value={7}>Depth 7</option>
<option value={8}>Depth 8</option>
</select>
</div>
<div className="graph-filter-controls">
<FilterButton label="Calls" active={showCalls} onClick={()=>setShowCalls(value=>!value)}/>
<FilterButton label="Imports" active={showImports} onClick={()=>setShowImports(value=>!value)}/>
<FilterButton label="Functions" active={showFunctions} onClick={()=>setShowFunctions(value=>!value)}/>
<FilterButton label="Methods" active={showMethods} onClick={()=>setShowMethods(value=>!value)}/>
<FilterButton label="Classes" active={showClasses} onClick={()=>setShowClasses(value=>!value)}/>
<FilterButton label="API" active={showEndpoints} onClick={()=>setShowEndpoints(value=>!value)}/>
</div>
</div>
<div className="graph-target-summary">
<Target size={15}/>
<div>
<span>CURRENT TARGET</span>
<strong>{targetNode?shortenName(targetNode.name):"No target selected"}</strong>
</div>
<div className="graph-count">
<strong>{blastRadius.nodes.length}</strong>
<span>nodes</span>
</div>
</div>
</div>
<div className="dependency-graph-shell">
<div className="dependency-graph-canvas">
{blastRadius.nodes.length>0?(
<ReactFlow nodes={flowNodes} edges={flowEdges} nodeTypes={nodeTypes} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onNodeClick={handleNodeClick} fitView fitViewOptions={{padding:.25}} minZoom={0.2} maxZoom={1.8}>
<Background gap={22} size={1}/>
<MiniMap zoomable pannable/>
<Controls/>
</ReactFlow>
):(
<div className="graph-empty">
<Network size={26}/>
<h3>No downstream dependencies</h3>
<p>This symbol currently has no detected blast radius.</p>
</div>
)}
</div>
<aside className="dependency-inspector">
<p className="eyebrow">NODE INSPECTOR</p>
{selected?(
<>
<h3>{selected.name}</h3>
<span className="node-type-pill">{selected.nodeType}</span>
<div className="inspector-block">
<span>Blast radius depth</span>
<strong>{selected.depth===0?"Target":selected.depth}</strong>
</div>
<div className="inspector-block">
<span>File</span>
<strong>{selected.filePath||"Unknown"}</strong>
</div>
<div className="inspector-grid">
<div>
<span>Dependents</span>
<strong>{selected.directDependents}</strong>
</div>
<div>
<span>Dependencies</span>
<strong>{selected.directDependencies}</strong>
</div>
</div>
{selected.isTarget?(
<div className="target-indicator">Current blast-radius target</div>
):(
<button className="inspect-target-button" type="button" onClick={()=>selectTarget(flowNodes.find(node=>node.data===selected)?.id||targetId)}>
<Target size={13}/>
Analyze this symbol
</button>
)}
</>
):(
<>
<div className="inspector-empty">
<p>Click any visible node to make it the new blast-radius target.</p>
</div>
<div className="blast-radius-stats">
<div>
<span>Visible nodes</span>
<strong>{blastRadius.nodes.length}</strong>
</div>
<div>
<span>Relationships</span>
<strong>{blastRadius.edges.length}</strong>
</div>
<div>
<span>Maximum depth</span>
<strong>{blastRadius.maximumDepth}</strong>
</div>
</div>
</>
)}
</aside>
</div>
</div>
)
}
function FilterButton({label,active,onClick}:{label:string,active:boolean,onClick:()=>void}){
return(
<button type="button" className={active?"graph-filter active":"graph-filter"} onClick={onClick}>
{label}
</button>
)
}
function calculateBlastRadius(nodes:GraphNode[],edges:GraphEdge[],targetId:string,maxDepth:number){
if(!targetId)return{nodes:[],edges:[],depths:new Map<string,number>(),maximumDepth:0}
const nodeMap=new Map(nodes.map(node=>[node.id,node]))
if(!nodeMap.has(targetId))return{nodes:[],edges:[],depths:new Map<string,number>(),maximumDepth:0}
const incoming=new Map<string,GraphEdge[]>()
for(const edge of edges){
if(!incoming.has(edge.target))incoming.set(edge.target,[])
incoming.get(edge.target)!.push(edge)
}
const included=new Set<string>([targetId])
const depths=new Map<string,number>([[targetId,0]])
const queue:[string,number][]=[[targetId,0]]
let maximumDepth=0
while(queue.length){
const [current,currentDepth]=queue.shift()!
if(currentDepth>=maxDepth)continue
for(const edge of incoming.get(current)??[]){
const dependentId=edge.source
const nextDepth=currentDepth+1
if(depths.has(dependentId)&&depths.get(dependentId)!<=nextDepth)continue
included.add(dependentId)
depths.set(dependentId,nextDepth)
maximumDepth=Math.max(maximumDepth,nextDepth)
queue.push([dependentId,nextDepth])
}
}
const blastNodes=nodes.filter(node=>included.has(node.id))
const blastEdges=edges.filter(edge=>included.has(edge.source)&&included.has(edge.target))
return{
nodes:blastNodes,
edges:blastEdges,
depths,
maximumDepth
}
}
function buildFlowNodes(nodes:GraphNode[],depths:Map<string,number>,targetId:string):Node<BlastNodeData>[]{
const grouped=new Map<number,GraphNode[]>()
for(const node of nodes){
const depth=depths.get(node.id)??0
if(!grouped.has(depth))grouped.set(depth,[])
grouped.get(depth)!.push(node)
}
const result:Node<BlastNodeData>[]=[]
const sortedDepths=Array.from(grouped.keys()).sort((a,b)=>a-b)
for(const depth of sortedDepths){
const levelNodes=grouped.get(depth)??[]
levelNodes.sort((a,b)=>b.direct_dependents-a.direct_dependents)
const width=Math.max((levelNodes.length-1)*260,0)
levelNodes.forEach((item,index)=>{
result.push({
id:item.id,
type:"blastNode",
position:{
x:index*260-width/2,
y:depth*165
},
data:{
name:item.name,
nodeType:item.node_type,
filePath:item.file_path,
directDependents:item.direct_dependents,
directDependencies:item.direct_dependencies,
isTarget:item.id===targetId,
depth
}
})
})
}
return result
}
function BlastNode({data}:NodeProps<Node<BlastNodeData>>){
return(
<div className={data.isTarget?"blast-flow-node target":"blast-flow-node"}>
<Handle type="target" position={Position.Top}/>
<div className="blast-node-header">
<span className="blast-flow-type">{data.nodeType}</span>
{data.depth>0&&<span className="blast-depth">D{data.depth}</span>}
</div>
<strong>{shortenName(data.name)}</strong>
{data.isTarget&&<span className="blast-target-label">CURRENT TARGET</span>}
<Handle type="source" position={Position.Bottom}/>
</div>
)
}
function shortenName(value:string){
if(value.length<=45)return value
const parts=value.split(".")
if(parts.length>=2)return`${parts[parts.length-2]}.${parts[parts.length-1]}`
return value.slice(-45)
}
export default DependencyGraph
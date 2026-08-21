import {Activity,GitBranch,History,LayoutDashboard,Plus,ShieldCheck} from "lucide-react"
import {NavLink,Outlet} from "react-router-dom"
const links=[
{to:"/",label:"Overview",icon:LayoutDashboard},
{to:"/analysis/new",label:"New Analysis",icon:Plus},
{to:"/history",label:"Analysis History",icon:History}
]
function AppLayout(){
return(
<div className="app-shell">
<aside className="sidebar">
<div className="brand">
<div className="brand-icon"><Activity size={20}/></div>
<div>
<strong>BlastScope</strong>
<span>Change Intelligence</span>
</div>
</div>
<nav>
{links.map(({to,label,icon:Icon})=>(
<NavLink key={to} to={to} end={to==="/"} className={({isActive})=>isActive?"nav-item active":"nav-item"}>
<Icon size={18}/>
<span>{label}</span>
</NavLink>
))}
</nav>
<div className="sidebar-footer">
<div className="status-row">
<ShieldCheck size={17}/>
<div>
<strong>Analysis Engine</strong>
<span>Ready</span>
</div>
</div>
<div className="status-row">
<GitBranch size={17}/>
<div>
<strong>Git aware</strong>
<span>Blast radius enabled</span>
</div>
</div>
</div>
</aside>
<main className="main-content">
<Outlet/>
</main>
</div>
)
}
export default AppLayout
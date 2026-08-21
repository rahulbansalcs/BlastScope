import {Navigate,Route,Routes} from "react-router-dom"
import AppLayout from "./layouts/AppLayout"
import Dashboard from "./pages/Dashboard"
import NewAnalysis from "./pages/NewAnalysis"
import AnalysisDetail from "./pages/AnalysisDetail"
import History from "./pages/History"
function App(){
return(
<Routes>
<Route element={<AppLayout/>}>
<Route path="/" element={<Dashboard/>}/>
<Route path="/analysis/new" element={<NewAnalysis/>}/>
<Route path="/analysis/:id" element={<AnalysisDetail/>}/>
<Route path="/history" element={<History/>}/>
</Route>
<Route path="*" element={<Navigate to="/" replace/>}/>
</Routes>
)
}
export default App
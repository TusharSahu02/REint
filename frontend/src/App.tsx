import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import DecisionView from './pages/DecisionView'
import Accuracy from './pages/Accuracy'
import Methodology from './pages/Methodology'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DecisionView />} />
        <Route path="accuracy" element={<Accuracy />} />
        <Route path="methodology" element={<Methodology />} />
        <Route path="*" element={<p className="card">Not found.</p>} />
      </Route>
    </Routes>
  )
}

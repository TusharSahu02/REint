import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import DecisionView from './pages/DecisionView'
import Accuracy from './pages/Accuracy'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DecisionView />} />
        <Route path="accuracy" element={<Accuracy />} />
        <Route
          path="*"
          element={<p className="card">This section arrives in a later milestone.</p>}
        />
      </Route>
    </Routes>
  )
}

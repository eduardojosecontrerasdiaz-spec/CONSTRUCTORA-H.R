import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/auth/LoginPage';
import { ProyectosPage } from './pages/proyectos/ProyectosPage';
import { ClientesPage } from './pages/clientes/ClientesPage';
import { ReportesPage } from './pages/reportes/ReportesPage';
import { PresupuestosPage } from './pages/presupuestos/PresupuestosPage';
import { HistorialPage } from './pages/historial/HistorialPage';
import { PlantillasPage } from './pages/plantillas/PlantillasPage';
import { PreciosPage } from './pages/precios/PreciosPage';
import Dashboard from './pages/dashboard/Dashboardpage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <ProyectosPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/proyectos"
            element={
              <ProtectedRoute>
                <ProyectosPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/clientes"
            element={
              <ProtectedRoute>
                <ClientesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reportes"
            element={
              <ProtectedRoute>
                <ReportesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/presupuestos"
            element={
              <ProtectedRoute>
                <PresupuestosPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/historial"
            element={
              <ProtectedRoute>
                <HistorialPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/plantillas"
            element={
              <ProtectedRoute>
                <PlantillasPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/precios"
            element={
              <ProtectedRoute>
                <PreciosPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}


export default App

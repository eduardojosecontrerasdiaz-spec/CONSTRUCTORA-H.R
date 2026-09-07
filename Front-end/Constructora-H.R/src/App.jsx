import { useState } from 'react'

import './App.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/auth/LoginPage';
import { ProyectosPage } from './pages/proyectos/ProyectosPage';
import { PresupuestosPage } from './pages/presupuestos/PresupuestosPage';
import { HistorialPage } from './pages/historial/HistorialPage';
import { PlantillasPage } from './pages/plantillas/PlantillasPage';
import { PreciosPage } from './pages/precios/PreciosPage';

function App() {
  const [count, setCount] = useState(0)

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

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AdminLogin from "./admin_site/Login";
import AdminDashboard from "./admin_site/AdminDashboard";
import TrainerDashboard from "./trainer_site/TrainerDashboard";
import './index.css';

function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/" element={<Navigate to="/admin-site/login" replace />} />
        <Route path="/admin-site/login" element={<AdminLogin />} />
        <Route path="/admin-site/dashboard" element={<AdminDashboard />} />
        <Route path="/trainer-site/dashboard" element={<TrainerDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

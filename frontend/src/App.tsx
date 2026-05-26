import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Header } from "@/components/Header";
import { Navigation } from "@/components/Navigation";
import Dashboard from "./pages/Dashboard";
import Detect from "./pages/Detect";
import Alerts from "./pages/Alerts";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import AdminLogin from "./pages/admin_site/Login";
import AdminDashboard from "./pages/admin_site/AdminDashboard";
import TrainerDashboard from "./pages/trainer_site/TrainerDashboard";
const queryClient = new QueryClient();

import { useLocation } from "react-router-dom";

const AppContent = () => {
  const location = useLocation();
  const isHome = location.pathname === "/";
  const isAdminOrTrainer = location.pathname.startsWith("/admin-site") || location.pathname.startsWith("/trainer-site");

  if (isAdminOrTrainer) {
    return (
      <Routes>
        <Route path="/admin-site/login" element={<AdminLogin />} />
        <Route path="/admin-site/dashboard" element={<AdminDashboard />} />
        <Route path="/trainer-site/dashboard" element={<TrainerDashboard />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white font-mono uppercase tracking-widest selection:bg-white selection:text-black">
      {!isHome && <Header />}
      <div className={isHome ? "p-0" : "p-2 sm:p-4 space-y-4 border-t-2 border-white overflow-hidden"}>
        {!isHome && <Navigation />}
        <main className={isHome ? "" : "max-w-7xl mx-auto border-2 border-white p-3 sm:p-6 overflow-x-hidden"}>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/main" element={<Dashboard />} />
            <Route path="/detect" element={<Detect />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AppContent />
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;

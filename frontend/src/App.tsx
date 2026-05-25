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
const queryClient = new QueryClient();

import { useLocation } from "react-router-dom";

const AppContent = () => {
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <div className="min-h-screen bg-black text-white font-mono uppercase tracking-widest selection:bg-white selection:text-black">
      {!isHome && <Header />}
      <div className={isHome ? "p-0" : "p-4 space-y-4 border-t-2 border-white"}>
        {!isHome && <Navigation />}
        <main className={isHome ? "" : "max-w-7xl mx-auto border-2 border-white p-6"}>
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

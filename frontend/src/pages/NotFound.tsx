import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-black text-white p-4 font-mono">
      <div className="text-center max-w-md w-full border border-white/20 bg-black/80 backdrop-blur-sm p-8 shadow-[0_0_30px_rgba(255,255,255,0.1)] relative overflow-hidden">
        
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-4 h-4 border-l-2 border-t-2 border-red-500"></div>
        <div className="absolute top-0 right-0 w-4 h-4 border-r-2 border-t-2 border-red-500"></div>
        <div className="absolute bottom-0 left-0 w-4 h-4 border-l-2 border-b-2 border-red-500"></div>
        <div className="absolute bottom-0 right-0 w-4 h-4 border-r-2 border-b-2 border-red-500"></div>
        
        <AlertTriangle className="w-16 h-16 mx-auto mb-6 text-red-500 animate-pulse" />
        
        <h1 className="mb-2 text-6xl font-black tracking-widest text-red-500 drop-shadow-[0_0_10px_rgba(239,68,68,0.5)]">404</h1>
        <p className="mb-6 text-sm md:text-base uppercase tracking-widest text-gray-400">
          &gt; SYSTEM.ERROR: ROUTE_NOT_FOUND
        </p>
        
        <div className="bg-red-500/10 border border-red-500/30 p-3 mb-8 text-left text-xs text-red-400 font-mono break-all">
          <p>PATH: {location.pathname}</p>
          <p>STATUS: UNRECOGNIZED</p>
          <p className="mt-2 animate-pulse">_ AWAITING REDIRECT...</p>
        </div>

        <Button asChild className="w-full bg-white text-black hover:bg-gray-200 hover:text-black uppercase tracking-[0.2em] font-bold py-6 rounded-none transition-all duration-300">
          <Link to="/">
            [ RETURN.TO.SYSTEM ]
          </Link>
        </Button>
      </div>
    </div>
  );
};

export default NotFound;

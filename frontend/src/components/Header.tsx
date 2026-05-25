import { Shield, Activity } from "lucide-react";
import { Link } from "react-router-dom";
import { StatusBadge } from "@/components/ui/status-badge";

export function Header() {
  return (
    <header className="flex items-center justify-between p-4 border-b-2 border-white bg-black">
      <Link to="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
        <div className="flex items-center justify-center w-8 h-8 bg-white border-2 border-white">
          <Shield className="h-5 w-5 text-black" />
        </div>
        <div>
          <h1 className="font-bold text-xl tracking-widest uppercase">Legit.ai</h1>
          <p className="text-xs text-gray-400">AI Content Verification</p>
        </div>
      </Link>
      <div className="flex items-center space-x-2 border-2 border-white p-2">
        <Activity className="h-4 w-4 text-white animate-pulse" />
        <span className="text-xs uppercase tracking-widest">[ ACTIVE PROTECTION ]</span>
      </div>
    </header>
  );
}
import { Shield, Activity } from "lucide-react";
import { StatusBadge } from "@/components/ui/status-badge";

export function Header() {
  return (
    <header className="flex items-center justify-between p-4 border-b bg-card">
      <div className="flex items-center space-x-3">
        <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-lg">
          <Shield className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <h1 className="font-semibold text-lg">Legit.ai</h1>
          <p className="text-xs text-muted-foreground">AI Content Verification</p>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <Activity className="h-4 w-4 text-safe animate-pulse" />
        <StatusBadge variant="protected">
          Active Protection
        </StatusBadge>
      </div>
    </header>
  );
}
import { Shield, Eye, AlertTriangle, TrendingUp, Users, Clock, Activity, Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { StatCard } from "@/components/ui/stat-card";
import { StatusBadge } from "@/components/ui/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { fetchHistory, fetchStats } from "@/lib/api";

function formatTimeAgo(iso: string) {
  const utcIso = iso.endsWith('Z') ? iso : `${iso}Z`;
  const diff = Date.now() - new Date(utcIso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hr ago`;
  return `${Math.floor(hrs / 24)} d ago`;
}

function severityFromConfidence(confidence: number, fake: boolean) {
  if (!fake) return "safe";
  if (confidence >= 85) return "critical";
  if (confidence >= 70) return "high";
  return "medium";
}

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: fetchStats,
    refetchInterval: 30000,
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ["history", "recent"],
    queryFn: () => fetchHistory({ limit: 5 }),
    refetchInterval: 30000,
  });

  const recentAlerts = (history?.items ?? []).map((item) => ({
    id: item.id,
    type: item.fake ? "fake-news" : "safe",
    severity: severityFromConfidence(item.confidence, item.fake),
    platform: item.type === "image" ? "Image" : "Text",
    content: item.content_preview,
    time: formatTimeAgo(item.created_at),
  }));

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case "critical":
        return "danger";
      case "high":
        return "warning";
      case "medium":
        return "info";
      default:
        return "safe";
    }
  };

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const scanned = stats?.scanned_today ?? 0;
  const threats = stats?.threats_today ?? 0;
  const rate = stats?.fake_rate_percent ?? 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Scanned Today"
          value={String(scanned)}
          description="detections run today"
          icon={<Eye className="h-4 w-4" />}
        />
        <StatCard
          title="Threats Flagged"
          value={String(threats)}
          description={`${stats?.threats_total ?? 0} total`}
          icon={<Shield className="h-4 w-4" />}
        />
        <StatCard
          title="Flag Rate"
          value={`${rate.toFixed(1)}%`}
          description="of all scans"
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <StatCard
          title="This Week"
          value={String(stats?.recent_count ?? 0)}
          description="scans in 7 days"
          icon={<Users className="h-4 w-4" />}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-lg sm:text-xl tracking-widest border-b-2 border-white pb-2">
            <Activity className="h-5 w-5 shrink-0 text-white animate-pulse" />
            <span>&gt; DETECTION.ACTIVITY</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Text analysis</span>
                <StatusBadge variant="monitoring" size="sm">
                  {stats?.by_type?.text ?? 0} runs
                </StatusBadge>
              </div>
              <Progress
                value={
                  scanned
                    ? ((stats?.by_type?.text ?? 0) / scanned) * 100
                    : 0
                }
                className="h-2"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Image analysis</span>
                <StatusBadge variant="scanning" size="sm">
                  {stats?.by_type?.image ?? 0} runs
                </StatusBadge>
              </div>
              <Progress
                value={
                  scanned
                    ? ((stats?.by_type?.image ?? 0) / scanned) * 100
                    : 0
                }
                className="h-2"
              />
            </div>
          </div>
          <Button asChild variant="outline" size="sm" className="w-full mt-4 bg-black border-2 border-white text-white hover:bg-white hover:text-black rounded-none">
            <Link to="/detect">[ INITIATE NEW SCAN ]</Link>
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b-2 border-white pb-4">
          <CardTitle className="flex items-center space-x-2 tracking-widest text-lg sm:text-xl">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <span>&gt; RECENT.LOGS</span>
          </CardTitle>
          <Button variant="outline" size="sm" asChild className="w-full sm:w-auto bg-black border-2 border-white text-white hover:bg-white hover:text-black rounded-none">
            <Link to="/alerts">[ VIEW.ALL ]</Link>
          </Button>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <Loader2 className="h-6 w-6 animate-spin mx-auto" />
          ) : recentAlerts.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No detections yet.{" "}
              <Link to="/detect" className="text-primary underline">
                Analyze content
              </Link>
            </p>
          ) : (
            <div className="space-y-3">
              {recentAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-3 border-2 border-white bg-black hover:bg-white hover:text-black transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <StatusBadge variant={getSeverityVariant(alert.severity)} size="sm">
                      [{alert.severity.toUpperCase()}]
                    </StatusBadge>
                    <div>
                      <p className="text-sm font-medium line-clamp-1">{alert.content}</p>
                      <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                        <span>{alert.platform}</span>
                        <span>•</span>
                        <Clock className="h-3 w-3" />
                        <span>{alert.time}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      <p className="text-center text-xs text-gray-500 uppercase tracking-widest mt-8">
        * Checked items are stored for 24 hours then automatically deleted *
      </p>
    </div>
  );
}

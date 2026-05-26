import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Filter, Search, Clock, Loader2, Download } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { downloadHistory, fetchHistory } from "@/lib/api";
import { Link } from "react-router-dom";

function severityFromConfidence(confidence: number, fake: boolean) {
  if (!fake) return "low";
  if (confidence >= 85) return "critical";
  if (confidence >= 70) return "high";
  return "medium";
}

export default function Alerts() {
  const [filter, setFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["history", "alerts"],
    queryFn: () => fetchHistory({ limit: 100 }),
    refetchInterval: 30000,
  });

  const alerts = (data?.items ?? []).map((item) => ({
    id: item.id,
    type: item.fake ? "fake-news" : "safe",
    severity: severityFromConfidence(item.confidence, item.fake),
    platform: item.type === "image" ? "Image" : "Text",
    title: item.fake ? "Misinformation flagged" : "Content cleared",
    description: item.reason,
    confidence: Math.round(item.confidence),
    timestamp: item.created_at,
    content: item.content_preview,
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

  const filteredAlerts = alerts.filter((alert) => {
    if (filter !== "all" && alert.severity !== filter) return false;
    const q = searchTerm.toLowerCase();
    if (q && !alert.title.toLowerCase().includes(q) && !alert.description.toLowerCase().includes(q)) {
      return false;
    }
    return true;
  });

  const fakeCount = alerts.filter((a) => a.type === "fake-news").length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4 border-b-2 border-white pb-4 mb-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold uppercase tracking-widest">&gt; DETECTION.HISTORY</h1>
          <p className="text-gray-400 text-xs uppercase tracking-widest mt-1">
            {data?.total ?? 0} total scans · {fakeCount} flagged
          </p>
        </div>
        <div className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-2">
          <div className="relative flex-1 sm:flex-none">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-full sm:w-64"
            />
          </div>
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-full sm:w-32">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()} className="flex-1 sm:flex-none">
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={() => downloadHistory("json")} className="flex-1 sm:flex-none">
              <Download className="h-4 w-4 sm:mr-1" />
              <span className="hidden sm:inline">JSON</span>
            </Button>
            <Button variant="outline" size="sm" onClick={() => downloadHistory("csv")} className="flex-1 sm:flex-none">
              <Download className="h-4 w-4 sm:mr-1" />
              <span className="hidden sm:inline">CSV</span>
            </Button>
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      )}

      {isError && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            Could not load history. Is the API running on port 8000?
          </CardContent>
        </Card>
      )}

      {!isLoading && !isError && filteredAlerts.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-4">No detections match your filters.</p>
            <Button asChild>
              <Link to="/detect">Run detection</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {filteredAlerts.map((alert) => (
          <Card key={alert.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-4">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <StatusBadge variant={getSeverityVariant(alert.severity)} size="sm">
                      {alert.severity.toUpperCase()}
                    </StatusBadge>
                    <span className="text-sm text-muted-foreground">{alert.platform}</span>
                  </div>
                  <CardTitle className="text-lg tracking-widest uppercase mt-2">
                    &gt; {alert.title}
                  </CardTitle>
                </div>
                <div className="text-right text-sm">
                  <div className="font-bold tracking-widest">{alert.confidence}%</div>
                  <div className="text-gray-400 uppercase text-xs tracking-widest">confidence</div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground line-clamp-2">{alert.content}</p>
              <p>{alert.description}</p>
              <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>{new Date(alert.timestamp.endsWith('Z') ? alert.timestamp : alert.timestamp + 'Z').toLocaleString()}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

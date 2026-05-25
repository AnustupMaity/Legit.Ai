import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp, Eye, Shield, AlertTriangle, Calendar, BarChart3, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { fetchHistory, fetchStats } from "@/lib/api";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

export default function Analytics() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: fetchStats,
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ["history", "analytics"],
    queryFn: () => fetchHistory({ limit: 200 }),
  });

  const threatTypes = useMemo(() => {
    const items = history?.items ?? [];
    const fake = items.filter((i) => i.fake).length;
    const safe = items.length - fake;
    const text = items.filter((i) => i.type === "text").length;
    const image = items.filter((i) => i.type === "image").length;
    const total = items.length || 1;
    return [
      { type: "Flagged", count: fake, percentage: Math.round((fake / total) * 100) },
      { type: "Cleared", count: safe, percentage: Math.round((safe / total) * 100) },
      { type: "Text scans", count: text, percentage: Math.round((text / total) * 100) },
      { type: "Image scans", count: image, percentage: Math.round((image / total) * 100) },
    ];
  }, [history]);

  const weeklyData = useMemo(() => {
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const buckets: Record<string, { scanned: number; threats: number }> = {};
    days.forEach((d) => {
      buckets[d] = { scanned: 0, threats: 0 };
    });
    (history?.items ?? []).forEach((item) => {
      const d = days[new Date(item.created_at).getDay()];
      buckets[d].scanned += 1;
      if (item.fake) buckets[d].threats += 1;
    });
    return days.slice(1).concat(days[0]).map((day) => ({
      day,
      scanned: buckets[day].scanned,
      threats: buckets[day].threats,
    }));
  }, [history]);

  const loading = statsLoading || historyLoading;

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const totalScanned = history?.total ?? 0;
  const threats = stats?.threats_total ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b-2 border-white pb-4 mb-4">
        <div>
          <h1 className="text-2xl font-bold uppercase tracking-widest">&gt; ANALYTICS.DASHBOARD</h1>
          <p className="text-gray-400 text-xs uppercase tracking-widest mt-1">Metrics from your detection history</p>
        </div>
        <Select defaultValue="7days">
          <SelectTrigger className="w-32">
            <Calendar className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7days">All time</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Scanned"
          value={String(totalScanned)}
          description="stored in database"
          icon={<Eye className="h-4 w-4" />}
        />
        <StatCard
          title="Threats Detected"
          value={String(threats)}
          description="flagged as fake"
          icon={<AlertTriangle className="h-4 w-4" />}
        />
        <StatCard
          title="Flag Rate"
          value={`${(stats?.fake_rate_percent ?? 0).toFixed(1)}%`}
          description="overall"
          icon={<Shield className="h-4 w-4" />}
        />
        <StatCard
          title="Scanned Today"
          value={String(stats?.scanned_today ?? 0)}
          description="last 24h (UTC)"
          icon={<TrendingUp className="h-4 w-4" />}
        />
      </div>

      <Card>
        <CardHeader className="border-b-2 border-white pb-2 mb-4 border-dashed">
          <CardTitle className="flex items-center space-x-2 tracking-widest uppercase">
            <BarChart3 className="h-5 w-5" />
            <span>&gt; VOL.OVER.TIME</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="scanned" stroke="#3b82f6" name="Total Scanned" />
              <Line type="monotone" dataKey="threats" stroke="#ef4444" name="Threats Detected" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="border-b-2 border-white pb-2 mb-4 border-dashed">
            <CardTitle className="tracking-widest uppercase text-sm">&gt; DIST.TYPE</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={threatTypes.filter(t => t.type === "Text scans" || t.type === "Image scans")}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b-2 border-white pb-2 mb-4 border-dashed">
            <CardTitle className="tracking-widest uppercase text-sm">&gt; FAKE.REAL.RATIO</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={threatTypes.filter(t => t.type === "Flagged" || t.type === "Cleared")}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({type, percentage}) => `${type}: ${percentage}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  <Cell fill="#ef4444" />
                  <Cell fill="#22c55e" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="border-b-2 border-white pb-2 mb-4 border-dashed">
          <CardTitle className="tracking-widest uppercase text-sm">&gt; BREAKDOWN.TYPE</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {Object.entries(stats?.by_type ?? {}).map(([name, count]) => (
              <div key={name} className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium capitalize">{name}</h4>
                  <span className="text-sm text-muted-foreground">{count} scans</span>
                </div>
                <Progress
                  value={totalScanned ? (count / totalScanned) * 100 : 0}
                  className="h-2"
                />
              </div>
            ))}
            {Object.keys(stats?.by_type ?? {}).length === 0 && (
              <p className="text-sm text-muted-foreground">No data yet.</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Search,
  Upload,
  Shield,
  AlertTriangle,
  Loader2,
  Link as LinkIcon,
  List,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  detectImage,
  detectText,
  detectTextBatch,
  detectUrl,
  type DetectionResult,
} from "@/lib/api";
import { loadLocalSettings } from "@/lib/settings";
import { useToast } from "@/hooks/use-toast";

function ResultCard({ result }: { result: DetectionResult }) {
  return (
    <Card>
      <CardHeader className="border-b-2 border-dashed border-white pb-2 mb-2">
        <CardTitle className="flex items-center gap-2 tracking-widest">
          {result.fake ? (
            <AlertTriangle className="h-5 w-5 text-red-500" />
          ) : (
            <Shield className="h-5 w-5 text-white" />
          )}
          &gt; RESULT.OUTPUT
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge variant={result.fake ? "danger" : "safe"}>
            {result.fake ? "Likely misinformation" : "Likely authentic"}
          </StatusBadge>
          {result.cached && (
            <StatusBadge variant="info" size="sm">
              Cached
            </StatusBadge>
          )}
          <span className="text-sm text-muted-foreground">ID: {result.id ?? "—"}</span>
          {result.latency_ms != null && (
            <span className="text-sm text-muted-foreground">
              {result.cached ? "Instant" : `${result.latency_ms} ms`}
            </span>
          )}
        </div>
        <div className="space-y-1">
          <div className="flex justify-between text-sm">
            <span>Confidence</span>
            <span>{result.confidence.toFixed(1)}%</span>
          </div>
          <Progress value={result.confidence} className="h-2" />
        </div>
        <p className="text-sm">{result.reason}</p>
        <p className="text-xs text-muted-foreground">Model: {result.model}</p>
      </CardContent>
    </Card>
  );
}

export default function Detect() {
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [batchText, setBatchText] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [batchResults, setBatchResults] = useState<DetectionResult[]>([]);
  const { toast } = useToast();

  const resetState = () => {
    setText("");
    setUrl("");
    setBatchText("");
    setPreview(null);
    setFile(null);
    setResult(null);
    setBatchResults([]);
  };

  const detectOpts = () => ({
    confidence_threshold: loadLocalSettings().confidence_threshold,
  });

  const textMutation = useMutation({
    mutationFn: () => detectText(text.trim(), detectOpts()),
    onSuccess: (data) => {
      setResult(data);
      setBatchResults([]);
      toast({
        title: "Analysis complete",
        description: data.fake ? "Potential misinformation" : "Looks safe",
      });
    },
    onError: (e: Error) =>
      toast({ title: "Analysis failed", description: e.message, variant: "destructive" }),
  });

  const urlMutation = useMutation({
    mutationFn: () => detectUrl(url.trim(), detectOpts()),
    onSuccess: (data) => {
      setResult(data);
      setBatchResults([]);
      toast({ title: "URL analyzed", description: data.fake ? "Flags raised" : "Looks OK" });
    },
    onError: (e: Error) =>
      toast({ title: "URL failed", description: e.message, variant: "destructive" }),
  });

  const batchMutation = useMutation({
    mutationFn: () => {
      const lines = batchText
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean)
        .slice(0, 20);
      return detectTextBatch(lines, detectOpts());
    },
    onSuccess: (data) => {
      setBatchResults(data.results);
      setResult(null);
      toast({ title: "Batch complete", description: `${data.total} items analyzed` });
    },
    onError: (e: Error) =>
      toast({ title: "Batch failed", description: e.message, variant: "destructive" }),
  });

  const imageMutation = useMutation({
    mutationFn: () => detectImage(file!, detectOpts()),
    onSuccess: (data) => {
      setResult(data);
      setBatchResults([]);
      toast({
        title: "Image analyzed",
        description: data.fake ? "Potential issue detected" : "No major flags",
      });
    },
    onError: (e: Error) =>
      toast({ title: "Analysis failed", description: e.message, variant: "destructive" }),
  });

  const loading =
    textMutation.isPending ||
    imageMutation.isPending ||
    urlMutation.isPending ||
    batchMutation.isPending;

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end border-b-2 border-white pb-2 mb-2">
        <div>
          <h1 className="text-2xl font-bold tracking-widest uppercase">&gt; CONTENT.DETECTION</h1>
          <p className="text-gray-400 text-xs tracking-widest uppercase mt-1">
            Text, URL, batch, or image — ML ensemble + optional Gemini (free mode: USE_LLM=false)
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={resetState} className="bg-black text-white hover:bg-white hover:text-black border-2 border-white uppercase tracking-widest rounded-none">
          [ RESET ]
        </Button>
      </div>

      <Tabs defaultValue="text" className="space-y-4">
        <TabsList className="flex flex-wrap h-auto gap-1">
          <TabsTrigger value="text">Text</TabsTrigger>
          <TabsTrigger value="url">URL</TabsTrigger>
          <TabsTrigger value="batch">Batch</TabsTrigger>
          <TabsTrigger value="image">Image</TabsTrigger>
        </TabsList>

        <TabsContent value="text">
          <Card>
            <CardHeader>
              <CardTitle>Paste content to analyze</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Paste headline, post, or article excerpt..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={8}
              />
              <Button disabled={!text.trim() || loading} onClick={() => textMutation.mutate()}>
                {loading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Search className="h-4 w-4 mr-2" />
                )}
                Analyze text
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="url">
          <Card>
            <CardHeader>
              <CardTitle>Analyze article from URL</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                placeholder="https://example.com/news-article"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
              <Button disabled={!url.trim() || loading} onClick={() => urlMutation.mutate()}>
                {loading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <LinkIcon className="h-4 w-4 mr-2" />
                )}
                Fetch and analyze
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="batch">
          <Card>
            <CardHeader>
              <CardTitle>Batch text (one per line, max 20)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder={"Line one\nLine two\n..."}
                value={batchText}
                onChange={(e) => setBatchText(e.target.value)}
                rows={8}
              />
              <Button
                disabled={!batchText.trim() || loading}
                onClick={() => batchMutation.mutate()}
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <List className="h-4 w-4 mr-2" />
                )}
                Analyze batch
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="image">
          <Card>
            <CardHeader>
              <CardTitle>Upload an image</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                onChange={onFileChange}
                className="block w-full text-sm"
              />
              {preview && (
                <img
                  src={preview}
                  alt="Preview"
                  className="max-h-64 rounded-lg border object-contain"
                />
              )}
              <Button disabled={!file || loading} onClick={() => imageMutation.mutate()}>
                {loading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Upload className="h-4 w-4 mr-2" />
                )}
                Analyze image
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {result && <ResultCard result={result} />}

      {batchResults.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-medium">Batch results ({batchResults.length})</h2>
          {batchResults.map((r) => (
            <ResultCard key={r.id ?? Math.random()} result={r} />
          ))}
        </div>
      )}
    </div>
  );
}

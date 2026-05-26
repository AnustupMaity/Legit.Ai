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
  const authScore = result.fake ? 100 - result.confidence : result.confidence;
  const isFake = result.fake;

  return (
    <Card className={`relative overflow-hidden transition-all duration-500 ${isFake ? 'animate-glitch border-red-500/40 shadow-[0_0_15px_rgba(239,68,68,0.2)]' : 'border-green-500/30'}`}>
      <CardHeader className="border-b border-white/10 pb-2 mb-2 bg-black/40">
        <CardTitle className="flex items-center gap-2 tracking-widest text-sm sm:text-base uppercase break-all sm:break-normal">
          {isFake ? (
            <AlertTriangle className="h-5 w-5 shrink-0 text-red-500 animate-pulse" />
          ) : (
            <Shield className="h-5 w-5 shrink-0 text-green-400" />
          )}
          <span>&gt; RESULT.OUTPUT</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 pt-4">
        <div className="flex flex-col md:flex-row items-center gap-8">
          
          {/* AUTHENTICITY SCORE GAUGE */}
          <div className="relative flex items-center justify-center w-36 h-36 shrink-0">
            <svg className="w-full h-full transform -rotate-90 drop-shadow-[0_0_10px_rgba(255,255,255,0.1)]" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-white/10" />
              <circle 
                cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" 
                strokeDasharray={`${2 * Math.PI * 40}`} 
                strokeDashoffset={`${2 * Math.PI * 40 * (1 - authScore / 100)}`}
                className={`transition-all duration-1500 ease-out ${isFake ? 'text-red-500' : 'text-green-500'}`} 
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-3xl font-black tracking-tighter ${isFake ? 'text-red-500' : 'text-green-500'}`}>
                {authScore.toFixed(0)}%
              </span>
              <span className="text-[9px] uppercase tracking-widest text-gray-400 mt-1">Authentic</span>
            </div>
          </div>

          <div className="flex-1 space-y-4 w-full">
            <div className="flex flex-col sm:flex-row sm:flex-wrap items-start sm:items-center gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge variant={isFake ? "danger" : "safe"}>
                  {isFake ? "Likely misinformation" : "Likely authentic"}
                </StatusBadge>
                {result.cached && <StatusBadge variant="info" size="sm">Cached</StatusBadge>}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-muted-foreground uppercase tracking-widest">ID: {result.id ?? "—"}</span>
                {result.latency_ms != null && (
                  <span className="text-xs text-muted-foreground uppercase tracking-widest">{result.cached ? "Instant" : `${result.latency_ms} ms`}</span>
                )}
              </div>
            </div>
            
            <div className="bg-white/5 p-4 rounded-md border border-white/10">
              <p className="text-sm font-medium tracking-wide leading-relaxed">{result.reason}</p>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground mt-3 opacity-60">Model: {result.model}</p>
            </div>
          </div>
        </div>
      </CardContent>
      {isFake && (
        <div className="absolute inset-0 bg-red-500/5 mix-blend-overlay pointer-events-none"></div>
      )}
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
  const [isDragging, setIsDragging] = useState(false);
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

  const processFile = (f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) processFile(f);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) processFile(f);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 border-b-2 border-white pb-4 mb-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-widest uppercase">&gt; CONTENT.DETECTION</h1>
          <p className="text-gray-400 text-xs tracking-widest uppercase mt-1">
            Text, URL, batch, or image — ML ensemble + optional Gemini
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={resetState} className="w-full sm:w-auto bg-black text-white hover:bg-white hover:text-black border-2 border-white uppercase tracking-widest rounded-none">
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
          <Card className="relative overflow-hidden border-white/10">
            {loading && (
              <div className="absolute inset-0 z-50 pointer-events-none overflow-hidden bg-black/40 backdrop-blur-[1px]">
                <div className="w-full h-[2px] bg-cyan-400 shadow-[0_0_20px_rgba(34,211,238,1)] absolute animate-scan"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="px-6 py-2 bg-black/90 border border-cyan-400/50 text-cyan-400 text-xs tracking-[0.3em] font-bold uppercase animate-pulse shadow-[0_0_15px_rgba(34,211,238,0.2)]">
                    Scanning Content...
                  </span>
                </div>
              </div>
            )}
            <CardHeader className="bg-white/5 border-b border-white/10">
              <CardTitle className="tracking-widest uppercase text-sm text-gray-300">Upload Media</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              
              {/* DRAG AND DROP ZONE */}
              <label 
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`flex flex-col items-center justify-center w-full min-h-[200px] border-2 border-dashed rounded-xl cursor-pointer transition-all duration-300 ${isDragging ? 'border-cyan-400 bg-cyan-400/10 scale-[1.02] shadow-[0_0_30px_rgba(34,211,238,0.15)]' : 'border-white/20 bg-black hover:bg-white/5 hover:border-white/40'}`}
              >
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <Upload className={`w-10 h-10 mb-4 transition-all duration-300 ${isDragging ? 'text-cyan-400 animate-bounce' : 'text-gray-500'}`} />
                  <p className="mb-2 text-sm text-gray-400 tracking-widest"><span className="font-semibold text-white">Click to upload</span> or drag and drop</p>
                  <p className="text-[10px] text-gray-600 uppercase tracking-[0.2em]">Image or Audio (MAX. 50MB)</p>
                </div>
                <input
                  type="file"
                  accept="image/*,audio/*,video/*"
                  onChange={onFileChange}
                  className="hidden"
                />
              </label>

              {preview && (
                <div className="relative mt-4 group rounded-xl overflow-hidden border border-white/20 bg-black/50 p-2">
                  <img
                    src={preview}
                    alt="Preview"
                    className="max-h-64 rounded-lg object-contain w-full drop-shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-opacity duration-300 group-hover:opacity-80"
                  />
                  {/* Subtle scanline overlay on preview */}
                  <div className="absolute inset-0 pointer-events-none opacity-20 bg-[linear-gradient(rgba(255,255,255,0)_50%,rgba(0,0,0,0.5)_50%)] bg-[length:100%_4px]"></div>
                </div>
              )}

              <Button 
                disabled={!file || loading} 
                onClick={() => imageMutation.mutate()}
                className="w-full py-7 uppercase tracking-[0.2em] font-bold bg-white text-black hover:bg-gray-200 transition-all duration-300 hover:scale-[1.01] shadow-[0_0_15px_rgba(255,255,255,0.1)]"
              >
                {loading ? (
                  <Loader2 className="h-5 w-5 mr-3 animate-spin" />
                ) : (
                  <Search className="h-5 w-5 mr-3" />
                )}
                Run Deepfake Analysis
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {result && <ResultCard result={result} />}

      {batchResults.length > 0 && (
        <div className="space-y-4 mt-8">
          <h2 className="text-xs text-gray-400 uppercase tracking-[0.3em] mb-4">Batch results ({batchResults.length})</h2>
          {batchResults.map((r) => (
            <ResultCard key={r.id ?? Math.random()} result={r} />
          ))}
        </div>
      )}

      {/* CUSTOM ANIMATIONS */}
      <style>{`
        @keyframes scan {
          0% { top: 0; opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
        .animate-scan {
          animation: scan 1.5s ease-in-out infinite;
        }
        @keyframes glitch {
          0%, 90% { transform: translate(0); filter: none; }
          92% { transform: translate(-3px, 2px); filter: hue-rotate(90deg); }
          94% { transform: translate(-3px, -2px); filter: none; }
          96% { transform: translate(3px, 2px); filter: hue-rotate(-90deg); }
          98% { transform: translate(3px, -2px); filter: none; }
          100% { transform: translate(0); filter: none; }
        }
        .animate-glitch {
          animation: glitch 3.5s infinite;
        }
      `}</style>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Shield, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import { fetchSettings, updateSettings } from "@/lib/api";
import { loadLocalSettings, saveLocalSettings } from "@/lib/settings";
import { useToast } from "@/hooks/use-toast";

export default function Settings() {
  const { toast } = useToast();
  const [confidence, setConfidence] = useState([loadLocalSettings().confidence_threshold]);
  const [useLlm, setUseLlm] = useState(true);

  const { data: apiSettings } = useQuery({
    queryKey: ["settings"],
    queryFn: fetchSettings,
  });

  useEffect(() => {
    if (apiSettings) {
      setConfidence([apiSettings.confidence_threshold]);
      setUseLlm(apiSettings.use_llm ?? true);
      saveLocalSettings({ confidence_threshold: apiSettings.confidence_threshold });
    }
  }, [apiSettings]);

  const saveSettingsMutation = useMutation({
    mutationFn: () =>
      updateSettings({
        confidence_threshold: confidence[0],
        use_llm: useLlm,
      }),
    onSuccess: (data) => {
      saveLocalSettings({ confidence_threshold: data.confidence_threshold });
      toast({ title: "System settings saved successfully" });
    },
    onError: (e: Error) =>
      toast({ title: "Save failed", description: e.message, variant: "destructive" }),
  });

  return (
    <div className="space-y-6">
      <div className="border-b-2 border-white pb-4 mb-4">
        <h1 className="text-2xl font-bold uppercase tracking-widest">&gt; SYSTEM.SETTINGS</h1>
        <p className="text-gray-400 text-xs uppercase tracking-widest mt-1">Configure your detection parameters</p>
      </div>

      <Card>
        <CardHeader className="border-b-2 border-white pb-2 mb-4 border-dashed">
          <CardTitle className="flex items-center space-x-2 tracking-widest uppercase text-sm">
            <Shield className="h-5 w-5" />
            <span>&gt; DETECTION.ENGINE</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-base uppercase tracking-widest">Confidence Threshold</Label>
              <p className="text-sm text-gray-400">
                Only flag content as fake when confidence is at or above this level.
              </p>
              <Slider
                value={confidence}
                onValueChange={setConfidence}
                max={100}
                step={1}
                className="w-full mt-4 mb-2"
              />
              <div className="flex justify-between text-xs text-gray-400 uppercase tracking-widest">
                <span>LOW</span>
                <span className="text-white font-bold">{confidence[0]}%</span>
                <span>HIGH</span>
              </div>
            </div>

            <Separator className="bg-white/20" />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="flex items-center space-x-2">
                  <Zap className="h-4 w-4" />
                  <Label className="text-base uppercase tracking-widest">Enable Gemini LLM</Label>
                </div>
                <p className="text-sm text-gray-400">
                  Use the Gemini API to provide natural language explanations for detections.
                </p>
              </div>
              <Switch
                checked={useLlm}
                onCheckedChange={setUseLlm}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end space-x-4 pt-4">
        <Button 
          variant="outline" 
          onClick={() => {
            setConfidence([50]);
            setUseLlm(true);
          }}
          className="uppercase tracking-widest border-2 border-white"
        >
          [ RESET ]
        </Button>
        <Button 
          onClick={() => saveSettingsMutation.mutate()}
          disabled={saveSettingsMutation.isPending}
          className="uppercase tracking-widest border-2 border-white bg-white text-black hover:bg-transparent hover:text-white"
        >
          {saveSettingsMutation.isPending ? "[ SAVING... ]" : "[ SAVE.SETTINGS ]"}
        </Button>
      </div>
    </div>
  );
}
const STORAGE_KEY = "legitai-settings";

export interface DetectionSettings {
  confidence_threshold: number;
}

const defaults: DetectionSettings = {
  confidence_threshold: 50,
};

export function loadLocalSettings(): DetectionSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaults;
    return { ...defaults, ...JSON.parse(raw) };
  } catch {
    return defaults;
  }
}

export function saveLocalSettings(s: DetectionSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

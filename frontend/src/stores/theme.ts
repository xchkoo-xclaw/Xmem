import { defineStore } from "pinia";

export type ThemeMode = "light" | "dark" | "auto";
export type ResolvedTheme = "light" | "dark";

type ThemeState = {
  mode: ThemeMode;
  autoEnabled: boolean;
  systemPrefersDark: boolean;
};

const STORAGE_KEY = "theme";
let subscriptionAttached = false;
let mediaListenerAttached = false;

const readJson = (value: string | null): unknown => {
  if (!value) return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
};

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === "object" && value !== null && !Array.isArray(value);
};

const coerceThemeMode = (value: unknown): ThemeMode | null => {
  if (value === "light" || value === "dark" || value === "auto") return value;
  return null;
};

const loadThemeFromStorage = (): Partial<Pick<ThemeState, "mode" | "autoEnabled">> => {
  if (typeof window === "undefined") return {};
  const parsed = readJson(localStorage.getItem(STORAGE_KEY));
  if (!isRecord(parsed)) return {};

  const result: Partial<Pick<ThemeState, "mode" | "autoEnabled">> = {};
  const mode = coerceThemeMode(parsed.mode);
  if (mode) result.mode = mode;
  if (typeof parsed.autoEnabled === "boolean") result.autoEnabled = parsed.autoEnabled;
  return result;
};

const persistThemeToStorage = (state: ThemeState) => {
  if (typeof window === "undefined") return;
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      mode: state.mode,
      autoEnabled: state.autoEnabled,
    }),
  );
};

const readSystemPrefersDark = (): boolean => {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
};

const applyThemeToDom = (resolved: ResolvedTheme) => {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.dataset.theme = resolved;
  root.style.colorScheme = resolved;
};

export const useThemeStore = defineStore("theme", {
  state: (): ThemeState => ({
    mode: "light",
    autoEnabled: false,
    systemPrefersDark: false,
  }),
  getters: {
    /**
     * 当前实际生效的主题（auto 会解析为 light/dark）。
     */
    resolvedTheme(state): ResolvedTheme {
      if (state.mode === "auto") {
        return state.systemPrefersDark ? "dark" : "light";
      }
      return state.mode;
    },
    /**
     * FAB 图标/文案应展示的模式（即用户选择的模式，而不是 resolved）。
     */
    selectedMode: (state) => state.mode,
  },
  actions: {
    /**
     * 初始化主题状态：从 localStorage 恢复 + 绑定系统主题监听 + 应用到 DOM。
     */
    init() {
      this.systemPrefersDark = readSystemPrefersDark();

      const loaded = loadThemeFromStorage();
      if (typeof loaded.autoEnabled === "boolean") {
        this.autoEnabled = loaded.autoEnabled;
      }
      if (loaded.mode) {
        this.mode = loaded.mode;
      }
      if (!this.autoEnabled && this.mode === "auto") {
        this.mode = "light";
      }

      applyThemeToDom(this.resolvedTheme);

      if (!subscriptionAttached) {
        subscriptionAttached = true;
        this.$subscribe((_mutation, state) => {
          persistThemeToStorage(state);
          applyThemeToDom(this.resolvedTheme);
        });
      }

      if (!mediaListenerAttached && typeof window !== "undefined" && typeof window.matchMedia === "function") {
        mediaListenerAttached = true;
        const mql = window.matchMedia("(prefers-color-scheme: dark)");
        const handler = (event: MediaQueryListEvent) => {
          this.systemPrefersDark = event.matches;
          if (this.mode === "auto") {
            applyThemeToDom(this.resolvedTheme);
          }
        };

        if (typeof mql.addEventListener === "function") {
          mql.addEventListener("change", handler);
        } else if (typeof (mql as any).addListener === "function") {
          (mql as any).addListener(handler);
        }
      }
    },
    /**
     * 切换是否允许“跟随系统”选项。
     */
    setAutoEnabled(enabled: boolean) {
      this.autoEnabled = enabled;
      if (!enabled && this.mode === "auto") {
        this.mode = "light";
      }
    },
    /**
     * 设置主题模式（非法输入会被忽略）。
     */
    setMode(mode: ThemeMode) {
      if (mode === "auto" && !this.autoEnabled) return;
      this.mode = mode;
    },
    /**
     * 按规则循环切换主题：
     * - autoEnabled=true：light → dark → auto → light
     * - autoEnabled=false：light ↔ dark
     */
    cycleTheme() {
      if (this.autoEnabled) {
        if (this.mode === "light") {
          this.mode = "dark";
          return;
        }
        if (this.mode === "dark") {
          this.mode = "auto";
          return;
        }
        this.mode = "light";
        return;
      }

      this.mode = this.mode === "dark" ? "light" : "dark";
    },
  },
});


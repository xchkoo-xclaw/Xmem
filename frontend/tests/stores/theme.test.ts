import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { nextTick } from "vue";

type MediaListener = (event: { matches: boolean }) => void;

const createMatchMedia = (initialMatches = false) => {
  let matches = initialMatches;
  const listeners = new Set<MediaListener>();
  const mql = {
    media: "(prefers-color-scheme: dark)",
    get matches() {
      return matches;
    },
    addEventListener: (_: string, cb: MediaListener) => listeners.add(cb),
    removeEventListener: (_: string, cb: MediaListener) => listeners.delete(cb),
    dispatch(matchesNext: boolean) {
      matches = matchesNext;
      for (const cb of listeners) cb({ matches: matchesNext });
    },
  };
  return mql;
};

describe("useThemeStore", () => {
  beforeEach(() => {
    vi.resetModules();
    localStorage.clear();
    setActivePinia(createPinia());
    document.documentElement.dataset.theme = "";
    document.documentElement.style.colorScheme = "";
  });

  it("init 会从 localStorage 读取并应用合法值", async () => {
    localStorage.setItem("theme", JSON.stringify({ mode: "dark", autoEnabled: true }));

    const mql = createMatchMedia(false);
    Object.defineProperty(window, "matchMedia", { value: vi.fn(() => mql), writable: true });

    const { useThemeStore } = await import("../../src/stores/theme");
    const theme = useThemeStore();
    theme.init();

    expect(theme.mode).toBe("dark");
    expect(theme.autoEnabled).toBe(true);
    expect(theme.resolvedTheme).toBe("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(document.documentElement.style.colorScheme).toBe("dark");
  });

  it("init 会忽略非法字段，并在 autoEnabled=false 时拒绝 auto 模式", async () => {
    localStorage.setItem("theme", JSON.stringify({ mode: "auto", autoEnabled: false }));

    const mql = createMatchMedia(true);
    Object.defineProperty(window, "matchMedia", { value: vi.fn(() => mql), writable: true });

    const { useThemeStore } = await import("../../src/stores/theme");
    const theme = useThemeStore();
    theme.init();

    expect(theme.autoEnabled).toBe(false);
    expect(theme.mode).toBe("light");
    expect(theme.resolvedTheme).toBe("light");
    expect(document.documentElement.dataset.theme).toBe("light");
  });

  it("cycleTheme 会根据 autoEnabled 在二态/三态间循环", async () => {
    const mql = createMatchMedia(false);
    Object.defineProperty(window, "matchMedia", { value: vi.fn(() => mql), writable: true });

    const { useThemeStore } = await import("../../src/stores/theme");
    const theme = useThemeStore();
    theme.init();

    expect(theme.mode).toBe("light");

    theme.setAutoEnabled(false);
    theme.cycleTheme();
    expect(theme.mode).toBe("dark");
    theme.cycleTheme();
    expect(theme.mode).toBe("light");

    theme.setAutoEnabled(true);
    expect(theme.mode).toBe("auto");
    theme.cycleTheme();
    expect(theme.mode).toBe("light");
    theme.cycleTheme();
    expect(theme.mode).toBe("dark");
    theme.cycleTheme();
    expect(theme.mode).toBe("auto");
  });

  it("系统主题变化时，auto 模式会实时更新 resolvedTheme 与 DOM", async () => {
    const mql = createMatchMedia(false);
    Object.defineProperty(window, "matchMedia", { value: vi.fn(() => mql), writable: true });

    const { useThemeStore } = await import("../../src/stores/theme");
    const theme = useThemeStore();
    theme.init();
    theme.setAutoEnabled(true);
    theme.setMode("auto");

    expect(theme.resolvedTheme).toBe("light");
    expect(document.documentElement.dataset.theme).toBe("light");

    mql.dispatch(true);
    expect(theme.resolvedTheme).toBe("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("状态变更会通过订阅持久化到 localStorage", async () => {
    const mql = createMatchMedia(false);
    Object.defineProperty(window, "matchMedia", { value: vi.fn(() => mql), writable: true });

    const { useThemeStore } = await import("../../src/stores/theme");
    const theme = useThemeStore();
    theme.init();

    theme.setAutoEnabled(true);
    theme.setMode("dark");
    await nextTick();

    expect(localStorage.getItem("theme")).toBe(JSON.stringify({ mode: "dark", autoEnabled: true }));
  });
});


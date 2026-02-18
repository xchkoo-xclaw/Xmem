import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, nextTick } from "vue";
import App from "../src/App.vue";
import { useUserStore } from "../src/stores/user";

let capturedConfig: any;
const driveMock = vi.fn();

vi.mock("driver.js", () => ({
  driver: vi.fn((config) => {
    capturedConfig = config;
    return {
      drive: driveMock,
      refresh: vi.fn(),
      destroy: vi.fn(),
      moveNext: vi.fn(),
      movePrevious: vi.fn(),
    };
  }),
}));

const DummyHome = defineComponent({
  template: '<div data-onboarding="quick-input"></div>',
});

/**
 * 预置引导相关 DOM 元素，避免等待逻辑悬挂。
 */
const seedOnboardingElements = () => {
  document.body.innerHTML = `
    <div data-onboarding="quick-input"></div>
    <div data-onboarding="notes-search"></div>
    <div data-onboarding="notes-export"></div>
    <div data-onboarding="todo-panel"></div>
    <div data-onboarding="ledger-quick-input-anchor"></div>
    <div data-onboarding="ledger-category-filter"></div>
    <div data-onboarding="statistics-overview"></div>
    <div data-onboarding="ledger-note-generator"></div>
    <div data-onboarding="fab-menu"></div>
    <button data-onboarding="tab-note"></button>
    <button data-onboarding="tab-ledger"></button>
  `;
};

/**
 * 创建测试路由并提供引导入口元素。
 */
const createTestRouter = () =>
  createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/", name: "home", component: DummyHome }],
  });

/**
 * 挂载 App 并等待引导配置生成。
 */
const mountAppWithOnboarding = async () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const user = useUserStore();
  user.token = "";
  localStorage.removeItem("token");
  seedOnboardingElements();

  const router = createTestRouter();
  await router.push({ path: "/", query: { tab: "note" } });
  await router.isReady();

  const wrapper = mount(App, {
    global: {
      plugins: [router, pinia],
      stubs: {
        FabMenu: true,
        Settings: true,
        Toast: true,
        ConfirmDialog: true,
        LedgerEditor: true,
        LoadingOverlay: true,
        AiAssistant: true,
      },
    },
  });

  await nextTick();
  user.token = "test-token";
  localStorage.setItem("token", "test-token");
  await nextTick();
  await nextTick();
  return { wrapper, router };
};

/**
 * 等待引导配置生成，避免异步导航影响断言。
 */
const waitForOnboardingConfig = async (timeoutMs: number = 1200) => {
  const startedAt = Date.now();
  while (!capturedConfig && Date.now() - startedAt < timeoutMs) {
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
};

describe("onboarding config", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedConfig = undefined;
    localStorage.removeItem("xmem_onboarding_done");
  });

  it("包含导出按钮步骤并更新文案", async () => {
    const { wrapper } = await mountAppWithOnboarding();
    await waitForOnboardingConfig();

    expect(capturedConfig).toBeTruthy();
    const steps = capturedConfig?.steps ?? [];
    const notesIndex = steps.findIndex(
      (step: any) => step.element === '[data-onboarding="notes-search"]'
    );

    expect(notesIndex).toBeGreaterThan(-1);
    expect(steps[notesIndex].popover.description).toBe("这里可以搜索全部笔记。");
    expect(steps[notesIndex + 1].element).toBe('[data-onboarding="notes-export"]');
    expect(steps[notesIndex + 1].popover.description).toBe("这里可以导出笔记");
    wrapper.unmount();
  });

  it("记账快速输入步骤使用完整输入框元素", async () => {
    const { wrapper } = await mountAppWithOnboarding();
    await waitForOnboardingConfig();

    expect(capturedConfig).toBeTruthy();
    const steps = capturedConfig?.steps ?? [];
    const ledgerStep = steps.find(
      (step: any) => step.popover?.title === "记账快速输入"
    );

    expect(typeof ledgerStep?.element).toBe("function");
    wrapper.unmount();
  });
});

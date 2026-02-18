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
  setActivePinia(createPinia());
  const user = useUserStore();
  localStorage.setItem("token", "test-token");

  const router = createTestRouter();
  await router.push("/");
  await router.isReady();

  const wrapper = mount(App, {
    global: {
      plugins: [router],
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
  await nextTick();
  await nextTick();
  return { wrapper, router };
};

describe("onboarding config", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedConfig = undefined;
    localStorage.removeItem("xmem_onboarding_done");
  });

  it("包含导出按钮步骤并更新文案", async () => {
    const { wrapper } = await mountAppWithOnboarding();

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

    expect(capturedConfig).toBeTruthy();
    const steps = capturedConfig?.steps ?? [];
    const ledgerStep = steps.find(
      (step: any) => step.popover?.title === "记账快速输入"
    );

    expect(typeof ledgerStep?.element).toBe("function");
    wrapper.unmount();
  });
});

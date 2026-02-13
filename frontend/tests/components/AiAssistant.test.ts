import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";

const dataStoreMock = {
  notes: [] as any[],
  ledgers: [] as any[],
  ledgerPagination: { page: 1, pageSize: 20, total: 0, totalPages: 1 },
  fetchNotes: vi.fn(async () => {}),
  fetchLedgers: vi.fn(async () => ({})),
};

const toastStoreMock = {
  success: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
};

const userStoreMock = {
  token: "",
  profile: null,
};

vi.mock("../../src/stores/data", () => ({
  useDataStore: () => dataStoreMock,
}));

vi.mock("../../src/stores/toast", () => ({
  useToastStore: () => toastStoreMock,
}));

vi.mock("../../src/stores/user", () => ({
  useUserStore: () => userStoreMock,
}));

const AiAssistantPanelStub = defineComponent({
  name: "AiAssistantPanel",
  template: `<div data-test="panel"></div>`,
});

/**
 * 创建 AiAssistant 组件，便于复用挂载逻辑。
 */
const mountAiAssistant = async (props: { visible: boolean; docked: boolean; isDesktop: boolean }) => {
  const AiAssistant = (await import("../../src/components/AiAssistant.vue")).default;
  return mount(AiAssistant, {
    props,
    global: {
      stubs: {
        Teleport: true,
        Transition: false,
        AiAssistantPanel: AiAssistantPanelStub,
      },
    },
  });
};

describe("AiAssistant", () => {
  beforeEach(() => {
    dataStoreMock.notes = [];
    dataStoreMock.ledgers = [];
    dataStoreMock.ledgerPagination = { page: 1, pageSize: 20, total: 0, totalPages: 1 };
    dataStoreMock.fetchNotes.mockClear();
    dataStoreMock.fetchLedgers.mockClear();
  });

  it("visible=false 时不会渲染面板", async () => {
    const wrapper = await mountAiAssistant({ visible: false, docked: false, isDesktop: true });
    expect(wrapper.find('[data-test="panel"]').exists()).toBe(false);
  });

  it("非 docked 模式点击遮罩会触发关闭", async () => {
    const wrapper = await mountAiAssistant({ visible: true, docked: false, isDesktop: true });
    const overlay = wrapper.get("div.bg-overlay\\/40");
    await overlay.trigger("click");
    expect(wrapper.emitted("close")).toBeTruthy();
  });

  it("docked 模式展示面板且不显示遮罩", async () => {
    const wrapper = await mountAiAssistant({ visible: true, docked: true, isDesktop: true });
    expect(wrapper.find('[data-test="panel"]').exists()).toBe(true);
    expect(wrapper.find("div.bg-overlay\\/40").exists()).toBe(false);
  });
});

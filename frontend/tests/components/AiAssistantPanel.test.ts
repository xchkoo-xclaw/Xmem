import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import AiAssistantPanel from "../../src/components/AiAssistantPanel.vue";
import type { LedgerEntry, Note } from "../../src/stores/data";

const CustomSelectStub = defineComponent({
  name: "CustomSelect",
  props: ["modelValue", "options", "placeholder"],
  emits: ["update:modelValue"],
  template: `
    <div>
      <button data-test="select-time" @click="$emit('update:modelValue', 'time_desc')">time</button>
      <button data-test="select-category" @click="$emit('update:modelValue', '餐饮美食')">category</button>
    </div>
  `,
});

/**
 * 构造笔记数据，便于测试附件选择行为。
 */
const createNote = (overrides: Partial<Note> = {}): Note => {
  return {
    id: 1,
    body_md: "hello",
    created_at: "2026-01-10T00:00:00Z",
    ...overrides,
  };
};

/**
 * 构造记账数据，便于测试附件选择行为。
 */
const createLedger = (overrides: Partial<LedgerEntry> = {}): LedgerEntry => {
  return {
    id: 10,
    raw_text: "午餐 23",
    currency: "CNY",
    status: "completed",
    created_at: "2026-01-10T06:30:00Z",
    updated_at: null,
    amount: 23,
    category: "餐饮美食",
    merchant: "便利店",
    event_time: "2026-01-10T05:32:00Z",
    meta: null,
    task_id: null,
    ...overrides,
  };
};

/**
 * 生成面板默认 props，便于按需覆盖。
 */
const createPanelProps = (overrides: Record<string, any> = {}) => {
  return {
    loading: false,
    isDragOver: false,
    contextSummary: "",
    showHistory: false,
    showHistoryMenu: false,
    history: [],
    messages: [],
    newConversationHint: false,
    isDesktop: true,
    draftText: "",
    error: null,
    showAttachPicker: false,
    attachPickerTab: "notes",
    attachSearch: "",
    attachLedgerCategoryFilter: "",
    attachSort: "time_desc",
    filteredAttachNotes: [],
    filteredAttachLedgers: [],
    attachSearchPlaceholder: "搜索",
    ledgerCategorySelectOptions: [{ label: "全部", value: "" }],
    attachSortOptions: [{ label: "时间倒序", value: "time_desc" }],
    setEditorEl: vi.fn(),
    handleDragEnter: vi.fn(),
    handleDragLeave: vi.fn(),
    handleDragOver: vi.fn(),
    handleDrop: vi.fn(),
    startNewConversation: vi.fn(),
    toggleHistory: vi.fn(),
    toggleHistoryMenu: vi.fn(),
    clearHistory: vi.fn(),
    close: vi.fn(),
    loadHistory: vi.fn(),
    sendWithText: vi.fn(),
    focusInput: vi.fn(),
    handleEditorInput: vi.fn(),
    handleEditorKeydown: vi.fn(),
    handlePaste: vi.fn(),
    handleCopy: vi.fn(),
    handleCut: vi.fn(),
    openAttachPicker: vi.fn(),
    closeAttachPicker: vi.fn(),
    setAttachPickerTab: vi.fn(),
    attachNote: vi.fn(),
    attachLedger: vi.fn(),
    send: vi.fn(),
    ...overrides,
  };
};

describe("AiAssistantPanel", () => {
  it("顶部按钮会触发对应回调", async () => {
    const props = createPanelProps({ showHistoryMenu: true });
    const wrapper = mount(AiAssistantPanel, {
      props,
      global: { stubs: { CustomSelect: CustomSelectStub } },
    });

    await wrapper.get('button[title="新对话"]').trigger("click");
    await wrapper.get('button[title="历史"]').trigger("click");
    await wrapper.get('button[title="更多"]').trigger("click");
    await wrapper.get('button[title="关闭"]').trigger("click");
    await wrapper.get(".dropdown-item").trigger("click");

    expect(props.startNewConversation).toHaveBeenCalledTimes(1);
    expect(props.toggleHistory).toHaveBeenCalledTimes(1);
    expect(props.toggleHistoryMenu).toHaveBeenCalledTimes(1);
    expect(props.close).toHaveBeenCalledTimes(1);
    expect(props.clearHistory).toHaveBeenCalledTimes(1);
  });

  it("历史卡片与快捷提示可触发操作", async () => {
    const props = createPanelProps({
      showHistory: true,
      history: [{ messages: [{ role: "user", content: "hi" }], context: [] }],
    });
    const wrapper = mount(AiAssistantPanel, {
      props,
      global: { stubs: { CustomSelect: CustomSelectStub } },
    });

    await wrapper.get(".history-card").trigger("click");
    await wrapper.findAll("button").find((btn) => btn.text().includes("总结笔记"))!.trigger("click");

    expect(props.loadHistory).toHaveBeenCalledWith(0);
    expect(props.sendWithText).toHaveBeenCalledWith("请总结这个笔记的内容");
  });

  it("附件选择器与发送按钮能触发事件", async () => {
    const props = createPanelProps({
      showAttachPicker: true,
      attachPickerTab: "notes",
      filteredAttachNotes: [createNote()],
      filteredAttachLedgers: [createLedger()],
      draftText: "你好",
    });
    const wrapper = mount(AiAssistantPanel, {
      props,
      global: { stubs: { CustomSelect: CustomSelectStub } },
    });

    await wrapper.get(".attach-btn").trigger("click");
    await wrapper.findAll(".attach-tabs button")[1]!.trigger("click");
    await wrapper.get(".attach-card").trigger("click");
    await wrapper.get(".attach-input").setValue("关键词");
    await wrapper.get(".send-btn").trigger("click");

    expect(props.openAttachPicker).toHaveBeenCalledTimes(1);
    expect(props.setAttachPickerTab).toHaveBeenCalledWith("ledgers");
    expect(props.attachNote).toHaveBeenCalledWith(1);
    expect(wrapper.emitted("update:attachSearch")?.[0]).toEqual(["关键词"]);
    expect(props.send).toHaveBeenCalledTimes(1);
  });
});

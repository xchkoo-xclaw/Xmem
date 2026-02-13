<template>
  <Teleport to="body">
    <template v-if="visible && docked">
      <transition
        enter-active-class="transition-transform duration-200"
        enter-from-class="translate-x-full"
        enter-to-class="translate-x-0"
        leave-active-class="transition-transform duration-150"
        leave-from-class="translate-x-0"
        leave-to-class="translate-x-full"
      >
        <AiAssistantPanel
          :loading="loading"
          :isDragOver="isDragOver"
          :contextSummary="contextSummary"
          :showHistory="showHistory"
          :showHistoryMenu="showHistoryMenu"
          :history="history"
          :messages="messages"
          :newConversationHint="newConversationHint"
          :isDesktop="isDesktop"
          :draftText="draftText"
          :error="error"
          :showAttachPicker="showAttachPicker"
          :attachPickerTab="attachPickerTab"
          :filteredAttachNotes="filteredAttachNotes"
          :filteredAttachLedgers="filteredAttachLedgers"
          :attachSearchPlaceholder="attachSearchPlaceholder"
          :ledgerCategorySelectOptions="ledgerCategorySelectOptions"
          :attachSortOptions="attachSortOptions"
          :setEditorEl="setEditorEl"
          :handleDragEnter="handleDragEnter"
          :handleDragLeave="handleDragLeave"
          :handleDragOver="handleDragOver"
          :handleDrop="handleDrop"
          :startNewConversation="startNewConversation"
          :toggleHistory="toggleHistory"
          :toggleHistoryMenu="toggleHistoryMenu"
          :clearHistory="clearHistory"
          :close="close"
          :loadHistory="loadHistory"
          :sendWithText="sendWithText"
          :focusInput="focusInput"
          :handleEditorInput="handleEditorInput"
          :handleEditorKeydown="handleEditorKeydown"
          :handlePaste="handlePaste"
          :handleCopy="handleCopy"
          :handleCut="handleCut"
          :openAttachPicker="openAttachPicker"
          :closeAttachPicker="closeAttachPicker"
          :setAttachPickerTab="setAttachPickerTab"
          :attachNote="attachNote"
          :attachLedger="attachLedger"
          :send="send"
          v-model:attachSearch="attachSearch"
          v-model:attachLedgerCategoryFilter="attachLedgerCategoryFilter"
          v-model:attachSort="attachSort"
        />
      </transition>
    </template>
    <div v-else-if="visible" class="fixed inset-0 z-[60]">
      <div class="absolute inset-0 bg-overlay/40" @click="close"></div>

      <!-- 右侧侧栏 -->
      <transition
        enter-active-class="transition-transform duration-200"
        enter-from-class="translate-x-full"
        enter-to-class="translate-x-0"
        leave-active-class="transition-transform duration-150"
        leave-from-class="translate-x-0"
        leave-to-class="translate-x-full"
      >
        <AiAssistantPanel
          :loading="loading"
          :isDragOver="isDragOver"
          :contextSummary="contextSummary"
          :showHistory="showHistory"
          :showHistoryMenu="showHistoryMenu"
          :history="history"
          :messages="messages"
          :newConversationHint="newConversationHint"
          :isDesktop="isDesktop"
          :draftText="draftText"
          :error="error"
          :showAttachPicker="showAttachPicker"
          :attachPickerTab="attachPickerTab"
          :filteredAttachNotes="filteredAttachNotes"
          :filteredAttachLedgers="filteredAttachLedgers"
          :attachSearchPlaceholder="attachSearchPlaceholder"
          :ledgerCategorySelectOptions="ledgerCategorySelectOptions"
          :attachSortOptions="attachSortOptions"
          :setEditorEl="setEditorEl"
          :handleDragEnter="handleDragEnter"
          :handleDragLeave="handleDragLeave"
          :handleDragOver="handleDragOver"
          :handleDrop="handleDrop"
          :startNewConversation="startNewConversation"
          :toggleHistory="toggleHistory"
          :toggleHistoryMenu="toggleHistoryMenu"
          :clearHistory="clearHistory"
          :close="close"
          :loadHistory="loadHistory"
          :sendWithText="sendWithText"
          :focusInput="focusInput"
          :handleEditorInput="handleEditorInput"
          :handleEditorKeydown="handleEditorKeydown"
          :handlePaste="handlePaste"
          :handleCopy="handleCopy"
          :handleCut="handleCut"
          :openAttachPicker="openAttachPicker"
          :closeAttachPicker="closeAttachPicker"
          :setAttachPickerTab="setAttachPickerTab"
          :attachNote="attachNote"
          :attachLedger="attachLedger"
          :send="send"
          v-model:attachSearch="attachSearch"
          v-model:attachLedgerCategoryFilter="attachLedgerCategoryFilter"
          v-model:attachSort="attachSort"
        />
      </transition>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch, type ComponentPublicInstance } from "vue";
import api from "../api/client";
import { useDataStore } from "../stores/data";
import type { LedgerEntry, Note } from "../stores/data";
import { useToastStore } from "../stores/toast";
import { useUserStore } from "../stores/user";
import { toPlainTextFromMarkdown } from "../utils/markdown";
import AiAssistantPanel from "./AiAssistantPanel.vue";

const props = defineProps<{
  visible: boolean;
  isDesktop: boolean;
  docked: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

type ChatMessage = { role: "user" | "assistant" | "system"; content: string };
type ContextItem =
  | { type: "note"; id: number; body_md: string }
  | { type: "ledger"; id: number; raw_text: string; amount?: number; category?: string };

const messages = ref<ChatMessage[]>([]);
const contextItems = ref<ContextItem[]>([]);
const draftText = ref("");
const loading = ref(false);
const error = ref<string | null>(null);
const showHistory = ref(false);
const history = ref<{ messages: ChatMessage[]; context: ContextItem[] }[]>([]);
const showHistoryMenu = ref(false);
const newConversationHint = ref(false);
const editorEl = ref<HTMLDivElement | null>(null);
/**
 * 绑定输入框 DOM 引用，保障 ref 类型安全。
 */
const setEditorEl = (el: Element | ComponentPublicInstance | null) => {
  editorEl.value = el instanceof HTMLDivElement ? el : null;
};
const data = useDataStore();
const user = useUserStore();
const showAttachPicker = ref(false);
const attachPickerTab = ref<"notes" | "ledgers">("notes");
const attachSearch = ref("");
const attachLedgerCategoryFilter = ref("");
const attachSort = ref<"time_desc" | "time_asc">("time_desc");
const toast = useToastStore();
const isDragOver = ref(false);

/**
 * 获取当前用户的历史记录存储 key。
 */
const getHistoryStorageKey = () => {
  const userId = user.profile?.id;
  if (userId) return `aiAssistantHistory:${userId}`;
  if (user.token) return `aiAssistantHistory:token:${user.token.slice(0, 8)}`;
  return "aiAssistantHistory:guest";
};

/**
 * 记录当前历史存储 key，避免切换账号时混淆。
 */
const historyStorageKey = ref(getHistoryStorageKey());

/**
 * 迁移历史记录存储 key，避免登录态切换导致历史丢失。
 */
const migrateHistoryStorage = (fromKey: string, toKey: string) => {
  if (!fromKey || fromKey === toKey) return;
  const raw = localStorage.getItem(fromKey);
  if (raw && !localStorage.getItem(toKey)) {
    localStorage.setItem(toKey, raw);
  }
  if (raw) {
    localStorage.removeItem(fromKey);
  }
};

/**
 * 同步历史记录存储 key，并在必要时迁移本地数据。
 */
const syncHistoryStorageKey = () => {
  const nextKey = getHistoryStorageKey();
  if (historyStorageKey.value === nextKey) return;
  migrateHistoryStorage(historyStorageKey.value, nextKey);
  historyStorageKey.value = nextKey;
};

/**
 * 关闭对话框。
 */
const close = () => {
  emit("close");
};

/**
 * 归一化搜索文本，便于匹配。
 */
const normalizeSearchText = (value: string) => value.trim().toLowerCase();

/**
 * 获取笔记时间戳。
 */
const getNoteTimeValue = (note: Note) => {
  const time = new Date(note.created_at);
  const ts = time.getTime();
  return Number.isNaN(ts) ? 0 : ts;
};

/**
 * 获取记账时间戳（优先事件时间）。
 */
const getLedgerTimeValue = (ledger: LedgerEntry) => {
  const preferred = ledger.event_time || ledger.created_at;
  const preferredDate = new Date(preferred);
  if (!Number.isNaN(preferredDate.getTime())) return preferredDate.getTime();
  const fallback = new Date(ledger.created_at);
  const fallbackTime = fallback.getTime();
  return Number.isNaN(fallbackTime) ? 0 : fallbackTime;
};

/**
 * 根据规则排序笔记。
 */
const sortNotesByRule = (items: Note[]) => {
  const rule = attachSort.value;
  return [...items].sort((a, b) => {
    if (rule === "time_desc") return getNoteTimeValue(b) - getNoteTimeValue(a);
    return getNoteTimeValue(a) - getNoteTimeValue(b);
  });
};

/**
 * 根据规则排序记账。
 */
const sortLedgersByRule = (items: LedgerEntry[]) => {
  const rule = attachSort.value;
  return [...items].sort((a, b) => {
    if (rule === "time_desc") return getLedgerTimeValue(b) - getLedgerTimeValue(a);
    return getLedgerTimeValue(a) - getLedgerTimeValue(b);
  });
};

/**
 * 获取记账分类选项。
 */
const ledgerCategoryOptions = computed(() => {
  const categories = new Set<string>();
  data.ledgers.forEach((ledger) => {
    if (ledger.category) categories.add(ledger.category);
  });
  return ["", ...Array.from(categories).sort((a, b) => a.localeCompare(b, "zh-CN"))];
});

/**
 * 记账分类选择项。
 */
const ledgerCategorySelectOptions = computed(() => [
  { label: "全部分类", value: "" },
  ...ledgerCategoryOptions.value.slice(1).map((cat) => ({ label: cat, value: cat })),
]);

/**
 * 时间排序选项。
 */
const attachSortOptions = computed(() => [
  { label: "时间：新到旧", value: "time_desc" },
  { label: "时间：旧到新", value: "time_asc" },
]);

/**
 * 过滤与排序附件中的笔记列表。
 */
const filteredAttachNotes = computed(() => {
  const query = normalizeSearchText(attachSearch.value);
  const filtered = data.notes.filter((note) => {
    if (!query) return true;
    const plain = normalizeSearchText(toPlainTextFromMarkdown(note.body_md || ""));
    const idHit = String(note.id).includes(query);
    return plain.includes(query) || idHit;
  });
  return sortNotesByRule(filtered);
});

/**
 * 过滤与排序附件中的记账列表。
 */
const filteredAttachLedgers = computed(() => {
  const query = normalizeSearchText(attachSearch.value);
  const selectedCategory = attachLedgerCategoryFilter.value;
  const filtered = data.ledgers.filter((ledger) => {
    if (selectedCategory && ledger.category !== selectedCategory) return false;
    if (!query) return true;
    const rawText = normalizeSearchText(ledger.raw_text || "");
    const category = normalizeSearchText(ledger.category || "");
    const merchant = normalizeSearchText(ledger.merchant || "");
    const amount = ledger.amount !== undefined ? String(ledger.amount) : "";
    return rawText.includes(query) || category.includes(query) || merchant.includes(query) || amount.includes(query);
  });
  return sortLedgersByRule(filtered);
});

/**
 * 获取附件搜索框占位文本。
 */
const attachSearchPlaceholder = computed(() =>
  attachPickerTab.value === "ledgers" ? "搜索记账内容/分类/商户" : "搜索笔记内容"
);

/**
 * 从节点中提取文本，可按需展开上下文 token。
 */
const buildTextFromNode = (node: Node, expandToken: boolean = true): string => {
  if (node.nodeType === Node.TEXT_NODE) {
    return node.textContent ?? "";
  }
  if (node.nodeType === Node.ELEMENT_NODE) {
    const el = node as HTMLElement;
    if (el.classList.contains("draft-token")) {
      if (expandToken) return el.dataset.text ?? el.textContent ?? "";
      return el.textContent ?? "";
    }
    return Array.from(el.childNodes).map((child) => buildTextFromNode(child, expandToken)).join("");
  }
  if (node.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
    return Array.from(node.childNodes).map((child) => buildTextFromNode(child, expandToken)).join("");
  }
  return "";
};

/**
 * 获取输入框内的纯文本内容（不展开 token）。
 */
const extractDraftText = () => {
  if (!editorEl.value) return "";
  return buildTextFromNode(editorEl.value, false);
};

/**
 * 更新草稿文本状态。
 */
const updateDraftText = () => {
  draftText.value = extractDraftText();
};

/**
 * 设置输入框文本并将光标置于末尾。
 */
const setEditorText = (text: string) => {
  if (!editorEl.value) return;
  editorEl.value.innerText = text;
  const range = document.createRange();
  range.selectNodeContents(editorEl.value);
  range.collapse(false);
  const sel = window.getSelection();
  sel?.removeAllRanges();
  sel?.addRange(range);
  updateDraftText();
};

/**
 * 判断选区是否位于输入框内。
 */
const isSelectionInEditor = () => {
  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0 || !editorEl.value) return false;
  const range = sel.getRangeAt(0);
  return editorEl.value.contains(range.startContainer);
};

/**
 * 在光标处插入纯文本。
 */
const insertTextAtCursor = (text: string) => {
  if (!editorEl.value) return;
  if (!isSelectionInEditor()) {
    editorEl.value.appendChild(document.createTextNode(text));
    const range = document.createRange();
    range.selectNodeContents(editorEl.value);
    range.collapse(false);
    const sel = window.getSelection();
    sel?.removeAllRanges();
    sel?.addRange(range);
    return;
  }
  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0) return;
  const range = sel.getRangeAt(0);
  range.deleteContents();
  const textNode = document.createTextNode(text);
  range.insertNode(textNode);
  range.setStartAfter(textNode);
  range.collapse(true);
  sel.removeAllRanges();
  sel.addRange(range);
};

/**
 * 在光标处插入上下文 token。
 */
const insertToken = (label: string, expandedText: string, linkHref?: string) => {
  if (!editorEl.value) return;
  if (!isSelectionInEditor()) {
    const range = document.createRange();
    range.selectNodeContents(editorEl.value);
    range.collapse(false);
    const sel = window.getSelection();
    sel?.removeAllRanges();
    sel?.addRange(range);
  }
  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0) return;
  const range = sel.getRangeAt(0);
  range.deleteContents();
  const token = document.createElement("a");
  token.className = "draft-token";
  token.textContent = label;
  token.dataset.text = expandedText;
  token.contentEditable = "false";
  if (linkHref) {
    token.href = linkHref;
    token.target = "_blank";
    token.rel = "noopener";
  } else {
    token.href = "javascript:void(0)";
  }
  const space = document.createTextNode(" ");
  range.insertNode(space);
  range.insertNode(token);
  range.setStartAfter(space);
  range.collapse(true);
  sel.removeAllRanges();
  sel.addRange(range);
  updateDraftText();
};

/**
 * 获取当前选区文本（展开 token）。
 */
const getSelectionText = () => {
  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0) return extractDraftText();
  const range = sel.getRangeAt(0);
  const fragment = range.cloneContents();
  return buildTextFromNode(fragment, true);
};

/**
 * 发送当前草稿消息并请求 AI 回复。
 */
const send = async () => {
  const content = draftText.value.trim();
  if (!content || loading.value) return;
  messages.value.push({ role: "user", content });
  if (editorEl.value) editorEl.value.innerHTML = "";
  draftText.value = "";
  loading.value = true;
  error.value = null;
  newConversationHint.value = false;
  closeAttachPicker();
  try {
    const payload = {
      messages: messages.value,
      context: {
        notes: contextItems.value.filter((x) => x.type === "note"),
        ledgers: contextItems.value.filter((x) => x.type === "ledger"),
      },
    };
    const { data } = await api.post("/ai/chat", payload, { timeout: 30000 });
    messages.value.push({ role: "assistant", content: data.reply || "" });
    // 保存到历史
    saveHistory();
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || "对话失败";
  } finally {
    loading.value = false;
  }
};

/**
 * 打开移动端附件选择器。
 */
const openAttachPicker = () => {
  resetAttachFilters();
  showAttachPicker.value = true;
  attachPickerTab.value = "notes";
};

/**
 * 关闭移动端附件选择器。
 */
const closeAttachPicker = () => {
  showAttachPicker.value = false;
};

/**
 * 重置附件筛选与排序条件。
 */
const resetAttachFilters = () => {
  attachSearch.value = "";
  attachLedgerCategoryFilter.value = "";
  attachSort.value = "time_desc";
};

/**
 * 切换移动端附件选择器的标签。
 */
const setAttachPickerTab = (tab: "notes" | "ledgers") => {
  attachPickerTab.value = tab;
};

/**
 * 处理输入框内容变化。
 */
const handleEditorInput = () => {
  updateDraftText();
  if (draftText.value.trim()) newConversationHint.value = false;
};

/**
 * 处理输入框按键行为。
 */
const handleEditorKeydown = (event: KeyboardEvent) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    if (loading.value) return;
    send();
    return;
  }
  if (event.key === "Enter" && event.shiftKey) {
    event.preventDefault();
    insertTextAtCursor("\n");
    updateDraftText();
  }
};

/**
 * 处理输入框粘贴，保持纯文本。
 */
const handlePaste = (event: ClipboardEvent) => {
  event.preventDefault();
  const text = event.clipboardData?.getData("text/plain") ?? "";
  insertTextAtCursor(text);
  updateDraftText();
};

/**
 * 处理复制，将 token 展开为纯文本。
 */
const handleCopy = (event: ClipboardEvent) => {
  const text = getSelectionText();
  if (!text) return;
  event.preventDefault();
  event.clipboardData?.setData("text/plain", text);
};

/**
 * 处理剪切，将 token 展开为纯文本并删除选区。
 */
const handleCut = (event: ClipboardEvent) => {
  const text = getSelectionText();
  if (!text) return;
  event.preventDefault();
  event.clipboardData?.setData("text/plain", text);
  const sel = window.getSelection();
  if (sel && sel.rangeCount > 0) {
    sel.getRangeAt(0).deleteContents();
    updateDraftText();
  }
};

/**
 * 处理拖拽进入侧栏，显示高亮。
 */
const handleDragEnter = (_event?: DragEvent) => {
  if (!props.isDesktop) return;
  isDragOver.value = true;
};

/**
 * 处理拖拽离开侧栏，取消高亮。
 */
const handleDragLeave = (_event?: DragEvent) => {
  if (!props.isDesktop) return;
  isDragOver.value = false;
};

/**
 * 处理拖拽进入状态（用于显示复制鼠标指示）。
 */
const handleDragOver = (event?: DragEvent) => {
  if (!props.isDesktop) return;
  if (!event) return;
  isDragOver.value = true;
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = "copy";
  }
};

/**
 * 处理拖拽释放，解析拖拽内容为上下文。
 */
const handleDrop = (event?: DragEvent) => {
  if (!event) return;
  error.value = null;
  newConversationHint.value = false;
  isDragOver.value = false;
  if (!props.isDesktop) return;
  const dt = event.dataTransfer;
  if (!dt) return;
  let parsed: any = null;
  try {
    const raw = dt.getData("application/x-xmem");
    if (raw) {
      parsed = JSON.parse(raw);
    }
  } catch {
    parsed = null;
  }
  if (parsed && parsed.type === "note") {
    const note = data.notes.find(n => n.id === parsed.id);
    const body = parsed.body_md ?? note?.body_md ?? "";
    const id = parsed.id ?? note?.id ?? Date.now();
    const expanded = `【笔记#${id}】\n${body}`.trim();
    contextItems.value.push({ type: "note", id, body_md: body });
    insertToken(`笔记#${id}`, expanded, `/note/${id}`);
    toast.success("已加入上下文：笔记");
    return;
  }
  if (parsed && parsed.type === "ledger") {
    const ledger = data.ledgers.find(l => l.id === parsed.id);
    const rawText = parsed.raw_text ?? ledger?.raw_text ?? "";
    const id = parsed.id ?? ledger?.id ?? Date.now();
    const amountText = parsed.amount ?? ledger?.amount;
    const categoryText = parsed.category ?? ledger?.category;
    const hasAmount = amountText !== undefined && amountText !== null;
    const expanded = `【记账#${id}】${rawText}${hasAmount ? ` 金额:${amountText}` : ""}${categoryText ? ` 分类:${categoryText}` : ""}`;
    contextItems.value.push({
      type: "ledger",
      id,
      raw_text: rawText,
      amount: parsed.amount ?? ledger?.amount,
      category: parsed.category ?? ledger?.category,
    });
    insertToken(`记账#${id}`, expanded, `/ledger/${id}`);
    toast.success("已加入上下文：记账");
    return;
  }
  {
    const text = dt.getData("text/plain");
    if (text && text.trim()) {
      // 作为临时笔记上下文
      contextItems.value.push({ type: "note", id: Date.now(), body_md: text.trim() });
      insertToken("文本", text.trim());
      toast.success("已加入上下文：文本");
    } else {
      error.value = "无法识别拖拽内容";
      toast.error("无法识别拖拽内容");
    }
  }
};

/**
 * 切换历史记录显示。
 */
const toggleHistory = () => {
  showHistory.value = !showHistory.value;
};

/**
 * 切换历史记录次级菜单显示。
 */
const toggleHistoryMenu = () => {
  showHistoryMenu.value = !showHistoryMenu.value;
};

/**
 * 加载指定历史会话。
 */
const loadHistory = (index: number) => {
  const item = history.value[index];
  if (!item) return;
  messages.value = [...item.messages];
  contextItems.value = [...item.context];
  if (editorEl.value) editorEl.value.innerHTML = "";
  draftText.value = "";
  error.value = null;
  closeAttachPicker();
  showHistory.value = false;
  showHistoryMenu.value = false;
  newConversationHint.value = false;
};

/**
 * 保存会话到本地历史。
 */
const saveHistory = () => {
  syncHistoryStorageKey();
  const messagesSnapshot = messages.value.map((m) => ({ ...m }));
  const contextSnapshot = contextItems.value.map((item) => ({ ...item }));
  const newItem = { messages: messagesSnapshot, context: contextSnapshot };
  const storageKey = historyStorageKey.value;
  const raw = localStorage.getItem(storageKey);
  let list: typeof history.value = [];
  try {
    if (raw) list = JSON.parse(raw);
  } catch {
    list = [];
  }
  list.unshift(newItem);
  // 仅保留最近 20 条
  list = list.slice(0, 20);
  localStorage.setItem(storageKey, JSON.stringify(list));
  history.value = list;
};

/**
 * 开启一条新对话：必要时先保存当前会话，然后清空消息与上下文。
 */
const startNewConversation = () => {
  if (messages.value.length || contextItems.value.length) {
    saveHistory();
  }
  messages.value = [];
  contextItems.value = [];
  if (editorEl.value) editorEl.value.innerHTML = "";
  draftText.value = "";
  error.value = null;
  showHistory.value = false;
  showHistoryMenu.value = false;
  newConversationHint.value = true;
};

/**
 * 聚焦输入框，便于开始输入问题。
 */
const focusInput = () => {
  editorEl.value?.focus();
};

/**
 * 根据 ID 附加笔记到上下文。
 */
const attachNote = (id: number) => {
  const note = data.notes.find(n => n.id === id);
  if (!note) return;
  const expanded = `【笔记#${note.id}】\n${note.body_md || ""}`.trim();
  contextItems.value.push({ type: "note", id: note.id, body_md: note.body_md || "" });
  insertToken(`笔记#${note.id}`, expanded, `/note/${note.id}`);
  closeAttachPicker();
  newConversationHint.value = false;
};

/**
 * 根据 ID 附加记账到上下文。
 */
const attachLedger = (id: number) => {
  const ledger = data.ledgers.find(l => l.id === id);
  if (!ledger) return;
  const hasAmount = ledger.amount !== undefined && ledger.amount !== null;
  const expanded = `【记账#${ledger.id}】${ledger.raw_text || ""}${hasAmount ? ` 金额:${ledger.amount}` : ""}${ledger.category ? ` 分类:${ledger.category}` : ""}`;
  contextItems.value.push({
    type: "ledger",
    id: ledger.id,
    raw_text: ledger.raw_text,
    amount: ledger.amount,
    category: ledger.category,
  });
  insertToken(`记账#${ledger.id}`, expanded, `/ledger/${ledger.id}`);
  closeAttachPicker();
  newConversationHint.value = false;
};

/**
 * 清除所有历史记录。
 */
const clearHistory = () => {
  syncHistoryStorageKey();
  localStorage.removeItem(historyStorageKey.value);
  history.value = [];
  showHistoryMenu.value = false;
};

/**
 * 初始化历史记录。
 */
const initHistory = () => {
  syncHistoryStorageKey();
  const raw = localStorage.getItem(historyStorageKey.value);
  try {
    history.value = raw ? JSON.parse(raw) : [];
  } catch {
    history.value = [];
  }
};

/**
 * 拉取完整记账列表，确保附件选择器可用。
 */
const loadLedgersForAttach = async () => {
  const pageSize = data.ledgerPagination.pageSize || 20;
  if (data.ledgers.length === 0) {
    await data.fetchLedgers(undefined, 1, pageSize);
  }
  const totalPages = data.ledgerPagination.totalPages;
  if (!totalPages || totalPages <= 1) return;
  const loadedPages = Math.ceil(data.ledgers.length / pageSize);
  for (let page = loadedPages + 1; page <= totalPages; page += 1) {
    await data.fetchLedgers(undefined, page, pageSize);
  }
};

onMounted(() => {
  syncHistoryStorageKey();
  initHistory();
  if (data.notes.length === 0) {
    data.fetchNotes();
  }
  loadLedgersForAttach();
});

watch(() => props.visible, (v) => {
  if (!v) return;
  // 打开时清空错误与加载态
  error.value = null;
  loading.value = false;
  closeAttachPicker();
});

/**
 * 同步用户变化对应的历史记录。
 */
watch(() => [user.token, user.profile?.id], () => {
  syncHistoryStorageKey();
  if (!user.token) {
    history.value = [];
    showHistory.value = false;
    showHistoryMenu.value = false;
    return;
  }
  initHistory();
});

/**
 * 快捷填充草稿并聚焦输入框。
 */
const sendWithText = (text: string) => {
  setEditorText(text);
  newConversationHint.value = false;
  focusInput();
};

/**
 * 当前上下文摘要字符串。
 */
const contextSummary = computed(() => {
  const notes = contextItems.value.filter((x) => x.type === "note").length;
  const ledgers = contextItems.value.filter((x) => x.type === "ledger").length;
  if (notes || ledgers) return `笔记 ${notes} · 记账 ${ledgers}`;
  return "";
});
</script>

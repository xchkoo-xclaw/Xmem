<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-[60]">
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
        <aside
          v-if="visible"
          class="fixed inset-y-0 right-0 w-[92vw] sm:w-[460px] bg-surface border-l border-border shadow-card flex flex-col ai-assistant"
          :class="{ 'ai-soft-loading': loading }"
          @dragover.prevent="handleDragOver"
          @drop.prevent="handleDrop"
          role="complementary"
          aria-label="AI 助手侧栏"
        >
          <!-- 顶部栏 -->
          <header class="px-4 py-3 border-b border-border flex items-center justify-between brand-header">
            <div class="flex items-center gap-2">
              <div class="brand-chip">
                <span class="brand-x">X</span><span class="brand-ia">ia</span>
              </div>
              <div class="flex flex-col">
                <span class="text-sm font-semibold text-text">xmem intelligence assistant</span>
                <span v-if="contextSummary" class="text-[11px] text-muted">上下文：{{ contextSummary }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2 relative">
              <!-- 开启新对话 -->
              <button class="icon-btn" @click="startNewConversation" title="新对话">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
              </button>
              <button class="icon-btn" @click="toggleHistory" title="历史">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3M12 22a10 10 0 100-20 10 10 0 000 20z"/>
                </svg>
              </button>
              <!-- 历史更多（次级菜单） -->
              <button class="icon-btn" @click="toggleHistoryMenu" title="更多">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.5a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm0 7a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm0 7a1.5 1.5 0 110-3 1.5 1.5 0 010 3z"/>
                </svg>
              </button>
              <div v-if="showHistoryMenu" class="dropdown-menu">
                <button class="dropdown-item" @click="clearHistory">清除历史记录</button>
              </div>
              <button class="icon-btn" @click="close" title="关闭">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </header>

          <!-- 历史记录（可折叠） -->
          <div v-if="showHistory" class="px-4 py-3 border-b border-border">
            <div v-if="history.length === 0" class="empty-muted">暂无历史记录</div>
            <div v-else class="history-grid">
              <button
                v-for="(item, idx) in history"
                :key="idx"
                class="history-card"
                @click="loadHistory(idx)"
              >
                <div class="history-title">会话 {{ idx + 1 }}</div>
                <div class="history-meta">消息数 {{ item.messages.length }}</div>
                <div class="history-preview">
                  {{ item.messages[item.messages.length - 1]?.content || '...' }}
                </div>
              </button>
            </div>
          </div>

          <!-- 快速提示与空状态 -->
          <div v-if="messages.length === 0 && !loading" class="px-4 py-3 border-b border-border">
            <div class="grid grid-cols-2 gap-3">
              <button class="prompt-card" @click="draft = '请总结已添加到上下文的笔记，输出要点与行动项。'; send()">
                <div class="prompt-title">总结上下文笔记</div>
                <div class="prompt-sub">快速提取重点与行动项</div>
              </button>
              <button class="prompt-card" @click="draft = '分析本月消费结构并给出节省建议。'; send()">
                <div class="prompt-title">分析当月消费</div>
                <div class="prompt-sub">洞察结构与优化建议</div>
              </button>
              <button class="prompt-card" @click="draft = '优化这段文字的表达，更精炼自然。'; send()">
                <div class="prompt-title">优化写作</div>
                <div class="prompt-sub">让表达更清晰专业</div>
              </button>
            </div>
          </div>
          <div v-else class="px-4 py-3 border-b border-border">
            <div class="flex gap-2 overflow-auto hide-scrollbar">
              <button class="chip" @click="draft = '请总结已添加到上下文的笔记，输出要点与行动项。'; send()">总结上下文笔记</button>
              <button class="chip" @click="draft = '分析本月消费结构并给出节省建议。'; send()">分析当月消费</button>
              <button class="chip" @click="draft = '优化这段文字的表达，更精炼自然。'; send()">优化写作</button>
            </div>
          </div>

          <!-- 对话区（可滚动） -->
          <main class="flex-1 overflow-auto px-4 py-3">
            <!-- 新对话大卡片层级 -->
            <div v-if="messages.length === 0 && newConversationHint" class="new-chat-card">
              <div class="new-chat-title">开启新对话</div>
              <div class="new-chat-desc">拖拽笔记或记账卡片到右侧作为上下文，或直接在下方输入你的问题。</div>
              <div class="mt-3">
                <button class="btn btn-gradient px-4 py-2" @click="focusInput">开始输入</button>
              </div>
            </div>
            <div v-else class="space-y-3">
              <div v-for="(m, i) in messages" :key="i" class="flex items-start gap-3">
                <div
                  class="w-7 h-7 rounded-full flex items-center justify-center text-[10px] bubble-avatar"
                  :class="m.role === 'user' ? 'bubble-avatar-user' : 'bubble-avatar-ai'"
                >
                  {{ m.role === 'user' ? '我' : 'Xia' }}
                </div>
                <div
                  class="flex-1 text-sm whitespace-pre-wrap bubble"
                  :class="m.role === 'user' ? 'bubble-user' : 'bubble-ai'"
                >{{ m.content }}</div>
              </div>
              <div v-if="loading" class="space-y-2">
                <div class="ai-skeleton-line w-3/4"></div>
                <div class="ai-skeleton-line w-2/3"></div>
                <div class="ai-skeleton-line w-1/2"></div>
              </div>
              <div v-if="error" class="text-xs text-red-500">{{ error }}</div>
            </div>
          </main>

          <!-- 底部输入栏 -->
          <footer class="px-4 py-3 border-t border-border">
            <div class="text-xs text-muted mb-2">
              支持拖拽笔记或记账卡片到侧栏，自动作为上下文；Shift+Enter 换行，Enter 发送。
            </div>
            <div class="flex items-end gap-3">
              <textarea
                v-model="draft"
                class="input input-pill flex-1 min-h-[64px]"
                placeholder="请输入问题或消息..."
                @keydown.enter.prevent="handleEnterKey"
                ref="inputEl"
              />
              <button class="btn btn-gradient px-4 py-2" :disabled="loading || !draft.trim()" @click="send">
                {{ loading ? '生成中...' : '发送' }}
              </button>
            </div>
          </footer>
        </aside>
      </transition>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch, nextTick } from "vue";
import api from "../api/client";

const props = defineProps<{
  visible: boolean;
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
const draft = ref("");
const loading = ref(false);
const error = ref<string | null>(null);
const showHistory = ref(false);
const history = ref<{ messages: ChatMessage[]; context: ContextItem[] }[]>([]);
const showHistoryMenu = ref(false);
const newConversationHint = ref(false);
const inputEl = ref<HTMLTextAreaElement | null>(null);

/**
 * 关闭对话框。
 */
const close = () => {
  emit("close");
};

/**
 * 发送当前草稿消息并请求 AI 回复。
 */
const send = async () => {
  if (!draft.value.trim()) return;
  const content = draft.value.trim();
  messages.value.push({ role: "user", content });
  draft.value = "";
  loading.value = true;
  error.value = null;
  newConversationHint.value = false;
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
 * 处理输入框 Enter 行为：Shift+Enter 换行，Enter 发送。
 */
const handleEnterKey = (event: KeyboardEvent) => {
  if (event.shiftKey) {
    const el = event.target as HTMLTextAreaElement;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    draft.value = draft.value.slice(0, start) + "\n" + draft.value.slice(end);
    nextTick(() => {
      el.selectionStart = el.selectionEnd = start + 1;
    });
    return;
  }
  send();
};

/**
 * 处理拖拽进入状态（用于显示复制鼠标指示）。
 */
const handleDragOver = (event: DragEvent) => {
  event.dataTransfer!.dropEffect = "copy";
};

/**
 * 处理拖拽释放，解析拖拽内容为上下文。
 */
const handleDrop = (event: DragEvent) => {
  error.value = null;
  newConversationHint.value = false;
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
  if (parsed && parsed.type === "note" && parsed.body_md) {
    contextItems.value.push({ type: "note", id: parsed.id, body_md: parsed.body_md });
  } else if (parsed && parsed.type === "ledger" && parsed.raw_text) {
    contextItems.value.push({
      type: "ledger",
      id: parsed.id,
      raw_text: parsed.raw_text,
      amount: parsed.amount,
      category: parsed.category,
    });
  } else {
    const text = dt.getData("text/plain");
    if (text && text.trim()) {
      // 作为临时笔记上下文
      contextItems.value.push({ type: "note", id: Date.now(), body_md: text.trim() });
    } else {
      error.value = "无法识别拖拽内容";
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
  showHistory.value = false;
  showHistoryMenu.value = false;
  newConversationHint.value = false;
};

/**
 * 保存会话到本地历史。
 */
const saveHistory = () => {
  const newItem = { messages: messages.value, context: contextItems.value };
  const raw = localStorage.getItem("aiAssistantHistory");
  let list: typeof history.value = [];
  try {
    if (raw) list = JSON.parse(raw);
  } catch {
    list = [];
  }
  list.unshift(newItem);
  // 仅保留最近 20 条
  list = list.slice(0, 20);
  localStorage.setItem("aiAssistantHistory", JSON.stringify(list));
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
  draft.value = "";
  error.value = null;
  showHistory.value = false;
  showHistoryMenu.value = false;
  newConversationHint.value = true;
};

/**
 * 聚焦输入框，便于开始输入问题。
 */
const focusInput = () => {
  inputEl.value?.focus();
};

/**
 * 清除所有历史记录。
 */
const clearHistory = () => {
  localStorage.removeItem("aiAssistantHistory");
  history.value = [];
  showHistoryMenu.value = false;
};

/**
 * 初始化历史记录。
 */
const initHistory = () => {
  const raw = localStorage.getItem("aiAssistantHistory");
  try {
    history.value = raw ? JSON.parse(raw) : [];
  } catch {
    history.value = [];
  }
};

onMounted(() => {
  initHistory();
});

watch(() => props.visible, (v) => {
  if (!v) return;
  // 打开时清空错误与加载态
  error.value = null;
  loading.value = false;
});

watch(draft, (val) => {
  if (val.trim()) newConversationHint.value = false;
});

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

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.input {
  @apply w-full rounded-xl border border-border bg-surface px-4 py-3 text-text placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/40 transition-shadow shadow-sm;
}
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-accent text-on-accent shadow-float active:scale-95;
}
.btn-gradient {
  background: linear-gradient(135deg, rgba(255,90,180,0.9), rgba(90,170,255,0.9));
  color: white;
  border-radius: 14px;
  box-shadow: 0 6px 20px rgba(255, 90, 180, 0.25);
}
.btn.ghost {
  @apply bg-surface text-text border border-border hover:border-border/70;
}
.link {
  @apply text-text underline decoration-dotted hover:decoration-solid;
}
.empty-muted {
  @apply text-xs text-muted rounded-xl border border-border/60 px-3 py-2;
  background: rgba(255,255,255,0.04);
}
.history-grid {
  @apply grid grid-cols-2 gap-3;
}
.history-card {
  @apply rounded-2xl border px-3 py-2 text-left transition-all duration-150;
  border-color: rgba(255,90,180,0.28);
  background: linear-gradient(135deg, rgba(255,90,180,0.06), rgba(90,170,255,0.06));
}
.history-card:hover {
  border-color: rgba(255,90,180,0.5);
  transform: translateY(-2px);
}
.history-title {
  @apply text-sm font-semibold text-text;
}
.history-meta {
  @apply text-[11px] text-muted;
}
.history-preview {
  @apply text-xs text-muted mt-1 line-clamp-2;
}
.prompt-card {
  @apply rounded-2xl border px-3 py-3 text-left transition-all duration-150;
  border-color: rgba(90,170,255,0.25);
  background: linear-gradient(135deg, rgba(90,170,255,0.08), rgba(255,90,180,0.08));
}
.prompt-card:hover {
  border-color: rgba(90,170,255,0.45);
  transform: translateY(-2px);
}
.prompt-title {
  @apply text-sm font-semibold text-text;
}
.prompt-sub {
  @apply text-xs text-muted mt-1;
}

.ai-skeleton-line {
  @apply h-3 rounded-full bg-surface2;
}
.ai-soft-loading {
  border-color: rgb(255, 90, 180);
  box-shadow: 0 0 12px rgba(255, 90, 180, 0.28);
  animation: ai-soft-pulse 3.2s ease-in-out infinite;
}
/* 品牌头部与芯片 */
.brand-header {
  backdrop-filter: saturate(160%) blur(8px);
}
.brand-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-weight: 800;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, rgba(255,90,180,0.18), rgba(90,170,255,0.18));
  border: 1px solid rgba(255,90,180,0.3);
  color: rgb(var(--c-text));
  padding: 4px 8px;
  border-radius: 12px;
}
.brand-x {
  background: linear-gradient(135deg, #ff5ab4, #5aaaff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.brand-ia {
  color: rgb(var(--c-text));
}
.icon-btn {
  @apply p-2 rounded-lg border border-border hover:border-accent/50;
}
.dropdown-menu {
  @apply absolute right-2 top-10 bg-surface border border-border rounded-xl shadow-card p-2 z-[70];
}
.dropdown-item {
  @apply text-sm text-text px-3 py-1.5 rounded-md hover:bg-surface2;
}
.chip {
  @apply px-3 py-1.5 rounded-full text-xs border;
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,90,180,0.28);
  color: rgb(var(--c-text));
}
.chip:hover {
  border-color: rgba(255,90,180,0.45);
}
.new-chat-card {
  @apply rounded-2xl border px-4 py-6 text-center;
  border-color: rgba(255,90,180,0.28);
  background: linear-gradient(135deg, rgba(255,90,180,0.06), rgba(90,170,255,0.06));
}
.new-chat-title {
  @apply text-base font-semibold text-text;
}
.new-chat-desc {
  @apply text-xs text-muted mt-1;
}
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
/* 对话气泡与头像 */
.bubble {
  border-radius: 14px;
  padding: 10px 12px;
}
.bubble-user {
  background: rgb(var(--c-accent) / 0.12);
  border: 1px solid rgba(90,170,255,0.3);
  color: rgb(var(--c-text));
}
.bubble-ai {
  background: linear-gradient(135deg, rgba(255,90,180,0.06), rgba(90,170,255,0.06));
  border: 1px solid rgba(255,90,180,0.28);
  color: rgb(var(--c-text));
}
.bubble-avatar {
  border: 1px solid rgba(255,90,180,0.28);
}
.bubble-avatar-ai {
  background: linear-gradient(135deg, rgba(255,90,180,0.25), rgba(90,170,255,0.25));
  color: white;
}
.bubble-avatar-user {
  background: rgb(var(--c-accent));
  color: rgb(var(--c-on-accent));
}
.input-pill {
  border-radius: 14px;
}
@keyframes ai-soft-pulse {
  0% {
    border-color: rgb(255, 90, 180);
    box-shadow: 0 0 12px rgba(255, 90, 180, 0.28);
  }
  33% {
    border-color: rgb(90, 170, 255);
    box-shadow: 0 0 12px rgba(90, 170, 255, 0.28);
  }
  66% {
    border-color: rgb(120, 255, 150);
    box-shadow: 0 0 12px rgba(120, 255, 150, 0.28);
  }
  100% {
    border-color: rgb(255, 90, 180);
    box-shadow: 0 0 12px rgba(255, 90, 180, 0.28);
  }
}
</style>

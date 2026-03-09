<template>
  <div class="home-view min-h-screen bg-bg text-text flex flex-col items-center">
    <header class="w-full max-w-4xl px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="text-xl font-bold leading-none">Xmem</div>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <span class="text-muted">{{ getGreeting() }}，{{ user.profile?.user_name || user.profile?.email }}</span>
        <button class="btn ghost" @click="handleLogout">登出</button>
      </div>
    </header>

    <main class="w-full max-w-4xl px-4 pb-20">
      <div class="bg-surface border border-border rounded-3xl shadow-card p-4 md:p-6 lg:p-8 mx-auto">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div class="w-fit">
            <TabSwitcher v-model="currentTab" :tabs="tabs" />
          </div>
        </div>

        <div class="space-y-6">
          <div class="bg-primary rounded-2xl p-4 md:p-6 shadow-inset" data-onboarding="quick-input">
          <span v-if="currentTab === 'ledger'" data-onboarding="ledger-quick-input-anchor"></span>
            <label class="block text-muted text-sm mb-2">快速输入</label>
            <textarea
              v-model="inputText"
              class="input h-32 md:h-40"
              placeholder="贴上文字或描述，自动按当前分页归类"
            />
            <!-- 按钮区域：手机视图下使用更紧凑的布局 -->
            <div class="mt-3 space-y-3">
              <!-- 第一行：操作按钮（手机视图下使用图标+短文字，桌面视图下使用完整文字） -->
              <div class="flex flex-wrap justify-between gap-2">
                <!-- 左侧按钮组 -->
                <div class="flex flex-wrap gap-2">
                  <label class="btn ghost cursor-pointer text-xs sm:text-sm px-2 sm:px-4 py-2 flex items-center gap-1.5">
                    <span>📷</span>
                    <span class="hidden sm:inline">{{ currentTab === 'ledger' ? '上传图片' : '插入图片' }}</span>
                    <span class="sm:hidden">{{ currentTab === 'ledger' ? '上传' : '图片' }}</span>
                    <input type="file" accept="image/*" :multiple="currentTab === 'note'" @change="handleImageUpload" class="hidden" />
                  </label>
                  <label v-if="currentTab === 'note'" class="btn ghost cursor-pointer text-xs sm:text-sm px-2 sm:px-4 py-2 flex items-center gap-1.5">
                    <span>📎</span>
                    <span class="hidden sm:inline">插入文件</span>
                    <span class="sm:hidden">文件</span>
                    <input type="file" multiple @change="handleFileUpload" class="hidden" />
                  </label>
                </div>
                <!-- 右侧按钮组 -->
                <div class="flex flex-wrap gap-2">
                  <button class="btn ghost text-xs sm:text-sm px-2 sm:px-4 py-2 flex items-center gap-1.5" @click="pasteFromClipboard">
                    <span>📋</span>
                    <span class="hidden sm:inline">粘贴</span>
                  </button>
                  <button class="btn ghost text-xs sm:text-sm px-2 sm:px-4 py-2" @click="clearInput" :disabled="isSubmitting">
                    清空
                  </button>
                </div>
              </div>
              
              <!-- 第二行：主要操作按钮 -->
              <div class="flex gap-2">
                <button 
                  v-if="currentTab === 'note'"
                  class="btn ghost text-xs sm:text-sm px-3 sm:px-4 py-2.5 flex items-center gap-1.5 whitespace-nowrap"
                  @click="router.push('/editor')"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 sm:h-5 sm:w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                  </svg>
                  <span class="hidden sm:inline">打开笔记编辑器</span>
                  <span class="sm:hidden">编辑器</span>
                </button>
                <button 
                  class="btn primary flex-1 text-sm sm:text-base py-2.5" 
                  @click="handleSubmit" 
                  :disabled="isSubmitting"
                >
                  {{ isSubmitting ? "提交中..." : `提交到 ${currentLabel}` }}
                </button>
              </div>
            </div>
            <!-- 记账模式下显示待提交的图片预览 -->
            <div v-if="currentTab === 'ledger' && pendingLedgerImage" class="mt-3 flex items-center gap-3 p-3 bg-surface2 rounded-lg border border-border">
              <img :src="pendingLedgerImagePreview" alt="待提交图片" class="w-20 h-20 object-cover rounded" />
              <div class="flex-1">
                <div class="text-sm text-muted">已选择图片，等待提交</div>
                <div class="text-xs text-muted mt-1">可以在上方输入框中添加备注</div>
              </div>
              <button class="btn ghost text-sm" @click="clearPendingImage">移除</button>
            </div>
            <!-- 已上传的文件列表 -->
          </div>

          <div v-if="currentTab === 'ledger'">
            <div class="flex items-center gap-3">
              <button class="banner-nav" @click="handleBannerPrev">‹</button>
              <div
                class="flex-1 overflow-hidden rounded-2xl bg-surface2 p-1"
                style="touch-action: pan-y;"
                @touchstart="handleBannerTouchStart"
                @touchmove="handleBannerTouchMove"
                @touchend="handleBannerTouchEnd"
                @touchcancel="handleBannerTouchEnd"
              >
                <div class="flex transition-transform duration-500 banner-track" :style="bannerTranslateStyle">
                  <div class="w-full flex-shrink-0 px-1">
                    <LedgerStatsCard @click="router.push('/statistics')" />
                  </div>
                  <div class="w-full flex-shrink-0 px-1">
                    <div
                      class="rounded-xl p-4 cursor-pointer transition-all duration-200 border border-border bg-surface shadow-card hover:shadow-float"
                      @click="router.push('/statistics')"
                    >
                      <div class="flex items-center justify-between mb-3">
                        <div>
                          <h3 class="text-sm font-semibold text-text">月度预算</h3>
                          <p class="text-xs text-muted mt-1">{{ bannerMonthLabel }}</p>
                        </div>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3-.895-3-2s1.343-2 3-2 3 .895 3 2-1.343 2-3 2zm0 0v8m0 0c-2.761 0-5 1.343-5 3h10c0-1.657-2.239-3-5-3z" />
                        </svg>
                      </div>
                      <div v-if="ledgerStatistics" class="h-24 flex flex-col justify-center gap-2">
                        <div v-if="bannerBudgetAmount !== null" class="space-y-1">
                          <div class="text-lg font-semibold text-text">{{ bannerBudgetCurrency }} {{ bannerBudgetAmount.toLocaleString() }}</div>
                          <div class="text-xs" :class="bannerBudgetRemaining >= 0 ? 'text-green-600' : 'text-red-600'">
                            {{ bannerBudgetRemaining >= 0 ? "剩余" : "超出" }} ¥{{ Math.abs(bannerBudgetRemaining).toLocaleString() }}
                          </div>
                          <div class="text-xs text-muted">已用 ¥{{ ledgerStatistics.current_month_total.toLocaleString() }}</div>
                          <div class="h-2 rounded-full bg-border/50 overflow-hidden">
                            <div
                              class="h-full transition-all duration-300"
                              :class="bannerBudgetRemaining >= 0 ? 'bg-green-500' : 'bg-red-500'"
                              :style="{ width: `${bannerBudgetProgress}%` }"
                            ></div>
                          </div>
                        </div>
                        <div v-else class="text-xs text-muted">未设置预算，请前往统计页面设置</div>
                      </div>
                      <div v-else class="h-24 flex items-center text-muted text-sm">加载中...</div>
                      <div class="mt-3 flex items-center justify-between text-xs">
                        <span class="text-muted">查看预算详情</span>
                        <span class="text-blue-500 hover:text-blue-400">查看详情 →</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <button class="banner-nav" @click="handleBannerNext">›</button>
            </div>
            <div class="mt-2 flex items-center justify-center gap-2">
              <button
                class="w-2 h-2 rounded-full"
                :class="bannerIndex === 0 ? 'bg-accent' : 'bg-border'"
                @click="setBannerIndex(0)"
              ></button>
              <button
                class="w-2 h-2 rounded-full"
                :class="bannerIndex === 1 ? 'bg-accent' : 'bg-border'"
                @click="setBannerIndex(1)"
              ></button>
            </div>
          </div>

          <div
            v-if="currentTab === 'ledger'"
            class="rounded-xl p-4 border border-border bg-surface shadow-card hover:shadow-float transition-all duration-200"
            data-onboarding="ledger-note-generator"
          >
            <div class="flex items-center justify-between mb-3">
              <div>
                <h3 class="text-sm font-semibold text-text">记账笔记</h3>
                <p class="text-xs text-muted mt-1">按时间范围自动汇总</p>
              </div>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h8M8 11h8M8 15h5M6 3h9l5 5v13a2 2 0 01-2 2H6a2 2 0 01-2-2V5a2 2 0 012-2z" />
              </svg>
            </div>
            <div class="flex items-center gap-2 mb-3">
              <button
                class="btn ghost text-xs px-3 py-1.5 active:scale-95"
                :class="ledgerNoteRange === 'day' ? '!border-green-500 !text-green-600 !bg-green-50' : ''"
                @click="ledgerNoteRange = 'day'"
              >
                本日
              </button>
              <button
                class="btn ghost text-xs px-3 py-1.5 active:scale-95"
                :class="ledgerNoteRange === 'week' ? '!border-green-500 !text-green-600 !bg-green-50' : ''"
                @click="ledgerNoteRange = 'week'"
              >
                本周
              </button>
              <button
                class="btn ghost text-xs px-3 py-1.5 active:scale-95"
                :class="ledgerNoteRange === 'month' ? '!border-green-500 !text-green-600 !bg-green-50' : ''"
                @click="ledgerNoteRange = 'month'"
              >
                本月
              </button>
            </div>
            <button class="btn primary w-full text-sm py-2" @click="handleGenerateLedgerNote">
              生成记账笔记
            </button>
          </div>

          <!-- 笔记模式：只显示最新笔记 -->
          <div v-if="currentTab === 'note'">
            <div class="flex items-center justify-between mb-2">
              <div class="section-title">最新笔记</div>
              <div class="flex items-center gap-3">
                <router-link
                  :to="{ name: 'notes' }"
                  class="text-sm text-muted hover:text-text underline"
                >
                  查看全部 →
                </router-link>
              </div>
            </div>
            <div v-if="data.notes.length" class="notes-masonry">
              <div
                v-for="note in displayedNotes"
                :key="note.id"
                class="card relative group hover:shadow-float transition-all duration-200 cursor-pointer"
                draggable="true"
                @dragstart="handleNoteDragStart($event, note)"
                @dragend="handleDragEnd"
                @click="handleNoteClick(note.id)"
              >
                <NoteCardContent
                  :note="note"
                  @copy="copyNoteText(note)"
                  @delete="handleDeleteNote(note.id)"
                  @pin="handlePinNote(note.id)"
                />
              </div>
              <!-- 如果笔记超过显示限制，显示省略号卡片 -->
              <router-link
                v-if="remainingNotesCount > 0"
                :to="{ name: 'notes' }"
                class="card card-ellipsis relative group hover:shadow-float transition-all duration-200 cursor-pointer flex items-center justify-center min-h-[200px] border-2 border-dashed"
              >
                <div class="text-center">
                  <div class="text-4xl font-light text-muted mb-2">⋯</div>
                  <div class="text-sm text-muted font-medium">
                    还有 <span class="text-text font-semibold">{{ remainingNotesCount }}</span> 条笔记
                  </div>
                  <div class="text-xs text-muted mt-1">点击查看全部</div>
                </div>
              </router-link>
            </div>
            <p v-else-if="!data.notes.length" class="text-gray-400 text-sm">暂无笔记</p>
          </div>

          <!-- 记账模式：只显示最新记账 -->
          <div v-if="currentTab === 'ledger'">
            <div class="flex items-center justify-between mb-2">
              <div class="section-title">最新记账</div>
              <div class="flex items-center gap-3">
                <button
                  @click="router.push('/ledgers')"
                  class="text-sm text-muted hover:text-text underline"
                >
                  查看全部 →
                </button>
              </div>
            </div>
            <div v-if="data.ledgers.length" class="space-y-4">
              <template v-for="group in groupedLedgers" :key="group.key">
                <!-- 日期分割线 -->
                <div class="flex items-center gap-4 my-4">
                  <div class="flex-1 border-t border-gray-300"></div>
                  <div class="text-sm font-semibold text-gray-500 px-3">{{ group.label }}</div>
                  <div class="flex-1 border-t border-gray-300"></div>
                </div>
                <!-- 该日期的 ledger 列表 -->
                <div class="space-y-3">
                  <div
                    v-for="ledger in group.items"
                    :key="ledger.id"
                    class="card relative group hover:shadow-lg transition-all duration-200"
                    draggable="true"
                    @dragstart="handleLedgerDragStart($event, ledger)"
                    @dragend="handleDragEnd"
                    :class="{ 
                      'opacity-60': ledger.status === 'pending' || ledger.status === 'processing',
                      'border-2 border-blue-300 border-dashed': ledger.status === 'pending' || ledger.status === 'processing'
                    }"
                    @click="handleLedgerClick(ledger.id)"
                  >
                    <!-- Ledger 内容 -->
                    <LedgerCardContent :ledger="ledger" />
                    
                    <!-- 操作按钮（右下角） -->
                    <div class="absolute bottom-2 right-2 flex items-center gap-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                      <button
                        v-if="ledger.status === 'completed'"
                        @click.stop="handleEditLedger(ledger)"
                        class="text-gray-500 hover:text-gray-700 p-1.5 rounded-md hover:bg-gray-50 active:scale-95"
                        title="编辑"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        @click.stop="handleDeleteLedger(ledger.id)"
                        class="text-red-500 hover:text-red-700 p-1.5 rounded-md hover:bg-red-50 active:scale-95"
                        title="删除"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </template>
            </div>
            <p v-else-if="!data.ledgers.length" class="text-gray-400 text-sm">暂无记账</p>
          </div>

          <!-- 待办事项：只在笔记模式下显示 -->
          <div v-if="currentTab === 'note'">
            <div class="flex items-center justify-between mb-2">
              <div class="section-title">待办事项</div>
              <button
                @click="router.push('/todos')"
                class="text-sm text-muted hover:text-text underline"
              >
                查看全部 →
              </button>
            </div>
            <div class="bg-primary rounded-2xl p-4 shadow-inner flex flex-col gap-3" data-onboarding="todo-panel">
              <!--添加待办输入框-->
              <TodoInput />

              <!--待办列表-->
              <TodoList
                :todos="data.todos.filter(t => !t.completed)"
                @toggle="data.toggleTodo"
                @update-title="(id, title) => data.updateTodo(id, { title })"
                @delete="data.removeTodo"
                @delete-group="data.removeTodo"
                @delete-item="data.removeTodo"
                @pin="data.togglePinTodo"
                @add-group-item="(groupId) => data.addTodo('新建待办', groupId)"
                @update-item-title="(id, title) => data.updateTodo(id, { title })"
                @toggle-item="data.toggleTodo"
                :show-completed="false"
                compact
              />
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <AppFooter class="mt-auto" />

  </div>
</template>


<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed, watch } from "vue";
import TabSwitcher from "../components/TabSwitcher.vue";
import LedgerCardContent from "../components/LedgerCardContent.vue";
import LedgerStatsCard from "../components/LedgerStatsCard.vue";
import NoteCardContent from "../components/NoteCardContent.vue";
import TodoList from "../components/TodoList.vue";
import TodoInput from "../components/TodoInput.vue";
import { useUserStore } from "../stores/user";
import { useDataStore } from "../stores/data";
import type { LedgerEntry, LedgerStatistics, Note } from "../stores/data";
import { useToastStore } from "../stores/toast";
import { useConfirmStore } from "../stores/confirm";
import { usePreferencesStore } from "../stores/preferences";
import { useLedgerEditorStore } from "../stores/ledgerEditor";
import { useRouter, useRoute } from "vue-router";
import { toPlainTextFromMarkdown } from "../utils/markdown";
import AppFooter from "../components/AppFooter.vue";

const router = useRouter();
const route = useRoute();

const tabs = [
  { label: "笔记模式", value: "note" },
  { label: "记账模式", value: "ledger" }
];

const parseTabQuery = (value: unknown): "note" | "ledger" | null => {
  if (value === "note" || value === "ledger") return value;
  return null;
};

/**
 * 处理笔记卡片拖拽，写入自定义数据格式。
 */
const handleNoteDragStart = (event: DragEvent, note: Note) => {
  if (!event.dataTransfer) return;
  isDragging.value = true;
  const payload = {
    type: "note",
    id: note.id,
    body_md: note.body_md || "",
  };
  event.dataTransfer.setData("application/x-xmem", JSON.stringify(payload));
  event.dataTransfer.setData("text/plain", note.body_md || "");
  event.dataTransfer.effectAllowed = "copy";
};

/**
 * 处理记账卡片拖拽，写入自定义数据格式。
 */
const handleLedgerDragStart = (event: DragEvent, ledger: LedgerEntry) => {
  if (!event.dataTransfer) return;
  isDragging.value = true;
  const payload = {
    type: "ledger",
    id: ledger.id,
    raw_text: ledger.raw_text || "",
    amount: ledger.amount ?? null,
    category: ledger.category ?? null,
  };
  event.dataTransfer.setData("application/x-xmem", JSON.stringify(payload));
  event.dataTransfer.setData("text/plain", ledger.raw_text || "");
  event.dataTransfer.effectAllowed = "copy";
};

/**
 * 处理拖拽结束，恢复点击行为。
 */
const handleDragEnd = () => {
  isDragging.value = false;
};

const getTabFromRoute = () => {
  const raw = Array.isArray(route.query.tab) ? route.query.tab[0] : route.query.tab;
  return parseTabQuery(raw) ?? "note";
};

const currentTab = computed<"note" | "ledger">({
  get: () => getTabFromRoute(),
  set: (newTab) => {
    const raw = Array.isArray(route.query.tab) ? route.query.tab[0] : route.query.tab;
    const currentQueryTab = parseTabQuery(raw);
    if (currentQueryTab !== newTab) {
      router.replace({ query: { ...route.query, tab: newTab } });
    }
  },
});

/**
 * 同步首页当前 Tab 到全局信号，便于引导流程等待状态。
 */
const syncHomeTabSignal = (tab: "note" | "ledger") => {
  if (typeof window === "undefined") return;
  (window as any).__xmemHomeTab = tab;
};

const inputText = ref("");
watch(
  currentTab,
  (tab) => {
    syncHomeTabSignal(tab);
  },
  { immediate: true }
);
const isDragging = ref(false);

// 从 localStorage 加载快速输入内容
const loadInputTextFromStorage = () => {
  if (typeof window !== "undefined") {
    const saved = localStorage.getItem("quickInputText");
    if (saved) {
      inputText.value = saved;
    }
  }
};

// 保存快速输入内容到 localStorage
const saveInputTextToStorage = () => {
  if (typeof window !== "undefined") {
    localStorage.setItem("quickInputText", inputText.value);
  }
};

// 监听 inputText 变化，自动保存到 localStorage
watch(inputText, () => {
  saveInputTextToStorage();
});
const showSettings = ref(false);
const isSubmitting = ref(false); // 提交状态，防止重复提交
// 记账模式下待提交的图片
const pendingLedgerImage = ref<File | null>(null);
const pendingLedgerImagePreview = ref<string>("");
const ledgerStatistics = ref<LedgerStatistics | null>(null);
const bannerIndex = ref(0);
const bannerTimer = ref<number | null>(null);
const bannerCount = 2;
const ledgerNoteRange = ref<"day" | "week" | "month">("month");

// 轮询相关的状态
const pollingIntervals = ref<Map<number, number>>(new Map()); // ledgerId -> intervalId
const pollingTimeouts = ref<Map<number, number>>(new Map()); // ledgerId -> timeoutId
const POLLING_INTERVAL = 5000; // 5秒
const POLLING_TIMEOUT = 180000; // 3分钟

const user = useUserStore();
const data = useDataStore();
const toast = useToastStore();
const confirm = useConfirmStore();
const preferences = usePreferencesStore();
const ledgerEditor = useLedgerEditorStore();

const currentLabel = computed(() => (currentTab.value === "note" ? "笔记库" : "记账"));

// 响应式窗口宽度
const windowWidth = ref(typeof window !== "undefined" ? window.innerWidth : 1024);

// 根据屏幕尺寸计算应该显示的笔记数量
const maxNotesToShow = computed(() => {
  const width = windowWidth.value;
  if (width < 640) {
    // xs: 移动端小屏，显示 4 条
    return 3;
  } else if (width < 768) {
    // sm: 移动端大屏，显示 6 条
    return 5;
  } else if (width < 1024) {
    // md: 平板，显示 8 条
    return 8;
  } else if (width < 1280) {
    // lg: 桌面小屏，显示 10 条
    return 8;
  } else {
    // xl: 桌面大屏，显示 12 条
    return 11;
  }
});

const bannerTranslateStyle = computed(() => ({
  transform: `translateX(calc(-${bannerIndex.value * 100}% + ${touchDeltaX.value}px))`,
}));

const bannerMonthLabel = computed(() => {
  if (!ledgerStatistics.value) return "";
  return formatMonthLabel(ledgerStatistics.value.current_month);
});

const bannerBudgetAmount = computed(() => ledgerStatistics.value?.budget?.amount ?? null);
const bannerBudgetCurrency = computed(() => ledgerStatistics.value?.budget?.currency ?? "CNY");
const touchStartX = ref(0);
const touchStartY = ref(0);
const touchDeltaX = ref(0);
const isSwipingBanner = ref(false);

const bannerBudgetRemaining = computed(() => {
  if (!ledgerStatistics.value) return 0;
  const budgetCny = ledgerStatistics.value.budget?.amount_cny ?? ledgerStatistics.value.budget?.amount ?? null;
  if (budgetCny === null) return 0;
  return budgetCny - ledgerStatistics.value.current_month_total;
});

const bannerBudgetProgress = computed(() => {
  if (!ledgerStatistics.value) return 0;
  const budgetCny = ledgerStatistics.value.budget?.amount_cny ?? ledgerStatistics.value.budget?.amount ?? 0;
  if (!budgetCny) return 0;
  const progress = (ledgerStatistics.value.current_month_total / budgetCny) * 100;
  return Math.min(100, Math.max(0, progress));
});

// 显示的笔记列表
const displayedNotes = computed(() => {
  return data.notes.slice(0, maxNotesToShow.value);
});

// 剩余的笔记数量
const remainingNotesCount = computed(() => {
  return Math.max(0, data.notes.length - maxNotesToShow.value);
});

// 窗口大小变化监听
const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

/**
 * 格式化月份显示文案。
 */
const formatMonthLabel = (month: string) => {
  const [year, monthValue] = month.split("-");
  return `${year}年${parseInt(monthValue)}月`;
};

/**
 * 获取记账笔记时间范围文案。
 */
const getLedgerNoteRangeLabel = (range: "day" | "week" | "month") => {
  if (range === "day") return "本日";
  if (range === "week") return "本周";
  return "本月";
};

/**
 * 获取日期范围起止时间。
 */
const getLedgerNoteRangeDates = (range: "day" | "week" | "month") => {
  const now = new Date();
  const start = new Date(now);
  const end = new Date(now);
  start.setHours(0, 0, 0, 0);
  end.setHours(0, 0, 0, 0);

  if (range === "week") {
    const day = now.getDay();
    const diffToMonday = (day + 6) % 7;
    start.setDate(now.getDate() - diffToMonday);
    end.setDate(start.getDate() + 6);
  } else if (range === "month") {
    start.setDate(1);
    end.setMonth(now.getMonth() + 1, 0);
  }

  return { start, end };
};

/**
 * 格式化日期为 YYYY-MM-DD。
 */
const formatDateLabel = (date: Date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

/**
 * 生成记账笔记 Markdown 内容。
 */
const buildLedgerNoteMarkdown = (
  range: "day" | "week" | "month",
  statistics: LedgerStatistics
) => {
  const rangeLabel = getLedgerNoteRangeLabel(range);
  const { start, end } = getLedgerNoteRangeDates(range);
  const rangeText = `${formatDateLabel(start)} 至 ${formatDateLabel(end)}`;
  const dailyMap = new Map(statistics.daily_data.map((item) => [item.date, item]));

  const lines: string[] = [];
  lines.push(`# 记账笔记（${rangeLabel}）`);
  lines.push("");
  lines.push(`统计范围：${rangeText}`);
  lines.push("");

  if (range === "month") {
    const monthTotal = statistics.current_month_total || 0;
    const monthCount = statistics.daily_data.reduce((sum, item) => sum + item.count, 0);
    lines.push(`本月总额：¥${monthTotal.toLocaleString()}`);
    lines.push(`本月笔数：${monthCount} 笔`);

    if (statistics.budget) {
      const remaining = statistics.budget.amount - monthTotal;
      const remainingLabel = remaining >= 0 ? "剩余" : "超出";
      lines.push(
        `预算：¥${statistics.budget.amount.toLocaleString()}，${remainingLabel} ¥${Math.abs(remaining).toLocaleString()}`
      );
    }

    const topDays = [...statistics.daily_data]
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 5);

    if (topDays.length) {
      lines.push("");
      lines.push("金额最高的日期：");
      for (const day of topDays) {
        lines.push(`- ${day.date}：¥${day.amount.toLocaleString()}（${day.count} 笔）`);
      }
    }

    if (statistics.ai_summary) {
      lines.push("");
      lines.push("AI 摘要：");
      lines.push(`> ${statistics.ai_summary}`);
    } 
  } else {
    const dates: string[] = [];
    const cursor = new Date(start);
    while (cursor <= end) {
      dates.push(formatDateLabel(cursor));
      cursor.setDate(cursor.getDate() + 1);
    }

    const rangeData = dates.map((date) => {
      const item = dailyMap.get(date);
      return {
        date,
        amount: item?.amount ?? 0,
        count: item?.count ?? 0,
      };
    });

    const totalAmount = rangeData.reduce((sum, item) => sum + item.amount, 0);
    const totalCount = rangeData.reduce((sum, item) => sum + item.count, 0);

    lines.push(`总额：¥${totalAmount.toLocaleString()}`);
    lines.push(`笔数：${totalCount} 笔`);
    lines.push("");
    lines.push(range === "day" ? "当日明细：" : "每日明细：");
    for (const item of rangeData) {
      lines.push(`- ${item.date}：¥${item.amount.toLocaleString()}（${item.count} 笔）`);
    }
  }

  return lines.join("\n");
};

/**
 * 加载记账统计数据用于 Banner 展示。
 */
const loadLedgerStatistics = async () => {
  try {
    ledgerStatistics.value = await data.fetchLedgerStatistics();
  } catch (error: any) {
    console.error("获取记账统计失败:", error);
  }
};

/**
 * 设置 Banner 当前索引。
 */
const setBannerIndex = (index: number) => {
  bannerIndex.value = index;
};

const handleBannerTouchStart = (event: TouchEvent) => {
  const touch = event.touches[0];
  if (!touch) return;
  touchStartX.value = touch.clientX;
  touchStartY.value = touch.clientY;
  touchDeltaX.value = 0;
  isSwipingBanner.value = true;
  stopBannerRotation();
};

const handleBannerTouchMove = (event: TouchEvent) => {
  if (!isSwipingBanner.value) return;
  const touch = event.touches[0];
  if (!touch) return;
  touchDeltaX.value = touch.clientX - touchStartX.value;
};

const handleBannerTouchEnd = () => {
  if (!isSwipingBanner.value) return;
  const threshold = 40;
  if (touchDeltaX.value > threshold) {
    handleBannerPrev();
  } else if (touchDeltaX.value < -threshold) {
    handleBannerNext();
  } else {
    startBannerRotation();
  }
  touchDeltaX.value = 0;
  isSwipingBanner.value = false;
};

/**
 * 生成记账笔记。
 */
const handleGenerateLedgerNote = async () => {
  const rangeLabel = getLedgerNoteRangeLabel(ledgerNoteRange.value);
  toast.info(`记账笔记生成中（${rangeLabel}）`);
  try {
    if (!ledgerStatistics.value) {
      await loadLedgerStatistics();
    }
    if (!ledgerStatistics.value) {
      toast.error("未获取到记账统计数据");
      return;
    }
    const markdown = buildLedgerNoteMarkdown(ledgerNoteRange.value, ledgerStatistics.value);
    const ledgerMonth = ledgerStatistics.value.current_month;
    const aiSummary =
      ledgerNoteRange.value === "month" ? ledgerStatistics.value.ai_summary?.trim() : undefined;
    await data.addNoteWithMD(markdown, {
      is_ledger_note: true,
      ledger_month: ledgerMonth,
      ai_summary: aiSummary || undefined,
    });
    toast.success(`已生成${rangeLabel}记账笔记`);
  } catch (error: any) {
    console.error("生成记账笔记失败:", error);
    toast.error(error.response?.data?.detail || error.message || "生成记账笔记失败");
  }
};

/**
 * 切换到上一张 Banner。
 */
const handleBannerPrev = () => {
  bannerIndex.value = (bannerIndex.value - 1 + bannerCount) % bannerCount;
  startBannerRotation();
};

/**
 * 切换到下一张 Banner。
 */
const handleBannerNext = () => {
  bannerIndex.value = (bannerIndex.value + 1) % bannerCount;
  startBannerRotation();
};

/**
 * 启动 Banner 自动轮播。
 */
const startBannerRotation = () => {
  stopBannerRotation();
  bannerTimer.value = window.setInterval(() => {
    bannerIndex.value = (bannerIndex.value + 1) % bannerCount;
  }, 5000);
};

/**
 * 停止 Banner 自动轮播。
 */
const stopBannerRotation = () => {
  if (bannerTimer.value) {
    clearInterval(bannerTimer.value);
    bannerTimer.value = null;
  }
};

// 监听标签页切换，切换到笔记模式时清空待提交的图片，并保存到localStorage
watch(currentTab, (newTab) => {
  // 切换到笔记模式时清空待提交的图片
  if (newTab === "note") {
    clearPendingImage();
    stopBannerRotation();
  } else {
    loadLedgerStatistics();
    startBannerRotation();
  }
});

onMounted(async () => {
  const raw = Array.isArray(route.query.tab) ? route.query.tab[0] : route.query.tab;
  const currentQueryTab = parseTabQuery(raw);
  if (!currentQueryTab) {
    await router.replace({ query: { ...route.query, tab: "note" } });
  }
  if (user.token) {
    await user.fetchProfile();
    await data.loadAll();
    
    // 检查是否有待处理的 ledger，如果有则开始轮询
    data.ledgers.forEach(ledger => {
      if (ledger.status === "pending" || ledger.status === "processing") {
        startPolling(ledger.id);
  }
});
    if (currentTab.value === "ledger") {
      await loadLedgerStatistics();
      startBannerRotation();
    }
    // 加载快速输入内容
    loadInputTextFromStorage();
  }
  // 监听窗口大小变化
  if (typeof window !== "undefined") {
    window.addEventListener("resize", handleResize);
    // 初始化窗口宽度
    windowWidth.value = window.innerWidth;
  }
});

onUnmounted(() => {
  // 清理所有轮询
  stopAllPolling();
  stopBannerRotation();
  
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", handleResize);
  }
});

// 通用的提交 ledger 函数
const submitLedger = async (text?: string, imageFile?: File) => {
  try {
    const ledger = await data.addLedger(text, imageFile);
    // 如果状态是 pending 或 processing，开始轮询
    if (ledger.status === "pending" || ledger.status === "processing") {
      startPolling(ledger.id);
    }
    toast.success("已提交，正在识别中...");
    clearInput();
    clearPendingImage();
  } catch (error: any) {
    console.error("提交记账失败:", error);
    toast.error(error.response?.data?.detail || error.message || "记账失败");
    // 不重新抛出错误，避免导致调用者卡住
    // 清理状态，确保界面可以继续使用
    clearPendingImage();
    throw error; // 仍然抛出，但调用者应该捕获
  }
};

const handleSubmit = async () => {
  // 防止重复提交
  if (isSubmitting.value) {
    return;
  }
  
  if (currentTab.value === "note") {
    if (!inputText.value.trim()) return;
    isSubmitting.value = true;
    try {
    // 统一使用 body_md 格式
    await data.addNoteWithMD(inputText.value);
      clearInput();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || "笔记提交失败");
    } finally {
      isSubmitting.value = false;
    }
  } else {
    // 记账模式：需要文本或图片至少有一个
    if (!inputText.value.trim() && !pendingLedgerImage.value) {
      toast.warning("请输入文本或上传图片");
      return;
    }
    isSubmitting.value = true;
    try {
      const text = inputText.value.trim() || undefined;
      const imageFile = pendingLedgerImage.value || undefined;
      await submitLedger(text, imageFile);
    } catch (error: any) {
      // submitLedger 已经显示了错误提示，这里只需要确保不会卡住
      console.error("提交记账失败:", error);
    } finally {
      isSubmitting.value = false;
    }
  }
};

const clearInput = () => {
  inputText.value = "";
  // 同时清空 localStorage
  if (typeof window !== "undefined") {
    localStorage.removeItem("quickInputText");
  }
  if (currentTab.value === "ledger") {
    clearPendingImage();
  }
};

const clearPendingImage = () => {
  pendingLedgerImage.value = null;
  pendingLedgerImagePreview.value = "";
};

const handleImageUpload = async (e: Event) => {
  const files = (e.target as HTMLInputElement).files;
  if (!files) return;
  
  const file = Array.from(files)[0]; // 记账模式只支持单张图片
  
  if (currentTab.value === "ledger") {
    // 记账模式：先保存图片到前端，弹出确认对话框
    pendingLedgerImage.value = file;
    // 创建预览
    const reader = new FileReader();
    reader.onload = (e) => {
      pendingLedgerImagePreview.value = e.target?.result as string;
    };
    reader.readAsDataURL(file);
    
    // 弹出确认对话框
    const confirmed = await confirm.show({
      title: "上传图片",
      message: "是否直接提交到记账？",
      confirmText: "是，直接提交",
      cancelText: "否，我要添加备注",
      type: "info"
    });
    
    if (confirmed) {
      // 直接提交，使用输入框中的文本（如果有）
      try {
        const text = inputText.value.trim() || undefined;
        await submitLedger(text, file);
      } catch (error: any) {
        // submitLedger 已经显示了错误提示，这里只需要清理图片
        clearPendingImage();
      }
    }
    // 如果选择"否"，图片已保存到 pendingLedgerImage，等待用户输入备注后点击提交
  } else {
    // 笔记模式：直接上传并插入 markdown
  for (const file of Array.from(files)) {
    try {
      const url = await data.uploadImage(file);
      // 直接在输入框中插入图片 markdown
      const markdown = `![图片](${url})\n`;
      inputText.value = inputText.value ? `${inputText.value}\n${markdown}` : markdown;
    } catch (err: any) {
        toast.error(err.message || "图片上传失败");
      }
    }
  }
  
  // 清空文件输入，以便再次选择同一文件时也能触发 change 事件
  (e.target as HTMLInputElement).value = "";
};

const handleFileUpload = async (e: Event) => {
  const files = (e.target as HTMLInputElement).files;
  if (!files) return;
  
  for (const file of Array.from(files)) {
    try {
      // const apiUrl = (import.meta as any).env?.VITE_API_URL || "/api";
      const fileInfo = await data.uploadFile(file);
      // store 已经处理了 URL 前缀，这里直接使用，避免重复拼接
      const fullUrl = fileInfo.url;
      const markdown = `[${fileInfo.name}](${fullUrl})\n`;
      inputText.value = inputText.value ? `${inputText.value}\n${markdown}` : markdown;
    } catch (err: any) {
      toast.error(err.message || "文件上传失败");
    }
  }
};


const pasteFromClipboard = async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      inputText.value = inputText.value ? `${inputText.value}\n${text}` : text;
    }
  } catch (err) {
    console.error("读取剪切板失败:", err);
    toast.error("无法读取剪切板，请确保已授予剪切板访问权限");
  }
};

// 开始轮询 ledger 状态
const startPolling = (ledgerId: number) => {
  // 清除已存在的轮询（如果存在）
  stopPolling(ledgerId);
  
  let pollCount = 0;
  const maxPolls = POLLING_TIMEOUT / POLLING_INTERVAL; // 3分钟 / 5秒 = 36次
  let completed = false;
  
  const poll = async () => {
    // 如果已完成，不再轮询
    if (completed) return;
    
    try {
      const ledger = await data.fetchLedgerStatus(ledgerId);
      
      // 调试日志（开发环境）
      if (import.meta.env.DEV) {
      }
      
      // 如果已完成或失败，停止轮询
      const status = String(ledger.status).toLowerCase().trim();
      if (status === "completed" || status === "failed") {
        completed = true;
        stopPolling(ledgerId);
        if (status === "completed") {
          toast.success("识别完成");
        } else {
          toast.error("识别失败，请重试");
        }
        return;
      }
      
      // 如果状态仍然是 pending 或 processing，继续轮询
      if (status === "pending" || status === "processing") {
        pollCount++;
        // 如果超过3分钟，停止轮询并提示
        if (pollCount >= maxPolls) {
          completed = true;
          stopPolling(ledgerId);
          toast.warning("识别超时，请稍后刷新查看结果");
          return;
        }
      } else {
        // 状态意外变化（可能是其他状态），停止轮询
        if (import.meta.env.DEV) {
          console.warn(`[轮询] Ledger ${ledgerId} 状态意外: "${ledger.status}"`);
        }
        completed = true;
        stopPolling(ledgerId);
      }
    } catch (error: any) {
      console.error("轮询失败:", error);
      // 轮询失败时不要立即停止，可能只是网络问题
      // 只在连续失败多次后才停止
      pollCount++;
      if (pollCount >= maxPolls) {
        completed = true;
        stopPolling(ledgerId);
      }
    }
  };
  
  // 立即执行第一次轮询
  poll();
  
  // 设置定时轮询
  const intervalId = window.setInterval(poll, POLLING_INTERVAL);
  pollingIntervals.value.set(ledgerId, intervalId);
  
  // 设置超时
  const timeoutId = window.setTimeout(() => {
    if (pollingIntervals.value.has(ledgerId)) {
      completed = true;
      stopPolling(ledgerId);
      toast.warning("识别超时，请稍后刷新查看结果");
    }
  }, POLLING_TIMEOUT);
  pollingTimeouts.value.set(ledgerId, timeoutId);
};

// 停止轮询
const stopPolling = (ledgerId: number) => {
  const intervalId = pollingIntervals.value.get(ledgerId);
  if (intervalId) {
    clearInterval(intervalId);
    pollingIntervals.value.delete(ledgerId);
  }
  
  const timeoutId = pollingTimeouts.value.get(ledgerId);
  if (timeoutId) {
    clearTimeout(timeoutId);
    pollingTimeouts.value.delete(ledgerId);
  }
};

// 停止所有轮询
const stopAllPolling = () => {
  pollingIntervals.value.forEach((intervalId) => {
    clearInterval(intervalId);
  });
  pollingIntervals.value.clear();
  
  pollingTimeouts.value.forEach((timeoutId) => {
    clearTimeout(timeoutId);
  });
  pollingTimeouts.value.clear();
};

const scrollToSection = (type: "notes" | "ledger") => {
  // 简单滚动示意，需结合实际标记
  window.scrollTo({ top: 200, behavior: "smooth" });
};


// 注意：笔记折叠逻辑已移至 NoteCardContent 组件

// 处理笔记点击 - 跳转到查看笔记界面
const handleNoteClick = (noteId: number) => {
  if (isDragging.value) {
    isDragging.value = false;
    return;
  }
  router.push({ name: 'note-view', params: { noteId } });
};


// 删除笔记（快速笔记区域）
const handleDeleteNote = async (noteId: number) => {
  const quickDeleteEnabled = preferences.quickDeleteEnabled;
  
  // 如果快速删除未启用，显示确认对话框
  if (!quickDeleteEnabled) {
    const result = await confirm.show({
      title: "确认删除",
      message: "确定要删除这条笔记吗？此操作不可恢复。",
      confirmText: "删除",
      cancelText: "取消",
      type: "danger",
    });
    
    if (!result) {
      return; // 用户取消删除
    }
  }
  
  // 执行删除
  try {
    await data.removeNote(noteId);
    toast.success("笔记删除成功");
  } catch (error: any) {
    console.error("删除笔记失败:", error);
    toast.error(error.response?.data?.detail || "笔记删除失败，请重试");
  }
};

// 置顶/取消置顶笔记
const handlePinNote = async (noteId: number) => {
  try {
    await data.togglePinNote(noteId);
    toast.success("操作成功");
  } catch (error: any) {
    console.error("置顶操作失败:", error);
    toast.error(error.response?.data?.detail || "操作失败，请重试");
  }
};


// 复制笔记文本（纯文本，不包括markdown格式和图片文件）
const copyNoteText = async (note: { body_md?: string | null }) => {
  const content = note.body_md || "";
  if (!content) return;
  
  const text =
    preferences.noteCopyFormat === "plain"
      ? toPlainTextFromMarkdown(content)
      : content.trim();
  
  try {
    await navigator.clipboard.writeText(text);
    toast.success("已复制到剪贴板");
  } catch (err) {
    console.error("复制失败:", err);
    toast.error("复制失败，请手动复制");
  }
};

// 按日期分组 ledger（只显示前12个）
const groupedLedgers = computed(() => {
  const maxCount = 12;

  const getTimeValue = (ledger: LedgerEntry) => {
    const preferred = ledger.event_time || ledger.created_at;
    const preferredDate = new Date(preferred);
    if (!Number.isNaN(preferredDate.getTime())) return preferred;
    return ledger.created_at;
  };

  const toGroupKey = (timeValue: string) => {
    const d = new Date(timeValue);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const toGroupLabel = (timeValue: string) => {
    return new Date(timeValue).toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const ledgers = [...data.ledgers].sort(
    (a, b) => new Date(getTimeValue(b)).getTime() - new Date(getTimeValue(a)).getTime()
  );

  const groups = new Map<string, { key: string; label: string; sortMs: number; items: LedgerEntry[] }>();
  let count = 0;

  for (const ledger of ledgers) {
    if (count >= maxCount) break;
    const timeValue = getTimeValue(ledger);
    const key = toGroupKey(timeValue);
    const sortMs = new Date(timeValue).getTime();
    const label = toGroupLabel(timeValue);

    const existing = groups.get(key);
    if (!existing) {
      groups.set(key, { key, label, sortMs, items: [ledger] });
    } else {
      existing.items.push(ledger);
      if (sortMs > existing.sortMs) existing.sortMs = sortMs;
    }

    count++;
  }

  const result = Array.from(groups.values()).sort((a, b) => b.sortMs - a.sortMs);
  for (const group of result) {
    group.items.sort((a, b) => new Date(getTimeValue(b)).getTime() - new Date(getTimeValue(a)).getTime());
  }
  return result;
});

const handleLedgerClick = (ledgerId: number) => {
  if (isDragging.value) {
    isDragging.value = false;
    return;
  }
  router.push({ name: 'ledger-view', params: { ledgerId } });
};


const handleEditLedger = (ledger: LedgerEntry) => {
  ledgerEditor.open(ledger);
};

const handleLogout = async () => {
  ledgerEditor.close();
  user.logout();
  await router.replace({
    name: "login",
    query: { redirect: route.fullPath },
  });
};

const handleDeleteLedger = async (ledgerId: number) => {
  const result = await confirm.show({
    title: "确认删除",
    message: "确定要删除这条记账吗？此操作不可恢复。",
    confirmText: "删除",
    cancelText: "取消",
    type: "danger",
  });

  if (result) {
    try {
      await data.removeLedger(ledgerId);
      toast.success("删除成功");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "删除失败");
    }
  }
};

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 9) {
    return "早上好";
  } else if (hour >= 9 && hour < 12) {
    return "上午好";
  } else if (hour >= 12 && hour < 18) {
    return "下午好";
  } else {
    return "晚上好";
  }
};
</script>


<style scoped>
.input {
  @apply w-full rounded-xl border border-border bg-surface px-4 py-3 text-text placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/50 transition-shadow shadow-sm;
}
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-accent text-on-accent shadow-float active:scale-95;
}
.btn.ghost {
  @apply bg-surface text-text border border-border hover:border-border/70;
}
.card {
  @apply bg-surface p-4 rounded-xl shadow-card border border-border;
}
.card-ellipsis {
  background-color: rgb(var(--c-surface));
  border-color: rgb(var(--c-border));
}
.card-ellipsis:hover {
  border-color: rgba(var(--c-border), 0.8);
}
.section-title {
  @apply text-sm font-semibold text-muted mb-2;
}
.banner-nav {
  @apply w-8 h-8 rounded-full flex items-center justify-center text-lg text-text bg-white/40 hover:bg-white/60 border border-border/50 backdrop-blur-sm transition shrink-0;
}
.banner-nav {
  display: inline-flex;
}
@media (max-width: 700px) {
  .banner-nav {
    display: none;
  }
}
.banner-track {
  margin: 0 -0.25rem;
}



/* 网格布局 - 优先水平填充（从左到右填满一行） */
.notes-masonry {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  grid-auto-flow: row; /* 优先水平填充 */
}

@media (min-width: 768px) {
  .notes-masonry {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .notes-masonry {
    grid-template-columns: repeat(3, 1fr);
  }
}

.notes-masonry .card {
  width: 100%;
  max-width: 100%; /* 限制最大宽度 */
  margin-bottom: 0; /* Grid 布局不需要 margin-bottom，使用 gap */
  overflow: hidden; /* 防止内容溢出 */
}



/* Toast 动画 */

/* 自定义滚动条样式 - 极简风格 */
.custom-scrollbar {
  scrollbar-width: thin; /* Firefox */
  scrollbar-color: rgba(156, 163, 175, 0.5) transparent; /* Firefox: 滑块颜色 轨道颜色 */
}

/* Webkit 浏览器 (Chrome, Safari, Edge) */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px; /* 滚动条宽度 */
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent; /* 滚动条轨道背景透明 */
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5); /* 滚动条滑块颜色 - 浅灰色 */
  border-radius: 3px;
  border: none; /* 移除边框 */
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(156, 163, 175, 0.7); /* 悬停时稍深一点 */
}

/* 隐藏滚动条按钮（上下箭头） */
.custom-scrollbar::-webkit-scrollbar-button {
  display: none; /* 不显示上下箭头按钮 */
}
</style>


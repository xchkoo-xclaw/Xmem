<template>
  <div class="min-h-screen bg-bg text-text">
    <header class="w-full max-w-4xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="handleBack()"
          class="btn ghost flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        <div class="text-xl font-bold">查看笔记</div>
      </div>
      <button
        v-if="canEdit"
        @click="handleEdit"
        class="btn primary flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        编辑
      </button>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div v-if="displayedNote" class="bg-surface border border-border rounded-3xl shadow-card p-4 md:p-6 lg:p-8 mx-auto">
        <!-- 笔记内容 -->
        <div class="mb-6 note-preview" @dblclick="handleEdit">
           <MdPreview v-secure-display :modelValue="displayedNote.body_md || ''" :theme="theme.resolvedTheme" />
        </div>

        <!-- 笔记信息 -->
        <div class="border-t border-border pt-4 flex items-center justify-between">
          <div class="text-xs text-muted space-y-1">
            <div>创建时间：{{ formatTime(displayedNote.created_at) }}</div>
            <div v-if="isShareView && shareOwnerName">分享人：{{ shareOwnerName }}</div>
          </div>
          <div class="flex items-center gap-2">
            <div v-if="!isShareView" class="flex items-center gap-2 max-[640px]:hidden">
              <button
                @click="handleShareToggle(!shareEnabled)"
                class="btn ghost text-sm"
                :class="shareEnabled ? 'text-green-500 hover:text-green-600' : 'text-muted hover:text-text'"
                title="切换分享状态"
                aria-label="切换分享状态"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1 max-[420px]:mr-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C9.886 14.534 11.657 15.25 13.5 15.25c2.761 0 5-1.567 5-3.5s-2.239-3.5-5-3.5c-1.843 0-3.614.716-4.816 1.908M15.316 10.658C14.114 9.466 12.343 8.75 10.5 8.75c-2.761 0-5 1.567-5 3.5s2.239 3.5 5 3.5c1.843 0 3.614-.716 4.816-1.908" />
                </svg>
                <span class="max-[420px]:hidden">分享</span>
                <span class="ml-1">{{ shareEnabled ? "公开" : "私密" }}</span>
              </button>
              <div
                v-if="shareEnabled && shareLink"
                class="h-px w-3 bg-border opacity-60 -mx-1"
              ></div>
              <button
                v-if="shareEnabled && shareLink"
                @click="handleCopyShareLink"
                class="btn ghost text-sm"
                title="复制分享链接"
                aria-label="复制分享链接"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1 max-[420px]:mr-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span class="max-[420px]:hidden">复制链接</span>
              </button>
            </div>
            <div v-if="!isShareView && canEdit" class="flex items-center gap-2 max-[640px]:hidden">
              <div class="h-4 w-px bg-border/70"></div>
              <button
                @click="toggleAiPanel"
                class="btn ghost text-sm"
                title="AI 功能"
                aria-label="AI 功能"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1 max-[420px]:mr-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3l2.09 6.26L20 9l-5 3.74L16.18 19 12 15.77 7.82 19 9 12.74 4 9l5.91-.74L12 3z" />
                </svg>
                <span class="max-[420px]:hidden">AI</span>
              </button>
            </div>
            <button
              @click="copyNoteText"
              class="btn ghost text-sm"
              title="复制文本"
              aria-label="复制"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1 max-[420px]:mr-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <span class="max-[420px]:hidden">复制</span>
            </button>
            <div v-if="!isShareView && canEdit" class="relative hidden max-[640px]:inline-flex">
              <button
                @click="toggleMobileActions"
                class="btn ghost text-sm"
                title="更多操作"
                aria-label="更多操作"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6h.01M12 12h.01M12 18h.01" />
                </svg>
              </button>
              <div
                v-if="mobileActionsOpen"
                class="absolute right-0 top-11 z-10 w-44 rounded-xl border border-border bg-surface shadow-float p-1"
              >
                <button
                  @click="handleMobileShareToggle(!shareEnabled)"
                  class="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-surface2"
                >
                  {{ shareEnabled ? "设为私密" : "设为公开" }}
                </button>
                <button
                  v-if="shareEnabled && shareLink"
                  @click="handleMobileCopyShareLink"
                  class="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-surface2"
                >
                  复制分享链接
                </button>
                <button
                  @click="handleMobileToggleAi"
                  class="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-surface2"
                >
                  AI 功能
                </button>
                <button
                  @click="handleMobileDelete"
                  class="w-full text-left px-3 py-2 rounded-lg text-sm text-red-500 hover:text-red-600 hover:bg-surface2"
                >
                  删除笔记
                </button>
              </div>
            </div>
            <button
              v-if="canEdit"
              @click="handleDelete"
              class="btn ghost text-sm text-red-500 hover:text-red-600 border-red-200/70 hover:border-red-300/80 max-[640px]:hidden"
              title="删除笔记"
              aria-label="删除"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1 max-[420px]:mr-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span class="max-[420px]:hidden">删除</span>
            </button>
          </div>
        </div>
        <div
          v-if="aiPanelOpen && !isShareView && canEdit"
          class="mt-4 rounded-2xl border border-border bg-surface2 p-3"
        >
          <div class="text-xs text-muted mb-2">AI 功能</div>
          <div class="grid gap-2">
            <button
              @click="handleAiSummary"
              class="btn ghost w-full text-left text-sm"
              :disabled="aiSummaryLoading"
            >
              <span class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m-6-8h6m-4-6a2 2 0 00-2 2v2H7a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2V6a2 2 0 00-2-2h-4V2a2 2 0 00-2-2z" />
                </svg>
                <span>{{ aiSummaryLoading ? "总结中..." : "AI 总结" }}</span>
              </span>
            </button>
            <button
              @click="handleAiTodos"
              class="btn ghost w-full text-left text-sm"
              :disabled="aiTodosLoading"
            >
              <span class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5h6m-6 7h6m-6 7h6M5 6l1 1 2-2M5 13l1 1 2-2M5 20l1 1 2-2" />
                </svg>
                <span>{{ aiTodosLoading ? "生成中..." : "AI 转待办" }}</span>
              </span>
            </button>
          </div>
        </div>
      </div>
      <div v-else class="bg-surface border border-border rounded-3xl shadow-card p-4 md:p-6 lg:p-8 mx-auto text-center">
        <p class="text-muted text-lg">{{ emptyMessage }}</p>
      </div>
      <transition name="fade-soft">
        <div
          v-if="(aiSummaryLoading || aiSummary) && !isShareView"
          class="bg-surface border border-border rounded-3xl shadow-card p-4 md:p-6 lg:p-8 mx-auto mt-4 relative overflow-hidden group note-preview"
          :class="{ 'ai-loading': aiSummaryLoading }"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="text-sm font-semibold text-text">AI 总结</div>
          </div>
          <div v-if="aiSummaryLoading" class="space-y-2">
            <div class="ai-skeleton-line w-3/4"></div>
            <div class="ai-skeleton-line w-2/3"></div>
            <div class="ai-skeleton-line w-1/2"></div>
          </div>
          <div v-else class="mb-2">
            <MdPreview v-secure-display :modelValue="aiSummary" :theme="theme.resolvedTheme" />
          </div>
          <div v-if="aiSummary" class="absolute bottom-3 left-4 text-[10px] text-muted">
            AI生成
          </div>
          <button
            v-if="aiSummary"
            @click="copyAiSummary"
            class="ai-copy-btn absolute bottom-2 right-3"
            title="复制总结"
            aria-label="复制总结"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>
        </div>
      </transition>
    </main>
    
    <!-- 确认对话框 -->
    <ConfirmDialog
      :visible="confirm.visible"
      :title="confirm.title"
      :message="confirm.message"
      :confirm-text="confirm.confirmText"
      :cancel-text="confirm.cancelText"
      :type="confirm.type"
      @confirm="confirm.confirm()"
      @cancel="confirm.cancel()"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue";
import { MdPreview } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import { useDataStore, type SharedNote } from "../stores/data";
import { useToastStore } from "../stores/toast";
import { useConfirmStore } from "../stores/confirm";
import { usePreferencesStore } from "../stores/preferences";
import { useThemeStore } from "../stores/theme";
import { useUserStore } from "../stores/user";
import ConfirmDialog from "../components/ConfirmDialog.vue";
import { useRouter, useRoute } from "vue-router";
import { toPlainTextFromMarkdown } from "../utils/markdown";

const router = useRouter()
const route = useRoute()

interface Props {
  noteId: number | string | null;
}

const props = defineProps<Props>();


const emit = defineEmits<{
  back: [];
  edit: [];
  deleted: [];
}>();

const data = useDataStore();
const toast = useToastStore();
const confirm = useConfirmStore();
const preferences = usePreferencesStore();
const theme = useThemeStore();
const user = useUserStore();

const note = computed(() => {
  if (!props.noteId) return null;
  const id = Number(props.noteId);
  return data.notes.find(n => n.id === id);
});

const sharedNote = ref<SharedNote | null>(null);
const shareError = ref("");

const isShareView = computed(() => route.name === "share-note");
const shareNoteUuid = computed(() => (route.query["note-uuid"] as string | undefined) ?? "");
const shareUserId = computed(() => (route.query["share-user-id"] as string | undefined) ?? "");

const displayedNote = computed(() => (isShareView.value ? sharedNote.value : note.value));
const canEdit = computed(() => (!isShareView.value ? true : sharedNote.value?.can_edit === true));
const activeNoteId = computed(() => displayedNote.value?.id ?? null);
const shareEnabled = ref(false);
const shareLinkOverride = ref("");
const aiPanelOpen = ref(false);
const mobileActionsOpen = ref(false);
const shareToggleLock = ref(false);
const shareToggleTimer = ref<number | null>(null);
const aiSummary = ref("");
const aiSummaryLoading = ref(false);
const aiTodosLoading = ref(false);
const noteLoading = ref(false);
const shareOwnerName = computed(() => {
  const user = sharedNote.value?.share_user;
  if (!user) return "";
  return user.user_name || user.email;
});
const emptyMessage = computed(() => {
  if (!isShareView.value) return noteLoading.value ? "笔记加载中..." : "笔记不存在";
  return shareError.value || "笔记不存在或未分享";
});

const shareLinkFallback = computed(() => {
  if (!note.value?.share_uuid) return "";
  const userId = user.profile?.id;
  if (!userId) return "";
  return `${window.location.origin}/view-share-note/?note-uuid=${note.value.share_uuid}&share-user-id=${userId}`;
});

const shareLink = computed(() => shareLinkOverride.value || shareLinkFallback.value);

const handleBack = () => {
  if (isShareView.value) {
    router.push({ name: "home" });
    return;
  }
  if (window.history.length > 1) {
    router.back();
    return;
  }
  router.push({ name: "home" });
};

// 格式化时间
const formatTime = (timeStr: string) => {
  const date = new Date(timeStr);
  return date.toLocaleString();
};

/**
 * 加载分享笔记内容。
 */
const loadSharedNote = async () => {
  if (!isShareView.value) return;
  if (!shareNoteUuid.value || !shareUserId.value) {
    sharedNote.value = null;
    shareError.value = "分享链接不完整";
    return;
  }

  try {
    shareError.value = "";
    sharedNote.value = await data.fetchSharedNote(shareNoteUuid.value, shareUserId.value);
  } catch (error: any) {
    sharedNote.value = null;
    shareError.value = error.response?.data?.detail || "笔记不存在或未分享";
  }
};

watch([shareNoteUuid, shareUserId, isShareView], () => {
  if (isShareView.value) {
    loadSharedNote();
  }
}, { immediate: true });

const ensureNoteLoaded = async () => {
  if (isShareView.value) return;
  if (!props.noteId) return;
  if (note.value) return;
  noteLoading.value = true;
  try {
    await data.fetchNotes();
  } finally {
    noteLoading.value = false;
  }
};

onMounted(() => {
  ensureNoteLoaded();
});

watch(() => props.noteId, () => {
  ensureNoteLoaded();
});

watch(note, () => {
  if (!note.value) return;
  shareEnabled.value = !!note.value.is_shared;
  if (!shareEnabled.value) {
    shareLinkOverride.value = "";
  }
  aiSummary.value = note.value.ai_summary || "";
  aiPanelOpen.value = false;
}, { immediate: true });

// 复制笔记文本
const copyNoteText = async () => {
  if (!displayedNote.value || !displayedNote.value.body_md) return;
  
  try {
    const content = displayedNote.value.body_md;
    const text =
      preferences.noteCopyFormat === "plain"
        ? toPlainTextFromMarkdown(content)
        : content.trim();
    await navigator.clipboard.writeText(text);
    toast.success("已复制到剪贴板");
  } catch (err) {
    console.error("复制失败:", err);
    toast.error("复制失败，请手动复制");
  }
};

/**
 * 进入编辑页。
 */
const handleEdit = () => {
  if (!canEdit.value) return;
  if (!activeNoteId.value) return;
  router.push({ name: "editor", params: { noteId: activeNoteId.value } });
};

/**
 * 切换分享状态并同步链接。
 */
const performShareToggle = async (nextValue: boolean) => {
  if (!activeNoteId.value) return;
  if (shareToggleLock.value) return;
  shareToggleLock.value = true;
  shareEnabled.value = nextValue;
  try {
    const shareInfo = await data.toggleNoteShareStatus(Number(activeNoteId.value), nextValue);
    if (shareInfo.is_shared && shareInfo.share_url) {
      const localBase = window.location.origin;
      const fallbackUrl = `${localBase}/view-share-note/?note-uuid=${shareInfo.note_uuid}&share-user-id=${shareInfo.share_user_id}`;
      shareLinkOverride.value = shareInfo.share_url.startsWith(localBase) ? shareInfo.share_url : fallbackUrl;
      await navigator.clipboard.writeText(shareLinkOverride.value);
      toast.success("分享已开启，链接已复制");
    } else {
      shareLinkOverride.value = "";
      toast.success("分享已关闭");
    }
    await data.fetchNotes();
  } catch (error: any) {
    shareEnabled.value = !nextValue;
    toast.error(error.response?.data?.detail || "切换分享状态失败");
  } finally {
    shareToggleLock.value = false;
  }
};

/** 切换分享状态并防抖处理 */
const handleShareToggle = (nextValue: boolean) => {
  if (shareToggleTimer.value !== null) {
    window.clearTimeout(shareToggleTimer.value);
  }
  shareToggleTimer.value = window.setTimeout(() => {
    performShareToggle(nextValue);
    shareToggleTimer.value = null;
  }, 350);
};

const handleCopyShareLink = async () => {
  if (!shareLink.value) return;
  try {
    await navigator.clipboard.writeText(shareLink.value);
    toast.success("分享链接已复制");
  } catch {
    toast.error("复制分享链接失败");
  }
};

/** 切换移动端更多操作菜单 */
const toggleMobileActions = () => {
  mobileActionsOpen.value = !mobileActionsOpen.value;
};

/** 关闭移动端更多操作菜单 */
const closeMobileActions = () => {
  mobileActionsOpen.value = false;
};

/** 移动端切换分享状态 */
const handleMobileShareToggle = async (nextValue: boolean) => {
  closeMobileActions();
  await handleShareToggle(nextValue);
};

/** 移动端复制分享链接 */
const handleMobileCopyShareLink = async () => {
  closeMobileActions();
  await handleCopyShareLink();
};

/** 移动端切换 AI 面板 */
const handleMobileToggleAi = () => {
  closeMobileActions();
  toggleAiPanel();
};

/** 移动端删除笔记 */
const handleMobileDelete = () => {
  closeMobileActions();
  handleDelete();
};

const toggleAiPanel = () => {
  aiPanelOpen.value = !aiPanelOpen.value;
};

const handleAiSummary = async () => {
  if (!activeNoteId.value) return;
  aiSummaryLoading.value = true;
  try {
    const result = await data.generateNoteAiSummary(Number(activeNoteId.value));
    aiSummary.value = result.summary;
    const index = data.notes.findIndex(n => n.id === Number(activeNoteId.value));
    if (index !== -1) {
      data.notes[index] = {
        ...data.notes[index],
        ai_summary: result.summary,
      };
    }
    aiPanelOpen.value = false;
    toast.success("AI 总结已生成");
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "AI 总结失败");
  } finally {
    aiSummaryLoading.value = false;
  }
};

const handleAiTodos = async () => {
  if (!activeNoteId.value) return;
  aiTodosLoading.value = true;
  try {
    const result = await data.generateNoteAiTodos(Number(activeNoteId.value));
    aiPanelOpen.value = false;
    if (result.todos.length === 0) {
      toast.info("未识别到待办");
    } else {
      await data.fetchTodos();
      const group = result.todos.find(t => !t.group_id) || result.todos[0];
      const groupId = group?.id;
      toast.success("AI 待办已生成", 5000, "查看", () => {
        router.push({ name: "todos", query: groupId ? { todoId: String(groupId) } : {} });
      });
    }
  } catch (error: any) {
    toast.error(error.response?.data?.detail || "AI 待办生成失败");
  } finally {
    aiTodosLoading.value = false;
  }
};

const copyAiSummary = async () => {
  if (!aiSummary.value) return;
  try {
    const text =
      preferences.noteCopyFormat === "plain"
        ? toPlainTextFromMarkdown(aiSummary.value)
        : aiSummary.value.trim();
    await navigator.clipboard.writeText(text);
    toast.success("总结已复制");
  } catch (err) {
    console.error("复制失败:", err);
    toast.error("复制失败，请手动复制");
  }
};

// 删除笔记
const handleDelete = () => {
  if (!canEdit.value) return;
  if (!activeNoteId.value) return;
  
  confirm.show({
    title: "删除笔记",
    message: "确定要删除这条笔记吗？此操作无法撤销。",
    confirmText: "删除",
    type: "danger"
  }).then(async (result) => {
    if (result) {
      try {
        await data.removeNote(Number(activeNoteId.value));
        toast.success("笔记删除成功");
        emit("deleted");
        router.back();
      } catch (error: any) {
        console.error("删除笔记失败:", error);
        toast.error(error.response?.data?.detail || "笔记删除失败，请重试");
      }
    }
  });
};
</script>

<style scoped>
/* 修复图片在没有 alt 文本时可能不显示的问题 */
:deep(.md-editor-preview img) {
  display: inline-block;
  max-width: 100%;
  min-height: 20px; /* 确保即使加载失败也有高度 */
  background-color: transparent;
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

.fade-soft-enter-active,
.fade-soft-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-soft-enter-from,
.fade-soft-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.ai-skeleton-line {
  @apply h-3 rounded-full bg-surface2;
}

.ai-loading {
  border-color: rgb(255, 90, 180);
  box-shadow: 0 0 18px rgba(255, 90, 180, 0.4);
  animation: ai-rgb-pulse 2.4s ease-in-out infinite;
}

.note-preview :deep(.md-editor-preview-wrapper),
.note-preview :deep(.md-editor-preview),
.note-preview :deep(.md-editor-preview .md-editor-v-5-preview),
.note-preview :deep(.md-editor-v-5-preview),
.note-preview :deep(.md-editor-v-5),
.note-preview :deep(.md-editor-v-5-content) {
  background-color: rgb(var(--c-surface));
  color: rgb(var(--c-text));
}

.ai-copy-btn {
  @apply p-1 rounded-md text-muted transition-all opacity-0;
}

.ai-copy-btn svg {
  @apply h-3.5 w-3.5;
}

.group:hover .ai-copy-btn {
  @apply text-text opacity-100;
}

@media (hover: none) {
  .ai-copy-btn {
    @apply text-text opacity-100;
  }
}

@keyframes ai-rgb-pulse {
  0% {
    border-color: rgb(255, 90, 180);
    box-shadow: 0 0 18px rgba(255, 90, 180, 0.45);
  }
  33% {
    border-color: rgb(90, 170, 255);
    box-shadow: 0 0 18px rgba(90, 170, 255, 0.45);
  }
  66% {
    border-color: rgb(120, 255, 150);
    box-shadow: 0 0 18px rgba(120, 255, 150, 0.45);
  }
  100% {
    border-color: rgb(255, 90, 180);
    box-shadow: 0 0 18px rgba(255, 90, 180, 0.45);
  }
}
</style>

<template>
  <div class="min-h-screen bg-bg text-text">
    <header class="w-full max-w-4xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="router.push('/')"
          class="btn ghost flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          <span class="max-[450px]:hidden">返回</span>
        </button>
        <div class="text-xl font-bold">笔记库</div>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="router.push('/notes/export')"
          class="btn ghost flex items-center gap-2"
          data-onboarding="notes-export"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v10m0 0l3-3m-3 3l-3-3m-6 7h12" />
          </svg>
          <span class="max-[450px]:hidden">导出</span>
        </button>
        <button
          @click="router.push('/editor')"
          class="btn primary flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span class="max-[450px]:hidden">添加新笔记</span>
        </button>
      </div>
    </header>

    <main class="w-full max-w-4xl mx-auto px-4 pb-20">
      <div class="bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8">
        <!-- 搜索框 -->
        <div class="mb-6">
          <div class="relative">
            <input
              v-model="searchQuery"
              @input="handleSearch"
              type="text"
              placeholder="搜索笔记..."
              class="w-full rounded-xl border border-border bg-surface !pl-11 pr-10 py-3 text-text placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/50 transition-shadow shadow-sm"
              data-onboarding="notes-search"
            />
            <!-- 搜索图标（始终显示） -->
            <div class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none flex items-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 text-muted"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <!-- 清除按钮（有文本时显示） -->
            <button
              v-if="searchQuery"
              @click="clearSearch"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-text"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 搜索状态提示 -->
        <div v-if="isSearching" class="mb-4 text-center text-muted text-sm">
          搜索中...
        </div>


        <!-- 笔记列表 -->
        <div v-if="!isSearching && data.notes.length" class="notes-masonry">
          <div
            v-for="note in data.notes"
            :key="note.id"
            class="card relative group hover:shadow-float transition-all duration-200 cursor-pointer"
            draggable="true"
            @dragstart="handleNoteDragStart($event, note)"
            @dragend="handleDragEnd"
            @click="handleNoteClick(note.id)"
          >
            <NoteCardContent
              :note="note"
              :search-query="searchQuery"
              @copy="copyNoteText(note)"
              @delete="handleDeleteNote(note.id)"
              @pin="handlePinNote(note.id)"
              @edit="$emit('edit-note', note.id)"
            />
        </div>
        </div>
        <div v-else-if="!isSearching" class="text-center py-12">
          <p class="text-muted text-lg">{{ searchQuery ? '没有找到匹配的笔记' : '还没有笔记' }}</p>
          <p v-if="!searchQuery" class="text-muted text-sm mt-2">在上方输入框中添加你的第一条笔记吧</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useDataStore } from "../stores/data";
import type { Note } from "../stores/data";
import { useToastStore } from "../stores/toast";
import { usePreferencesStore } from "../stores/preferences";
import NoteCardContent from "../components/NoteCardContent.vue";
import { useRouter } from "vue-router";
import { toPlainTextFromMarkdown } from "../utils/markdown";

const router = useRouter();

const data = useDataStore();
const toast = useToastStore();
const preferences = usePreferencesStore();
const searchQuery = ref("");
const isSearching = ref(false);
const isDragging = ref(false);

// 处理笔记点击
const handleNoteClick = (noteId: number) => {
  if (isDragging.value) {
    isDragging.value = false;
    return;
  }
  router.push({ name: 'note-view', params: { noteId } });
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
 * 处理拖拽结束，恢复点击行为。
 */
const handleDragEnd = () => {
  isDragging.value = false;
};

// 搜索处理（防抖）
let searchTimeout: number | null = null;
const handleSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  
  searchTimeout = window.setTimeout(async () => {
    isSearching.value = true;
    try {
      const query = searchQuery.value.trim();
      // 明确传递搜索参数：如果有内容就传递，否则传递 undefined
      if (query) {
        await data.fetchNotes(query);
      } else {
        // 如果搜索框为空，加载所有笔记
        await data.fetchNotes();
      }
    } catch (error) {
      console.error('搜索失败:', error);
    } finally {
      isSearching.value = false;
    }
  }, 300); // 300ms 防抖
};

// 清除搜索
const clearSearch = async () => {
  searchQuery.value = "";
  isSearching.value = true;
  try {
    await data.fetchNotes();
  } finally {
    isSearching.value = false;
  }
};

// 组件挂载时加载笔记
onMounted(async () => {
  // 如果 store 中没有笔记，或者有搜索关键词但 store 中可能不是搜索结果，则加载
  if (data.notes.length === 0 || searchQuery.value) {
    await data.fetchNotes();
  }
});

// 注意：笔记折叠逻辑已移至 NoteCardContent 组件

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

// 删除笔记
const handleDeleteNote = async (noteId: number) => {
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

/* 网格布局 */
.notes-masonry {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  grid-auto-flow: row;
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
  max-width: 100%;
  margin-bottom: 0;
  overflow: hidden;
}


</style>

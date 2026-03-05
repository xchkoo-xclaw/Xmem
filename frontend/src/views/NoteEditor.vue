<template>
  <div class="min-h-screen bg-bg text-text">
    <header class="w-full max-w-4xl md:max-w-7xl mx-auto px-4 pt-8 pb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="handleBack"
          class="btn ghost flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        <div class="text-xl font-bold">{{ props.noteId ? '编辑笔记' : '添加新笔记' }}</div>
      </div>
      
      <div class="flex items-center gap-2">
        <button
          v-if="isMobileViewportActive"
          @click="togglePreviewMode"
          class="btn ghost flex items-center gap-2"
        >
          {{ previewToggleLabel }}
        </button>
        <button
          @click="handleSave"
          class="btn ghost flex items-center gap-2"
          :disabled="!content.trim() || saving"
        >
          {{ saving ? "保存中..." : "保存" }}
        </button>
      </div>
    </header>

    <main class="w-full max-w-4xl md:max-w-7xl mx-auto px-4 pb-20">
      <div
        ref="cardRef"
        class="note-editor-card bg-surface border border-border rounded-3xl shadow-card p-6 md:p-8"
        :class="mobileEditorClass"
      >
        <MdEditor  
          v-secure-display
          v-model="content" 
          @onUploadImg="onUploadImg"
          class="min-h-[600px] rounded-xl border border-border"
          :toolbars="isMobileViewportActive ? toolbarsMobile : toolbarsDesktop"
          :toolbarsExclude="['github']"
          :theme="theme.resolvedTheme"
        >
          <template #defToolbars>
            <NormalToolbar title="插入文件" @click="triggerFileUpload">
              <template #trigger>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </template>
            </NormalToolbar>
          </template>
        </MdEditor>
        <!-- 隐藏的文件输入框 -->
        <input ref="fileInput" type="file" multiple @change="handleFileUpload" class="hidden" />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from "vue";
import { useRouter } from "vue-router";
import { MdEditor, NormalToolbar, type ToolbarNames } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import { useDataStore } from "../stores/data";
import { useToastStore } from "../stores/toast";
import { useThemeStore } from "../stores/theme";

interface Props {
  noteId?: number | null;
}

const props = withDefaults(defineProps<Props>(), {
  noteId: null
});


const router = useRouter();
const data = useDataStore();
const toast = useToastStore();
const theme = useThemeStore();
const handleBack = () => {
  if (window.history.length > 1) {
    router.back();
    return;
  }
  router.push({ name: "notes" });
};
const content = ref("");
const saving = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const cardRef = ref<HTMLElement | null>(null);
const resizeRaf = ref<number | null>(null);
const isMobileViewportActive = ref(false);
const isMobilePreviewMode = ref(false);

// 自定义工具栏配置
const toolbarsDesktop: ToolbarNames[] = [
  'bold',
  'underline',
  'italic',
  '-',
  'title',
  'strikeThrough',
  'sub',
  'sup',
  'quote',
  'unorderedList',
  'orderedList',
  'task',
  '-',
  'codeRow',
  'code',
  'link',
  'image',
  0, // 自定义工具栏位置：上传文件
  'table',
  'mermaid',
  'katex',
  '-',
  'revoke',
  'next',
  '=',
  'preview',
  'pageFullscreen',
  'fullscreen',
  'catalog',
];
const toolbarsMobile: ToolbarNames[] = [
  'bold',
  'underline',
  'italic',
  '-',
  'title',
  'strikeThrough',
  'sub',
  'sup',
  'quote',
  'unorderedList',
  'orderedList',
  'task',
  '-',
  'codeRow',
  'code',
  'link',
  'image',
  0,
  'table',
  'mermaid',
  'katex',
  '-',
  'revoke',
  'next',
  '=',
  'pageFullscreen',
  'fullscreen',
  'catalog',
];

/**
 * 判断当前窗口是否为手机端视口尺寸
 */
const isMobileViewport = () => {
  if (typeof window === "undefined") return false;
  return window.innerWidth <= 700;
};

const previewToggleLabel = computed(() => (isMobilePreviewMode.value ? "输入" : "预览"));
const mobileEditorClass = computed(() => {
  if (!isMobileViewportActive.value) return "";
  return isMobilePreviewMode.value ? "mobile-preview-only" : "mobile-input-only";
});

/**
 * 移动端默认关闭预览面板，避免左右分屏
 */
const applyMobilePreviewDefault = async () => {
  if (!isMobileViewport()) return;
  isMobilePreviewMode.value = false;
  await nextTick();
};

/**
 * 同步视口尺寸与移动端模式状态
 */
const updateViewportState = () => {
  if (typeof window === "undefined") return;
  const next = isMobileViewport();
  if (next === isMobileViewportActive.value) return;
  isMobileViewportActive.value = next;
  if (next) {
    isMobilePreviewMode.value = false;
    nextTick(() => {
      scheduleEditorPaneHeight();
    });
  }
};

/**
 * 切换移动端预览与输入模式
 */
const togglePreviewMode = () => {
  const next = !isMobilePreviewMode.value;
  isMobilePreviewMode.value = next;
  scheduleEditorPaneHeight();
};

/**
 * 计算上下布局时的面板与卡片高度
 */
const updateEditorPaneHeight = () => {
  if (!cardRef.value) return;
  const scroller = cardRef.value.querySelector(".md-editor-input .cm-scroller") as HTMLElement | null;
  if (!scroller) return;
  const rawHeight = Math.ceil(scroller.scrollHeight || scroller.clientHeight || 0);
  const paneHeight = Math.min(1200, rawHeight > 0 ? rawHeight : 600);
  const totalHeight = isMobileViewportActive.value ? paneHeight : Math.min(2400, paneHeight * 2);
  cardRef.value.style.setProperty("--note-editor-pane-height", `${paneHeight}px`);
  cardRef.value.style.setProperty("--note-editor-total-height", `${totalHeight}px`);
};

/**
 * 调度面板高度刷新
 */
const scheduleEditorPaneHeight = () => {
  if (typeof window === "undefined") return;
  if (resizeRaf.value !== null) {
    cancelAnimationFrame(resizeRaf.value);
  }
  resizeRaf.value = requestAnimationFrame(() => {
    resizeRaf.value = null;
    updateEditorPaneHeight();
  });
};

// 触发文件选择
const triggerFileUpload = () => {
  fileInput.value?.click();
};

// 处理文件上传
const handleFileUpload = async (e: Event) => {
  const files = (e.target as HTMLInputElement).files;
  if (!files || files.length === 0) return;
  
  for (const file of Array.from(files)) {
    try {
      const fileInfo = await data.uploadFile(file);
      // 插入文件链接到 Markdown 内容
      const fileLink = `[${fileInfo.name}](${fileInfo.url})`;
      
      // 在光标位置插入（如果支持）或者追加
      // 这里简单追加或插入到最后，MdEditor 提供了 insert 方法但我们需要 ref
      // 简单起见，我们直接追加到末尾，或者尝试寻找 better way
      // MdEditor 的 modelValue 是双向绑定的，直接修改 content 即可
      // 但最好是插入到光标处。MdEditor 实例 exposed insert 方法
      // 暂时追加到新行
      content.value = content.value ? `${content.value}\n${fileLink}` : fileLink;
      
    } catch (err: any) {
      toast.error(err.message || "文件上传失败");
    }
  }
  
  // 清空文件输入
  (e.target as HTMLInputElement).value = "";
};

// 处理图片上传
const onUploadImg = async (files: File[], callback: (urls: string[]) => void) => {
  const urls: string[] = [];
  for (const file of files) {
    try {
      const url = await data.uploadImage(file);
      urls.push(url);
    } catch (err: any) {
      toast.error(err.message || "图片上传失败");
    }
  }
  callback(urls);
};

// 加载笔记内容（编辑模式）
const loadNoteContent = async () => {
  if (!props.noteId) {
    // 新建模式：从 localStorage 加载快速输入内容
    if (typeof window !== "undefined") {
      const quickInputText = localStorage.getItem("quickInputText");
      if (quickInputText) {
        content.value = quickInputText;
        // 加载后清空 localStorage 中的快速输入内容
        localStorage.removeItem("quickInputText");
      } else {
        content.value = "";
      }
    } else {
      content.value = "";
    }
    return;
  }

  try {
    // 确保笔记列表已加载
    if (data.notes.length === 0) {
      await data.fetchNotes();
    }

    // 查找要编辑的笔记
    const note = data.notes.find(n => n.id === props.noteId);
    if (note) {
      // 加载笔记内容（编辑模式，不从快速输入加载）
      content.value = note.body_md || "";
    } else {
      // 笔记不存在，清空内容
      content.value = "";
    }
  } catch (err: any) {
    console.error("加载笔记内容失败:", err);
    // 如果加载失败，至少清空编辑器
    content.value = "";
  }
};

// 组件挂载时加载笔记内容
onMounted(() => {
  loadNoteContent();
  updateViewportState();
  applyMobilePreviewDefault();
  scheduleEditorPaneHeight();
  window.addEventListener("resize", handleResize);
});

// 监听 noteId 变化，重新加载内容
watch(() => props.noteId, () => {
  loadNoteContent();
  scheduleEditorPaneHeight();
});

watch(content, () => {
  scheduleEditorPaneHeight();
}, { flush: "post" });

/**
 * 处理窗口尺寸变化
 */
const handleResize = () => {
  updateViewportState();
  scheduleEditorPaneHeight();
};

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  if (resizeRaf.value !== null) {
    cancelAnimationFrame(resizeRaf.value);
  }
});

// 保存笔记
const handleSave = async () => {
  // 检查内容是否为空
  if (!content.value.trim()) return;
  
  saving.value = true;
  try {
    if (props.noteId) {
      const id = Number(props.noteId);
      await data.updateNote(id, content.value);
      toast.success("保存成功");
    } else {
      await data.addNoteWithMD(content.value);
      toast.success("创建成功");
      // 清除快速输入缓存
      if (typeof window !== "undefined") {
        localStorage.removeItem("quickInputText");
      }
    }
    router.back();
  } catch (err: any) {
    toast.error(err.message || "保存失败");
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
.btn {
  @apply px-4 py-2 rounded-xl font-semibold transition-all duration-150;
}
.btn.primary {
  @apply bg-accent text-on-accent shadow-float active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed;
}
.btn.ghost {
  @apply bg-surface text-text border border-border hover:border-border/70 disabled:opacity-50 disabled:cursor-not-allowed;
}

:deep(.md-editor),
:deep(.md-editor-toolbar),
:deep(.md-editor-input .cm-editor),
:deep(.md-editor-input .cm-content),
:deep(.md-editor-v-5) {
  background-color: rgb(var(--c-surface));
  color: rgb(var(--c-text));
}

:deep(.md-editor-input),
:deep(.md-editor-input-wrapper),
:deep(.md-editor-preview),
:deep(.md-editor-preview-wrapper),
:deep(.md-editor-v-5-preview),
:deep(.md-editor-v-5-content) {
  background-color: rgb(var(--c-surface-2));
  color: rgb(var(--c-text));
}

:deep(.md-editor-input .cm-scroller),
:deep(.cm-scroller) {
  background-color: rgb(var(--c-surface-2));
  color: rgb(var(--c-text));
}

@media (max-width: 1024px) {
  .note-editor-card {
    height: var(--note-editor-total-height, 2400px);
    max-height: 2400px;
    box-sizing: border-box;
  }
  :deep(.md-editor) {
    display: block !important;
    height: 100% !important;
    min-height: 0 !important;
  }
  :deep(.md-editor-content) {
    display: block !important;
    flex-direction: column !important;
    align-items: stretch;
    width: 100% !important;
    max-width: 100% !important;
    height: 100% !important;
    overflow: hidden !important;
  }
  :deep(.md-editor-content-wrapper) {
    display: block !important;
    width: 100% !important;
    max-width: 100% !important;
  }
  :deep(.md-editor-content-wrapper > *) {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    display: block !important;
    position: static !important;
    float: none !important;
  }
  :deep(.md-editor-input),
  :deep(.md-editor-preview) {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    display: block !important;
    float: none !important;
    left: auto !important;
    right: auto !important;
  }
  :deep(.md-editor-input-wrapper),
  :deep(.md-editor-preview-wrapper) {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    flex: 0 0 auto !important;
    display: block !important;
    position: static !important;
    float: none !important;
    height: var(--note-editor-pane-height, 1200px) !important;
    max-height: 1200px !important;
    overflow: hidden !important;
  }
  :deep(.md-editor-input),
  :deep(.md-editor-preview) {
    height: 100% !important;
    overflow: auto !important;
  }
  :deep(.md-editor-input .cm-editor),
  :deep(.md-editor-input .cm-scroller),
  :deep(.md-editor-preview .md-editor-v-5-preview) {
    height: 100% !important;
    overflow: auto !important;
  }
  :deep(.md-editor-resize),
  :deep(.md-editor-split) {
    display: none !important;
  }
  :deep(.md-editor-resize-operate) {
    display: none !important;
  }
  :deep(.md-editor-input-wrapper) {
    order: 1;
  }
  :deep(.md-editor-preview-wrapper) {
    order: 2;
  }
  :deep(.md-editor-preview-wrapper) {
    border-left: 0;
    border-top: 1px solid rgb(var(--c-border));
  }
}

@media (max-width: 700px) {
  .note-editor-card {
    height: var(--note-editor-pane-height, 1200px);
    max-height: 1200px;
  }
  .note-editor-card.mobile-input-only :deep(.md-editor-preview-wrapper),
  .note-editor-card.mobile-input-only :deep(.md-editor-preview) {
    display: none !important;
  }
  .note-editor-card.mobile-preview-only :deep(.md-editor-input-wrapper),
  .note-editor-card.mobile-preview-only :deep(.md-editor-input) {
    display: none !important;
  }
}
</style>

<template>
  <div
    class="flex items-center justify-between px-4 py-3 rounded-xl shadow-card min-h-[44px] group border relative"
    :class="todo.is_pinned ? 'bg-yellow-500/10 border-yellow-500/50' : 'bg-surface border-border'"
  >
    <div class="flex items-center gap-3 flex-1 min-w-0">
      <input 
        type="checkbox" 
        :checked="todo.completed" 
        @change="$emit('toggle', todo.id)" 
        class="flex-shrink-0 cursor-pointer"
      />
      <span v-if="todo.is_ai_generated" class="text-muted flex-shrink-0" title="AI生成">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3l1.8 4.8L19 9l-4.2 2.7L16 16l-4-2.6L8 16l1.2-4.3L5 9l5.2-1.2L12 3z" />
        </svg>
      </span>
      
      <!-- 置顶图标（始终显示） -->
      <span v-if="todo.is_pinned" class="text-yellow-500 flex-shrink-0" title="已置顶">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
      </span>
      
      <textarea
        v-model="editTitle"
        @blur="finishEdit"
        @keydown.enter.prevent="finishEdit"
        @keydown.esc="cancelEdit"
        @input="handleTitleInput"
        ref="editInputRef"
        :class="{ 'line-through text-muted': todo.completed }"
        class="flex-1 text-sm bg-transparent border-none outline-none px-0 py-0 cursor-text focus:ring-0 resize-none whitespace-pre-wrap break-words"
        :readonly="todo.completed"
        rows="1"
      ></textarea>
    </div>
    <div class="flex items-center gap-2">
      <div class="hidden sm:flex items-center gap-2 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
        <button
          @click.stop="copyItem"
          class="text-muted hover:text-text p-1.5 rounded-md hover:bg-surface2 active:scale-95"
          title="复制待办"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
        <button
          v-if="!todo.completed"
          @click.stop="$emit('pin', todo.id)"
          class="p-1.5 rounded-md active:scale-95 transition-colors"
          :class="todo.is_pinned ? 'text-yellow-500 hover:text-yellow-400 hover:bg-yellow-500/10' : 'text-muted hover:text-text hover:bg-surface2'"
          :title="todo.is_pinned ? '取消置顶' : '置顶'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" :fill="todo.is_pinned ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </button>
        <button 
          class="text-red-500 hover:text-red-400 p-1.5 rounded-md hover:bg-red-500/10 active:scale-95 transition-opacity flex-shrink-0"
          @click="$emit('delete', todo.id)"
          title="删除待办"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
      <div ref="mobileMenuRef" class="relative sm:hidden">
        <button
          class="text-muted hover:text-text px-2 py-1.5 rounded-md border border-border bg-surface2 active:scale-95"
          @click.stop="toggleMobileActions"
        >
          {{ mobileActionsOpen ? ">" : "…" }}
        </button>
        <transition name="fade">
          <div
            v-if="mobileActionsOpen"
            class="absolute right-0 mt-2 w-32 rounded-xl border border-border bg-surface shadow-float p-2 flex flex-col gap-1 z-10"
          >
            <button
              @click.stop="handleMobileCopy"
              class="text-left text-sm px-2 py-1.5 rounded-md hover:bg-surface2"
            >
              复制
            </button>
            <button
              v-if="!todo.completed"
              @click.stop="handleMobilePin"
              class="text-left text-sm px-2 py-1.5 rounded-md hover:bg-surface2"
            >
              {{ todo.is_pinned ? "取消置顶" : "置顶" }}
            </button>
            <button
              @click.stop="handleMobileDelete"
              class="text-left text-sm px-2 py-1.5 rounded-md hover:bg-surface2 text-red-500"
            >
              删除
            </button>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from "vue";
import type { Todo } from "../stores/data";
import { useToastStore } from "../stores/toast";

const props = defineProps<{
  todo: Todo;
}>();

const emit = defineEmits<{
  toggle: [id: number];
  "update-title": [id: number, title: string];
  delete: [id: number];
  pin: [id: number];
}>();

const editTitle = ref(props.todo.title);
const editInputRef = ref<HTMLTextAreaElement | null>(null);
const toast = useToastStore();
const mobileActionsOpen = ref(false);
const mobileMenuRef = ref<HTMLElement | null>(null);
const mobileMenuId = computed(() => `todo-item-${props.todo.id}`);

// 监听 todo.title 的变化
watch(() => props.todo.title, (newTitle) => {
  editTitle.value = newTitle;
  nextTick(() => {
    resizeEditTextarea();
  });
});

const finishEdit = () => {
  if (props.todo.completed) return; // 已完成的不能编辑
  if (editTitle.value.trim() && editTitle.value !== props.todo.title) {
    emit("update-title", props.todo.id, editTitle.value.trim());
  } else {
    // 如果内容为空或未改变，恢复原值
    editTitle.value = props.todo.title;
  }
};

const cancelEdit = () => {
  editTitle.value = props.todo.title;
};

onMounted(() => {
  editTitle.value = props.todo.title;
  document.addEventListener("click", handleDocumentClick, true);
  window.addEventListener("todo-mobile-menu-open", handleOtherMenuOpen as EventListener);
  window.addEventListener("resize", handleViewportResize);
  nextTick(() => {
    resizeEditTextarea();
  });
});

onUnmounted(() => {
  document.removeEventListener("click", handleDocumentClick, true);
  window.removeEventListener("todo-mobile-menu-open", handleOtherMenuOpen as EventListener);
  window.removeEventListener("resize", handleViewportResize);
});

/**
 * 切换移动端更多操作菜单。
 */
const toggleMobileActions = () => {
  const nextValue = !mobileActionsOpen.value;
  mobileActionsOpen.value = nextValue;
  if (nextValue) {
    announceMenuOpen();
  }
};

/**
 * 关闭移动端更多操作菜单。
 */
const closeMobileActions = () => {
  mobileActionsOpen.value = false;
};

/**
 * 自动调整待办输入框高度以适配内容。
 */
const resizeEditTextarea = () => {
  const el = editInputRef.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight}px`;
};

/**
 * 处理待办输入变化时的高度更新。
 */
const handleTitleInput = () => {
  resizeEditTextarea();
};

/**
 * 处理视口变化时的高度更新。
 */
const handleViewportResize = () => {
  resizeEditTextarea();
};

const copyItem = async () => {
  const text = (props.todo.title || "").trim();
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    toast.success("待办已复制");
  } catch {
    toast.error("复制失败，请重试");
  }
};

/**
 * 处理点击空白关闭菜单。
 */
const handleDocumentClick = (event: MouseEvent) => {
  if (!mobileActionsOpen.value) return;
  const target = event.target as Node | null;
  if (!target) return;
  if (mobileMenuRef.value && mobileMenuRef.value.contains(target)) return;
  closeMobileActions();
};

/**
 * 通知其它菜单关闭。
 */
const announceMenuOpen = () => {
  window.dispatchEvent(new CustomEvent("todo-mobile-menu-open", { detail: { id: mobileMenuId.value } }));
};

/**
 * 响应其它菜单开启事件。
 */
const handleOtherMenuOpen = (event: CustomEvent<{ id: string }>) => {
  if (event.detail.id === mobileMenuId.value) return;
  closeMobileActions();
};

/**
 * 移动端复制待办。
 */
const handleMobileCopy = async () => {
  closeMobileActions();
  await copyItem();
};

/**
 * 移动端切换置顶状态。
 */
const handleMobilePin = () => {
  closeMobileActions();
  emit("pin", props.todo.id);
};

/**
 * 移动端删除待办。
 */
const handleMobileDelete = () => {
  closeMobileActions();
  emit("delete", props.todo.id);
};
</script>

<style scoped>
/* 确保输入框没有黑边 */
input[type="text"],
textarea {
  @apply border-border;
}
</style>

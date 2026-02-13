<template>
  <div
    class="rounded-xl shadow-card border relative"
    :class="[
      todo.is_pinned ? 'bg-yellow-500/10 border-yellow-500/50' : 'bg-surface border-border',
      mobileActionsOpen || activeItemMenuId !== null ? 'overflow-visible' : 'overflow-hidden'
    ]"
  >
    <!-- 组标题栏 -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-border group" :class="todo.is_pinned ? 'bg-yellow-500/10' : 'bg-surface'">
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
        
        <input
          v-model="editTitle"
          @blur="finishEditTitle"
          @keydown.enter="finishEditTitle"
          @keydown.esc="cancelEditTitle"
          ref="titleInputRef"
          :class="{ 'line-through text-muted': todo.completed }"
          :readonly="todo.completed"
          class="flex-1 text-sm font-medium bg-transparent border-none outline-none px-0 py-0 cursor-text focus:ring-0"
        />
      </div>
      
      <!-- 操作按钮 -->
      <div class="flex items-center gap-2">
        <div class="hidden sm:flex items-center gap-2 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
          <button
            @click="isCollapsed = !isCollapsed"
            class="flex-shrink-0 text-muted hover:text-text p-1.5 rounded-md hover:bg-surface2 transition-transform"
            :class="{ 'rotate-90': isCollapsed }"
            title="折叠/展开"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <button
            @click.stop="copyGroupTitle"
            class="text-muted hover:text-text p-1.5 rounded-md hover:bg-surface2 active:scale-95"
            title="复制组待办"
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
            v-if="!todo.completed"
            @click="handleAddItem"
            class="text-muted hover:text-text p-1.5 rounded-md hover:bg-surface2 active:scale-95"
            title="添加待办"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </button>
          <button
            @click="$emit('delete', todo.id)"
            class="text-red-500 hover:text-red-400 p-1.5 rounded-md hover:bg-red-500/10 active:scale-95"
            title="删除组"
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
              class="absolute right-0 mt-2 w-36 rounded-xl border border-border bg-surface shadow-float p-2 flex flex-col gap-1 z-10"
            >
              <button
                @click.stop="handleMobileToggleCollapse"
                class="text-left text-sm px-2 py-1.5 rounded-md hover:bg-surface2"
              >
                {{ isCollapsed ? "展开" : "折叠" }}
              </button>
              <button
                @click.stop="handleMobileCopyGroupTitle"
                class="text-left text-sm px-2 py-1.5 rounded-md hover:bg-surface2"
              >
                复制组
              </button>
              <button
                v-if="!todo.completed"
                @click.stop="handleMobilePin"
                class="text-left text-sm px-2 py-1.5 rounded-md hover:bg-surface2"
              >
                {{ todo.is_pinned ? "取消置顶" : "置顶" }}
              </button>
              <button
                v-if="!todo.completed"
                @click.stop="handleMobileAddItem"
                class="text-left text-sm px-2 py-1.5 rounded-md hover:bg-surface2"
              >
                新增待办
              </button>
              <button
                @click.stop="handleMobileDeleteGroup"
                class="text-left text-sm px-2 py-1.5 rounded-md hover:bg-surface2 text-red-500"
              >
                删除组
              </button>
            </div>
          </transition>
        </div>
      </div>
    </div>
    
    <!-- 组内待办列表 -->
    <div v-if="!isCollapsed" class="space-y-2 p-3 bg-surface2">
      <div
        v-for="item in sortedGroupItems"
        :key="item.id"
        class="flex items-center gap-3 bg-surface px-3 py-2 rounded-lg min-h-[40px] group/item border border-border relative"
      >
        <input 
          type="checkbox" 
          :checked="item.completed" 
          @change="$emit('toggle-item', item.id)" 
          class="flex-shrink-0 cursor-pointer"
        />
        <span v-if="item.is_ai_generated" class="text-muted flex-shrink-0" title="AI生成">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3l1.8 4.8L19 9l-4.2 2.7L16 16l-4-2.6L8 16l1.2-4.3L5 9l5.2-1.2L12 3z" />
          </svg>
        </span>
        <textarea
          v-model="editingItems[item.id]"
          @blur="finishEditItem(item.id)"
          @keydown.esc="cancelEditItem(item.id)"
          @keydown.enter.prevent="handleItemEnter(item.id)"
          @input="handleItemInput(item.id)"
          :ref="el => setItemInputRef(item.id, el)"
          :class="{ 'line-through text-muted': item.completed }"
          :placeholder="item.completed ? '' : '（待输入）'"
          :readonly="item.completed"
          class="flex-1 text-sm bg-transparent border-none outline-none px-0 py-0 cursor-text focus:ring-0 resize-none whitespace-pre-wrap break-words"
          rows="1"
        ></textarea>
        <div class="hidden sm:flex items-center gap-2 transition-opacity md:opacity-0 md:group-hover/item:opacity-100">
          <button
            @click.stop="copyGroupItem(item.id)"
            class="text-muted hover:text-text p-1.5 rounded-md hover:bg-surface2 active:scale-95 transition-opacity flex-shrink-0"
            title="复制待办"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>
          <button
            @click="$emit('delete-item', item.id)"
            class="text-red-500 hover:text-red-400 p-1.5 rounded-md hover:bg-red-500/10 active:scale-95 transition-opacity flex-shrink-0"
            title="删除待办"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
        <div :ref="el => setItemMenuRef(item.id, el)" class="relative flex-shrink-0 sm:hidden">
          <button
            class="text-muted hover:text-text px-2 py-1.5 rounded-md border border-border bg-surface2 active:scale-95"
            @click.stop="toggleItemMenu(item.id)"
          >
            {{ activeItemMenuId === item.id ? ">" : "…" }}
          </button>
          <transition name="fade">
            <div
              v-if="activeItemMenuId === item.id"
              class="absolute right-0 mt-2 w-28 rounded-xl border border-border bg-surface shadow-float p-2 flex flex-col gap-1 z-10"
            >
              <button
                @click.stop="handleItemMenuCopy(item.id)"
                class="text-left text-sm px-2 py-1.5 rounded-md hover:bg-surface2"
              >
                复制
              </button>
              <button
                @click.stop="handleItemMenuDelete(item.id)"
                class="text-left text-sm px-2 py-1.5 rounded-md hover:bg-surface2 text-red-500"
              >
                删除
              </button>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from "vue";
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
  "add-item": [groupId: number];
  "update-item-title": [id: number, title: string];
  "toggle-item": [id: number];
  "delete-item": [id: number];
}>();

const isCollapsed = ref(false);
const editTitle = ref(props.todo.title);
const titleInputRef = ref<HTMLInputElement | null>(null);
const editingItems = ref<Record<number, string>>({});
const itemInputRefs = ref<Record<number, HTMLTextAreaElement | null>>({});
const focusOnNextNewItem = ref(false);
const toast = useToastStore();
const mobileActionsOpen = ref(false);
const mobileMenuRef = ref<HTMLElement | null>(null);
const mobileMenuId = computed(() => `todo-group-${props.todo.id}`);
const activeItemMenuId = ref<number | null>(null);
const itemMenuRefs = ref<Record<number, HTMLElement | null>>({});
// 记录之前的待办 ID 列表，用于检测新添加的待办
const previousItemIds = ref<Set<number>>(new Set());

// 排序后的组内待办（按创建时间正序，最新的在下面）
const sortedGroupItems = computed(() => {
  if (!props.todo.group_items) return [];
  return [...props.todo.group_items].sort((a, b) => {
    const timeA = new Date(a.created_at).getTime();
    const timeB = new Date(b.created_at).getTime();
    return timeA - timeB; // 正序：旧的在上，新的在下
  });
});

// 监听组标题的变化
watch(() => props.todo.title, (newTitle) => {
  editTitle.value = newTitle;
});

const finishEditTitle = () => {
  if (props.todo.completed) return; // 已完成的不能编辑
  if (editTitle.value.trim() && editTitle.value !== props.todo.title) {
    emit("update-title", props.todo.id, editTitle.value.trim());
  } else {
    // 如果内容为空或未改变，恢复原值
    editTitle.value = props.todo.title;
  }
};

const cancelEditTitle = () => {
  editTitle.value = props.todo.title;
};

const handleAddItem = () => {
  focusOnNextNewItem.value = true;
  emit("add-item", props.todo.id);
};

/**
 * 自动调整子待办输入框高度以适配内容。
 */
const resizeItemTextarea = (id: number) => {
  const el = itemInputRefs.value[id];
  if (!el) return;
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight}px`;
};

/**
 * 批量调整所有子待办输入框高度。
 */
const resizeAllItemTextareas = () => {
  Object.keys(itemInputRefs.value).forEach((key) => {
    const id = Number(key);
    if (!Number.isNaN(id)) {
      resizeItemTextarea(id);
    }
  });
};

/**
 * 处理子待办输入变化时的高度更新。
 */
const handleItemInput = (id: number) => {
  resizeItemTextarea(id);
};

/**
 * 切换移动端更多操作菜单。
 */
const toggleMobileActions = () => {
  const nextValue = !mobileActionsOpen.value;
  mobileActionsOpen.value = nextValue;
  if (nextValue) {
    activeItemMenuId.value = null;
  }
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

const copyGroupTitle = async () => {
  const title = (props.todo.title || "").trim();
  const items = (props.todo.group_items || [])
    .map(item => (item.title || "").trim())
    .filter(Boolean);
  const lines = title ? [title, ...items.map(item => `- ${item}`)] : items.map(item => `- ${item}`);
  if (lines.length === 0) return;
  const text = lines.join("\n");
  try {
    await navigator.clipboard.writeText(text);
    toast.success("组待办已复制");
  } catch {
    toast.error("复制失败，请重试");
  }
};

/**
 * 处理点击空白关闭菜单。
 */
const handleDocumentClick = (event: MouseEvent) => {
  const target = event.target as Node | null;
  if (!target) return;
  if (mobileActionsOpen.value && mobileMenuRef.value && mobileMenuRef.value.contains(target)) return;
  const activeItemId = activeItemMenuId.value;
  if (activeItemId !== null) {
    const menuRef = itemMenuRefs.value[activeItemId];
    if (menuRef && menuRef.contains(target)) return;
  }
  closeMobileActions();
  activeItemMenuId.value = null;
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
  activeItemMenuId.value = null;
};

/**
 * 移动端切换折叠状态。
 */
const handleMobileToggleCollapse = () => {
  closeMobileActions();
  isCollapsed.value = !isCollapsed.value;
};

/**
 * 移动端复制组待办。
 */
const handleMobileCopyGroupTitle = async () => {
  closeMobileActions();
  await copyGroupTitle();
};

/**
 * 移动端切换置顶状态。
 */
const handleMobilePin = () => {
  closeMobileActions();
  emit("pin", props.todo.id);
};

/**
 * 移动端新增组内待办。
 */
const handleMobileAddItem = () => {
  closeMobileActions();
  handleAddItem();
};

/**
 * 移动端删除组待办。
 */
const handleMobileDeleteGroup = () => {
  closeMobileActions();
  emit("delete", props.todo.id);
};

const setItemMenuRef = (id: number, el: HTMLElement | null) => {
  if (!el) {
    delete itemMenuRefs.value[id];
    return;
  }
  itemMenuRefs.value[id] = el;
};

const toggleItemMenu = (id: number) => {
  activeItemMenuId.value = activeItemMenuId.value === id ? null : id;
  if (activeItemMenuId.value !== null) {
    closeMobileActions();
  }
};

const handleItemMenuCopy = async (id: number) => {
  activeItemMenuId.value = null;
  await copyGroupItem(id);
};

const handleItemMenuDelete = (id: number) => {
  activeItemMenuId.value = null;
  emit("delete-item", id);
};

const copyGroupItem = async (itemId: number) => {
  const item = props.todo.group_items?.find(target => target.id === itemId);
  const text = (item?.title || "").trim();
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    toast.success("待办已复制");
  } catch {
    toast.error("复制失败，请重试");
  }
};

// 设置输入框引用
const setItemInputRef = (itemId: number, el: any) => {
  if (el && el instanceof HTMLTextAreaElement) {
    itemInputRefs.value[itemId] = el;
  } else if (el && '$el' in el && el.$el instanceof HTMLTextAreaElement) {
    itemInputRefs.value[itemId] = el.$el;
  }
  resizeItemTextarea(itemId);
};

// 初始化组内待办的编辑状态
const initializeItemEditing = () => {
  if (props.todo.group_items) {
    props.todo.group_items.forEach(item => {
      editingItems.value[item.id] = item.title || "";
    });
  }
};

// 监听组内待办的变化
watch(() => props.todo.group_items, (newItems: typeof props.todo.group_items) => {
  if (newItems) {
    const currentItemIds = new Set(newItems.map(item => item.id));
    
    // 检测是否有新待办添加（通过比较 ID 集合）
    const hasNewItem = newItems.length > previousItemIds.value.size || 
      [...currentItemIds].some(id => !previousItemIds.value.has(id));
    
    newItems.forEach((item) => {
      if (!(item.id in editingItems.value)) {
        editingItems.value[item.id] = item.title || "";
      } else {
        // 如果已存在，同步更新值
        editingItems.value[item.id] = item.title || "";
      }
    });
    
    if (focusOnNextNewItem.value && !hasNewItem) {
      focusOnNextNewItem.value = false;
    }

    // 当有新待办添加时，尝试聚焦到最后一个（仅限用户主动新增）
    if (hasNewItem && focusOnNextNewItem.value && newItems.length > 0) {
      focusOnNextNewItem.value = false;
      nextTick(() => {
        // 按创建时间排序，找到最新的（最后一个）
        const sorted = [...newItems].sort((a, b) => {
          const timeA = new Date(a.created_at).getTime();
          const timeB = new Date(b.created_at).getTime();
          return timeA - timeB; // 正序
        });
        const lastItem = sorted[sorted.length - 1];

        // 使用重试机制确保 ref 已设置
        const tryFocus = (attempts = 0) => {
          setTimeout(() => {
            const input = itemInputRefs.value[lastItem.id];
            if (input) {
              input.focus();
              const length = input.value.length;
              input.setSelectionRange(length, length);
            } else if (attempts < 5) {
              tryFocus(attempts + 1);
            }
          }, attempts === 0 ? 100 : 50);
        };
        tryFocus();
      });
    }

    // 更新记录的 ID 集合
    previousItemIds.value = currentItemIds;
  }
}, { deep: true });

const finishEditItem = (itemId: number) => {
  const item = props.todo.group_items?.find(i => i.id === itemId);
  if (!item || item.completed) return; // 已完成的不能编辑
  
  const title = editingItems.value[itemId]?.trim() || "";
  if (title && title !== item.title) {
    emit("update-item-title", itemId, title);
  } else if (!title && item.title) {
    // 如果内容为空但原值不为空，恢复原值
    editingItems.value[itemId] = item.title;
  }
};

const cancelEditItem = (itemId: number) => {
  const item = props.todo.group_items?.find(i => i.id === itemId);
  if (item) {
    editingItems.value[itemId] = item.title || "";
  }
};

// 处理组内待办回车：保存当前待办并创建新待办
const handleItemEnter = async (itemId: number) => {
  const title = editingItems.value[itemId]?.trim() || "";
  
  // 如果当前待办有内容，先保存（异步等待保存完成）
  if (title) {
    emit("update-item-title", itemId, title);
    // 等待一个 tick 确保更新完成
    await nextTick();
  }
  
  // 创建新待办（由本组件决定是否需要聚焦新待办）
  focusOnNextNewItem.value = true;
  emit("add-item", props.todo.id);
};

// 监听全局事件：聚焦第一个待办
const handleFocusFirstItem = (event: CustomEvent) => {
  if (event.detail.groupId === props.todo.id && props.todo.group_items && props.todo.group_items.length > 0) {
    nextTick(() => {
      const firstItem = props.todo.group_items![0];
      const input = itemInputRefs.value[firstItem.id];
      input?.focus();
      // 将光标移到末尾
      if (input) {
        const length = input.value.length;
        input.setSelectionRange(length, length);
      }
    });
  }
};

// 监听全局事件：聚焦最后一个待办
const handleFocusLastItem = (event: CustomEvent) => {
  if (event.detail.groupId === props.todo.id) {
    // 使用多次 nextTick 和 setTimeout 确保 DOM 和数据都更新完成
    nextTick(() => {
      setTimeout(() => {
        nextTick(() => {
          if (props.todo.group_items && props.todo.group_items.length > 0) {
            const lastItem = props.todo.group_items[props.todo.group_items.length - 1];
            // 尝试多次查找输入框，因为 ref 可能还没设置好
            const tryFocus = (attempts = 0) => {
              const input = itemInputRefs.value[lastItem.id];
              if (input) {
                input.focus();
                // 全选文本
                input.select();
              } else if (attempts < 5) {
                // 如果还没找到，再等一会儿重试
                setTimeout(() => tryFocus(attempts + 1), 50);
              }
            };
            tryFocus();
          }
        });
      }, 100);
    });
  }
  nextTick(() => {
    resizeAllItemTextareas();
  });
};

onMounted(() => {
  window.addEventListener('focus-first-item', handleFocusFirstItem as EventListener);
  window.addEventListener('focus-last-item', handleFocusLastItem as EventListener);
  document.addEventListener("click", handleDocumentClick, true);
  window.addEventListener("todo-mobile-menu-open", handleOtherMenuOpen as EventListener);
  window.addEventListener("resize", handleViewportResize);
  // 初始化组标题的编辑状态
  editTitle.value = props.todo.title;
  // 初始化组内待办的编辑状态
  initializeItemEditing();
  nextTick(() => {
    resizeAllItemTextareas();
  });
});

onUnmounted(() => {
  window.removeEventListener('focus-first-item', handleFocusFirstItem as EventListener);
  window.removeEventListener('focus-last-item', handleFocusLastItem as EventListener);
  document.removeEventListener("click", handleDocumentClick, true);
  window.removeEventListener("todo-mobile-menu-open", handleOtherMenuOpen as EventListener);
  window.removeEventListener("resize", handleViewportResize);
});

/**
 * 处理视口变化时的高度更新。
 */
const handleViewportResize = () => {
  resizeAllItemTextareas();
};
</script>

<style scoped>
/* 确保输入框没有黑边 */
input[type="text"],
textarea {
  @apply border-border;
}
</style>


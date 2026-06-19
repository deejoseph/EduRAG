import { create } from 'zustand';
import type { TopicCategory, HotTopic } from '../types/hotTopics';

interface HotTopicsState {
  // 分类列表
  categories: TopicCategory[];
  
  // 搜索结果
  topics: HotTopic[];
  
  // 筛选条件
  selectedCategory: string | undefined;
  
  // 收藏列表
  favorites: HotTopic[];
  favoritedTitles: Set<string>;
  showFavoritesOnly: boolean;
  
  // Actions
  setCategories: (categories: TopicCategory[]) => void;
  setTopics: (topics: HotTopic[]) => void;
  setSelectedCategory: (category: string | undefined) => void;
  setFavorites: (favorites: HotTopic[]) => void;
  addFavorite: (topic: HotTopic) => void;
  removeFavorite: (title: string) => void;
  setShowFavoritesOnly: (show: boolean) => void;
  reset: () => void;
}

const initialState = {
  categories: [],
  topics: [],
  selectedCategory: undefined,
  favorites: [],
  favoritedTitles: new Set<string>(),
  showFavoritesOnly: false,
};

const useHotTopicsStore = create<HotTopicsState>((set) => ({
  ...initialState,
  
  setCategories: (categories) => set({ categories }),
  
  setTopics: (topics) => set((state) => {
    // 去重：基于标题过滤已存在的话题
    const existingTitles = new Set(state.topics.map(t => t.title));
    const newTopics = topics.filter(t => !existingTitles.has(t.title));
    return { topics: [...state.topics, ...newTopics] };
  }),
  
  setSelectedCategory: (selectedCategory) => set({ selectedCategory }),
  
  setFavorites: (favorites) => set({ 
    favorites,
    favoritedTitles: new Set(favorites.map(t => t.title))
  }),
  
  addFavorite: (topic) => set((state) => ({
    favorites: [...state.favorites, topic],
    favoritedTitles: new Set([...state.favoritedTitles, topic.title])
  })),
  
  removeFavorite: (title) => set((state) => ({
    favorites: state.favorites.filter(t => t.title !== title),
    favoritedTitles: new Set([...state.favoritedTitles].filter(t => t !== title))
  })),
  
  setShowFavoritesOnly: (showFavoritesOnly) => set({ showFavoritesOnly }),
  
  reset: () => set(initialState),
}));

export default useHotTopicsStore;

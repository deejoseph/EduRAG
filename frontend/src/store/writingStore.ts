import { create } from 'zustand';
import type { Reference } from '../types/api';

interface WritingSession {
  // 当前步骤 0-3
  currentStep: number;
  setStep: (step: number) => void;

  // 步骤 1 产出
  topic: string;
  setTopic: (topic: string) => void;
  topicType: string;
  setTopicType: (t: string) => void;
  gradeLevel: string;
  setGradeLevel: (g: string) => void;
  analysisResult: string | null;
  setAnalysisResult: (r: string | null) => void;
  analysisRefs: Reference[];
  setAnalysisRefs: (refs: Reference[]) => void;

  // 步骤 2 产出
  thesis: string;
  setThesis: (t: string) => void;
  style: string;
  setStyle: (s: string) => void;
  wordCount: number;
  setWordCount: (w: number) => void;
  outlineResult: string | null;
  setOutlineResult: (r: string | null) => void;
  outlineRefs: Reference[];
  setOutlineRefs: (refs: Reference[]) => void;

  // 步骤 3 产出
  currentEssay: string;
  setCurrentEssay: (text: string) => void;
  assistResult: string | null;
  setAssistResult: (r: string | null) => void;

  // 步骤 4 产出
  evaluationResult: string | null;
  setEvaluationResult: (r: string | null) => void;
  evaluationRefs: Reference[];
  setEvaluationRefs: (refs: Reference[]) => void;

  // 重置
  reset: () => void;
}

const initialState = {
  currentStep: 0,
  topic: '',
  topicType: '材料作文',
  gradeLevel: '高中',
  analysisResult: null,
  analysisRefs: [],
  thesis: '',
  style: '议论文',
  wordCount: 800,
  outlineResult: null,
  outlineRefs: [],
  currentEssay: '',
  assistResult: null,
  evaluationResult: null,
  evaluationRefs: [],
};

export const useWritingStore = create<WritingSession>((set) => ({
  ...initialState,

  setStep: (step) => set({ currentStep: step }),
  setTopic: (topic) => set({ topic }),
  setTopicType: (topicType) => set({ topicType }),
  setGradeLevel: (gradeLevel) => set({ gradeLevel }),
  setAnalysisResult: (analysisResult) => set({ analysisResult }),
  setAnalysisRefs: (analysisRefs) => set({ analysisRefs }),
  setThesis: (thesis) => set({ thesis }),
  setStyle: (style) => set({ style }),
  setWordCount: (wordCount) => set({ wordCount }),
  setOutlineResult: (outlineResult) => set({ outlineResult }),
  setOutlineRefs: (outlineRefs) => set({ outlineRefs }),
  setCurrentEssay: (currentEssay) => set({ currentEssay }),
  setAssistResult: (assistResult) => set({ assistResult }),
  setEvaluationResult: (evaluationResult) => set({ evaluationResult }),
  setEvaluationRefs: (evaluationRefs) => set({ evaluationRefs }),
  reset: () => set(initialState),
}));
